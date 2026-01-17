package io.github.sharmanish.schemasculpt.service;

import io.github.sharmanish.schemasculpt.entity.OperationMockData;
import io.github.sharmanish.schemasculpt.entity.OperationTestCases;
import io.github.sharmanish.schemasculpt.entity.Project;
import io.github.sharmanish.schemasculpt.entity.Specification;
import io.github.sharmanish.schemasculpt.entity.TestDataGenerationHistory;
import io.github.sharmanish.schemasculpt.entity.User;
import io.github.sharmanish.schemasculpt.repository.OperationMockDataRepository;
import io.github.sharmanish.schemasculpt.repository.OperationTestCasesRepository;
import io.github.sharmanish.schemasculpt.repository.TestDataGenerationHistoryRepository;
import io.github.sharmanish.schemasculpt.exception.MockDataGenerationException;
import io.github.sharmanish.schemasculpt.exception.SpecificationProcessingException;
import io.github.sharmanish.schemasculpt.exception.TestGenerationException;
import io.github.sharmanish.schemasculpt.service.ai.AIService;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Slf4j
public class TestDataService {

  private final AIService aiService;
  private final OperationTestCasesRepository testCasesRepository;
  private final OperationMockDataRepository mockDataRepository;
  private final TestDataGenerationHistoryRepository historyRepository;

  public TestDataService(
      AIService aiService,
      OperationTestCasesRepository testCasesRepository,
      OperationMockDataRepository mockDataRepository,
      TestDataGenerationHistoryRepository historyRepository) {
    this.aiService = Objects.requireNonNull(aiService, "aiService must not be null");
    this.testCasesRepository =
        Objects.requireNonNull(testCasesRepository, "testCasesRepository must not be null");
    this.mockDataRepository =
        Objects.requireNonNull(mockDataRepository, "mockDataRepository must not be null");
    this.historyRepository =
        Objects.requireNonNull(historyRepository, "historyRepository must not be null");
  }

  /**
   * Generate or retrieve cached test cases for an operation. Implements two-level caching: DB
   * (persistent) + AI service in-memory cache.
   */
  @Transactional
  public Map<String, Object> generateTestCases(
      Map<String, Object> request, Project project, Specification specification, User user) {

    long startTime = System.currentTimeMillis();
    String path = (String) request.get("path");
    String method = (String) request.get("method");
    String specText = (String) request.get("spec_text");
    Boolean includeAiTests = (Boolean) request.getOrDefault("include_ai_tests", true);

    String specHash = calculateSpecHash(specText);

    try {
      // Check database cache first
      Optional<OperationTestCases> cachedTests =
          testCasesRepository.findByProject_IdAndPathAndMethod(project.getId(), path, method);

      if (cachedTests.isPresent()
          && MessageDigest.isEqual(
              cachedTests.get().getSpecHash().getBytes(), specHash.getBytes())) {
        log.info(
            "Found cached test cases in DB for {}/{} (project: {})", method, path, project.getId());

        // Record cache hit in history
        recordGenerationHistory(
            project,
            user,
            "test_cases",
            path,
            method,
            true,
            null,
            System.currentTimeMillis() - startTime,
            true);

        return Map.of(
            "test_cases",
            cachedTests.get().getTestCases(),
            "total_tests",
            cachedTests.get().getTotalTests(),
            "cached",
            true,
            "cache_source",
            "database");
      }

      // Generate new test cases via AI service (which has its own in-memory cache)
      log.info("Generating new test cases for {}/{} (project: {})", method, path, project.getId());

      Map<String, Object> generatedTests = aiService.generateTestCases(request);

      // Save to database for persistence
      OperationTestCases testCases = cachedTests.orElse(new OperationTestCases());
      testCases.setProject(project);
      testCases.setSpecification(specification);
      testCases.setPath(path);
      testCases.setMethod(method);
      testCases.setOperationSummary((String) request.get("operation_summary"));
      testCases.setTestCases(generatedTests.get("test_cases").toString());
      testCases.setIncludeAiTests(includeAiTests);
      testCases.setTotalTests((Integer) generatedTests.getOrDefault("total_tests", 0));
      testCases.setSpecHash(specHash);
      testCases.setCreatedBy(user);

      testCasesRepository.save(testCases);
      log.info("Saved test cases to database for {}/{}", method, path);

      // Record generation in history
      boolean wasAiCached = (Boolean) generatedTests.getOrDefault("cached", false);
      recordGenerationHistory(
          project,
          user,
          "test_cases",
          path,
          method,
          true,
          null,
          System.currentTimeMillis() - startTime,
          wasAiCached);

      generatedTests.put("cache_source", wasAiCached ? "ai_memory" : "generated");
      return generatedTests;

    } catch (Exception e) {
      log.error("Failed to generate test cases for {}/{}: {}", method, path, e.getMessage(), e);

      // Record failure in history
      recordGenerationHistory(
          project,
          user,
          "test_cases",
          path,
          method,
          false,
          e.getMessage(),
          System.currentTimeMillis() - startTime,
          false);

      throw new TestGenerationException("Test case generation failed", e);
    }
  }

  /** Calculate SHA-256 hash of specification text for change detection. */
  private String calculateSpecHash(String specText) {
    try {
      MessageDigest digest = MessageDigest.getInstance("SHA-256");
      byte[] hash = digest.digest(specText.getBytes(StandardCharsets.UTF_8));
      return HexFormat.of().formatHex(hash);
    } catch (NoSuchAlgorithmException e) {
      throw new SpecificationProcessingException("SHA-256 algorithm not available", e);
    }
  }

  /** Record test data generation attempt in history for analytics. */
  private void recordGenerationHistory(
      Project project,
      User user,
      String dataType,
      String path,
      String method,
      boolean success,
      String errorMessage,
      long durationMs,
      boolean cacheHit) {

    try {
      TestDataGenerationHistory history = new TestDataGenerationHistory();
      history.setProject(project);
      history.setDataType(dataType);
      history.setPath(path);
      history.setMethod(method);
      history.setSuccess(success);
      history.setErrorMessage(errorMessage);
      history.setGenerationTimeMs((int) durationMs);
      history.setCacheHit(cacheHit);
      history.setCreatedBy(user);

      historyRepository.save(history);
    } catch (Exception e) {
      // Don't fail the main operation if history recording fails
      log.warn("Failed to record generation history: {}", e.getMessage());
    }
  }

  /**
   * Generate or retrieve cached mock data variations for an operation. Implements two-level
   * caching: DB (persistent) + AI service in-memory cache.
   */
  @Transactional
  public Map<String, Object> generateMockDataVariations(
      Map<String, Object> request, Project project, Specification specification, User user) {

    long startTime = System.currentTimeMillis();
    String path = (String) request.get("path");
    String method = (String) request.get("method");
    String specText = (String) request.get("spec_text");
    String responseCode = (String) request.getOrDefault("response_code", "200");
    Integer count = (Integer) request.getOrDefault("count", 3);

    String specHash = calculateSpecHash(specText);

    try {
      // Check database cache first
      Optional<OperationMockData> cachedMock =
          mockDataRepository.findByProject_IdAndPathAndMethodAndResponseCode(
              project.getId(), path, method, responseCode);

      if (cachedMock.isPresent()
          && cachedMock.get().getSpecHash().equals(specHash)
          && cachedMock.get().getVariationCount().equals(count)) {

        log.info(
            "Found cached mock data in DB for {}/{} response {} (project: {})",
            method,
            path,
            responseCode,
            project.getId());

        // Record cache hit in history
        recordGenerationHistory(
            project,
            user,
            "mock_data",
            path,
            method,
            true,
            null,
            System.currentTimeMillis() - startTime,
            true);

        return Map.of(
            "variations",
            cachedMock.get().getMockVariations(),
            "count",
            cachedMock.get().getVariationCount(),
            "cached",
            true,
            "cache_source",
            "database");
      }

      // Generate new mock data via AI service endpoint
      log.info(
          "Generating new mock data for {}/{} response {} (project: {})",
          method,
          path,
          responseCode,
          project.getId());

      // Call AI service endpoint for mock data generation
      Map<String, Object> generatedMock = callAIServiceForMockData(request);

      // Save to database for persistence
      OperationMockData mockData = cachedMock.orElse(new OperationMockData());
      mockData.setProject(project);
      mockData.setSpecification(specification);
      mockData.setPath(path);
      mockData.setMethod(method);
      mockData.setResponseCode(responseCode);
      mockData.setMockVariations(generatedMock.get("variations").toString());
      mockData.setVariationCount(count);
      mockData.setSpecHash(specHash);
      mockData.setCreatedBy(user);

      mockDataRepository.save(mockData);
      log.info("Saved mock data to database for {}/{} response {}", method, path, responseCode);

      // Record generation in history
      boolean wasAiCached = (Boolean) generatedMock.getOrDefault("cached", false);
      recordGenerationHistory(
          project,
          user,
          "mock_data",
          path,
          method,
          true,
          null,
          System.currentTimeMillis() - startTime,
          wasAiCached);

      generatedMock.put("cache_source", wasAiCached ? "ai_memory" : "generated");
      return generatedMock;

    } catch (Exception e) {
      log.error(
          "Failed to generate mock data for {}/{} response {}: {}",
          method,
          path,
          responseCode,
          e.getMessage(),
          e);

      // Record failure in history
      recordGenerationHistory(
          project,
          user,
          "mock_data",
          path,
          method,
          false,
          e.getMessage(),
          System.currentTimeMillis() - startTime,
          false);

      throw new MockDataGenerationException("Mock data generation failed", e);
    }
  }

  /**
   * Call AI service endpoint for mock data generation. This is a placeholder - should call the
   * actual endpoint when available.
   */
  private Map<String, Object> callAIServiceForMockData(Map<String, Object> request) {
    // TODO: Implement actual AI service call for mock data generation
    // For now, return a simple response structure
    log.warn("Mock data generation endpoint not yet implemented, returning placeholder");
    return Map.of("variations", "[]", "count", request.getOrDefault("count", 3), "cached", false);
  }

  /** Invalidate cached test data when specification changes. */
  @Transactional
  public void invalidateCache(Long projectId, String specText) {
    String newSpecHash = calculateSpecHash(specText);
    log.info(
        "Invalidating stale cache entries for project {} (new spec hash: {})",
        projectId,
        newSpecHash);

    // Note: We don't actually delete entries, just let the hash mismatch trigger regeneration
    // This preserves historical data for analytics
  }
}

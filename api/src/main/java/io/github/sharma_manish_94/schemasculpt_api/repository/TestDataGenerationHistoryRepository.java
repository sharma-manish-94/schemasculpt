package io.github.sharma_manish_94.schemasculpt_api.repository;

import io.github.sharma_manish_94.schemasculpt_api.entity.TestDataGenerationHistory;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;

@Repository
public interface TestDataGenerationHistoryRepository extends JpaRepository<TestDataGenerationHistory, Long> {

    List<TestDataGenerationHistory> findByProject_IdOrderByCreatedAtDesc(Long projectId);

    List<TestDataGenerationHistory> findByProject_IdAndDataTypeOrderByCreatedAtDesc(Long projectId, String dataType);

    List<TestDataGenerationHistory> findByCreatedAtAfterOrderByCreatedAtDesc(LocalDateTime after);

    @Query("SELECT AVG(h.generationTimeMs) FROM TestDataGenerationHistory h WHERE h.project.id = :projectId AND h.dataType = :dataType AND h.success = true")
    Double getAverageGenerationTime(Long projectId, String dataType);

    @Query("SELECT COUNT(h) FROM TestDataGenerationHistory h WHERE h.project.id = :projectId AND h.cacheHit = true")
    Long countCacheHits(Long projectId);

    @Query("SELECT COUNT(h) FROM TestDataGenerationHistory h WHERE h.project.id = :projectId AND h.cacheHit = false")
    Long countCacheMisses(Long projectId);
}

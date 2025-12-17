package io.github.sharmanish.schemasculpt.controller.project;

import io.github.sharmanish.schemasculpt.dto.specification.SaveSpecificationRequest;
import io.github.sharmanish.schemasculpt.dto.specification.SpecificationDTO;
import io.github.sharmanish.schemasculpt.dto.specification.SpecificationDetailDTO;
import io.github.sharmanish.schemasculpt.entity.Specification;
import io.github.sharmanish.schemasculpt.security.CustomOAuth2User;
import io.github.sharmanish.schemasculpt.service.SpecificationService;
import jakarta.validation.Valid;
import java.util.List;
import java.util.stream.Collectors;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * REST controller for specification version management
 */
@RestController
@RequestMapping("/api/v1/projects/{projectId}/specifications")
@Slf4j
public class SpecificationManagementController {

  private final SpecificationService specificationService;

  public SpecificationManagementController(SpecificationService specificationService) {
    this.specificationService = specificationService;
  }

  /**
   * Save a new version of the specification
   */
  @PostMapping
  public ResponseEntity<SpecificationDTO> saveSpecification(
      @AuthenticationPrincipal CustomOAuth2User principal,
      @PathVariable Long projectId,
      @Valid @RequestBody SaveSpecificationRequest request) {

    log.info("Saving new specification version for project {}", projectId);

    Specification spec =
        specificationService.saveSpecification(
            projectId,
            principal.getUserId(),
            request.specContent(),
            request.specFormat(),
            request.commitMessage());

    return ResponseEntity.status(HttpStatus.CREATED).body(new SpecificationDTO(spec));
  }

  /**
   * Get the current version of the specification
   */
  @GetMapping("/current")
  public ResponseEntity<SpecificationDetailDTO> getCurrentSpecification(
      @AuthenticationPrincipal CustomOAuth2User principal, @PathVariable Long projectId) {

    log.debug("Fetching current specification for project {}", projectId);

    Specification spec =
        specificationService.getCurrentSpecification(projectId, principal.getUserId());

    if (spec == null) {
      return ResponseEntity.notFound().build();
    }

    return ResponseEntity.ok(new SpecificationDetailDTO(spec));
  }

  /**
   * Get all versions of the specification
   */
  @GetMapping
  public ResponseEntity<List<SpecificationDTO>> getSpecificationVersions(
      @AuthenticationPrincipal CustomOAuth2User principal, @PathVariable Long projectId) {

    log.debug("Fetching all specification versions for project {}", projectId);

    List<SpecificationDTO> versions =
        specificationService.getSpecificationVersions(projectId, principal.getUserId()).stream()
            .map(SpecificationDTO::new)
            .collect(Collectors.toList());

    return ResponseEntity.ok(versions);
  }

  /**
   * Get a specific version of the specification
   */
  @GetMapping("/versions/{version}")
  public ResponseEntity<SpecificationDetailDTO> getSpecificationByVersion(
      @AuthenticationPrincipal CustomOAuth2User principal,
      @PathVariable Long projectId,
      @PathVariable String version) {

    log.debug("Fetching specification version {} for project {}", version, projectId);

    Specification spec =
        specificationService.getSpecificationByVersion(projectId, version, principal.getUserId());

    return ResponseEntity.ok(new SpecificationDetailDTO(spec));
  }

  /**
   * Revert to a previous version
   */
  @PostMapping("/versions/{version}/revert")
  public ResponseEntity<SpecificationDTO> revertToVersion(
      @AuthenticationPrincipal CustomOAuth2User principal,
      @PathVariable Long projectId,
      @PathVariable String version,
      @RequestParam(required = false) String commitMessage) {

    log.info("Reverting project {} to version {}", projectId, version);

    Specification spec =
        specificationService.revertToVersion(
            projectId, version, principal.getUserId(), commitMessage);

    return ResponseEntity.ok(new SpecificationDTO(spec));
  }
}

package io.github.sharma_manish_94.schemasculpt_api.dto.analysis;

import java.util.List;

public record ZombieApiResponse(
    List<ZombieEndpoint> shadowedEndpoints,
    List<String> orphanedOperations // "GET /placeholder"
) {
  public record ZombieEndpoint(
      String shadowedPath,   // e.g., "/users/current"
      String shadowingPath,  // e.g., "/users/{id}"
      String reason
  ) {
  }
}
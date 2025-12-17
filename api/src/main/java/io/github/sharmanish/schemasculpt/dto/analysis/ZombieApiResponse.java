package io.github.sharmanish.schemasculpt.dto.analysis;

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
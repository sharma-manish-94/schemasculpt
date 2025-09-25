package io.github.sharma_manish_94.schemasculpt_api.dto.ai;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.Map;

public record HealthResponse(
    String status,
    String version,
    @JsonProperty("uptime_seconds") Long uptimeSeconds,
    Map<String, String> dependencies,
    @JsonProperty("total_requests") Long totalRequests,
    @JsonProperty("average_response_time_ms") Double averageResponseTimeMs,
    @JsonProperty("error_rate") Double errorRate
) {
    public HealthResponse {
        if (uptimeSeconds == null) {
            uptimeSeconds = 0L;
        }
        if (totalRequests == null) {
            totalRequests = 0L;
        }
        if (averageResponseTimeMs == null) {
            averageResponseTimeMs = 0.0;
        }
        if (errorRate == null) {
            errorRate = 0.0;
        }
    }

    // Simple healthy response constructor
    public static HealthResponse healthy(String version) {
        return new HealthResponse("healthy", version, 0L, Map.of(), 0L, 0.0, 0.0);
    }

    // Simple unhealthy response constructor
    public static HealthResponse unhealthy(String version) {
        return new HealthResponse("unhealthy", version, 0L, Map.of(), 0L, 0.0, 1.0);
    }
}
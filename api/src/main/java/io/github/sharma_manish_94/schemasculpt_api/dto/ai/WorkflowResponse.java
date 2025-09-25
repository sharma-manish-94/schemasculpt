package io.github.sharma_manish_94.schemasculpt_api.dto.ai;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.time.Instant;
import java.util.List;
import java.util.Map;

public record WorkflowResponse(
    @JsonProperty("workflow_id") String workflowId,
    @JsonProperty("workflow_name") String workflowName,
    String status,
    Object result,
    @JsonProperty("execution_time_ms") Long executionTimeMs,
    @JsonProperty("steps_completed") Integer stepsCompleted,
    @JsonProperty("total_steps") Integer totalSteps,
    @JsonProperty("error_message") String errorMessage,
    @JsonProperty("created_at") Instant createdAt,
    @JsonProperty("completed_at") Instant completedAt,
    Map<String, Object> metadata
) {
    public WorkflowResponse {
        if (createdAt == null) {
            createdAt = Instant.now();
        }
        if (status == null) {
            status = "completed";
        }
        if (stepsCompleted == null) {
            stepsCompleted = 0;
        }
        if (totalSteps == null) {
            totalSteps = 1;
        }
    }

    // Constructor for successful workflow completion
    public static WorkflowResponse success(String workflowName, Object result, Long executionTime) {
        return new WorkflowResponse(null, workflowName, "completed", result,
                                  executionTime, 1, 1, null, Instant.now(),
                                  Instant.now(), null);
    }

    // Constructor for failed workflow
    public static WorkflowResponse failed(String workflowName, String errorMessage) {
        return new WorkflowResponse(null, workflowName, "failed", null,
                                  null, 0, 1, errorMessage, Instant.now(),
                                  null, null);
    }
}
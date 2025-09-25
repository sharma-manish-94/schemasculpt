package io.github.sharma_manish_94.schemasculpt_api.dto.ai;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.time.Instant;
import java.util.List;
import java.util.Map;

public record SessionContextResponse(
    @JsonProperty("session_id") String sessionId,
    @JsonProperty("user_id") String userId,
    @JsonProperty("created_at") Instant createdAt,
    @JsonProperty("last_activity") Instant lastActivity,
    @JsonProperty("conversation_turns") Integer conversationTurns,
    @JsonProperty("session_summary") Map<String, Object> sessionSummary,
    List<String> suggestions,
    @JsonProperty("context_statistics") Map<String, Object> contextStatistics
) {
    public SessionContextResponse {
        if (createdAt == null) {
            createdAt = Instant.now();
        }
        if (lastActivity == null) {
            lastActivity = Instant.now();
        }
        if (conversationTurns == null) {
            conversationTurns = 0;
        }
    }
}
package io.github.sharma_manish_94.schemasculpt_api.service.fix;

import io.github.sharma_manish_94.schemasculpt_api.dto.QuickFixRequest;
import io.github.sharma_manish_94.schemasculpt_api.service.SessionService;
import io.swagger.v3.oas.models.OpenAPI;
import org.springframework.context.annotation.Primary;
import org.springframework.stereotype.Service;

import java.util.Arrays;
import java.util.List;

@Service
@Primary
public class EnhancedQuickFixService {

    private final SessionService sessionService;
    private final QuickFixService quickFixService;
    private final AIEnhancedFixService aiEnhancedFixService;

    // Define which rules require AI processing
    private static final List<String> AI_REQUIRED_RULES = Arrays.asList(
        "add-api-description", "add-operation-description", "add-parameter-description",
        "add-schema-description", "add-property-description", "add-schema-example",
        "add-response-example", "add-operation-summary", "add-operation-tags"
    );

    public EnhancedQuickFixService(SessionService sessionService,
                                  QuickFixService quickFixService,
                                  AIEnhancedFixService aiEnhancedFixService) {
        this.sessionService = sessionService;
        this.quickFixService = quickFixService;
        this.aiEnhancedFixService = aiEnhancedFixService;
    }

    public OpenAPI applyFix(String sessionId, QuickFixRequest request) {
        // Check if this fix requires AI processing
        boolean requiresAI = AI_REQUIRED_RULES.contains(request.ruleId());

        if (requiresAI) {
            // Delegate to AI service for complex fixes
            return aiEnhancedFixService.applyAIFix(sessionId, request);
        } else {
            // Handle with deterministic fixes
            return quickFixService.applyFix(sessionId, request);
        }
    }

    public boolean isAIRequiredRule(String ruleId) {
        return AI_REQUIRED_RULES.contains(ruleId);
    }
}
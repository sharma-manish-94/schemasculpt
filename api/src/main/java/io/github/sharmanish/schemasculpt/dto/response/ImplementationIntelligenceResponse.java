package io.github.sharmanish.schemasculpt.dto.response;

import io.github.sharmanish.schemasculpt.dto.analysis.AuthVerificationResponse;
import io.github.sharmanish.schemasculpt.dto.analysis.ContractVerificationResponse;
import java.util.List;

public record ImplementationIntelligenceResponse(
    ImplementationCodeResponse implementation,
    ContractVerificationResponse contractVerification,
    AuthVerificationResponse authVerification,
    List<String> callStack) {}

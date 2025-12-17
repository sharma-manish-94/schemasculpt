package io.github.sharmanish.schemasculpt.service;

import io.github.sharmanish.schemasculpt.dto.request.UpdateOperationRequest;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.Operation;
import io.swagger.v3.oas.models.PathItem;
import org.apache.commons.lang3.StringUtils;
import org.springframework.stereotype.Service;

@Service
public class SpecUpdateService {
  private final SessionService sessionService;

  public SpecUpdateService(SessionService sessionService) {
    this.sessionService = sessionService;
  }

  public void updateOperation(String sessionId, UpdateOperationRequest request) {
    OpenAPI openAPI = sessionService.getSpecForSession(sessionId);
    if (null == openAPI) {
      throw new IllegalArgumentException("Invalid session ID: " + sessionId);
    }
    Operation operation =
        openAPI
            .getPaths()
            .get(request.path())
            .readOperationsMap()
            .get(PathItem.HttpMethod.valueOf(request.method().toUpperCase()));

    if (null != operation) {
      if (StringUtils.isNotBlank(request.summary())) {
        operation.setSummary(request.summary());
      }
      if (StringUtils.isNotBlank(request.description())) {
        operation.setDescription(request.description());
      }
    }
    sessionService.updateSessionSpec(sessionId, openAPI);
  }
}

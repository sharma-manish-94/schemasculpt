export function buildRequestDetails(endpoint, requestState) {
  const { serverTarget, mockServer, customServerUrl, pathParams, requestBody } =
    requestState;

  if (!endpoint) {
    return { error: "No endpoint selected." };
  }

  let baseUrl = serverTarget === "mock" ? mockServer.url : customServerUrl;
  if ((serverTarget === "mock" && !mockServer.active) || !baseUrl) {
    return { error: "Please configure a target server URL." };
  }

  // Replace path parameters in the URL
  let finalUrl = baseUrl + endpoint.path;
  for (const paramName in pathParams) {
    finalUrl = finalUrl.replace(`{${paramName}}`, pathParams[paramName] || "");
  }

  return {
    error: null,
    request: {
      method: endpoint.method,
      url: finalUrl,
      headers: { "Content-Type": "application/json" },
      body: requestBody || null,
    },
  };
}

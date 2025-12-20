import yaml from "js-yaml";

export function parseEndpointsFromSpec(specText) {
  try {
    const specObject = yaml.load(specText);
    const validMethods = new Set([
      "get",
      "post",
      "put",
      "delete",
      "patch",
      "options",
      "head",
    ]);

    if (!specObject?.paths) {
      return [];
    }

    return Object.entries(specObject.paths).flatMap(([path, pathItem]) =>
      Object.entries(pathItem)
        .filter(([method]) => validMethods.has(method.toLowerCase()))
        .map(([method, details]) => ({
          path,
          method: method.toUpperCase(),
          details,
        })),
    );
  } catch (e) {
    console.error(e);
    return [];
  }
}

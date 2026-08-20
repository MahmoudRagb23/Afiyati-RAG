export const SUPPORTED_CONDITION_VALUES = new Set([
  "hypertension",
  "type_2_diabetes",
]);

export function supportedConditions(values = []) {
  return [...new Set(values.filter((value) => SUPPORTED_CONDITION_VALUES.has(value)))];
}

export function getRiskLabel(score) {
  if (score > 0.6) return "High Risk";
  if (score > 0.3) return "Medium Risk";
  return "Low Risk";
}

export function getRiskClass(score) {
  if (score > 0.6) return "high";
  if (score > 0.3) return "medium";
  return "low";
}
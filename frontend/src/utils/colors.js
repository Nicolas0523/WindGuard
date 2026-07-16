export const RISK_COLORS = {
  low: "#10b981",    // Emerald Green
  medium: "#f59e0b", // Amber Orange
  high: "#ef4444",   // Rose Red
};

export function getRiskColor(score) {
  if (score > 0.6) return RISK_COLORS.high;
  if (score > 0.3) return RISK_COLORS.medium;
  return RISK_COLORS.low;
}
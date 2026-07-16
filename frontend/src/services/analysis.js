import { postRequest } from "./api";

export async function runSoilAnalysis(geometry, type, startDate, endDate) {
  let endpoint = "/analyze";
  if (type === "forecast") endpoint = "/analyze/short";
  if (type === "climate") endpoint = "/analyze/climate";

  return postRequest(endpoint, {
    geometry,
    start_date: startDate,
    end_date: endDate,
  });
}
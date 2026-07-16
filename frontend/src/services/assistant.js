import { postRequest } from "./api";

export async function askAssistant(question, context) {
  return postRequest("/assistant", { question, context });
}
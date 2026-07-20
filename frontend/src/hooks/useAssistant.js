import { useState } from "react";
import { api } from "../services/api";

export function useAssistant(context) {
  const [answer, setAnswer] = useState("Draw an area and generate an analysis. Then, you can ask WindGuard AI questions about the soil conditions of this territory.");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const askQuestion = async (question) => {
    if (!question.trim()) return;

    setLoading(true);
    setError(null);
    setAnswer("Thinking...");

    try {
      const data = await api.askAssistant(question, context || {});
      
      if (data && data.response) {
        setAnswer(data.response);
      } else if (data && data.error) {
        setAnswer(`Error: ${data.error}`);
      } else {
        setAnswer("I couldn't process that. Please try again.");
      }
    } catch (err) {
      console.error("AI Assistant request failed:", err);
      setError(err.message);
      setAnswer("Failed to connect to the AI service. Make sure backend is running.");
    } finally {
      setLoading(false);
    }
  };

  return {
    answer,
    loading,
    error,
    askQuestion,
  };
}
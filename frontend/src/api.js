const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");

export async function calculate(query, calculator) {
  const response = await fetch(`${API_BASE_URL}/api/v1/calculate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, calculator: calculator || null }),
  });

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = data?.detail;
    const questions = Array.isArray(detail?.questions) ? detail.questions.join(" ") : "";
    const message = typeof detail === "string" ? detail : questions || detail?.message;
    throw new Error(message || "The calculation could not be completed.");
  }
  return data;
}

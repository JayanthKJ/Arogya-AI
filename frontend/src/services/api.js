/**
 * api.js — Arogya AI service layer
 * Swap BASE_URL and endpoint for your real backend.
 * Currently returns mock responses for local development.
 */

const BASE_URL = import.meta.env.VITE_API_URL || "";
const USE_MOCK = !BASE_URL;

// ------------------------------------------------------------------
// Mock responses (used when VITE_API_URL is not set)
// ------------------------------------------------------------------
const MOCK_RESPONSES = [
  "Thank you for your question. Based on what you've shared, staying well-hydrated, getting adequate rest, and monitoring your symptoms is important. If symptoms persist beyond 2–3 days, please consult your doctor in person.",
  "That is a common concern. A balanced diet rich in vegetables, whole grains, and lean proteins helps greatly. Reducing processed foods and sugar also makes a significant difference for long-term wellness.",
  "Blood pressure fluctuations can often be managed with lifestyle changes — regular light exercise like morning walks, reducing salt intake, and practicing slow deep-breathing for 10 minutes daily.",
  "For joint or knee discomfort, gentle leg-raise exercises and warm-water therapy are commonly recommended. A physiotherapist can design a routine suited to your specific condition.",
  "Sleep difficulties are very common. A consistent sleep schedule, avoiding screens one hour before bed, and a warm glass of turmeric milk or chamomile tea can significantly improve rest quality.",
  "I understand your concern. It is always wise to keep a record of your symptoms with dates and share them with your physician. Would you like me to help you prepare a symptom summary?",
];

let mockIndex = 0;

function getMockResponse() {
  const response = MOCK_RESPONSES[mockIndex % MOCK_RESPONSES.length];
  mockIndex++;
  return response;
}

// ------------------------------------------------------------------
// Real API call
// ------------------------------------------------------------------
async function callAPI(messages) {
  const response = await fetch(`${BASE_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.message || `Server error: ${response.status}`);
  }

  const data = await response.json();
  return data.reply || data.message || data.content || "";
}

// ------------------------------------------------------------------
// Exported function — used by useChat hook
// ------------------------------------------------------------------
/**
 * sendMessage
 * @param {Array<{role: "user"|"assistant", text: string}>} messageHistory
 * @returns {Promise<string>} AI reply text
 */
export async function sendMessage(messageHistory) {
  if (USE_MOCK) {
    // Simulate realistic network latency
    await new Promise((resolve) =>
      setTimeout(resolve, 1400 + Math.random() * 900)
    );
    return getMockResponse();
  }

  const formatted = messageHistory.map((m) => ({
    role: m.role === "ai" ? "assistant" : "user",
    content: m.text,
  }));

  return callAPI(formatted);
}

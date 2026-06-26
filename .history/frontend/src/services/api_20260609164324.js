/**
 * api.js — Arogya AI service layer
 * Swap BASE_URL and endpoint for your real backend.
 * Currently returns mock responses for local development.
 */

const ENV_API_URL = import.meta.env.VITE_API_URL;
const BASE_URL = ENV_API_URL || "http://localhost:8000";
const USE_MOCK = !ENV_API_URL;

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

const getAuthHeader = () => {
  const token = localStorage.getItem("auth_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export const authAPI = {
  async signup(email, password) {
    const response = await fetch(`${BASE_URL}/auth/signup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || "Signup failed");
    }

    return response.json();
  },

  async login(email, password) {
    const response = await fetch(`${BASE_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Login failed");
    }

    const data = await response.json();
    localStorage.setItem("auth_token", data.access_token);
    return data;
  },

  logout() {
    localStorage.removeItem("auth_token");
  },

  isAuthenticated() {
    return !!localStorage.getItem("auth_token");
  },
};

// Helper function to create a delay
const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

export const chatAPI = {
  // Sends a user message to the backend
  async sendMessage(message, sessionId) {
    if (USE_MOCK) {
      await delay(1400 + Math.random() * 900);
      return { reply: getMockResponse() };
    }

    // Delay to simulate processing or thinking time
    await delay(500);

    const response = await fetch(`${BASE_URL}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeader(),
      },
      body: JSON.stringify({ message, session_id: sessionId }),
    });

    if (!response.ok) {
      if (response.status === 401) {
        authAPI.logout();
        throw new Error("Session expired. Please login again.");
      }
      const error = await response.json();
      throw new Error(error.detail || "Failed to send message");
    }

    return response.json();
  },

  // Receives specific chat history from the backend
  async getHistory(sessionId) {
    if (USE_MOCK) {
      await delay(500);
      return [];
    }

    const response = await fetch(`${BASE_URL}/chat/history/${sessionId}`, {
      method: "GET",
      headers: {
        ...getAuthHeader(),
      },
    });

    if (!response.ok) {
      if (response.status === 401) {
        authAPI.logout();
        throw new Error("Session expired. Please login again.");
      }
      const error = await response.json();
      throw new Error(error.detail || "Failed to fetch history");
    }

    return response.json();
  },

  // Receives all chat history from the backend
  async getSessions() {
    if (USE_MOCK) {
    await delay(300);
    return [];
    }

    const response = await fetch(`${BASE_URL}/chat/sessions`, {
    method: "GET",
    headers: {
    ...getAuthHeader(),
    },
    });

    if (!response.ok) {
    if (response.status === 401) {
    authAPI.logout();
    throw new Error("Session expired. Please login again.");
    }

    ```
    const error = await response.json();
    throw new Error(error.detail || "Failed to fetch sessions");
    ```

    }

    return response.json();
  },
};
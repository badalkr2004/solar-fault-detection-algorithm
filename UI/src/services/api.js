import axios from "axios";

const API_BASE_URL =
  import.meta.env.REACT_APP_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log("Making request to:", config.url);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error("API Error:", error);
    return Promise.reject(error);
  }
);

export const solarAPI = {
  // Health check
  healthCheck: () => api.get("/health"),

  // Generate sample data
  generateSampleData: (params = {}) => {
    const { num_days = 30, num_inverters = 5, include_faults = true } = params;
    return api.post("/generate-sample-data", null, {
      params: { num_days, num_inverters, include_faults },
    });
  },

  // Detect faults
  detectFaults: (data, detection_type = "comprehensive") => {
    return api.post("/detect-faults", {
      data,
      detection_type,
    });
  },

  // Get model info
  getModelInfo: () => api.get("/model-info"),

  // Get fault statistics
  getFaultStatistics: () => api.get("/fault-statistics"),

  // Retrain models
  retrainModels: () => api.post("/retrain-models"),
};

export default api;

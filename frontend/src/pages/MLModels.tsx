// This file is a React wrapper for the ML page, rendering the provided HTML inside a React component.
// If you want to use this as a standalone page, add a route to it in your router.

import React, { useRef, useState } from "react";

// Add this TypeScript declaration to recognize import.meta.env
interface ImportMetaEnv {
  readonly VITE_REACT_APP_GEMINI_API_KEY?: string;
  // add other env variables here if needed
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

// Tailwind CSS is assumed to be globally available in your project

const riskColors: Record<
  string,
  { bg: string; text: string; icon: JSX.Element }
> = {
  High: {
    bg: "bg-red-500",
    text: "text-red-500",
    icon: (
      <svg
        xmlns="http://www.w3.org/2000/svg"
        className="w-5 h-5 mr-2"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M12 2L2 22h20z"></path>
      </svg>
    ),
  },
  Medium: {
    bg: "bg-yellow-500",
    text: "text-yellow-500",
    icon: (
      <svg
        xmlns="http://www.w3.org/2000/svg"
        className="w-5 h-5 mr-2"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M12 2l10 20H2z"></path>
      </svg>
    ),
  },
  Low: {
    bg: "bg-green-500",
    text: "text-green-500",
    icon: (
      <svg
        xmlns="http://www.w3.org/2000/svg"
        className="w-5 h-5 mr-2"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M12 2l-10 20h20z"></path>
      </svg>
    ),
  },
};

type Threat = {
  name: string;
  description: string;
  risk_level: "High" | "Medium" | "Low";
};

type AnalysisData = {
  threat_summary: string;
  threats: Threat[];
  recommended_actions: string[];
};

const MLStandalone: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [dataInput, setDataInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisData | null>(null);
  const [error, setError] = useState<string | null>(null);

  const API_KEY = process.env.REACT_APP_GEMINI_API_KEY || "";
  const API_URL = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key=${API_KEY}`;
  const RETRY_ATTEMPTS = 5;
  const RETRY_DELAY = 1000;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFile(e.target.files?.[0] || null);
  };

  const handleAnalyze = async () => {
    setError(null);
    setResult(null);

    let userInput = "";

    if (file) {
      if (file.type && !file.type.startsWith("text/")) {
        setError("Please upload a text-based file (e.g., .txt, .csv, .json).");
        return;
      }
      const text = await file.text();
      userInput = text;
    } else {
      if (!dataInput.trim()) {
        setError("Please enter some data or upload a file to analyze.");
        return;
      }
      userInput = dataInput.trim();
    }

    await processData(userInput);
  };

  async function makeApiCallWithRetry(
    payload: any,
    retries = RETRY_ATTEMPTS
  ): Promise<any> {
    try {
      const response = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        if (response.status === 429 && retries > 0) {
          const delay = RETRY_DELAY * Math.pow(2, RETRY_ATTEMPTS - retries);
          await new Promise((resolve) => setTimeout(resolve, delay));
          return makeApiCallWithRetry(payload, retries - 1);
        }
        throw new Error(`API call failed with status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      throw error;
    }
  }

  async function processData(data: string) {
    setLoading(true);
    setError(null);
    setResult(null);

    const systemPrompt = `
      You are a world-class coastal environmental analyst. Your task is to analyze the provided data to identify current trends and predict future coastal threats. You MUST respond with a single JSON object.

      The JSON object must have the following structure:
      {
        "threat_summary": "A concise paragraph summarizing the key predicted threats.",
        "threats": [
          {
            "name": "Threat Name (e.g., Rising Sea Levels, Algal Bloom)",
            "description": "A brief description of this specific threat and its potential impact.",
            "risk_level": "High" | "Medium" | "Low"
          }
        ],
        "recommended_actions": [
          "Actionable step 1 for relevant authorities.",
          "Actionable step 2 for relevant authorities.",
          "Actionable step 3 for relevant authorities."
        ]
      }
      You must strictly adhere to this format. Do not include any other text or markdown outside the JSON object.
    `;

    const userQuery = `Analyze the following historical and real-time coastal data to identify current trends and predict future threats. The data is as follows:\n\n${data}`;

    const payload = {
      contents: [{ parts: [{ text: userQuery }] }],
      tools: [{ google_search: {} }],
      systemInstruction: {
        parts: [{ text: systemPrompt }],
      },
    };

    try {
      const result = await makeApiCallWithRetry(payload);
      const candidate = result.candidates?.[0];
      let responseText = candidate?.content?.parts?.[0]?.text;

      if (responseText) {
        // Attempt to parse the JSON response
        const startIndex = responseText.indexOf("{");
        const endIndex = responseText.lastIndexOf("}") + 1;
        const jsonString = responseText.substring(startIndex, endIndex);

        const analysisData = JSON.parse(jsonString);
        setResult(analysisData);
      } else {
        setError(
          "Failed to get a structured response from the API. Please try a different dataset."
        );
      }
    } catch (error: any) {
      setError(
        `An error occurred while processing the data. Please ensure the data format is correct. Error: ${error.message}`
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex items-center justify-center min-h-screen p-4 bg-gray-100">
      <div className="container bg-white shadow-2xl rounded-3xl p-8 w-full max-w-3xl">
        <h1 className="text-4xl font-extrabold text-gray-800 mb-2 text-center">
          Coastal Threat AI
        </h1>
        <p className="text-gray-500 mb-6 text-center">
          Analyze data to predict future coastal threats.
        </p>

        <div className="space-y-6">
          <p className="text-sm text-gray-500">
            You can either paste data directly or upload a text file. The system
            will prioritize the uploaded file if both are provided.
          </p>
          <div>
            <label
              htmlFor="fileInput"
              className="block text-sm font-semibold text-gray-700 mb-1"
            >
              Upload Data File (e.g., .txt, .csv)
            </label>
            <input
              type="file"
              id="fileInput"
              className="w-full text-sm text-gray-500 rounded-lg border border-gray-300 p-2 focus:outline-none focus:ring-2 focus:ring-blue-500 transition duration-200"
              onChange={handleFileChange}
            />
          </div>
          <textarea
            id="dataInput"
            className="w-full h-48 p-4 rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 transition duration-200"
            placeholder="Or paste your coastal data here..."
            value={dataInput}
            onChange={(e) => setDataInput(e.target.value)}
          />
          <button
            id="analyzeButton"
            className="w-full flex items-center justify-center px-6 py-3 bg-blue-600 text-white font-semibold rounded-xl shadow-lg hover:bg-blue-700 transition duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            onClick={handleAnalyze}
            disabled={loading}
          >
            Analyze and Predict Threats
            {loading && (
              <div className="ml-3">
                <span className="loading-animation inline-block align-middle border-4 border-white border-opacity-30 border-t-white rounded-full w-6 h-6 animate-spin"></span>
              </div>
            )}
          </button>
        </div>

        {/* Result Display */}
        {result && (
          <div id="resultContainer" className="mt-12">
            <div className="bg-gray-50 p-8 rounded-2xl border border-gray-200">
              <h2 className="text-2xl font-bold text-gray-800 mb-4 text-center">
                Prediction Results
              </h2>

              {/* Threat Summary */}
              <div className="mb-6">
                <h3 className="text-xl font-semibold text-gray-700 flex items-center mb-2">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="w-6 h-6 mr-2 text-blue-500"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth={2}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M12 2L2 22h20zM12 9v4m0 4h.01"></path>
                  </svg>
                  Threat Summary
                </h3>
                <p
                  id="threatSummary"
                  className="text-gray-600 leading-relaxed"
                >
                  {result.threat_summary}
                </p>
              </div>

              {/* Predicted Threats Grid */}
              <div className="mb-6">
                <h3 className="text-xl font-semibold text-gray-700 flex items-center mb-4">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="w-6 h-6 mr-2 text-blue-500"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth={2}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M12 2v20m-5-5l5 5 5-5m-5-5l5 5 5-5"></path>
                  </svg>
                  Predicted Threats
                </h3>
                <div
                  id="threatsGrid"
                  className="grid gap-4 md:grid-cols-2"
                >
                  {result.threats.map((threat, idx) => {
                    const riskInfo =
                      riskColors[threat.risk_level] || riskColors["Low"];
                    return (
                      <div
                        key={idx}
                        className="bg-white p-6 rounded-xl shadow-md border border-gray-100 flex items-start space-x-4"
                      >
                        <div
                          className={`p-3 rounded-full ${riskInfo.bg} bg-opacity-10 ${riskInfo.text}`}
                        >
                          {riskInfo.icon}
                        </div>
                        <div>
                          <h4 className="text-lg font-semibold text-gray-800">
                            {threat.name}
                          </h4>
                          <p className="text-sm text-gray-500 mt-1">
                            {threat.description}
                          </p>
                          <div
                            className={`mt-2 text-sm font-bold ${riskInfo.text}`}
                          >
                            Risk Level: {threat.risk_level}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Recommended Actions */}
              <div>
                <h3 className="text-xl font-semibold text-gray-700 flex items-center mb-4">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="w-6 h-6 mr-2 text-blue-500"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth={2}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M12 2L2 22h20L12 2z"></path>
                    <path d="M12 9v4"></path>
                    <path d="M12 17h.01"></path>
                  </svg>
                  Recommended Actions
                </h3>
                <ul
                  id="recommendedActions"
                  className="list-disc pl-5 space-y-2 text-gray-600"
                >
                  {result.recommended_actions.map((action, idx) => (
                    <li key={idx}>{action}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div
            id="errorMessage"
            className="text-center text-red-500 mt-4"
          >
            {error}
          </div>
        )}
      </div>
      {/* Loading animation style */}
      <style>
        {`
          .loading-animation {
            border: 4px solid rgba(255, 255, 255, 0.3);
            border-top: 4px solid #ffffff;
            border-radius: 50%;
            width: 24px;
            height: 24px;
            animation: spin 1s linear infinite;
          }
          @keyframes spin {
            to { transform: rotate(360deg); }
          }
        `}
      </style>
    </div>
  );
};

export default MLStandalone;

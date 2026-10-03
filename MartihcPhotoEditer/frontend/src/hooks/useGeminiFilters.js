import { useState } from "react";

export const useGeminiFilters = () => {
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState(null);
  
  const GOOGLE_API_KEY = import.meta.env.VITE_GOOGLE_API_KEY;

  const generateFilters = async (prompt, currentFilters = {}) => {
    if (!prompt || prompt.trim().length === 0) return null;
    
    if (!GOOGLE_API_KEY) {
      setError("No Google API Key found. Please set VITE_GOOGLE_API_KEY.");
      return null;
    }

    setIsGenerating(true);
    setError(null);

    const systemPrompt = `
You are an expert Photo Colorist AI. Your job is to translate a user's natural language request into exact CSS filter values.
You must output ONLY a valid JSON object. No markdown, no explanation, no backticks.

The filters you can adjust are:
- exposure (range -50 to 50, default 0, affects brightness)
- contrast (range -50 to 50, default 0)
- saturation (range -50 to 50, default 0)
- temperature (range 0 to 100, default 0, acts as sepia/warmth)
- tint (range -180 to 180, default 0, acts as hue-rotate)
- vignette (range 0 to 100, default 0)

Current Filters:
${JSON.stringify(currentFilters)}

User Request: "${prompt}"

Return ONLY a JSON object containing the new values for these 6 keys.
    `.trim();

    try {
      const response = await fetch(
        `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${GOOGLE_API_KEY}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            contents: [
              {
                parts: [{ text: systemPrompt }]
              }
            ],
            generationConfig: {
                responseMimeType: "application/json"
            }
          }),
        }
      );

      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }

      const data = await response.json();
      const textResponse = data.candidates?.[0]?.content?.parts?.[0]?.text;
      
      if (textResponse) {
        try {
            const filters = JSON.parse(textResponse);
            return filters;
        } catch (e) {
            console.error("Failed to parse Gemini JSON", textResponse);
            throw new Error("Gemini returned invalid format");
        }
      }
      return null;
    } catch (err) {
      setError(err.message);
      return null;
    } finally {
      setIsGenerating(false);
    }
  };

  return { generateFilters, isGenerating, error };
};

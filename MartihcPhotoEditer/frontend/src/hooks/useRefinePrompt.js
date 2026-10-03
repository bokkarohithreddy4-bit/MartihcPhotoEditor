import { useState } from "react";

/**
 * Hook to refine prompts using Gemini API
 * @returns {object} { refinePrompt, isRefining, error }
 */
export const useRefinePrompt = () => {
  const [isRefining, setIsRefining] = useState(false);
  const [error, setError] = useState(null);
  
  // Need to add this in .env file in the web app
  const GOOGLE_API_KEY = import.meta.env.VITE_GOOGLE_API_KEY;

  const refinePrompt = async (prompt, suggestions = []) => {
    if (!prompt || prompt.trim().length === 0) {
      console.warn("Refine: Empty prompt provided");
      return null;
    }
    
    if (!GOOGLE_API_KEY) {
      setError("No Google API Key found. Please set VITE_GOOGLE_API_KEY.");
      return null;
    }

    setIsRefining(true);
    setError(null);

    const lightSuggestions =
      suggestions.length > 0
        ? suggestions
        : [
            "Enhance the colors",
            "Add warmth to the scene",
            "Boost contrast",
            "Soften the image",
            "Increase clarity",
            "Make it cinematic"
          ];

    try {
      const refinePromptText = `
You are a creative Photo Editing Prompt Enhancer.
Your job is to take the user's short input and turn it into a highly detailed, professional instruction for photo editing.

RULES:
- Expand on the user's idea with beautiful, cinematic, and descriptive language.
- Ensure the tone fits the user's core idea (e.g., if they say "make it dark", describe deep shadows, moody contrast, and cinematic tones).
- Output ONLY the enhanced prompt. Do not include any explanations.
- Keep the total length around 15 to 20 words.

User's Input: "${prompt}"
`;

      const response = await fetch(
        `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${GOOGLE_API_KEY}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            systemInstruction: {
              parts: [
                {
                  text: "Refine using ONLY the allowed suggestions. Generate approximately 12 words.",
                },
              ],
            },
            contents: [
              {
                parts: [
                  {
                    text: refinePromptText,
                  },
                ],
              },
            ],
          }),
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      let completion = "";
      if (
        data.candidates &&
        data.candidates[0] &&
        data.candidates[0].content &&
        data.candidates[0].content.parts &&
        data.candidates[0].content.parts[0]
      ) {
        completion = data.candidates[0].content.parts[0].text;
      }

      if (completion && typeof completion === "string") {
        const trimmedCompletion = completion.trim();
        return trimmedCompletion;
      } else {
        return null;
      }
    } catch (err) {
      setError(err.message);
      return null;
    } finally {
      setIsRefining(false);
    }
  };

  return { refinePrompt, isRefining, error };
};

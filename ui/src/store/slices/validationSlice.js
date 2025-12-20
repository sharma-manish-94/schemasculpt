import {
  validateSpec,
  applyQuickFix,
  updateSessionSpec,
  performAIMetaAnalysis,
  analyzeDescriptions,
} from "../../api/validationService";
import { useSpecStore } from "../specStore";

export const createValidationSlice = (set, get) => ({
  // --- STATE ---
  errors: [],
  suggestions: [],
  isLoading: false,
  aiInsights: [],
  aiSummary: null,
  aiConfidenceScore: 0,
  isAIAnalysisLoading: false,
  descriptionQuality: {
    results: [],
    overallScore: 0,
    patches: [],
  },
  isDescriptionAnalysisLoading: false,
  // --- ACTIONS ---
  setIsLoading: (loading) => set({ isLoading: loading }),
  validateCurrentSpec: async () => {
    const { sessionId, specText } = useSpecStore.getState();
    if (!sessionId) return;

    set({ isLoading: true });

    try {
      // CRITICAL FIX: Update the session with current spec BEFORE validation
      // This ensures validation uses the latest changes from the editor
      await updateSessionSpec(sessionId, specText);

      // Now validate against the updated session spec
      const result = await validateSpec(sessionId);
      if (result.success) {
        set({
          errors: result.data.errors,
          suggestions: result.data.suggestions,
        });
      } else {
        set({ errors: [{ message: result.error }], suggestions: [] });
      }
    } catch (error) {
      console.error("Validation error:", error);
      set({
        errors: [{ message: "Validation failed: " + error.message }],
        suggestions: [],
      });
    }

    set({ isLoading: false });
  },

  applyQuickFix: async (suggestion) => {
    const { sessionId, specText, setSpecText, setSkipNextValidation } =
      useSpecStore.getState();
    const { format } = useSpecStore.getState();

    // Set loading state for this specific fix
    set({ isLoading: true });

    try {
      // CRITICAL FIX: Update the session with current spec BEFORE applying fix
      // This ensures the fix is applied to the latest changes from the editor
      await updateSessionSpec(sessionId, specText);

      // Create the fix request object
      const fixRequest = {
        ruleId: suggestion.ruleId,
        context: suggestion.context,
        format,
      };

      const result = await applyQuickFix(sessionId, fixRequest);
      if (result && result.success) {
        const updatedSpecText = JSON.stringify(result.data, null, 2);

        // Set flag to skip the next auto-validation since backend already validated
        setSkipNextValidation(true);

        // Update spec text
        setSpecText(updatedSpecText);

        // Update validation results directly from backend response
        if (result.validationResult) {
          set({
            errors: result.validationResult.errors || [],
            suggestions: result.validationResult.suggestions || [],
            isLoading: false,
          });
        } else {
          // If no validation result, clear loading but don't validate
          set({ isLoading: false });
        }
      } else if (result && result.error) {
        console.error("Fix failed:", result.error);
        set({ isLoading: false });
      }
    } catch (error) {
      console.error("Fix error:", error);
      set({ isLoading: false });
    }
  },

  runAIMetaAnalysis: async () => {
    const { sessionId } = useSpecStore.getState();
    if (!sessionId) return;

    set({ isAIAnalysisLoading: true });

    try {
      const result = await performAIMetaAnalysis(sessionId);

      if (result && result.success) {
        set({
          aiInsights: result.data.insights || [],
          aiSummary: result.data.summary || null,
          aiConfidenceScore: result.data.confidenceScore || 0,
          isAIAnalysisLoading: false,
        });
      } else {
        console.error("AI meta-analysis failed:", result?.error);
        set({
          aiInsights: [],
          aiSummary:
            "AI analysis failed: " + (result?.error || "Unknown error"),
          aiConfidenceScore: 0,
          isAIAnalysisLoading: false,
        });
      }
    } catch (error) {
      console.error("AI meta-analysis error:", error);
      set({
        aiInsights: [],
        aiSummary: "AI analysis error: " + error.message,
        aiConfidenceScore: 0,
        isAIAnalysisLoading: false,
      });
    }
  },

  runDescriptionAnalysis: async () => {
    const { sessionId, specText } = useSpecStore.getState();
    if (!sessionId) return;

    set({ isDescriptionAnalysisLoading: true });

    try {
      // Update session with current spec before analysis
      await updateSessionSpec(sessionId, specText);

      const result = await analyzeDescriptions(sessionId);

      if (result && result.success) {
        set({
          descriptionQuality: {
            results: result.data.results || [],
            overallScore: result.data.overallScore || 0,
            patches: result.data.patches || [],
          },
          isDescriptionAnalysisLoading: false,
        });
      } else {
        console.error("Description analysis failed:", result?.error);
        set({
          descriptionQuality: {
            results: [],
            overallScore: 0,
            patches: [],
          },
          isDescriptionAnalysisLoading: false,
        });
      }
    } catch (error) {
      console.error("Description analysis error:", error);
      set({
        descriptionQuality: {
          results: [],
          overallScore: 0,
          patches: [],
        },
        isDescriptionAnalysisLoading: false,
      });
    }
  },

  applyDescriptionPatches: async (patches) => {
    const { sessionId, specText, setSpecText } = useSpecStore.getState();
    if (!sessionId || !patches || patches.length === 0) return;

    try {
      // Parse current spec
      let spec = JSON.parse(specText);

      // Apply each JSON Patch operation
      patches.forEach((patch) => {
        const pathParts = patch.path.split("/").filter((p) => p);
        let current = spec;

        // Navigate to the parent of the target
        for (let i = 0; i < pathParts.length - 1; i++) {
          const part = pathParts[i].replace(/~1/g, "/").replace(/~0/g, "~");
          if (!current[part]) {
            current[part] = {};
          }
          current = current[part];
        }

        // Apply the operation
        const lastPart = pathParts[pathParts.length - 1]
          .replace(/~1/g, "/")
          .replace(/~0/g, "~");
        if (patch.op === "add" || patch.op === "replace") {
          current[lastPart] = patch.value;
        } else if (patch.op === "remove") {
          delete current[lastPart];
        }
      });

      // Update spec
      const updatedSpecText = JSON.stringify(spec, null, 2);
      setSpecText(updatedSpecText);

      // Update session
      await updateSessionSpec(sessionId, updatedSpecText);

      // Re-run analysis to get updated scores
      await get().runDescriptionAnalysis();
    } catch (error) {
      console.error("Failed to apply description patches:", error);
    }
  },
});

import {validateSpec, applyQuickFix, updateSessionSpec, performAIMetaAnalysis} from '../../api/validationService';
import {useSpecStore} from "../specStore";

export const createValidationSlice = (set, get) => ({
    // --- STATE ---
    errors: [],
    suggestions: [],
    isLoading: false,
    aiInsights: [],
    aiSummary: null,
    aiConfidenceScore: 0,
    isAIAnalysisLoading: false,
    // --- ACTIONS ---
    setIsLoading: (loading) => set({isLoading: loading}), validateCurrentSpec: async () => {
        const {sessionId, specText} = useSpecStore.getState();
        if (!sessionId) return;

        set({isLoading: true});

        try {
            // CRITICAL FIX: Update the session with current spec BEFORE validation
            // This ensures validation uses the latest changes from the editor
            await updateSessionSpec(sessionId, specText);

            // Now validate against the updated session spec
            const result = await validateSpec(sessionId);
            if (result.success) {
                set({errors: result.data.errors, suggestions: result.data.suggestions});
            } else {
                set({errors: [{message: result.error}], suggestions: []});
            }
        } catch (error) {
            console.error('Validation error:', error);
            set({errors: [{message: 'Validation failed: ' + error.message}], suggestions: []});
        }

        set({isLoading: false});
    },

    applyQuickFix: async (suggestion) => {
        const { sessionId, specText, setSpecText, setSkipNextValidation } = useSpecStore.getState();
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
                format
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
                        isLoading: false
                    });
                } else {
                    // If no validation result, clear loading but don't validate
                    set({ isLoading: false });
                }
            } else if (result && result.error) {
                console.error('Fix failed:', result.error);
                set({ isLoading: false });
            }
        } catch (error) {
            console.error('Fix error:', error);
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
                    isAIAnalysisLoading: false
                });
            } else {
                console.error('AI meta-analysis failed:', result?.error);
                set({
                    aiInsights: [],
                    aiSummary: 'AI analysis failed: ' + (result?.error || 'Unknown error'),
                    aiConfidenceScore: 0,
                    isAIAnalysisLoading: false
                });
            }
        } catch (error) {
            console.error('AI meta-analysis error:', error);
            set({
                aiInsights: [],
                aiSummary: 'AI analysis error: ' + error.message,
                aiConfidenceScore: 0,
                isAIAnalysisLoading: false
            });
        }
    }
});
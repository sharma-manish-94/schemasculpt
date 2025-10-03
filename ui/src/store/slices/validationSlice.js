import {validateSpec, applyQuickFix} from '../../api/validationService';
import {useSpecStore} from "../specStore";

export const createValidationSlice = (set, get) => ({
    // --- STATE ---
    errors: [], suggestions: [], isLoading: false, // --- ACTIONS ---
    setIsLoading: (loading) => set({isLoading: loading}), validateCurrentSpec: async () => {
        const {sessionId} = useSpecStore.getState();
        if (!sessionId) return;

        set({isLoading: true});
        const result = await validateSpec(sessionId);
        if (result.success) {
            set({errors: result.data.errors, suggestions: result.data.suggestions});
        } else {
            set({errors: [{message: result.error}], suggestions: []});
        }
        set({isLoading: false});
    },

    applyQuickFix: async (suggestion) => {
        const { sessionId, setSpecText, setSkipNextValidation } = useSpecStore.getState();
        const { format } = useSpecStore.getState();

        // Set loading state for this specific fix
        set({ isLoading: true });

        // Create the fix request object
        const fixRequest = {
            ruleId: suggestion.ruleId,
            context: suggestion.context,
            format
        };

        try {
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
    }
});
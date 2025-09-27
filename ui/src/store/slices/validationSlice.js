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
        const { sessionId, setSpecText } = useSpecStore.getState();
        const { format } = useSpecStore.getState();
        // Create the fix request object
        const fixRequest = {
            ruleId: suggestion.ruleId,
            context: suggestion.context,
            format
        };

        const result = await applyQuickFix(sessionId, fixRequest);
        if (result && result.success) {
            const updatedSpecText = JSON.stringify(result.data, null, 2);
            setSpecText(updatedSpecText);
        } else if (result && result.error) {
            console.error('Fix failed:', result.error);
            // You could also show this error to the user via state if needed
        }
    }
});
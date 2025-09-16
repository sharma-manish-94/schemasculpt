import {executeAiAction} from "../../api/validationService";

export const createAiSlice = (set, get) => ({

    // --- STATE ---
    aiPrompt: '',

    // --- ACTIONS ---

    setAiPrompt: (prompt) => set({aiPrompt: prompt}),

    submitAiRequest: async () => {
        const {specText, aiPrompt, setSpecText} = get();
        if(!aiPrompt.trim) return;
        set({isLoading: true});
        const result = await executeAiAction(specText, aiPrompt);
        if(result?.updatedSpecText) {
            setSpecText(result.updatedSpecText);
        }
        set({aiPrompt: '', isLoading: false});
    }
});
import {executeAiAction} from "../../api/validationService";
import {useSpecStore} from "../specStore";

export const createAiSlice = (set, get) => ({

    // --- STATE ---
    aiPrompt: '',

    // --- ACTIONS ---

    setAiPrompt: (prompt) => set({aiPrompt: prompt}),

    submitAIRequest: async () => {
        const { sessionId, aiPrompt, setSpecText } = useSpecStore.getState();
        if (!aiPrompt.trim() || !sessionId) return;
        set({isLoading: true});
        const result = await executeAiAction(sessionId, aiPrompt);
        if(result) {
            const updatedSpecText = JSON.stringify(result, null, 2);
            setSpecText(updatedSpecText);
        }
        set({aiPrompt: '', isLoading: false});
    }
});
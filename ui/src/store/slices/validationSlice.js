import { validateSpec, applyQuickFix } from '../../api/validationService';

export const createValidationSlice = (set, get) => ({
   errors:[],
   suggestions:[],
   isLoading: false,

    validateCurrentSpec: async() => {
       set({isLoading: true});
       const result = await validateSpec(get().specText);
       if(result.success) {
           set({errors: result.data.errors, suggestions: result.data.suggestions});
       } else {
           set({errors: [{message: result.error}], suggestions: []});
       }
       set({isLoading: false});
    },

    applyQuickFix: async(suggestion) => {
       const {specText, format} = get();
       const result = await applyQuickFix({
           specText,
           ruleId: suggestion.ruleId,
            context: suggestion.context,
           format,
       });
       if(result?.updatedSpecText) {
           get().setSpecText(result.updatedSpecText);
       }
    }
});
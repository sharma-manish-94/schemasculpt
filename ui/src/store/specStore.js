import { create } from 'zustand';
import { coreSlice } from './slices/coreSlice';
import { createValidationSlice } from './slices/validationSlice';
import { createAiSlice } from './slices/aiSlice';
import { createApiLabSlice } from './slices/apiLabSlice';

export const useSpecStore = create((set, get) => ({
    ...coreSlice(set, get),
    ...createValidationSlice(set, get),
    ...createAiSlice(set, get),
    ...createApiLabSlice(set, get),
}));
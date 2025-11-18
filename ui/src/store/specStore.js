import { create } from 'zustand';
import { coreSlice } from './slices/coreSlice';
import { createValidationSlice } from './slices/validationSlice';
import { createAiSlice } from './slices/aiSlice';
import { createRequestSlice } from './slices/requestSlice';
import { createRepositorySlice } from './slices/repositorySlice';

export const useSpecStore = create((set, get) => ({
    ...coreSlice(set, get),
    ...createValidationSlice(set, get),
    ...createAiSlice(set, get),
    ...createRequestSlice(set, get),
    ...createRepositorySlice(set, get)
}));
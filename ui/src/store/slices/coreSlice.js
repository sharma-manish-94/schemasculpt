import yaml from 'js-yaml';
import axios from 'axios';
import * as websocketService from '../../api/websocketService';


export const coreSlice = (set, get) => ({
    // --- STATE ---
    specText: `openapi: 3.0.0\ninfo:\n  title: Simple Pet Store API\n  version: 1.0.0\nservers:\n  - url: http://localhost:8080/api/v1\npaths:\n  /pets:\n    get:\n      summary: List all pets\n      responses:\n        '200':\n          description: A paged array of pets`,
    sessionId: null,
    format: 'yaml',
    activeTab: 'validation',

    // --- ACTIONS ---
    setActiveTab: (tabName) => set({activeTab: tabName}),

    setSpecText: (newSpecText) => {
        set({specText: newSpecText});
        const sessionId = get().sessionId;
        if (sessionId) {
            websocketService.sendMessage(sessionId, newSpecText);
        }
    },

    createSession: async () => {
        try {
            const response = await axios.post('http://localhost:8080/api/v1/sessions', get().specText, {
                headers: {'Content-Type': 'text/plain'}
            });
            set({sessionId: response.data.sessionId});
            console.log('Session created with ID:', response.data.sessionId);
        } catch (error) {
            console.error('Failed to create session:', error);
        }
    },

    convertToYAML: () => {
        try {
            const jsonObject = JSON.parse(get().specText);
            const yamlText = yaml.dump(jsonObject);
            get().setSpecText(yamlText);
            set({format: 'yaml'});
        } catch (error) {
            alert("Could not convert to YAML. Please ensure the content is valid JSON.");
        }
    },

    convertToJSON: () => {
        try {
            const jsonObject = yaml.load(get().specText);
            const jsonText = JSON.stringify(jsonObject, null, 2);
            get().setSpecText(jsonText);
            set({format: 'json'});
        } catch (error) {
            alert("Could not convert to JSON. Please ensure the content is valid YAML.");
        }
    },
});
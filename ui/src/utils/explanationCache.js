/**
 * In-memory cache for validation explanations
 * Reduces redundant API calls for the same validation rules
 */

class ExplanationCache {
    constructor(ttl = 3600000) { // Default TTL: 1 hour
        this.cache = new Map();
        this.ttl = ttl;
    }

    /**
     * Generate cache key from rule parameters
     */
    generateKey(ruleId, message, category) {
        return `${ruleId}:${category}:${message}`;
    }

    /**
     * Get cached explanation if available and not expired
     */
    get(ruleId, message, category) {
        const key = this.generateKey(ruleId, message, category);
        const cached = this.cache.get(key);

        if (!cached) {
            return null;
        }

        // Check if expired
        if (Date.now() - cached.timestamp > this.ttl) {
            this.cache.delete(key);
            return null;
        }

        return cached.data;
    }

    /**
     * Store explanation in cache
     */
    set(ruleId, message, category, data) {
        const key = this.generateKey(ruleId, message, category);
        this.cache.set(key, {
            data,
            timestamp: Date.now()
        });
    }

    /**
     * Clear entire cache
     */
    clear() {
        this.cache.clear();
    }

    /**
     * Get cache statistics
     */
    getStats() {
        return {
            size: this.cache.size,
            keys: Array.from(this.cache.keys())
        };
    }

    /**
     * Remove expired entries
     */
    cleanup() {
        const now = Date.now();
        for (const [key, value] of this.cache.entries()) {
            if (now - value.timestamp > this.ttl) {
                this.cache.delete(key);
            }
        }
    }
}

// Create singleton instance
const explanationCache = new ExplanationCache();

// Cleanup expired entries every 5 minutes
setInterval(() => {
    explanationCache.cleanup();
}, 300000);

export default explanationCache;

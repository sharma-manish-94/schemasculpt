/**
 * Suggestion Grouping Utilities
 * Groups validation suggestions by category for better organization and LLM context
 */

// Category definitions with priorities and descriptions
export const SUGGESTION_CATEGORIES = {
    SECURITY: {
        name: 'Security',
        priority: 1,
        description: 'Security-related issues and recommendations',
        keywords: ['security', 'auth', 'authorization', 'authentication', 'oauth', 'api-key', 'token', 'credentials', 'password', 'secret', 'encrypt', 'https', 'ssl', 'tls']
    },
    VALIDATION: {
        name: 'Validation',
        priority: 2,
        description: 'Schema validation and data validation issues',
        keywords: ['validation', 'schema', 'type', 'format', 'pattern', 'required', 'constraint']
    },
    DOCUMENTATION: {
        name: 'Documentation',
        priority: 3,
        description: 'Missing or incomplete documentation',
        keywords: ['description', 'summary', 'example', 'documentation', 'docs', 'comment']
    },
    BEST_PRACTICES: {
        name: 'Best Practices',
        priority: 4,
        description: 'API design and naming best practices',
        keywords: ['best-practice', 'convention', 'naming', 'kebab-case', 'camel-case', 'snake-case', 'rest', 'design']
    },
    STRUCTURE: {
        name: 'Structure',
        priority: 5,
        description: 'OpenAPI specification structure and format',
        keywords: ['structure', 'format', 'openapi', 'version', 'paths', 'components', 'schemas']
    },
    PERFORMANCE: {
        name: 'Performance',
        priority: 6,
        description: 'Performance and optimization recommendations',
        keywords: ['performance', 'optimization', 'cache', 'rate-limit', 'pagination', 'compression']
    },
    OTHER: {
        name: 'Other',
        priority: 99,
        description: 'Other issues and recommendations',
        keywords: []
    }
};

/**
 * Determine category based on rule ID and message
 * @param {Object} suggestion - Validation suggestion
 * @returns {string} Category key
 */
export const categorizeSuggestion = (suggestion) => {
    const searchText = `${suggestion.ruleId || ''} ${suggestion.message || ''} ${suggestion.category || ''}`.toLowerCase();

    // Check each category's keywords
    for (const [categoryKey, category] of Object.entries(SUGGESTION_CATEGORIES)) {
        if (categoryKey === 'OTHER') continue; // Skip OTHER, it's the fallback

        for (const keyword of category.keywords) {
            if (searchText.includes(keyword)) {
                return categoryKey;
            }
        }
    }

    return 'OTHER';
};

/**
 * Group suggestions by category
 * @param {Array} suggestions - Array of validation suggestions
 * @returns {Object} Grouped suggestions with metadata
 */
export const groupSuggestionsByCategory = (suggestions) => {
    if (!suggestions || !Array.isArray(suggestions)) {
        return {};
    }

    const grouped = {};

    // Initialize all categories
    Object.keys(SUGGESTION_CATEGORIES).forEach(categoryKey => {
        grouped[categoryKey] = {
            category: SUGGESTION_CATEGORIES[categoryKey].name,
            description: SUGGESTION_CATEGORIES[categoryKey].description,
            priority: SUGGESTION_CATEGORIES[categoryKey].priority,
            suggestions: [],
            count: 0,
            severityCounts: {
                error: 0,
                warning: 0,
                info: 0
            }
        };
    });

    // Group suggestions
    suggestions.forEach(suggestion => {
        const categoryKey = categorizeSuggestion(suggestion);
        grouped[categoryKey].suggestions.push(suggestion);
        grouped[categoryKey].count++;

        // Count by severity
        const severity = (suggestion.severity || 'info').toLowerCase();
        if (grouped[categoryKey].severityCounts[severity] !== undefined) {
            grouped[categoryKey].severityCounts[severity]++;
        }
    });

    // Remove empty categories and sort by priority
    const result = {};
    Object.entries(grouped)
        .filter(([_, data]) => data.count > 0)
        .sort((a, b) => a[1].priority - b[1].priority)
        .forEach(([key, data]) => {
            result[key] = data;
        });

    return result;
};

/**
 * Get security-related suggestions only
 * @param {Array} suggestions - Array of validation suggestions
 * @returns {Array} Security suggestions
 */
export const getSecuritySuggestions = (suggestions) => {
    if (!suggestions || !Array.isArray(suggestions)) {
        return [];
    }

    return suggestions.filter(suggestion => {
        const category = categorizeSuggestion(suggestion);
        return category === 'SECURITY';
    });
};

/**
 * Format grouped suggestions for LLM context
 * @param {Object} groupedSuggestions - Grouped suggestions from groupSuggestionsByCategory
 * @returns {string} Formatted text for LLM
 */
export const formatSuggestionsForLLM = (groupedSuggestions) => {
    if (!groupedSuggestions || Object.keys(groupedSuggestions).length === 0) {
        return 'No validation suggestions available.';
    }

    let formatted = 'Validation Suggestions by Category:\n\n';

    Object.entries(groupedSuggestions).forEach(([categoryKey, data]) => {
        formatted += `## ${data.category} (${data.count} issues)\n`;
        formatted += `${data.description}\n\n`;

        data.suggestions.forEach((suggestion, idx) => {
            formatted += `${idx + 1}. [${suggestion.severity?.toUpperCase() || 'INFO'}] `;
            formatted += `${suggestion.ruleId || 'Unknown'}: ${suggestion.message}\n`;
            if (suggestion.path) {
                formatted += `   Location: ${suggestion.path}\n`;
            }
        });

        formatted += '\n';
    });

    return formatted;
};

/**
 * Get summary statistics for all suggestions
 * @param {Array} suggestions - Array of validation suggestions
 * @returns {Object} Summary statistics
 */
export const getSuggestionsSummary = (suggestions) => {
    if (!suggestions || !Array.isArray(suggestions)) {
        return {
            total: 0,
            byCategory: {},
            bySeverity: { error: 0, warning: 0, info: 0 }
        };
    }

    const grouped = groupSuggestionsByCategory(suggestions);

    const summary = {
        total: suggestions.length,
        byCategory: {},
        bySeverity: { error: 0, warning: 0, info: 0 }
    };

    Object.entries(grouped).forEach(([key, data]) => {
        summary.byCategory[data.category] = data.count;
        summary.bySeverity.error += data.severityCounts.error;
        summary.bySeverity.warning += data.severityCounts.warning;
        summary.bySeverity.info += data.severityCounts.info;
    });

    return summary;
};

import React, { useState } from 'react';
import { useSpecStore } from '../../../store/specStore';
import Button from '../../../components/ui/Button';
import LoadingSpinner from '../../../components/ui/LoadingSpinner';
import ErrorMessage from '../../../components/ui/ErrorMessage';

const DOMAINS = [
    { value: 'ecommerce', label: 'E-commerce' },
    { value: 'finance', label: 'Finance & Banking' },
    { value: 'healthcare', label: 'Healthcare' },
    { value: 'education', label: 'Education' },
    { value: 'social', label: 'Social Media' },
    { value: 'gaming', label: 'Gaming' },
    { value: 'iot', label: 'IoT & Devices' },
    { value: 'saas', label: 'SaaS Platform' },
    { value: 'custom', label: 'Custom/Other' }
];

const COMPLEXITY_LEVELS = [
    { value: 'simple', label: 'Simple (5-10 endpoints)' },
    { value: 'moderate', label: 'Moderate (10-20 endpoints)' },
    { value: 'complex', label: 'Complex (20+ endpoints)' }
];

const AUTHENTICATION_TYPES = [
    { value: 'none', label: 'None' },
    { value: 'api_key', label: 'API Key' },
    { value: 'bearer', label: 'Bearer Token' },
    { value: 'oauth2', label: 'OAuth 2.0' },
    { value: 'basic', label: 'Basic Auth' }
];

function AISpecGenerator() {
    const {
        generateSpecification,
        isAiProcessing,
        aiResponse,
        aiError,
        clearAiResponse
    } = useSpecStore();

    const [formData, setFormData] = useState({
        domain: '',
        complexityLevel: 'moderate',
        authentication: 'api_key',
        customDomain: '',
        description: '',
        features: '',
        includeExamples: true,
        includeValidation: true,
        includeDocumentation: true
    });

    const [generatedSpecs, setGeneratedSpecs] = useState([]);

    const handleInputChange = (field, value) => {
        setFormData(prev => ({
            ...prev,
            [field]: value
        }));
    };

    const handleGenerate = async () => {
        clearAiResponse();

        const request = {
            domain: formData.domain === 'custom' ? formData.customDomain : formData.domain,
            complexityLevel: formData.complexityLevel,
            authentication: formData.authentication,
            description: formData.description,
            features: formData.features.split('\n').filter(f => f.trim()),
            options: {
                includeExamples: formData.includeExamples,
                includeValidation: formData.includeValidation,
                includeDocumentation: formData.includeDocumentation
            }
        };

        const result = await generateSpecification(request);

        if (result.success && result.data) {
            setGeneratedSpecs(prev => [
                {
                    id: Date.now(),
                    timestamp: new Date(),
                    domain: request.domain,
                    complexity: request.complexityLevel,
                    spec: result.data
                },
                ...prev
            ]);
        }
    };

    const handleUseSpec = (spec) => {
        if (spec.generatedSpec) {
            const { setSpecText } = useSpecStore.getState();
            setSpecText(typeof spec.generatedSpec === 'string'
                ? spec.generatedSpec
                : JSON.stringify(spec.generatedSpec, null, 2)
            );
        }
    };

    const isFormValid = () => {
        if (!formData.domain) return false;
        if (formData.domain === 'custom' && !formData.customDomain.trim()) return false;
        return formData.description.trim().length > 0;
    };

    return (
        <div className="ai-spec-generator">
            <div className="generator-header">
                <h4>AI Specification Generator</h4>
                <p>Generate complete OpenAPI specifications from high-level descriptions</p>
            </div>

            <div className="generator-form">
                <div className="form-section">
                    <h5>Basic Information</h5>

                    <div className="form-group">
                        <label>Domain</label>
                        <select
                            value={formData.domain}
                            onChange={(e) => handleInputChange('domain', e.target.value)}
                        >
                            <option value="">Select a domain...</option>
                            {DOMAINS.map(domain => (
                                <option key={domain.value} value={domain.value}>
                                    {domain.label}
                                </option>
                            ))}
                        </select>
                    </div>

                    {formData.domain === 'custom' && (
                        <div className="form-group">
                            <label>Custom Domain</label>
                            <input
                                type="text"
                                placeholder="e.g., Pet Store, Recipe Management"
                                value={formData.customDomain}
                                onChange={(e) => handleInputChange('customDomain', e.target.value)}
                            />
                        </div>
                    )}

                    <div className="form-group">
                        <label>API Description</label>
                        <textarea
                            placeholder="Describe your API's purpose and main functionality..."
                            value={formData.description}
                            onChange={(e) => handleInputChange('description', e.target.value)}
                            rows={4}
                        />
                    </div>

                    <div className="form-group">
                        <label>Key Features (one per line)</label>
                        <textarea
                            placeholder="User management&#10;Product catalog&#10;Order processing&#10;Payment integration"
                            value={formData.features}
                            onChange={(e) => handleInputChange('features', e.target.value)}
                            rows={6}
                        />
                    </div>
                </div>

                <div className="form-section">
                    <h5>Configuration</h5>

                    <div className="form-group">
                        <label>Complexity Level</label>
                        <select
                            value={formData.complexityLevel}
                            onChange={(e) => handleInputChange('complexityLevel', e.target.value)}
                        >
                            {COMPLEXITY_LEVELS.map(level => (
                                <option key={level.value} value={level.value}>
                                    {level.label}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div className="form-group">
                        <label>Authentication</label>
                        <select
                            value={formData.authentication}
                            onChange={(e) => handleInputChange('authentication', e.target.value)}
                        >
                            {AUTHENTICATION_TYPES.map(auth => (
                                <option key={auth.value} value={auth.value}>
                                    {auth.label}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div className="form-group">
                        <label>Options</label>
                        <div className="checkbox-group">
                            <label className="checkbox-item">
                                <input
                                    type="checkbox"
                                    checked={formData.includeExamples}
                                    onChange={(e) => handleInputChange('includeExamples', e.target.checked)}
                                />
                                Include Examples
                            </label>
                            <label className="checkbox-item">
                                <input
                                    type="checkbox"
                                    checked={formData.includeValidation}
                                    onChange={(e) => handleInputChange('includeValidation', e.target.checked)}
                                />
                                Include Validation Rules
                            </label>
                            <label className="checkbox-item">
                                <input
                                    type="checkbox"
                                    checked={formData.includeDocumentation}
                                    onChange={(e) => handleInputChange('includeDocumentation', e.target.checked)}
                                />
                                Include Documentation
                            </label>
                        </div>
                    </div>
                </div>

                <div className="form-actions">
                    <Button
                        variant="ai"
                        onClick={handleGenerate}
                        disabled={!isFormValid() || isAiProcessing}
                        loading={isAiProcessing}
                    >
                        Generate Specification
                    </Button>
                </div>
            </div>

            {aiError && (
                <div className="generator-error">
                    <ErrorMessage message={aiError} />
                </div>
            )}

            {isAiProcessing && (
                <div className="generator-loading">
                    <LoadingSpinner />
                    <span>Generating your API specification...</span>
                    <small>This may take up to 2 minutes for complex specifications</small>
                </div>
            )}

            {generatedSpecs.length > 0 && (
                <div className="generated-specs">
                    <h5>Generated Specifications</h5>
                    {generatedSpecs.map((specItem) => (
                        <div key={specItem.id} className="generated-spec-item">
                            <div className="spec-header">
                                <div className="spec-info">
                                    <h6>{specItem.domain} API</h6>
                                    <span className="spec-complexity">{specItem.complexity}</span>
                                    <span className="spec-timestamp">
                                        {specItem.timestamp.toLocaleString()}
                                    </span>
                                </div>
                                <div className="spec-actions">
                                    <Button
                                        variant="primary"
                                        size="small"
                                        onClick={() => handleUseSpec(specItem.spec)}
                                    >
                                        Use This Spec
                                    </Button>
                                    <Button
                                        variant="secondary"
                                        size="small"
                                        onClick={() => {
                                            navigator.clipboard.writeText(
                                                JSON.stringify(specItem.spec, null, 2)
                                            );
                                        }}
                                    >
                                        Copy
                                    </Button>
                                </div>
                            </div>
                            <div className="spec-preview">
                                <pre>{JSON.stringify(specItem.spec, null, 2)}</pre>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default AISpecGenerator;
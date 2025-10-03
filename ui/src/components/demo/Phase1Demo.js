import React, { useState, useEffect } from 'react';
import Button from '../ui/Button';
import LoadingSpinner from '../ui/LoadingSpinner';
import ErrorMessage from '../ui/ErrorMessage';
import ValidationSuggestion from '../validation/ValidationSuggestion';
import {
    explainValidationIssue,
    hardenOperationComplete,
    addOAuth2Security,
    addRateLimiting,
    addCaching,
    generateOperationTestCases,
    generateTestSuite,
    getHardeningPatterns
} from '../../api/validationService';
import './Phase1Demo.css';

const Phase1Demo = ({ sessionId, specText }) => {
    const [activeDemo, setActiveDemo] = useState('why-button');
    const [demoResults, setDemoResults] = useState({});
    const [loading, setLoading] = useState({});
    const [errors, setErrors] = useState({});

    // Sample validation suggestions for demo
    const sampleSuggestions = [
        {
            message: "Operation 'GET /users' is missing a summary.",
            ruleId: "missing-summary",
            severity: "warning",
            category: "documentation",
            context: { path: "/users", method: "GET", operationId: "getUsers" },
            explainable: true
        },
        {
            message: "No security requirements defined for sensitive endpoint.",
            ruleId: "missing-security",
            severity: "error",
            category: "security",
            context: { path: "/admin", method: "POST", operationId: "createAdmin" },
            explainable: true
        },
        {
            message: "Response schema missing for 404 error.",
            ruleId: "missing-error-response",
            severity: "info",
            category: "completeness",
            context: { path: "/users/{id}", method: "GET", operationId: "getUserById" },
            explainable: true
        }
    ];

    const runDemo = async (demoType, params = {}) => {
        setLoading(prev => ({ ...prev, [demoType]: true }));
        setErrors(prev => ({ ...prev, [demoType]: null }));

        try {
            let result;
            switch (demoType) {
                case 'explain-demo':
                    result = await explainValidationIssue({
                        ruleId: params.ruleId,
                        message: params.message,
                        specText: specText || '{}',
                        category: params.category,
                        context: params.context
                    }, sessionId);
                    break;

                case 'harden-oauth2':
                    result = await addOAuth2Security(sessionId || 'demo', '/users', 'GET');
                    break;

                case 'harden-rate-limit':
                    result = await addRateLimiting(sessionId || 'demo', '/users', 'GET', '100/hour');
                    break;

                case 'harden-caching':
                    result = await addCaching(sessionId || 'demo', '/users', 'GET', '300');
                    break;

                case 'harden-complete':
                    result = await hardenOperationComplete(sessionId || 'demo', '/users', 'POST');
                    break;

                case 'generate-tests':
                    result = await generateOperationTestCases(
                        sessionId || 'demo',
                        params.path || '/users',
                        params.method || 'GET',
                        params.summary || 'Get list of users'
                    );
                    break;

                case 'generate-suite':
                    result = await generateTestSuite(
                        specText || '{"openapi": "3.0.0", "info": {"title": "Demo API", "version": "1.0.0"}, "paths": {}}',
                        { testTypes: ['positive', 'negative', 'edge_cases'], maxOperations: 5 }
                    );
                    break;

                default:
                    throw new Error(`Unknown demo type: ${demoType}`);
            }

            setDemoResults(prev => ({ ...prev, [demoType]: result }));
        } catch (error) {
            setErrors(prev => ({ ...prev, [demoType]: error.message || 'Demo failed' }));
        } finally {
            setLoading(prev => ({ ...prev, [demoType]: false }));
        }
    };

    const renderWhyButtonDemo = () => (
        <div className="demo-section">
            <h3>🤔 AI "Why?" Button Demo</h3>
            <p>Click the "Why?" button on any validation suggestion to get detailed AI-powered explanations.</p>

            <div className="suggestions-demo">
                {sampleSuggestions.map((suggestion, index) => (
                    <ValidationSuggestion
                        key={index}
                        suggestion={suggestion}
                        sessionId={sessionId}
                        specText={specText}
                    />
                ))}
            </div>

            <div className="demo-benefits">
                <h4>✨ Features Demonstrated:</h4>
                <ul>
                    <li>RAG-enhanced explanations with knowledge base context</li>
                    <li>Contextual best practices and example solutions</li>
                    <li>Severity-based styling and categorization</li>
                    <li>Fallback handling for service unavailability</li>
                </ul>
            </div>
        </div>
    );

    const renderHardeningDemo = () => (
        <div className="demo-section">
            <h3>🛡️ One-Click API Hardening Demo</h3>
            <p>Apply security and performance patterns to your API operations instantly.</p>

            <div className="hardening-controls">
                <div className="pattern-buttons">
                    <Button
                        variant="primary"
                        onClick={() => runDemo('harden-oauth2')}
                        loading={loading['harden-oauth2']}
                    >
                        Add OAuth2 Security
                    </Button>

                    <Button
                        variant="secondary"
                        onClick={() => runDemo('harden-rate-limit')}
                        loading={loading['harden-rate-limit']}
                    >
                        Add Rate Limiting
                    </Button>

                    <Button
                        variant="secondary"
                        onClick={() => runDemo('harden-caching')}
                        loading={loading['harden-caching']}
                    >
                        Add HTTP Caching
                    </Button>

                    <Button
                        variant="ai"
                        onClick={() => runDemo('harden-complete')}
                        loading={loading['harden-complete']}
                    >
                        Complete Hardening
                    </Button>
                </div>

                {Object.entries(demoResults).map(([key, result]) => {
                    if (!key.startsWith('harden-') || !result.success) return null;
                    return (
                        <div key={key} className="demo-result success">
                            <h4>✅ {key.replace('harden-', '').replace('-', ' ')} Applied</h4>
                            <p>Applied patterns: {result.data?.appliedPatterns?.join(', ')}</p>
                            {result.data?.warnings?.length > 0 && (
                                <div className="warnings">
                                    <strong>Warnings:</strong>
                                    <ul>
                                        {result.data.warnings.map((warning, i) => (
                                            <li key={i}>{warning}</li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                        </div>
                    );
                })}

                {Object.entries(errors).map(([key, error]) => {
                    if (!key.startsWith('harden-')) return null;
                    return <ErrorMessage key={key} message={`Hardening failed: ${error}`} />;
                })}
            </div>

            <div className="demo-benefits">
                <h4>✨ Features Demonstrated:</h4>
                <ul>
                    <li>OAuth2 security scheme and requirements</li>
                    <li>Rate limiting headers and 429 responses</li>
                    <li>HTTP caching with ETag and 304 responses</li>
                    <li>Idempotency keys for safe retries</li>
                    <li>Standard error response patterns</li>
                    <li>Input validation error handling</li>
                </ul>
            </div>
        </div>
    );

    const renderTestGenerationDemo = () => (
        <div className="demo-section">
            <h3>🧪 AI Test Generation Demo</h3>
            <p>Generate comprehensive test cases for your API operations using AI.</p>

            <div className="test-controls">
                <div className="test-buttons">
                    <Button
                        variant="primary"
                        onClick={() => runDemo('generate-tests', {
                            path: '/users',
                            method: 'GET',
                            summary: 'Get list of users'
                        })}
                        loading={loading['generate-tests']}
                    >
                        Generate Operation Tests
                    </Button>

                    <Button
                        variant="ai"
                        onClick={() => runDemo('generate-suite')}
                        loading={loading['generate-suite']}
                    >
                        Generate Complete Test Suite
                    </Button>
                </div>

                {demoResults['generate-tests']?.success && (
                    <div className="demo-result success">
                        <h4>✅ Test Cases Generated</h4>
                        <div className="test-summary">
                            <p><strong>Operation:</strong> {demoResults['generate-tests'].data.summary?.operation}</p>
                            <p><strong>Total Tests:</strong> {demoResults['generate-tests'].data.summary?.total_tests}</p>
                            <p><strong>Positive:</strong> {demoResults['generate-tests'].data.summary?.positive_tests}</p>
                            <p><strong>Negative:</strong> {demoResults['generate-tests'].data.summary?.negative_tests}</p>
                            <p><strong>Edge Cases:</strong> {demoResults['generate-tests'].data.summary?.edge_case_tests}</p>
                        </div>

                        <div className="test-cases">
                            <h5>Sample Test Cases:</h5>
                            {demoResults['generate-tests'].data.test_cases?.slice(0, 3).map((testCase, index) => (
                                <div key={index} className="test-case">
                                    <div className="test-header">
                                        <span className={`test-type ${testCase.type}`}>{testCase.type}</span>
                                        <span className="test-name">{testCase.name}</span>
                                    </div>
                                    <p className="test-description">{testCase.description}</p>
                                    <div className="test-details">
                                        <p><strong>Expected Status:</strong> {testCase.expected_response?.status_code}</p>
                                        <p><strong>Assertions:</strong> {testCase.assertions?.length || 0}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {demoResults['generate-suite']?.success && (
                    <div className="demo-result success">
                        <h4>✅ Test Suite Generated</h4>
                        <div className="suite-summary">
                            <p><strong>Suite:</strong> {demoResults['generate-suite'].data.test_suite?.name}</p>
                            <p><strong>Total Tests:</strong> {demoResults['generate-suite'].data.test_suite?.statistics?.total_tests}</p>
                            <p><strong>Coverage:</strong> {demoResults['generate-suite'].data.test_suite?.statistics?.coverage}</p>
                            <p><strong>Estimated Duration:</strong> {demoResults['generate-suite'].data.execution_plan?.estimated_duration}</p>
                        </div>
                    </div>
                )}

                {(errors['generate-tests'] || errors['generate-suite']) && (
                    <ErrorMessage message={`Test generation failed: ${errors['generate-tests'] || errors['generate-suite']}`} />
                )}
            </div>

            <div className="demo-benefits">
                <h4>✨ Features Demonstrated:</h4>
                <ul>
                    <li>AI-powered test case generation with realistic data</li>
                    <li>Positive, negative, and edge case coverage</li>
                    <li>Framework-agnostic test structure (Jest, Postman, etc.)</li>
                    <li>Complete test suite generation for entire APIs</li>
                    <li>Test organization and execution planning</li>
                </ul>
            </div>
        </div>
    );

    return (
        <div className="phase1-demo">
            <div className="demo-header">
                <h2>🚀 Phase 1 Features Demo</h2>
                <p>Experience the latest AI-powered enhancements to SchemaSculpt</p>

                <div className="demo-tabs">
                    <button
                        className={`demo-tab ${activeDemo === 'why-button' ? 'active' : ''}`}
                        onClick={() => setActiveDemo('why-button')}
                    >
                        Why? Button
                    </button>
                    <button
                        className={`demo-tab ${activeDemo === 'hardening' ? 'active' : ''}`}
                        onClick={() => setActiveDemo('hardening')}
                    >
                        API Hardening
                    </button>
                    <button
                        className={`demo-tab ${activeDemo === 'testing' ? 'active' : ''}`}
                        onClick={() => setActiveDemo('testing')}
                    >
                        Test Generation
                    </button>
                </div>
            </div>

            <div className="demo-content">
                {activeDemo === 'why-button' && renderWhyButtonDemo()}
                {activeDemo === 'hardening' && renderHardeningDemo()}
                {activeDemo === 'testing' && renderTestGenerationDemo()}
            </div>

            <div className="demo-footer">
                <div className="implementation-status">
                    <h4>✅ Implementation Status</h4>
                    <div className="status-grid">
                        <div className="status-item completed">
                            <span className="status-icon">✅</span>
                            <span>AI "Why?" Button with RAG</span>
                        </div>
                        <div className="status-item completed">
                            <span className="status-icon">✅</span>
                            <span>One-Click API Hardening</span>
                        </div>
                        <div className="status-item completed">
                            <span className="status-icon">✅</span>
                            <span>AI Test Case Generation</span>
                        </div>
                        <div className="status-item upcoming">
                            <span className="status-icon">🔄</span>
                            <span>Phase 2: Advanced Intelligence</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Phase1Demo;
import React, { useState } from 'react';
import { useSpecStore } from '../../../store/specStore';
import Button from '../../../components/ui/Button';
import LoadingSpinner from '../../../components/ui/LoadingSpinner';
import ErrorMessage from '../../../components/ui/ErrorMessage';
import AISpecGenerator from './AISpecGenerator';
import SecurityAnalysisTab from './SecurityAnalysisTab';
import {
    addOAuth2Security,
    addRateLimiting,
    addCaching,
    hardenOperationComplete,
    generateOperationTestCases,
    generateTestSuite
} from '../../../api/validationService';
import '../ai-features.css';

const AI_TABS = {
    ASSISTANT: 'assistant',
    SECURITY: 'security',
    HARDENING: 'hardening',
    TESTING: 'testing',
    GENERATOR: 'generator'
};

function AIPanel() {
    const [activeTab, setActiveTab] = useState(AI_TABS.ASSISTANT);
    const {
        aiResponse,
        aiError,
        clearAiResponse,
        specText
    } = useSpecStore();

    const renderTabContent = () => {
        switch (activeTab) {
            case AI_TABS.ASSISTANT:
                return <AIAssistantTab />;
            case AI_TABS.SECURITY:
                return <SecurityAnalysisTab specContent={specText} />;
            case AI_TABS.HARDENING:
                return <AIHardeningTab />;
            case AI_TABS.TESTING:
                return <AITestingTab />;
            case AI_TABS.GENERATOR:
                return <AISpecGenerator />;
            default:
                return <AIAssistantTab />;
        }
    };

    return (
        <div className="ai-panel">
            <div className="ai-panel-header">
                <h3>AI Features</h3>
                <div className="ai-tabs">
                    {Object.entries(AI_TABS).map(([key, value]) => (
                        <button
                            key={value}
                            className={`ai-tab ${activeTab === value ? 'active' : ''}`}
                            onClick={() => setActiveTab(value)}
                        >
                            {key.charAt(0) + key.slice(1).toLowerCase()}
                        </button>
                    ))}
                </div>
            </div>

            <div className="ai-panel-content">
                {renderTabContent()}
            </div>

            {/* Response/Error Display */}
            {aiError && (
                <div className="ai-response-section">
                    <ErrorMessage message={aiError} />
                </div>
            )}

            {aiResponse && (
                <div className="ai-response-section">
                    <h4>AI Response</h4>
                    <div className="ai-response-content">
                        <pre>{JSON.stringify(aiResponse, null, 2)}</pre>
                    </div>
                    <Button
                        variant="secondary"
                        size="small"
                        onClick={clearAiResponse}
                    >
                        Clear Response
                    </Button>
                </div>
            )}
        </div>
    );
}

function AIAssistantTab() {
    const {
        aiPrompt,
        setAiPrompt,
        submitAIRequest,
        processSpecification,
        isAiProcessing,
        isStreaming
    } = useSpecStore();

    const [streamingMode, setStreamingMode] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!aiPrompt.trim()) return;

        if (streamingMode) {
            const request = {
                operationType: 'MODIFY',
                prompt: aiPrompt,
                streaming: 'REALTIME'
            };
            await processSpecification(request);
        } else {
            await submitAIRequest();
        }
    };

    return (
        <div className="ai-assistant-tab">
            <div className="ai-settings">
                <label>
                    <input
                        type="checkbox"
                        checked={streamingMode}
                        onChange={(e) => setStreamingMode(e.target.checked)}
                    />
                    Enable Streaming Mode
                </label>
            </div>

            <form className="ai-assistant-form" onSubmit={handleSubmit}>
                <div className="ai-input-group">
                    <textarea
                        className="ai-input"
                        placeholder="Describe what you want to do with your API specification..."
                        value={aiPrompt}
                        onChange={(e) => setAiPrompt(e.target.value)}
                        disabled={isAiProcessing}
                        rows={4}
                    />
                    <div className="ai-input-actions">
                        <Button
                            type="submit"
                            variant="ai"
                            loading={isAiProcessing}
                            disabled={!aiPrompt.trim()}
                        >
                            {streamingMode ? 'Stream Process' : 'Process'}
                        </Button>
                    </div>
                </div>
            </form>

            {isStreaming && (
                <div className="streaming-indicator">
                    <LoadingSpinner />
                    <span>Streaming response...</span>
                </div>
            )}

            <div className="ai-suggestions">
                <h4>Suggestion Templates</h4>
                <div className="suggestion-buttons">
                    <Button
                        variant="secondary"
                        size="small"
                        onClick={() => setAiPrompt('Add input validation to all POST endpoints')}
                    >
                        Add Validation
                    </Button>
                    <Button
                        variant="secondary"
                        size="small"
                        onClick={() => setAiPrompt('Add error response schemas to all endpoints')}
                    >
                        Add Error Schemas
                    </Button>
                    <Button
                        variant="secondary"
                        size="small"
                        onClick={() => setAiPrompt('Add authentication security scheme')}
                    >
                        Add Security
                    </Button>
                    <Button
                        variant="secondary"
                        size="small"
                        onClick={() => setAiPrompt('Generate realistic example responses')}
                    >
                        Add Examples
                    </Button>
                </div>
            </div>
        </div>
    );
}

function AIHardeningTab() {
    const { sessionId, specText } = useSpecStore();
    const [selectedPath, setSelectedPath] = useState('/users');
    const [selectedMethod, setSelectedMethod] = useState('GET');
    const [rateLimit, setRateLimit] = useState('100/hour');
    const [cacheTtl, setCacheTtl] = useState('300');
    const [loading, setLoading] = useState({});
    const [results, setResults] = useState({});
    const [errors, setErrors] = useState({});

    const runHardening = async (type, apiCall) => {
        setLoading(prev => ({ ...prev, [type]: true }));
        setErrors(prev => ({ ...prev, [type]: null }));

        try {
            const result = await apiCall();
            setResults(prev => ({ ...prev, [type]: result }));
        } catch (error) {
            setErrors(prev => ({ ...prev, [type]: error.message || 'Operation failed' }));
        } finally {
            setLoading(prev => ({ ...prev, [type]: false }));
        }
    };

    return (
        <div className="ai-hardening-tab">
            <h4>🛡️ One-Click API Hardening</h4>
            <p>Apply security and performance patterns to your API operations instantly.</p>

            <div className="hardening-controls">
                <div className="input-group">
                    <label>Path:</label>
                    <input
                        type="text"
                        value={selectedPath}
                        onChange={(e) => setSelectedPath(e.target.value)}
                        placeholder="/users"
                    />
                </div>
                <div className="input-group">
                    <label>Method:</label>
                    <select value={selectedMethod} onChange={(e) => setSelectedMethod(e.target.value)}>
                        <option value="GET">GET</option>
                        <option value="POST">POST</option>
                        <option value="PUT">PUT</option>
                        <option value="DELETE">DELETE</option>
                        <option value="PATCH">PATCH</option>
                    </select>
                </div>
            </div>

            <div className="pattern-buttons">
                <Button
                    variant="primary"
                    onClick={() => runHardening('oauth2', () =>
                        addOAuth2Security(sessionId, selectedPath, selectedMethod)
                    )}
                    loading={loading['oauth2']}
                >
                    Add OAuth2 Security
                </Button>

                <div className="input-group inline">
                    <input
                        type="text"
                        value={rateLimit}
                        onChange={(e) => setRateLimit(e.target.value)}
                        placeholder="100/hour"
                        style={{ width: '100px', marginRight: '8px' }}
                    />
                    <Button
                        variant="secondary"
                        onClick={() => runHardening('rateLimit', () =>
                            addRateLimiting(sessionId, selectedPath, selectedMethod, rateLimit)
                        )}
                        loading={loading['rateLimit']}
                    >
                        Add Rate Limiting
                    </Button>
                </div>

                <div className="input-group inline">
                    <input
                        type="text"
                        value={cacheTtl}
                        onChange={(e) => setCacheTtl(e.target.value)}
                        placeholder="300"
                        style={{ width: '80px', marginRight: '8px' }}
                    />
                    <Button
                        variant="secondary"
                        onClick={() => runHardening('caching', () =>
                            addCaching(sessionId, selectedPath, selectedMethod, cacheTtl)
                        )}
                        loading={loading['caching']}
                    >
                        Add HTTP Caching
                    </Button>
                </div>

                <Button
                    variant="ai"
                    onClick={() => runHardening('complete', () =>
                        hardenOperationComplete(sessionId, selectedPath, selectedMethod)
                    )}
                    loading={loading['complete']}
                >
                    Complete Hardening
                </Button>
            </div>

            {Object.entries(results).map(([key, result]) => {
                if (!result?.success) return null;
                return (
                    <div key={key} className="result-success">
                        <h5>✅ {key.replace(/([A-Z])/g, ' $1').trim()} Applied</h5>
                        {result.data?.appliedPatterns && (
                            <p>Applied patterns: {result.data.appliedPatterns.join(', ')}</p>
                        )}
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

            {Object.entries(errors).map(([key, error]) => (
                error && <ErrorMessage key={key} message={`${key} failed: ${error}`} />
            ))}

            <div className="features-info">
                <h5>✨ Features:</h5>
                <ul>
                    <li>OAuth2 security scheme and requirements</li>
                    <li>Rate limiting headers and 429 responses</li>
                    <li>HTTP caching with ETag and 304 responses</li>
                    <li>Idempotency keys for safe retries</li>
                    <li>Standard error response patterns</li>
                </ul>
            </div>
        </div>
    );
}

function AITestingTab() {
    const { sessionId, specText } = useSpecStore();
    const [selectedPath, setSelectedPath] = useState('/users');
    const [selectedMethod, setSelectedMethod] = useState('GET');
    const [operationSummary, setOperationSummary] = useState('Get list of users');
    const [loading, setLoading] = useState({});
    const [results, setResults] = useState({});
    const [errors, setErrors] = useState({});

    const runTestGeneration = async (type, apiCall) => {
        setLoading(prev => ({ ...prev, [type]: true }));
        setErrors(prev => ({ ...prev, [type]: null }));

        try {
            const result = await apiCall();
            setResults(prev => ({ ...prev, [type]: result }));
        } catch (error) {
            setErrors(prev => ({ ...prev, [type]: error.message || 'Test generation failed' }));
        } finally {
            setLoading(prev => ({ ...prev, [type]: false }));
        }
    };

    return (
        <div className="ai-testing-tab">
            <h4>🧪 AI Test Generation</h4>
            <p>Generate comprehensive test cases for your API operations using AI.</p>

            <div className="test-controls">
                <div className="input-group">
                    <label>Path:</label>
                    <input
                        type="text"
                        value={selectedPath}
                        onChange={(e) => setSelectedPath(e.target.value)}
                        placeholder="/users"
                    />
                </div>
                <div className="input-group">
                    <label>Method:</label>
                    <select value={selectedMethod} onChange={(e) => setSelectedMethod(e.target.value)}>
                        <option value="GET">GET</option>
                        <option value="POST">POST</option>
                        <option value="PUT">PUT</option>
                        <option value="DELETE">DELETE</option>
                        <option value="PATCH">PATCH</option>
                    </select>
                </div>
                <div className="input-group">
                    <label>Summary:</label>
                    <input
                        type="text"
                        value={operationSummary}
                        onChange={(e) => setOperationSummary(e.target.value)}
                        placeholder="Operation summary"
                    />
                </div>
            </div>

            <div className="test-buttons">
                <Button
                    variant="primary"
                    onClick={() => runTestGeneration('operation', () =>
                        generateOperationTestCases(sessionId, selectedPath, selectedMethod, operationSummary)
                    )}
                    loading={loading['operation']}
                >
                    Generate Operation Tests
                </Button>

                <Button
                    variant="ai"
                    onClick={() => runTestGeneration('suite', () =>
                        generateTestSuite(specText, { testTypes: ['positive', 'negative', 'edge_cases'], maxOperations: 5 })
                    )}
                    loading={loading['suite']}
                >
                    Generate Complete Test Suite
                </Button>
            </div>

            {results['operation']?.success && (
                <div className="result-success">
                    <h5>✅ Test Cases Generated</h5>
                    <div className="test-summary">
                        <p><strong>Operation:</strong> {results['operation'].data.summary?.operation}</p>
                        <p><strong>Total Tests:</strong> {results['operation'].data.summary?.total_tests}</p>
                        <p><strong>Positive:</strong> {results['operation'].data.summary?.positive_tests}</p>
                        <p><strong>Negative:</strong> {results['operation'].data.summary?.negative_tests}</p>
                        <p><strong>Edge Cases:</strong> {results['operation'].data.summary?.edge_case_tests}</p>
                    </div>

                    <div className="test-cases">
                        <h6>Sample Test Cases:</h6>
                        {results['operation'].data.test_cases?.slice(0, 3).map((testCase, index) => (
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

            {results['suite']?.success && (
                <div className="result-success">
                    <h5>✅ Test Suite Generated</h5>
                    <div className="suite-summary">
                        <p><strong>Suite:</strong> {results['suite'].data.test_suite?.name}</p>
                        <p><strong>Total Tests:</strong> {results['suite'].data.test_suite?.statistics?.total_tests}</p>
                        <p><strong>Coverage:</strong> {results['suite'].data.test_suite?.statistics?.coverage}</p>
                        <p><strong>Estimated Duration:</strong> {results['suite'].data.execution_plan?.estimated_duration}</p>
                    </div>
                </div>
            )}

            {Object.entries(errors).map(([key, error]) => (
                error && <ErrorMessage key={key} message={error} />
            ))}

            <div className="features-info">
                <h5>✨ Features:</h5>
                <ul>
                    <li>AI-powered test case generation with realistic data</li>
                    <li>Positive, negative, and edge case coverage</li>
                    <li>Framework-agnostic test structure</li>
                    <li>Complete test suite generation for entire APIs</li>
                </ul>
            </div>
        </div>
    );
}

export default AIPanel;
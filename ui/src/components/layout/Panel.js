import React from 'react';
import PropTypes from 'prop-types';
import ErrorBoundary from '../common/ErrorBoundary';
import LoadingSpinner from '../ui/LoadingSpinner';

function Panel({
    title,
    children,
    className = '',
    loading = false,
    error = null,
    onRetry,
    header = null,
    footer = null,
    collapsible = false,
    collapsed = false,
    onToggleCollapse,
    ...props
}) {
    const panelClass = `panel-container ${className} ${collapsed ? 'collapsed' : ''}`;

    const handleToggleCollapse = () => {
        if (collapsible && onToggleCollapse) {
            onToggleCollapse(!collapsed);
        }
    };

    return (
        <div className={panelClass} {...props}>
            {title && (
                <div className="panel-header">
                    <span className="panel-title">{title}</span>
                    {collapsible && (
                        <button
                            className="panel-collapse-btn"
                            onClick={handleToggleCollapse}
                            type="button"
                            aria-label={collapsed ? 'Expand panel' : 'Collapse panel'}
                        >
                            {collapsed ? '▶' : '▼'}
                        </button>
                    )}
                    {header}
                </div>
            )}

            <div className="panel-content">
                <ErrorBoundary
                    title="Panel Error"
                    message="This panel encountered an error. Please try again."
                >
                    {loading ? (
                        <LoadingSpinner centered text="Loading..." />
                    ) : error ? (
                        <div className="panel-error">
                            <div className="error-content">
                                <span className="error-icon">⚠️</span>
                                <div className="error-message">{error}</div>
                                {onRetry && (
                                    <button
                                        className="error-retry-btn"
                                        onClick={onRetry}
                                        type="button"
                                    >
                                        Retry
                                    </button>
                                )}
                            </div>
                        </div>
                    ) : (
                        children
                    )}
                </ErrorBoundary>
            </div>

            {footer && (
                <div className="panel-footer">
                    {footer}
                </div>
            )}
        </div>
    );
}

Panel.propTypes = {
    title: PropTypes.string,
    children: PropTypes.node,
    className: PropTypes.string,
    loading: PropTypes.bool,
    error: PropTypes.string,
    onRetry: PropTypes.func,
    header: PropTypes.node,
    footer: PropTypes.node,
    collapsible: PropTypes.bool,
    collapsed: PropTypes.bool,
    onToggleCollapse: PropTypes.func
};

export default Panel;
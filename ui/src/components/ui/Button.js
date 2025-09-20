import React from 'react';
import PropTypes from 'prop-types';

const BUTTON_VARIANTS = {
    primary: 'toolbar-button',
    secondary: 'toolbar-button secondary',
    danger: 'toolbar-button danger',
    success: 'toolbar-button success',
    ai: 'ai-submit-button',
    fix: 'fix-button',
    mock: 'start-mock-button',
    request: 'send-request-button',
    refresh: 'refresh-button'
};

const BUTTON_SIZES = {
    small: 'btn-small',
    medium: 'btn-medium',
    large: 'btn-large'
};

function Button({
    variant = 'primary',
    size = 'medium',
    disabled = false,
    loading = false,
    children,
    onClick,
    type = 'button',
    className = '',
    ...props
}) {
    const baseClass = BUTTON_VARIANTS[variant] || BUTTON_VARIANTS.primary;
    const sizeClass = BUTTON_SIZES[size] || '';
    const loadingClass = loading ? 'loading' : '';
    const disabledClass = disabled ? 'disabled' : '';

    const combinedClassName = [
        baseClass,
        sizeClass,
        loadingClass,
        disabledClass,
        className
    ].filter(Boolean).join(' ');

    const handleClick = (event) => {
        if (disabled || loading) {
            event.preventDefault();
            return;
        }
        if (onClick) {
            onClick(event);
        }
    };

    return (
        <button
            type={type}
            className={combinedClassName}
            disabled={disabled || loading}
            onClick={handleClick}
            {...props}
        >
            {loading ? (
                <span>
                    <span className="loading-spinner">⟳</span>
                    {children}
                </span>
            ) : (
                children
            )}
        </button>
    );
}

Button.propTypes = {
    variant: PropTypes.oneOf(Object.keys(BUTTON_VARIANTS)),
    size: PropTypes.oneOf(Object.keys(BUTTON_SIZES)),
    disabled: PropTypes.bool,
    loading: PropTypes.bool,
    children: PropTypes.node.isRequired,
    onClick: PropTypes.func,
    type: PropTypes.oneOf(['button', 'submit', 'reset']),
    className: PropTypes.string
};

export default Button;
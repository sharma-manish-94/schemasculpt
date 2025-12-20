import React, {
  useMemo,
  useCallback,
  useRef,
  useEffect,
  useState,
} from "react";

/**
 * Memoization utility for expensive computations
 * @param {Function} fn - Function to memoize
 * @param {Array} deps - Dependencies array
 * @returns {any} Memoized result
 */
export const useMemoizedValue = (fn, deps) => {
  return useMemo(fn, deps);
};

/**
 * Stable callback that doesn't change on every render
 * @param {Function} callback - Callback function
 * @param {Array} deps - Dependencies array
 * @returns {Function} Stable callback
 */
export const useStableCallback = (callback, deps) => {
  return useCallback(callback, deps);
};

/**
 * Custom hook for preventing unnecessary renders
 * @param {Object} props - Component props
 * @returns {Object} Previous props if no change detected
 */
export const usePreviousProps = (props) => {
  const ref = useRef();
  useEffect(() => {
    ref.current = props;
  });
  return ref.current;
};

/**
 * Throttle function calls
 * @param {Function} func - Function to throttle
 * @param {number} limit - Time limit in milliseconds
 * @returns {Function} Throttled function
 */
export const throttle = (func, limit) => {
  let inThrottle;
  return function (...args) {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
};

/**
 * Debounce function calls
 * @param {Function} func - Function to debounce
 * @param {number} delay - Delay in milliseconds
 * @returns {Function} Debounced function
 */
export const debounce = (func, delay) => {
  let timeoutId;
  return function (...args) {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func.apply(this, args), delay);
  };
};

/**
 * Check if two objects are shallowly equal
 * @param {Object} obj1 - First object
 * @param {Object} obj2 - Second object
 * @returns {boolean} True if shallowly equal
 */
export const shallowEqual = (obj1, obj2) => {
  if (obj1 === obj2) return true;

  if (!obj1 || !obj2) return false;

  const keys1 = Object.keys(obj1);
  const keys2 = Object.keys(obj2);

  if (keys1.length !== keys2.length) return false;

  for (let key of keys1) {
    if (obj1[key] !== obj2[key]) return false;
  }

  return true;
};

/**
 * HOC for preventing unnecessary re-renders
 * @param {Component} Component - React component
 * @param {Function} areEqual - Custom comparison function
 * @returns {Component} Memoized component
 */
export const withMemo = (Component, areEqual = shallowEqual) => {
  return React.memo(Component, areEqual);
};

/**
 * Custom hook for intersection observer (lazy loading)
 * @param {Object} options - Intersection observer options
 * @returns {[Function, boolean]} [ref, isVisible]
 */
export const useIntersectionObserver = (options = {}) => {
  const [isIntersecting, setIsIntersecting] = useState(false);
  const ref = useRef();

  useEffect(() => {
    const observer = new IntersectionObserver(([entry]) => {
      setIsIntersecting(entry.isIntersecting);
    }, options);

    if (ref.current) {
      observer.observe(ref.current);
    }

    return () => {
      observer.disconnect();
    };
  }, [options]);

  return [ref, isIntersecting];
};

/**
 * Virtual scrolling utilities
 */
export const calculateVisibleItems = (
  containerHeight,
  itemHeight,
  scrollTop,
  totalItems,
) => {
  const startIndex = Math.floor(scrollTop / itemHeight);
  const visibleCount = Math.ceil(containerHeight / itemHeight);
  const endIndex = Math.min(startIndex + visibleCount + 1, totalItems - 1);

  return {
    startIndex: Math.max(0, startIndex),
    endIndex,
    visibleCount,
  };
};

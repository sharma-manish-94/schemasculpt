import { useEffect, useCallback } from "react";

const useKeyboardShortcuts = (shortcuts, deps = []) => {
  const handleKeyDown = useCallback(
    (event) => {
      const isMac = navigator.platform.toUpperCase().indexOf("MAC") >= 0;
      const modifier = isMac ? event.metaKey : event.ctrlKey;

      shortcuts.forEach(
        ({
          key,
          modifier: needsModifier,
          shift,
          callback,
          preventDefault = true,
        }) => {
          const keyMatch = event.key.toLowerCase() === key.toLowerCase();
          const modifierMatch = needsModifier ? modifier : !modifier;
          const shiftMatch = shift ? event.shiftKey : !event.shiftKey;

          if (keyMatch && modifierMatch && shiftMatch) {
            if (preventDefault) {
              event.preventDefault();
            }
            callback(event);
          }
        },
      );
      // eslint-disable-next-line react-hooks/exhaustive-deps
    },
    [shortcuts, ...deps],
  );

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);
};

export default useKeyboardShortcuts;

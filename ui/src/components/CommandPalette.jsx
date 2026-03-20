import React, { useState, useEffect, useRef, useMemo } from "react";
import "./CommandPalette.css";

const CommandPalette = ({ isOpen, onClose, commands, onExecute }) => {
  const [search, setSearch] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef(null);
  const listRef = useRef(null);

  // Filter commands based on search
  const filteredCommands = useMemo(() => {
    if (!search.trim()) return commands;
    const searchLower = search.toLowerCase();
    return commands.filter(
      (cmd) =>
        cmd.label.toLowerCase().includes(searchLower) ||
        cmd.category?.toLowerCase().includes(searchLower) ||
        cmd.keywords?.some((k) => k.toLowerCase().includes(searchLower)),
    );
  }, [commands, search]);

  // Reset selection when filtered results change
  useEffect(() => {
    setSelectedIndex(0);
  }, [filteredCommands]);

  // Focus input when opened
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
      setSearch("");
      setSelectedIndex(0);
    }
  }, [isOpen]);

  // Handle keyboard navigation
  const handleKeyDown = (e) => {
    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        setSelectedIndex((prev) =>
          prev < filteredCommands.length - 1 ? prev + 1 : 0,
        );
        break;
      case "ArrowUp":
        e.preventDefault();
        setSelectedIndex((prev) =>
          prev > 0 ? prev - 1 : filteredCommands.length - 1,
        );
        break;
      case "Enter":
        e.preventDefault();
        if (filteredCommands[selectedIndex]) {
          onExecute(filteredCommands[selectedIndex]);
          onClose();
        }
        break;
      case "Escape":
        e.preventDefault();
        onClose();
        break;
      default:
        break;
    }
  };

  // Scroll selected item into view
  useEffect(() => {
    if (listRef.current) {
      const selectedItem = listRef.current.children[selectedIndex];
      if (selectedItem) {
        selectedItem.scrollIntoView({ block: "nearest" });
      }
    }
  }, [selectedIndex]);

  if (!isOpen) return null;

  // Group commands by category
  const groupedCommands = filteredCommands.reduce((acc, cmd) => {
    const category = cmd.category || "Actions";
    if (!acc[category]) acc[category] = [];
    acc[category].push(cmd);
    return acc;
  }, {});

  const isMac = navigator.platform.toUpperCase().indexOf("MAC") >= 0;
  const modKey = isMac ? "⌘" : "Ctrl";

  let flatIndex = 0;

  return (
    <div className="command-palette-overlay" onClick={onClose}>
      <div className="command-palette" onClick={(e) => e.stopPropagation()}>
        <div className="command-palette-input-wrapper">
          <span className="command-palette-icon">🔍</span>
          <input
            ref={inputRef}
            type="text"
            className="command-palette-input"
            placeholder="Type a command or search..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <kbd className="command-palette-hint">esc</kbd>
        </div>

        <div className="command-palette-results" ref={listRef}>
          {Object.entries(groupedCommands).map(([category, cmds]) => (
            <div key={category} className="command-group">
              <div className="command-group-label">{category}</div>
              {cmds.map((cmd) => {
                const currentIndex = flatIndex++;
                const isSelected = currentIndex === selectedIndex;
                return (
                  <button
                    key={cmd.id}
                    className={`command-item ${isSelected ? "selected" : ""}`}
                    onClick={() => {
                      onExecute(cmd);
                      onClose();
                    }}
                    onMouseEnter={() => setSelectedIndex(currentIndex)}
                  >
                    <span className="command-icon">{cmd.icon}</span>
                    <span className="command-label">{cmd.label}</span>
                    {cmd.shortcut && (
                      <kbd className="command-shortcut">
                        {cmd.shortcut
                          .replace("Cmd", modKey)
                          .replace("Ctrl", modKey)}
                      </kbd>
                    )}
                  </button>
                );
              })}
            </div>
          ))}

          {filteredCommands.length === 0 && (
            <div className="command-empty">
              <p>No commands found</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CommandPalette;

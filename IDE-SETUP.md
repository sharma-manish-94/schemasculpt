# IDE Setup Guide for SchemaSculpt

This guide will help you configure IntelliJ IDEA, PyCharm, and VS Code to automatically format code according to SchemaSculpt's standards. This will prevent CI/CD failures due to formatting issues.

## Quick Start

### 1. Install Pre-commit Hooks (Recommended)

The easiest way to ensure consistent formatting is to install pre-commit hooks that automatically format your code before each commit:

```bash
# Install pre-commit (requires Python)
pip install pre-commit

# Install the hooks (run from project root)
pre-commit install

# Test the setup (optional)
pre-commit run --all-files
```

Now every time you commit, your code will be automatically formatted!

### 2. Manual Formatting Scripts

If you prefer to format manually before committing:

```bash
# Format all code
./format-all.sh

# Or format individual services
cd api && ./format-java.sh          # Java backend
cd ai_service && ./format-python.sh # Python AI service
cd ui && ./format-ui.sh             # React frontend
```

---

## IDE-Specific Configuration

### IntelliJ IDEA (for Java Backend)

#### 1. Install EditorConfig Plugin
- EditorConfig is usually bundled with IntelliJ IDEA
- Verify: **Settings → Plugins → Installed → EditorConfig**
- The `.editorconfig` file at the project root will be automatically detected

#### 2. Configure Google Java Format

**Option A: Using Google Java Format Plugin (Recommended)**

1. Install the plugin:
   - **Settings → Plugins → Marketplace**
   - Search for "google-java-format"
   - Install and restart

2. Enable the plugin:
   - **Settings → google-java-format Settings**
   - ✓ Enable google-java-format
   - Select **Code Style: Google**

3. Configure formatting shortcut:
   - **Settings → Keymap → Main Menu → Code → Reformat Code**
   - Will now use Google Java Format

**Option B: Using Spotless Maven Plugin**

1. In IntelliJ, open the Maven tool window
2. Navigate to: **schemasculpt_api → Plugins → spotless → spotless:apply**
3. Right-click → **Create 'schemasculpt_api [spotless:apply]'...**
4. Save this configuration for quick access

Run before committing:
```bash
cd api
./mvnw spotless:apply
```

#### 3. Configure Save Actions

Install "Save Actions" plugin for auto-formatting on save:

1. **Settings → Plugins → Marketplace**
2. Search for "Save Actions"
3. Install and restart

4. Configure:
   - **Settings → Save Actions**
   - ✓ Activate save actions on save
   - ✓ Reformat file
   - ✓ Optimize imports

#### 4. Disable Conflicting Formatters

Ensure IntelliJ doesn't use conflicting formatting:
- **Settings → Editor → Code Style → Java**
- Click **Set from...** → **Predefined Style** → **Google Style**
- This matches the Google Java Format plugin

---

### PyCharm (for Python AI Service)

#### 1. Install EditorConfig Plugin
- Usually bundled with PyCharm
- Verify: **Settings → Plugins → Installed → EditorConfig**

#### 2. Configure Black Formatter

**Option A: Using Black Plugin (Recommended)**

1. Install Black:
   ```bash
   cd ai_service
   source venv/bin/activate  # or .venv/bin/activate
   pip install black
   ```

2. Install PyCharm Black plugin:
   - **Settings → Plugins → Marketplace**
   - Search for "BlackConnect" or use File Watchers (below)

**Option B: Using File Watchers**

1. **Settings → Tools → File Watchers**
2. Click **+** → **Custom**
3. Configure:
   - **Name:** Black Formatter
   - **File type:** Python
   - **Scope:** Project Files
   - **Program:** `$PyInterpreterDirectory$/black`
   - **Arguments:** `$FilePath$`
   - **Output paths to refresh:** `$FilePath$`
   - **Working directory:** `$ProjectFileDir$`
   - ✓ Auto-save edited files to trigger the watcher

4. Repeat for isort:
   - **Name:** isort
   - **Program:** `$PyInterpreterDirectory$/isort`
   - **Arguments:** `$FilePath$`

#### 3. Configure Flake8

1. Install flake8:
   ```bash
   pip install flake8
   ```

2. **Settings → Tools → External Tools**
3. Click **+** and configure:
   - **Name:** Flake8
   - **Program:** `$PyInterpreterDirectory$/flake8`
   - **Arguments:** `$FilePath$`
   - **Working directory:** `$ProjectFileDir$`

4. Optionally create a keyboard shortcut for quick linting

---

### VS Code (for All Services)

#### 1. Install EditorConfig Extension

```
ext install EditorConfig.EditorConfig
```

The `.editorconfig` file will be automatically detected and applied.

#### 2. Configure Java Formatting

1. Install Java extensions:
   ```
   ext install vscjava.vscode-java-pack
   ```

2. Install "Language Support for Java(TM) by Red Hat"

3. Create/edit `.vscode/settings.json` in the project root:

```json
{
  "java.format.settings.url": "https://raw.githubusercontent.com/google/styleguide/gh-pages/eclipse-java-google-style.xml",
  "java.format.settings.profile": "GoogleStyle",
  "java.checkstyle.configuration": "${workspaceFolder}/api/checkstyle.xml",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "[java]": {
    "editor.defaultFormatter": "redhat.java",
    "editor.tabSize": 2,
    "editor.insertSpaces": true
  }
}
```

#### 3. Configure Python Formatting

1. Install Python extensions:
   ```
   ext install ms-python.python
   ext install ms-python.black-formatter
   ext install ms-python.isort
   ext install ms-python.flake8
   ```

2. Update `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/ai_service/venv/bin/python",
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    },
    "editor.tabSize": 4,
    "editor.insertSpaces": true
  },
  "black-formatter.args": [
    "--config",
    "${workspaceFolder}/ai_service/pyproject.toml"
  ],
  "isort.args": [
    "--settings-path",
    "${workspaceFolder}/ai_service/pyproject.toml"
  ],
  "flake8.args": [
    "--config",
    "${workspaceFolder}/ai_service/.flake8"
  ],
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true
}
```

#### 4. Configure JavaScript/TypeScript Formatting

1. Install extensions:
   ```
   ext install dbaeumer.vscode-eslint
   ext install esbenp.prettier-vscode
   ```

2. Update `.vscode/settings.json`:

```json
{
  "[javascript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true,
    "editor.tabSize": 2
  },
  "[javascriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true,
    "editor.tabSize": 2
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true,
    "editor.tabSize": 2
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true,
    "editor.tabSize": 2
  },
  "eslint.workingDirectories": [
    "ui"
  ],
  "prettier.tabWidth": 2,
  "prettier.printWidth": 80
}
```

---

## Formatting Standards Summary

| Language | Indentation | Line Length | Formatter |
|----------|-------------|-------------|-----------|
| **Java** | 2 spaces | 100 chars | Google Java Format |
| **Python** | 4 spaces | 88 chars | Black |
| **JavaScript/TypeScript** | 2 spaces | 80 chars | Prettier |
| **JSON/YAML** | 2 spaces | - | Prettier |

---

## Troubleshooting

### "My IDE formatting differs from CI"

1. Ensure you've pulled the latest changes (especially `.editorconfig` and config files)
2. Restart your IDE to reload configuration
3. Run the format scripts manually: `./format-all.sh`
4. Check that pre-commit hooks are installed: `pre-commit run --all-files`

### "Checkstyle errors in CI but local formatting looks fine"

- Run `cd api && ./mvnw checkstyle:check` locally
- Ensure you're using Spotless: `cd api && ./mvnw spotless:apply`
- Check that your IntelliJ is using Google Java Format (2 spaces, not 4)

### "Black/Flake8 errors in CI"

- Activate your Python venv: `cd ai_service && source venv/bin/activate`
- Run formatters: `black . && isort .`
- Check linting: `flake8 .`
- Ensure config files exist: `.flake8` and `pyproject.toml`

### "ESLint/Prettier conflicts"

- Prettier should be the final formatter
- Ensure ESLint config doesn't conflict with Prettier
- Run: `cd ui && npx prettier --write "src/**/*.{js,jsx,ts,tsx}"`

---

## Complete VS Code Configuration

Create `.vscode/settings.json` at project root with these complete settings:

```json
{
  "editor.formatOnSave": true,
  "editor.insertSpaces": true,
  "files.insertFinalNewline": true,
  "files.trimTrailingWhitespace": true,

  "java.format.settings.url": "https://raw.githubusercontent.com/google/styleguide/gh-pages/eclipse-java-google-style.xml",
  "java.format.settings.profile": "GoogleStyle",
  "java.checkstyle.configuration": "${workspaceFolder}/api/checkstyle.xml",

  "[java]": {
    "editor.defaultFormatter": "redhat.java",
    "editor.tabSize": 2,
    "editor.insertSpaces": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  },

  "python.defaultInterpreterPath": "${workspaceFolder}/ai_service/venv/bin/python",

  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.formatOnSave": true,
    "editor.tabSize": 4,
    "editor.insertSpaces": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  },

  "black-formatter.args": ["--config", "${workspaceFolder}/ai_service/pyproject.toml"],
  "isort.args": ["--settings-path", "${workspaceFolder}/ai_service/pyproject.toml"],
  "flake8.args": ["--config", "${workspaceFolder}/ai_service/.flake8"],
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,

  "[javascript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true,
    "editor.tabSize": 2
  },
  "[javascriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true,
    "editor.tabSize": 2
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true,
    "editor.tabSize": 2
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true,
    "editor.tabSize": 2
  },
  "[json]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.tabSize": 2
  },
  "[yaml]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.tabSize": 2
  },

  "eslint.workingDirectories": ["ui"],
  "prettier.tabWidth": 2,
  "prettier.printWidth": 80
}
```

---

## Verification

After setting up your IDE, verify everything works:

```bash
# 1. Install pre-commit hooks
pip install pre-commit
pre-commit install

# 2. Format all code
./format-all.sh

# 3. Run pre-commit checks
pre-commit run --all-files

# 4. Verify no changes are needed
git status  # Should show no unstaged changes
```

If you see no formatting changes after running these commands, your IDE is configured correctly!

---

## Additional Resources

- [EditorConfig Documentation](https://editorconfig.org/)
- [Google Java Style Guide](https://google.github.io/styleguide/javaguide.html)
- [Black Python Formatter](https://black.readthedocs.io/)
- [Prettier Documentation](https://prettier.io/docs/en/)
- [Pre-commit Framework](https://pre-commit.com/)

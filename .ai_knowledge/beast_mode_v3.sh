#!/bin/bash
# =============================================================================
# AI BEAST MODE v3: Peer Review Architecture
# =============================================================================
# Source this file in your shell: source .ai_knowledge/beast_mode_v3.sh
# Or add to ~/.zshrc: source /path/to/project/.ai_knowledge/beast_mode_v3.sh
# =============================================================================

# shellcheck disable=SC2034  # Variables are used when sourced

# -----------------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------------
export AI_WORKSPACE=".ai_workspace"
export AI_KNOWLEDGE=".ai_knowledge"
export MAX_REVIEW_ITERATIONS=3
export MAX_CONSENSUS_ATTEMPTS=2

# Project type detection (java, node, python, or auto)
export PROJECT_TYPE="${PROJECT_TYPE:-auto}"

# ANSI color codes for better readability
export COLOR_RESET='\033[0m'
export COLOR_RED='\033[0;31m'
export COLOR_GREEN='\033[0;32m'
export COLOR_YELLOW='\033[0;33m'
export COLOR_BLUE='\033[0;34m'
export COLOR_CYAN='\033[0;36m'

# -----------------------------------------------------------------------------
# PROJECT TYPE DETECTION AND COMMANDS
# -----------------------------------------------------------------------------

function _detect_project_type() {
    if [ "$PROJECT_TYPE" != "auto" ]; then
        echo "$PROJECT_TYPE"
        return
    fi

    # Auto-detect based on project files (prioritize Gradle over Maven)
    if [ -f "build.gradle" ] || [ -f "build.gradle.kts" ] || \
       [ -f "api/build.gradle" ] || [ -f "api/build.gradle.kts" ] || \
       [ -f "pom.xml" ] || [ -f "api/pom.xml" ]; then
        echo "java"
    elif [ -f "package.json" ] || [ -f "ui/package.json" ]; then
        echo "node"
    elif [ -f "requirements.txt" ] || [ -f "pyproject.toml" ] || [ -f "ai_service/requirements.txt" ]; then
        echo "python"
    else
        echo "unknown"
    fi
}

function _get_linter_command() {
    local component=$1
    local ptype
    ptype=$(_detect_project_type)

    case "$ptype" in
        java)
            # Support both Gradle and Maven
            if [ -f "api/build.gradle" ] || [ -f "api/build.gradle.kts" ]; then
                echo "cd api && ./gradlew checkstyleMain checkstyleTest --quiet && cd .."
            elif [ -f "build.gradle" ] || [ -f "build.gradle.kts" ]; then
                echo "./gradlew checkstyleMain checkstyleTest --quiet"
            elif [ -f "api/pom.xml" ]; then
                echo "./mvnw checkstyle:check -q -f api/pom.xml"
            else
                echo "./mvnw checkstyle:check -q"
            fi
            ;;
        node)
            if [ "$component" = "frontend" ] || [ -d "ui" ]; then
                echo "npm run lint --prefix ui"
            else
                echo "npm run lint"
            fi
            ;;
        python)
            if [ -d "ai_service" ]; then
                echo "cd ai_service && flake8 app/ && cd .."
            else
                echo "flake8"
            fi
            ;;
        *)
            echo "echo 'No linter configured for project type: $ptype'"
            ;;
    esac
}

function _get_test_command() {
    local component=$1
    local ptype
    ptype=$(_detect_project_type)

    case "$ptype" in
        java)
            # Support both Gradle and Maven
            if [ -f "api/build.gradle" ] || [ -f "api/build.gradle.kts" ]; then
                echo "cd api && ./gradlew test --quiet && cd .."
            elif [ -f "build.gradle" ] || [ -f "build.gradle.kts" ]; then
                echo "./gradlew test --quiet"
            elif [ -f "api/pom.xml" ]; then
                echo "./mvnw test -q -f api/pom.xml"
            else
                echo "./mvnw test -q"
            fi
            ;;
        node)
            if [ "$component" = "frontend" ] || [ -d "ui" ]; then
                echo "npm test --prefix ui -- --watchAll=false"
            else
                echo "npm test -- --watchAll=false"
            fi
            ;;
        python)
            if [ -d "ai_service" ]; then
                echo "cd ai_service && pytest && cd .."
            else
                echo "pytest"
            fi
            ;;
        *)
            echo "echo 'No test command configured for project type: $ptype'"
            ;;
    esac
}

# -----------------------------------------------------------------------------
# UTILITY FUNCTIONS
# -----------------------------------------------------------------------------

function _ai_log() {
    local level=$1
    local msg=$2
    local timestamp
    timestamp=$(date '+%H:%M:%S')

    case $level in
        INFO)  echo -e "${COLOR_CYAN}[$timestamp]${COLOR_RESET} ℹ️  $msg" ;;
        OK)    echo -e "${COLOR_GREEN}[$timestamp]${COLOR_RESET} ✅ $msg" ;;
        WARN)  echo -e "${COLOR_YELLOW}[$timestamp]${COLOR_RESET} ⚠️  $msg" ;;
        ERROR) echo -e "${COLOR_RED}[$timestamp]${COLOR_RESET} ❌ $msg" ;;
        STEP)  echo -e "${COLOR_BLUE}[$timestamp]${COLOR_RESET} 🔹 $msg" ;;
    esac
}

function _ensure_workspace() {
    mkdir -p "$AI_WORKSPACE"/{specs,pushbacks,checkpoints,reports}
    mkdir -p "$AI_KNOWLEDGE"/{patterns,architecture,tech_debt,disputes}
    mkdir -p "$AI_KNOWLEDGE/architecture/decisions"
}

function _slugify() {
    # Improved slugify: lowercase, replace spaces/hyphens with underscore,
    # remove non-alphanumeric, add hash suffix for uniqueness
    local input="$1"
    local base
    local hash
    base=$(echo "$input" | tr '[:upper:]' '[:lower:]' | tr ' -' '_' | tr -cd '[:alnum:]_' | cut -c1-40)
    hash=$(echo "$input" | md5sum | cut -c1-6)
    echo "${base}_${hash}"
}

# -----------------------------------------------------------------------------
# IMPROVED CHECKPOINT SYSTEM (Grok's feedback)
# -----------------------------------------------------------------------------

function _checkpoint_create() {
    local name=$1
    local checkpoint_dir
    checkpoint_dir="$AI_WORKSPACE/checkpoints/$name-$(date +%s)"
    mkdir -p "$checkpoint_dir"

    # Save base commit reference for accurate diff tracking
    git rev-parse HEAD > "$checkpoint_dir/base_commit" 2>/dev/null || echo "HEAD" > "$checkpoint_dir/base_commit"

    # Save current state as patches
    git diff > "$checkpoint_dir/unstaged.patch" 2>/dev/null || true
    git diff --cached > "$checkpoint_dir/staged.patch" 2>/dev/null || true

    # Track list of modified files
    git diff --name-only > "$checkpoint_dir/modified_files.txt" 2>/dev/null || true
    git diff --cached --name-only >> "$checkpoint_dir/modified_files.txt" 2>/dev/null || true

    # Check if there were any changes to checkpoint
    if [ ! -s "$checkpoint_dir/unstaged.patch" ] && [ ! -s "$checkpoint_dir/staged.patch" ]; then
        _ai_log WARN "No uncommitted changes to checkpoint (clean working tree)"
    fi

    # Record timestamp
    date '+%Y-%m-%d %H:%M:%S' > "$checkpoint_dir/created_at"

    echo "$checkpoint_dir"
}

function _checkpoint_restore() {
    local checkpoint_dir=$1

    if [ ! -d "$checkpoint_dir" ]; then
        _ai_log ERROR "Checkpoint directory not found: $checkpoint_dir"
        return 1
    fi

    local has_unstaged=false
    local has_staged=false

    [ -s "$checkpoint_dir/unstaged.patch" ] && has_unstaged=true
    [ -s "$checkpoint_dir/staged.patch" ] && has_staged=true

    if [ "$has_unstaged" = false ] && [ "$has_staged" = false ]; then
        _ai_log WARN "No changes to restore from checkpoint"
        return 0
    fi

    # First, check if restore is possible (dry run)
    if [ "$has_unstaged" = true ]; then
        if ! git apply --check -R "$checkpoint_dir/unstaged.patch" >/dev/null 2>&1; then
            _ai_log ERROR "Cannot restore: conflicts detected with unstaged changes"
            _ai_log INFO "Manual resolution needed. Patch file: $checkpoint_dir/unstaged.patch"
            return 1
        fi
    fi

    # Perform the restore
    # First, discard current changes
    git checkout -- . 2>/dev/null || true
    git reset HEAD . 2>/dev/null || true

    _ai_log OK "Restored to pre-modification state"
    _ai_log INFO "Base commit was: $(cat "$checkpoint_dir/base_commit" 2>/dev/null || echo 'unknown')"

    return 0
}

function _get_changes_since_checkpoint() {
    local slug=$1
    local checkpoint_dir
    checkpoint_dir=$(find "$AI_WORKSPACE/checkpoints" -maxdepth 1 -type d -name "pre-build-$slug*" 2>/dev/null | sort -r | head -1)

    if [ -z "$checkpoint_dir" ] || [ ! -f "$checkpoint_dir/base_commit" ]; then
        # Fallback to current uncommitted changes
        git diff --name-only HEAD 2>/dev/null
        return
    fi

    local base_commit
    base_commit=$(cat "$checkpoint_dir/base_commit")

    # Get all changes since checkpoint (both committed and uncommitted)
    {
        git diff --name-only "$base_commit" 2>/dev/null
        git diff --name-only HEAD 2>/dev/null
    } | sort -u
}

# -----------------------------------------------------------------------------
# LINTER AND TEST RUNNERS
# -----------------------------------------------------------------------------

function _run_linter() {
    local component=${1:-all}
    local ptype
    ptype=$(_detect_project_type)

    _ai_log STEP "Running linter (project type: $ptype, component: $component)..."

    case $component in
        backend|java)
            eval "$(_get_linter_command backend)" > /dev/null 2>&1
            ;;
        frontend|node)
            eval "$(_get_linter_command frontend)" > /dev/null 2>&1
            ;;
        python|ai)
            eval "$(_get_linter_command python)" > /dev/null 2>&1
            ;;
        *)
            # Run all applicable linters
            local exit_code=0
            if [ -f "api/pom.xml" ] || [ -f "pom.xml" ]; then
                eval "$(_get_linter_command backend)" > /dev/null 2>&1 || exit_code=1
            fi
            if [ -f "ui/package.json" ] || [ -f "package.json" ]; then
                eval "$(_get_linter_command frontend)" > /dev/null 2>&1 || exit_code=1
            fi
            if [ -d "ai_service" ] || [ -f "requirements.txt" ]; then
                eval "$(_get_linter_command python)" > /dev/null 2>&1 || exit_code=1
            fi
            return $exit_code
            ;;
    esac
}

function _run_tests() {
    local component=${1:-all}
    local ptype
    ptype=$(_detect_project_type)

    _ai_log STEP "Running tests (project type: $ptype, component: $component)..."

    case $component in
        backend|java)
            eval "$(_get_test_command backend)"
            ;;
        frontend|node)
            eval "$(_get_test_command frontend)"
            ;;
        python|ai)
            eval "$(_get_test_command python)"
            ;;
        *)
            # Run all applicable tests
            local exit_code=0
            if [ -f "api/pom.xml" ] || [ -f "pom.xml" ]; then
                eval "$(_get_test_command backend)" || exit_code=1
            fi
            if [ -f "ui/package.json" ]; then
                eval "$(_get_test_command frontend)" || exit_code=1
            fi
            # Note: Python tests skipped by default (TD-001 in tech debt register)
            return $exit_code
            ;;
    esac
}

# -----------------------------------------------------------------------------
# PHASE 1: PLANNING
# -----------------------------------------------------------------------------

function plan() {
    local feature_desc="$1"

    if [ -z "$feature_desc" ]; then
        echo "Usage: plan \"<feature description>\""
        echo ""
        echo "Example: plan \"Add rate limiting to public API endpoints\""
        return 1
    fi

    _ensure_workspace

    local slug
    slug=$(_slugify "$feature_desc")
    local spec_file="$AI_WORKSPACE/specs/SPEC_${slug}.md"

    _ai_log INFO "Planning feature: $feature_desc"
    _ai_log STEP "Spec file will be: $spec_file"
    _ai_log STEP "Feature slug: $slug"

    # Stage knowledge base (no commit - human approves)
    git add "$AI_KNOWLEDGE" 2>/dev/null || true

    # Reminder about staged files
    _ai_log WARN "Knowledge base staged. Remember to commit or unstage if not proceeding."

    echo ""
    echo "═══════════════════════════════════════════════════════════════════"
    echo "📋 NEXT STEPS"
    echo "═══════════════════════════════════════════════════════════════════"
    echo ""
    echo "1. Have Gemini (Architect) create the spec:"
    echo "   - Provide feature description and .ai_knowledge/architecture/constraints.md"
    echo "   - Save output to: $spec_file"
    echo ""
    echo "2. Have Claude Code review the spec for feasibility"
    echo "   - If issues, Claude creates: .ai_workspace/pushbacks/PUSHBACK_${slug}.md"
    echo ""
    echo "3. Resolve any disagreements, then run:"
    echo "   build $slug"
    echo ""
}

# -----------------------------------------------------------------------------
# PHASE 2: BUILDING
# -----------------------------------------------------------------------------

function build() {
    local slug=$1

    if [ -z "$slug" ]; then
        echo "Usage: build <feature_slug>"
        echo ""
        echo "Available specs:"
        for f in "$AI_WORKSPACE/specs/"SPEC_*.md; do
            [ -f "$f" ] || continue
            local name
            name=$(basename "$f" .md)
            echo "  ${name#SPEC_}"
        done
        return 1
    fi

    local spec_file="$AI_WORKSPACE/specs/SPEC_${slug}.md"

    if [ ! -f "$spec_file" ]; then
        _ai_log ERROR "Spec not found: $spec_file"
        return 1
    fi

    # Check for unresolved pushbacks
    local has_pushbacks=false
    shopt -s nullglob
    for f in "$AI_WORKSPACE/pushbacks/"*"${slug}"*; do
        [ -f "$f" ] && has_pushbacks=true && break
    done
    shopt -u nullglob

    if [ "$has_pushbacks" = true ]; then
        _ai_log ERROR "Unresolved pushbacks exist. Resolve before building:"
        for f in "$AI_WORKSPACE/pushbacks/"*"${slug}"*; do
            [ -f "$f" ] && echo "  $f"
        done
        echo ""
        echo "To resolve, either:"
        echo "  1. Address the pushback and delete the file"
        echo "  2. Run: resolve_pushback $slug"
        return 1
    fi

    _ensure_workspace

    # Create checkpoint with base commit tracking
    local checkpoint
    checkpoint=$(_checkpoint_create "pre-build-$slug")
    _ai_log OK "Checkpoint created: $checkpoint"

    echo ""
    echo "═══════════════════════════════════════════════════════════════════"
    echo "📋 BUILD INSTRUCTIONS FOR CLAUDE CODE"
    echo "═══════════════════════════════════════════════════════════════════"
    echo ""
    echo "Spec file: $spec_file"
    echo "Checkpoint: $checkpoint"
    echo ""
    echo "Claude Code should:"
    echo "1. Read the spec file thoroughly"
    echo "2. Check .claude/skills/ for relevant patterns"
    echo "3. Implement the feature following project standards"
    echo "4. Write tests for new functionality"
    echo "5. If issues with spec arise, create:"
    echo "   $AI_WORKSPACE/pushbacks/PUSHBACK_${slug}.md"
    echo ""
    echo "When implementation is complete, run: review $slug"
    echo ""
    echo "If build issues occur, run: resolve_build_issue $slug"
    echo ""
}

function rollback() {
    local slug=$1

    if [ -z "$slug" ]; then
        echo "Usage: rollback <feature_slug>"
        echo ""
        echo "Available checkpoints:"
        for d in "$AI_WORKSPACE/checkpoints/"*/; do
            [ -d "$d" ] && echo "  $(basename "$d")"
        done
        return 1
    fi

    local checkpoint_dir
    checkpoint_dir=$(find "$AI_WORKSPACE/checkpoints" -maxdepth 1 -type d -name "pre-build-$slug*" 2>/dev/null | sort -r | head -1)

    if [ -z "$checkpoint_dir" ]; then
        _ai_log ERROR "No checkpoint found for $slug"
        return 1
    fi

    _ai_log INFO "Rolling back to checkpoint: $checkpoint_dir"
    _checkpoint_restore "$checkpoint_dir"
}

function resolve_pushback() {
    local slug=$1

    if [ -z "$slug" ]; then
        echo "Usage: resolve_pushback <feature_slug>"
        return 1
    fi

    local found_files=()
    shopt -s nullglob
    for f in "$AI_WORKSPACE/pushbacks/"*"${slug}"*; do
        [ -f "$f" ] && found_files+=("$f")
    done
    shopt -u nullglob

    if [ ${#found_files[@]} -eq 0 ]; then
        _ai_log INFO "No pushbacks found for $slug"
        return 0
    fi

    echo "Pushback files for $slug:"
    for f in "${found_files[@]}"; do
        echo "  $f"
    done
    echo ""

    local confirm
    read -rp "Mark as resolved and archive? [y/N] " confirm

    if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
        mkdir -p "$AI_WORKSPACE/pushbacks/resolved"
        for f in "${found_files[@]}"; do
            mv "$f" "$AI_WORKSPACE/pushbacks/resolved/"
        done
        _ai_log OK "Pushbacks archived to resolved/"
    else
        _ai_log INFO "Cancelled"
    fi
}

function resolve_build_issue() {
    local slug=$1

    if [ -z "$slug" ]; then
        echo "Usage: resolve_build_issue <feature_slug>"
        return 1
    fi

    local issue_file="$AI_WORKSPACE/pushbacks/BUILD_ISSUE_${slug}.md"
    local today
    today=$(date '+%Y-%m-%d %H:%M')

    echo ""
    echo "═══════════════════════════════════════════════════════════════════"
    echo "🔧 BUILD ISSUE RESOLUTION: $slug"
    echo "═══════════════════════════════════════════════════════════════════"
    echo ""
    echo "Options:"
    echo "  1. Create build issue report for Architect review"
    echo "  2. Rollback to checkpoint and restart"
    echo "  3. Continue building (issue resolved)"
    echo ""

    local choice
    read -rp "Choose [1/2/3]: " choice

    case $choice in
        1)
            cat > "$issue_file" << EOF
# Build Issue Report: $slug

**Date**: $today
**Phase**: Build

## Issue Description

[Describe the technical issue encountered during build]

## Error Output

\`\`\`
[Paste error messages here]
\`\`\`

## Attempted Solutions

1. [What was tried]

## Proposed Resolution

[Suggested fix or spec change needed]

## Impact

[What parts of the spec are affected]
EOF
            _ai_log OK "Created: $issue_file"
            echo "Edit the file, then have Architect review."
            ;;
        2)
            rollback "$slug"
            ;;
        3)
            _ai_log OK "Continuing build..."
            ;;
        *)
            _ai_log ERROR "Invalid choice"
            return 1
            ;;
    esac
}

# -----------------------------------------------------------------------------
# PHASE 3: REVIEW
# -----------------------------------------------------------------------------

function review() {
    local slug=$1

    if [ -z "$slug" ]; then
        echo "Usage: review <feature_slug>"
        return 1
    fi

    local report_file="$AI_WORKSPACE/reports/REVIEW_${slug}.md"

    _ensure_workspace

    # Get changed files since checkpoint (more accurate than HEAD~5)
    local changed_files
    changed_files=$(_get_changes_since_checkpoint "$slug")

    if [ -z "$changed_files" ]; then
        # Fallback to current uncommitted changes
        changed_files=$(git diff --name-only HEAD 2>/dev/null | head -30)
    fi

    echo ""
    echo "═══════════════════════════════════════════════════════════════════"
    echo "📋 REVIEW INSTRUCTIONS"
    echo "═══════════════════════════════════════════════════════════════════"
    echo ""
    echo "Changed files since build started:"
    echo "$changed_files" | while IFS= read -r line; do
        echo "  $line"
    done
    echo ""
    echo "1. Have Gemini (Architect) review the changes against:"
    echo "   - .ai_knowledge/patterns/security_standards.md"
    echo "   - .ai_knowledge/patterns/code_review_checklist.md"
    echo "   - .ai_knowledge/tech_debt/register.md (ignore known debt)"
    echo ""
    echo "2. Save review findings to: $report_file"
    echo "   - Use tags: [CRITICAL], [WARNING], [SUGGESTION], [QUESTION]"
    echo "   - Output 'PASSED' if no issues"
    echo ""
    echo "3. If issues found:"
    echo "   - Claude Code fixes agreed issues"
    echo "   - Claude Code defends disagreed issues in DEFENSE_${slug}.md"
    echo ""
    echo "4. When review passes, run: approve $slug"
    echo ""
}

# -----------------------------------------------------------------------------
# PHASE 4: APPROVAL (Human commits)
# -----------------------------------------------------------------------------

function approve() {
    local slug=$1
    local commit_msg=$2

    if [ -z "$slug" ]; then
        echo "Usage: approve <feature_slug> [commit_message]"
        echo ""
        echo "Available specs:"
        for f in "$AI_WORKSPACE/specs/"SPEC_*.md; do
            [ -f "$f" ] || continue
            local name
            name=$(basename "$f" .md)
            echo "  ${name#SPEC_}"
        done
        return 1
    fi

    # Check for unresolved pushbacks
    local has_pushbacks=false
    shopt -s nullglob
    for f in "$AI_WORKSPACE/pushbacks/"*"${slug}"*; do
        [ -f "$f" ] && has_pushbacks=true && break
    done
    shopt -u nullglob

    if [ "$has_pushbacks" = true ]; then
        _ai_log ERROR "Unresolved pushbacks exist:"
        for f in "$AI_WORKSPACE/pushbacks/"*"${slug}"*; do
            [ -f "$f" ] && echo "  $f"
        done
        return 1
    fi

    # Stage all changes
    _ai_log STEP "Staging changes..."
    git add -A

    echo ""
    echo "═══════════════════════════════════════════════════════════════════"
    echo "📋 STAGED CHANGES FOR YOUR REVIEW"
    echo "═══════════════════════════════════════════════════════════════════"
    git status --short
    echo ""
    echo "═══════════════════════════════════════════════════════════════════"
    echo "📝 DIFF SUMMARY"
    echo "═══════════════════════════════════════════════════════════════════"
    git diff --cached --stat
    echo ""

    local suggested_msg="${commit_msg:-feat: implement $slug}"

    echo "═══════════════════════════════════════════════════════════════════"
    echo "✅ READY FOR YOUR COMMIT"
    echo "═══════════════════════════════════════════════════════════════════"
    echo ""
    echo "Review the diff:"
    echo "  git diff --cached"
    echo ""
    echo "Commit when ready:"
    echo "  git commit -m \"$suggested_msg\""
    echo ""
    echo "To abort:"
    echo "  git reset HEAD"
    echo ""
}

# -----------------------------------------------------------------------------
# QUICK SURGERY (Single file review)
# -----------------------------------------------------------------------------

function surgery() {
    local target_file=$1

    if [ -z "$target_file" ] || [ ! -f "$target_file" ]; then
        echo "Usage: surgery <file_path>"
        return 1
    fi

    local slug
    slug=$(basename "$target_file" | sed 's/\.[^.]*$//')
    local report_file="$AI_WORKSPACE/reports/SURGERY_${slug}.md"
    local checkpoint
    checkpoint=$(_checkpoint_create "pre-surgery-$slug")

    _ai_log OK "Checkpoint: $checkpoint"

    echo ""
    echo "═══════════════════════════════════════════════════════════════════"
    echo "🔪 SURGERY: $target_file"
    echo "═══════════════════════════════════════════════════════════════════"
    echo ""
    echo "1. Have Gemini review $target_file against:"
    echo "   - .ai_knowledge/patterns/security_standards.md"
    echo "   - .ai_knowledge/patterns/code_review_checklist.md"
    echo ""
    echo "2. Save findings to: $report_file"
    echo ""
    echo "3. Claude Code fixes issues (or defends with evidence)"
    echo ""
    echo "4. Repeat until PASSED"
    echo ""
    echo "5. Run: approve_surgery $target_file"
    echo ""
    echo "To rollback: rollback_surgery $slug"
    echo ""
}

function approve_surgery() {
    local file=$1
    local commit_msg=$2

    if [ -z "$file" ]; then
        echo "Usage: approve_surgery <file_path> [commit_message]"
        return 1
    fi

    git add "$file"

    echo ""
    echo "═══════════════════════════════════════════════════════════════════"
    echo "📋 STAGED: $file"
    echo "═══════════════════════════════════════════════════════════════════"
    git diff --cached --stat "$file"
    echo ""

    local suggested_msg="${commit_msg:-fix: surgical fixes to $(basename "$file")}"

    echo "Commit when ready:"
    echo "  git commit -m \"$suggested_msg\""
    echo ""
}

function rollback_surgery() {
    local slug=$1
    local checkpoint_dir
    checkpoint_dir=$(find "$AI_WORKSPACE/checkpoints" -maxdepth 1 -type d -name "pre-surgery-$slug*" 2>/dev/null | sort -r | head -1)

    if [ -z "$checkpoint_dir" ]; then
        _ai_log ERROR "No checkpoint found for $slug"
        return 1
    fi

    _checkpoint_restore "$checkpoint_dir"
}

# -----------------------------------------------------------------------------
# UTILITIES
# -----------------------------------------------------------------------------

function ai_status() {
    echo ""
    echo "═══════════════════════════════════════════════════════════════════"
    echo "📊 AI BEAST MODE v3 STATUS"
    echo "═══════════════════════════════════════════════════════════════════"
    echo ""
    echo "🔧 Project Type: $(_detect_project_type)"
    echo ""
    echo "📋 Pending Specs:"
    local spec_count=0
    for f in "$AI_WORKSPACE/specs/"*.md; do
        if [ -f "$f" ]; then
            echo "   $(basename "$f")"
            ((spec_count++))
        fi
    done
    [ $spec_count -eq 0 ] && echo "   (none)"
    echo ""
    echo "⚠️  Unresolved Pushbacks:"
    local pushback_count=0
    for f in "$AI_WORKSPACE/pushbacks/"*.md; do
        if [ -f "$f" ]; then
            echo "   $(basename "$f")"
            ((pushback_count++))
        fi
    done
    [ $pushback_count -eq 0 ] && echo "   (none)"
    echo ""
    echo "📝 Recent Reports:"
    local report_count=0
    for f in "$AI_WORKSPACE/reports/"*.md; do
        if [ -f "$f" ] && [ $report_count -lt 5 ]; then
            echo "   $(basename "$f")"
            ((report_count++))
        fi
    done
    [ $report_count -eq 0 ] && echo "   (none)"
    echo ""
    echo "💾 Checkpoints:"
    local checkpoint_count=0
    for d in "$AI_WORKSPACE/checkpoints/"*/; do
        if [ -d "$d" ] && [ $checkpoint_count -lt 3 ]; then
            echo "   $(basename "$d")"
            ((checkpoint_count++))
        fi
    done
    [ $checkpoint_count -eq 0 ] && echo "   (none)"
    echo ""
    echo "📐 Architecture Decisions (ADRs):"
    local adr_count=0
    for f in "$AI_KNOWLEDGE/architecture/decisions/"ADR-*.md; do
        [ -f "$f" ] && ((adr_count++))
    done
    if [ "$adr_count" -gt 0 ]; then
        echo "   $adr_count ADR(s) - run 'adr_list' for details"
    else
        echo "   (none)"
    fi
    echo ""
    echo "📜 Dispute History:"
    local dispute_count=0
    if [ -f "$AI_KNOWLEDGE/disputes/resolution_log.md" ]; then
        dispute_count=$(grep -c '###.*Feature:' "$AI_KNOWLEDGE/disputes/resolution_log.md" 2>/dev/null || echo "0")
    fi
    echo "   $dispute_count resolved dispute(s)"
    echo ""
}

function ai_clean() {
    echo "This will remove:"
    echo "  - All specs in $AI_WORKSPACE/specs/"
    echo "  - All pushbacks in $AI_WORKSPACE/pushbacks/"
    echo "  - All reports in $AI_WORKSPACE/reports/"
    echo "  - All checkpoints in $AI_WORKSPACE/checkpoints/"
    echo ""

    local confirm
    read -rp "Continue? [y/N] " confirm

    if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
        rm -rf "${AI_WORKSPACE:?}"/{specs,pushbacks,reports,checkpoints}/*
        _ai_log OK "Workspace cleaned"
    else
        _ai_log INFO "Cancelled"
    fi
}

function ai_cleanup_checkpoints() {
    local keep_count=${1:-3}

    echo "Cleaning up old checkpoints (keeping last $keep_count)..."

    local checkpoint_dir="$AI_WORKSPACE/checkpoints"
    local checkpoints=()
    for d in "$checkpoint_dir/"*/; do
        [ -d "$d" ] && checkpoints+=("$d")
    done

    local total=${#checkpoints[@]}

    if [ "$total" -le "$keep_count" ]; then
        _ai_log INFO "Only $total checkpoints exist, nothing to clean"
        return 0
    fi

    local to_delete=$((total - keep_count))

    echo "Will delete $to_delete oldest checkpoint(s):"
    # Sort by modification time and get oldest
    local sorted_checkpoints
    sorted_checkpoints=$(find "$checkpoint_dir" -maxdepth 1 -type d -not -path "$checkpoint_dir" -printf '%T@ %p\n' 2>/dev/null | sort -n | head -n "$to_delete" | cut -d' ' -f2-)
    echo "$sorted_checkpoints" | while IFS= read -r line; do
        echo "  $(basename "$line")"
    done
    echo ""

    local confirm
    read -rp "Continue? [y/N] " confirm

    if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
        echo "$sorted_checkpoints" | while IFS= read -r line; do
            rm -rf "$line"
        done
        _ai_log OK "Deleted $to_delete old checkpoint(s)"
    else
        _ai_log INFO "Cancelled"
    fi
}

function resolve_dispute() {
    local slug=$1

    if [ -z "$slug" ]; then
        echo "Usage: resolve_dispute <feature_slug>"
        echo ""
        echo "This opens the dispute resolution log for manual resolution."
        return 1
    fi

    local log_file="$AI_KNOWLEDGE/disputes/resolution_log.md"
    local today
    today=$(date '+%Y-%m-%d')

    echo ""
    echo "═══════════════════════════════════════════════════════════════════"
    echo "🤝 DISPUTE RESOLUTION: $slug"
    echo "═══════════════════════════════════════════════════════════════════"
    echo ""
    echo "1. Review the pushback: $AI_WORKSPACE/pushbacks/PUSHBACK_${slug}.md"
    echo "2. Review the spec: $AI_WORKSPACE/specs/SPEC_${slug}.md"
    echo ""
    echo "Resolution options:"
    echo "  a) Architect wins - update spec, Claude implements as specified"
    echo "  b) Implementer wins - spec is modified per Claude's suggestion"
    echo "  c) Compromise - both parties agree on middle ground"
    echo "  d) Human decides - escalate to human for final decision"
    echo ""

    local choice
    read -rp "Choose resolution [a/b/c/d]: " choice

    local resolution=""
    case $choice in
        a) resolution="Architect" ;;
        b) resolution="Implementer" ;;
        c) resolution="Compromise" ;;
        d) resolution="Human" ;;
        *) _ai_log ERROR "Invalid choice"; return 1 ;;
    esac

    # Append to resolution log
    cat >> "$log_file" << EOF

### [$today] Feature: $slug

**Architect Position**:
[See spec file]

**Implementer Position**:
[See pushback file]

**Evidence Provided**:
[Summarize evidence]

**Resolution**: $resolution

**Final Approach**:
[Document what was decided]

**Learning**:
[What to improve for next time]

---
EOF

    _ai_log OK "Resolution logged. Edit $log_file to complete details."

    # Archive the pushback
    resolve_pushback "$slug"
}

# -----------------------------------------------------------------------------
# ARCHITECTURE DECISION RECORDS (ADR)
# -----------------------------------------------------------------------------

function _get_next_adr_number() {
    local max_num=0
    for f in "$AI_KNOWLEDGE/architecture/decisions/"ADR-*.md; do
        if [ -f "$f" ]; then
            local num
            num=$(basename "$f" | sed -n 's/ADR-\([0-9]*\).*/\1/p')
            if [ -n "$num" ] && [ "$num" -gt "$max_num" ]; then
                max_num=$num
            fi
        fi
    done
    printf "%03d" $((max_num + 1))
}

function adr() {
    local title="$1"

    if [ -z "$title" ]; then
        echo "Usage: adr \"<decision title>\""
        echo ""
        echo "Example: adr \"Rate Limiting Approach\""
        echo ""
        echo "This creates a new Architecture Decision Record from the template."
        return 1
    fi

    _ensure_workspace
    mkdir -p "$AI_KNOWLEDGE/architecture/decisions"

    local adr_num
    adr_num=$(_get_next_adr_number)
    local slug
    slug=$(_slugify "$title")
    local adr_file="$AI_KNOWLEDGE/architecture/decisions/ADR-${adr_num}_${slug}.md"
    local template="$AI_KNOWLEDGE/architecture/decisions/_TEMPLATE.md"
    local today
    today=$(date '+%Y-%m-%d')

    if [ -f "$template" ]; then
        sed "s/ADR-XXX/ADR-$adr_num/g; s/\[Title\]/$title/g; s/YYYY-MM-DD/$today/g" "$template" > "$adr_file"
    else
        # Create minimal ADR if template missing
        cat > "$adr_file" << EOF
# ADR-${adr_num}: ${title}

**Status**: PROPOSED

**Date**: ${today}

**Participants**:
- Architect (Gemini):
- Implementer (Claude):
- Human:

---

## Context

[Why this decision is needed]

## Decision

[What was decided]

## Options Considered

### Option 1:
- **Pros**:
- **Cons**:

### Option 2:
- **Pros**:
- **Cons**:

## Rationale

[Why this option was chosen]

## Consequences

### Positive
-

### Negative
-

## References

- **Spec**:
- **Patterns**:
EOF
    fi

    _ai_log OK "Created: $adr_file"
    echo ""
    echo "Next steps:"
    echo "  1. Fill in the ADR details"
    echo "  2. Get AI consensus (Claude + Gemini)"
    echo "  3. Update status to ACCEPTED"
    echo "  4. Human approves and commits"
    echo "  5. Update status to APPROVED"
    echo ""
}

function adr_list() {
    echo ""
    echo "═══════════════════════════════════════════════════════════════════"
    echo "📋 ARCHITECTURE DECISION RECORDS"
    echo "═══════════════════════════════════════════════════════════════════"
    echo ""

    local adr_dir="$AI_KNOWLEDGE/architecture/decisions"
    local has_adrs=false

    for f in "$adr_dir/"ADR-*.md; do
        [ -f "$f" ] && has_adrs=true && break
    done

    if [ "$has_adrs" = false ]; then
        echo "   (no ADRs yet)"
        echo ""
        echo "Create one with: adr \"Decision Title\""
        return 0
    fi

    printf "%-8s %-40s %-12s %s\n" "ADR" "TITLE" "STATUS" "DATE"
    printf "%-8s %-40s %-12s %s\n" "---" "-----" "------" "----"

    for file in "$adr_dir"/ADR-*.md; do
        [ -f "$file" ] || continue

        local filename
        filename=$(basename "$file")
        local adr_num
        adr_num=${filename#ADR-}
        adr_num=${adr_num%%_*}
        local title
        title=$(head -1 "$file" | sed 's/# ADR-[0-9]*: //')
        local status
        status=$(grep -m1 "^\*\*Status\*\*:" "$file" | sed 's/.*: //' | tr -d ' ')
        local adr_date
        adr_date=$(grep -m1 "^\*\*Date\*\*:" "$file" | sed 's/.*: //' | tr -d ' ')

        # Truncate title if too long
        if [ ${#title} -gt 38 ]; then
            title="${title:0:35}..."
        fi

        printf "%-8s %-40s %-12s %s\n" "ADR-$adr_num" "$title" "$status" "$adr_date"
    done
    echo ""
}

function adr_show() {
    local adr_id="$1"

    if [ -z "$adr_id" ]; then
        echo "Usage: adr_show <ADR-number>"
        echo ""
        echo "Example: adr_show 001"
        echo "         adr_show ADR-001"
        return 1
    fi

    # Normalize input (remove ADR- prefix if present)
    adr_id=${adr_id#ADR-}

    local adr_file=""
    for f in "$AI_KNOWLEDGE/architecture/decisions/ADR-${adr_id}"*.md; do
        [ -f "$f" ] && adr_file="$f" && break
    done

    if [ -z "$adr_file" ] || [ ! -f "$adr_file" ]; then
        _ai_log ERROR "ADR-$adr_id not found"
        echo ""
        echo "Available ADRs:"
        adr_list
        return 1
    fi

    cat "$adr_file"
}

# -----------------------------------------------------------------------------
# ALIASES
# -----------------------------------------------------------------------------
alias p='plan'
alias b='build'
alias r='review'
alias s='surgery'
alias a='approve'
alias as='approve_surgery'
alias ais='ai_status'
alias aic='ai_clean'
alias adrl='adr_list'
alias adrs='adr_show'
alias rbi='resolve_build_issue'
alias rp='resolve_pushback'
alias rd='resolve_dispute'
alias aicc='ai_cleanup_checkpoints'

# -----------------------------------------------------------------------------
# INITIALIZATION MESSAGE
# -----------------------------------------------------------------------------
echo -e "${COLOR_GREEN}🤖 Beast Mode v3 loaded.${COLOR_RESET}"
echo "   Project type: $(_detect_project_type)"
echo "   Commands: plan, build, review, approve, surgery, ai_status, adr, adr_list"
echo "   New: resolve_build_issue, resolve_pushback, resolve_dispute, ai_cleanup_checkpoints"
echo "   Aliases: p, b, r, a, s, ais, adrl, adrs, rbi, rp, rd, aicc"

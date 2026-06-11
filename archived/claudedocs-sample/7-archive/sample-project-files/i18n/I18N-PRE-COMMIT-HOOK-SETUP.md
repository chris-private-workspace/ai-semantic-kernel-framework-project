# I18N Pre-commit Hook Setup Guide

## Overview

This guide explains how to set up the Git pre-commit hook for automatic I18N translation validation.

---

## What It Does

The pre-commit hook automatically runs `pnpm validate:i18n` whenever you commit changes to:
- `apps/web/src/messages/en.json`
- `apps/web/src/messages/zh-TW.json`

This prevents duplicate keys, syntax errors, and locale inconsistencies from being committed.

---

## Setup Instructions

### Option 1: Manual Setup (Windows/Mac/Linux)

The hook file has already been created at:
```
.git/hooks/pre-commit
```

**For Unix-like systems (Mac, Linux, Git Bash on Windows):**

Make the hook executable:
```bash
chmod +x .git/hooks/pre-commit
```

**For Windows Command Prompt/PowerShell:**

Git will automatically detect and run the hook. No additional setup needed.

### Option 2: Verify Hook Installation

Test if the hook is working:

```bash
# Make a dummy change to a translation file
echo " " >> apps/web/src/messages/en.json

# Try to commit
git add apps/web/src/messages/en.json
git commit -m "test: verify pre-commit hook"

# You should see validation output
# Revert the dummy change
git restore apps/web/src/messages/en.json
```

---

## Hook Behavior

### When Translation Files Are Modified

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌐 Translation files detected in commit
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Modified files:
  - apps/web/src/messages/en.json
  - apps/web/src/messages/zh-TW.json

Running I18N validation...

[Validation output]

✅ Translation validation passed!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### When Validation Fails

```
❌ Translation validation failed!

Common issues:
  1. Duplicate keys - check for duplicate object keys in JSON
  2. JSON syntax errors - check for missing commas, brackets
  3. Key structure mismatch - ensure en.json and zh-TW.json have same keys

Fix the issues and try again, or use:
  git commit --no-verify  (NOT RECOMMENDED)

For help, see:
  - claudedocs/I18N-TRANSLATION-KEY-GUIDE.md
  - Run: pnpm validate:i18n
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

The commit will be **blocked** until issues are fixed.

### When Other Files Are Modified

If your commit doesn't include translation files, the hook runs silently and exits immediately.

---

## Bypassing the Hook

**⚠️ NOT RECOMMENDED** - Use only in emergencies:

```bash
git commit --no-verify -m "emergency fix"
```

This skips all pre-commit hooks, including I18N validation.

**When to use:**
- Emergency hotfixes
- Intentional WIP commits
- Testing hook behavior

**Always validate manually afterward:**
```bash
pnpm validate:i18n
```

---

## Troubleshooting

### Hook Not Running

**Symptom:** Commits succeed even with translation errors.

**Causes:**
1. Hook file doesn't exist
2. Hook file isn't executable (Unix systems)
3. Git core.hooksPath configured to different directory

**Fix:**
```bash
# Check if hook exists
ls -la .git/hooks/pre-commit

# Check Git hooks path
git config core.hooksPath

# If empty or not set, hooks should be in .git/hooks/
# If set to a custom path, copy the hook there
```

### Hook Runs But Validation Fails Incorrectly

**Symptom:** Hook reports errors that don't exist.

**Causes:**
1. Working directory is not project root
2. Node.js not in PATH
3. Dependencies not installed

**Fix:**
```bash
# Ensure you're in project root
cd /path/to/project

# Check Node.js is available
node --version

# Reinstall dependencies
pnpm install

# Test validation manually
pnpm validate:i18n
```

### Permission Denied (Unix)

**Symptom:** `Permission denied: .git/hooks/pre-commit`

**Fix:**
```bash
chmod +x .git/hooks/pre-commit
```

---

## Hook Customization

### Changing Validation Behavior

Edit `.git/hooks/pre-commit`:

**Make validation warnings non-blocking:**
```bash
# Change exit code check
if [ $VALIDATION_EXIT_CODE -eq 0 ] || [ $VALIDATION_EXIT_CODE -eq 1 ]; then
  # Allow commit even with warnings (exit 1 from script)
  exit 0
fi
```

**Add additional checks:**
```bash
# Run TypeScript type checking
echo "Running type check..."
pnpm typecheck || exit 1

# Run linting
echo "Running linter..."
pnpm lint || exit 1
```

### Disabling the Hook Permanently

**Option 1: Rename the hook**
```bash
mv .git/hooks/pre-commit .git/hooks/pre-commit.disabled
```

**Option 2: Delete the hook**
```bash
rm .git/hooks/pre-commit
```

**Option 3: Configure Git to skip hooks**
```bash
# NOT RECOMMENDED - affects all hooks
git config core.hooksPath /dev/null
```

---

## Best Practices

### 1. Always Let the Hook Run

Don't use `--no-verify` unless absolutely necessary. The hook exists to protect code quality.

### 2. Fix Issues, Don't Skip Them

If validation fails:
1. Read the error message carefully
2. Fix the reported issues
3. Run `pnpm validate:i18n` manually to confirm
4. Try committing again

### 3. Test Translation Changes Locally First

Before committing:
```bash
# Run validation
pnpm validate:i18n

# Start dev server
pnpm dev

# Test in browser
# - Switch between en and zh-TW locales
# - Check for MISSING_MESSAGE errors
# - Verify translations display correctly
```

### 4. Commit Translation Files Together

When modifying translations:
```bash
# Add both files together
git add apps/web/src/messages/en.json apps/web/src/messages/zh-TW.json

# Commit with descriptive message
git commit -m "i18n: add vendor form translation keys"
```

---

## Related Documentation

- **Usage Guide**: `claudedocs/I18N-TRANSLATION-KEY-GUIDE.md`
- **Validation Script**: `scripts/validate-i18n.js`
- **CLAUDE.md**: Section on "Internationalization (I18N)"
- **Related Fixes**: FIX-074, FIX-075

---

## Maintenance

### Updating the Hook

1. Edit `.git/hooks/pre-commit` directly
2. Test with a dummy commit
3. Document changes in this file

### Sharing with Team

**Note:** `.git/hooks/` is not tracked by Git.

To share the hook with team members:

**Option 1: Manual copy**
```bash
# Team member copies from another developer
cp /path/to/colleague/.git/hooks/pre-commit .git/hooks/
chmod +x .git/hooks/pre-commit
```

**Option 2: Use Husky (future enhancement)**
```bash
# Install Husky
pnpm add -D husky

# Initialize Husky
pnpx husky install

# Create hook
pnpx husky add .husky/pre-commit "pnpm validate:i18n"
```

**Option 3: Script-based installation**

Create `scripts/install-hooks.sh`:
```bash
#!/bin/sh
cp .git-hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
echo "✅ Git hooks installed"
```

Team members run:
```bash
./scripts/install-hooks.sh
```

---

**Last Updated:** 2025-11-06
**Maintained By:** Development Team

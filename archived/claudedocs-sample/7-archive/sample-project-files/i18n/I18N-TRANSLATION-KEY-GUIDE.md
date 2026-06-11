# I18N Translation Key Usage Guide

## 📋 Overview

This guide provides best practices for adding and managing translation keys in the IT Project Management Platform. Following these guidelines will prevent common issues like duplicate keys, missing translations, and inconsistent naming.

---

## 🎯 Key Principles

### 1. Always Check Before Adding
**Before adding new translation keys:**
- Check if similar keys already exist in both `en.json` and `zh-TW.json`
- Search for existing patterns in the same namespace
- Use consistent naming with existing keys

### 2. Maintain Consistency Across Locales
**Both language files must have identical structure:**
- Same key paths in `en.json` and `zh-TW.json`
- Same nesting levels and object structure
- Only the translation values should differ

### 3. No Duplicate Keys
**JSON does not allow duplicate keys:**
- JavaScript's `JSON.parse()` silently overwrites earlier keys with later ones
- This causes keys to "disappear" and show MISSING_MESSAGE errors
- Always verify no duplicate keys exist before committing

---

## 📁 Translation File Structure

### File Locations
```
apps/web/src/messages/
├── en.json       # English translations
└── zh-TW.json    # Traditional Chinese translations
```

### Key Naming Convention
```
namespace.category.subcategory.field.property
```

**Examples:**
```json
{
  "projects": {                    // namespace
    "form": {                      // category
      "name": {                    // field
        "label": "Project Name",   // property
        "placeholder": "Enter project name"
      }
    }
  }
}
```

---

## ✅ Correct Usage Patterns

### Pattern 1: Form Fields
```json
{
  "vendors": {
    "form": {
      "name": {
        "label": "Vendor Name",
        "placeholder": "Enter vendor name"
      },
      "email": {
        "label": "Email",
        "placeholder": "vendor@example.com"
      }
    }
  }
}
```

**Component Usage:**
```typescript
const t = useTranslations('vendors');

<label>{t('form.name.label')}</label>
<input placeholder={t('form.name.placeholder')} />
```

### Pattern 2: List Views
```json
{
  "projects": {
    "list": {
      "title": "Project List",
      "subtitle": "Manage all projects",
      "search": "Search projects...",
      "table": {
        "name": "Project Name",
        "manager": "Manager",
        "status": "Status"
      }
    }
  }
}
```

### Pattern 3: Detail Pages
```json
{
  "proposals": {
    "detail": {
      "title": "Proposal Details",
      "tabs": {
        "overview": "Overview",
        "comments": "Comments",
        "history": "History"
      },
      "actions": {
        "approve": "Approve",
        "reject": "Reject"
      }
    }
  }
}
```

---

## ❌ Common Mistakes to Avoid

### Mistake 1: Duplicate Keys
**WRONG:**
```json
{
  "vendors": {
    "form": {
      "name": { "label": "Vendor Name" }
    },
    "list": { ... },
    "form": {  // ❌ DUPLICATE KEY!
      "create": { "title": "Create Vendor" }
    }
  }
}
```

**Problem:** The second "form" object overwrites the first one. `vendors.form.name.label` becomes undefined!

**CORRECT:**
```json
{
  "vendors": {
    "form": {
      "name": { "label": "Vendor Name" },
      "create": { "title": "Create Vendor" }
    },
    "list": { ... }
  }
}
```

### Mistake 2: Hardcoded Chinese in Components
**WRONG:**
```typescript
<label>供應商名稱</label>  // ❌ Hardcoded Chinese
```

**CORRECT:**
```typescript
const t = useTranslations('vendors');
<label>{t('form.name.label')}</label>  // ✅ Uses translation key
```

### Mistake 3: Inconsistent Key Structure
**WRONG:**
```json
// en.json
{
  "vendors": {
    "form": {
      "name": { "label": "Vendor Name" }
    }
  }
}

// zh-TW.json
{
  "vendors": {
    "form": {
      "vendorName": { "label": "供應商名稱" }  // ❌ Different key name!
    }
  }
}
```

**CORRECT:**
Both files must have identical key paths:
```json
// Both files
{
  "vendors": {
    "form": {
      "name": { "label": "..." }  // ✅ Same key path
    }
  }
}
```

### Mistake 4: Missing Keys in One Locale
**WRONG:**
```json
// en.json - has the key
{
  "vendors": {
    "form": {
      "phone": { "label": "Phone" }
    }
  }
}

// zh-TW.json - missing the key
{
  "vendors": {
    "form": {
      // ❌ Missing "phone" key!
    }
  }
}
```

**Result:** MISSING_MESSAGE error in Chinese locale!

---

## 🔧 Validation Tools

### 1. Run Validation Script
```bash
# Check translation files for issues
pnpm validate:i18n
```

**What it checks:**
- ✅ JSON syntax correctness
- ✅ Duplicate key detection
- ✅ Empty value detection
- ✅ Multi-locale key consistency

### 2. Example Output
```
✅ JSON 語法正確
✅ 沒有發現重複鍵
⚠️  zh-TW.json 缺少 2 個鍵:
   - vendors.form.phone.label
   - vendors.form.phone.placeholder
```

### 3. When to Run
- Before committing translation changes
- After adding new translation keys
- When encountering MISSING_MESSAGE errors
- As part of pre-commit hooks (recommended)

---

## 🚀 Step-by-Step: Adding New Translation Keys

### Step 1: Identify Required Keys
Look at your component and identify all translation keys needed:

```typescript
// VendorForm.tsx
const t = useTranslations('vendors');

// Keys needed:
// - vendors.form.name.label
// - vendors.form.name.placeholder
// - vendors.form.email.label
// - vendors.form.email.placeholder
```

### Step 2: Check for Existing Keys
```bash
# Search in translation files
grep -r "vendors.form.name" apps/web/src/messages/
```

### Step 3: Add to Both Language Files

**en.json:**
```json
{
  "vendors": {
    "form": {
      "name": {
        "label": "Vendor Name",
        "placeholder": "Enter vendor name"
      },
      "email": {
        "label": "Email",
        "placeholder": "vendor@example.com"
      }
    }
  }
}
```

**zh-TW.json:**
```json
{
  "vendors": {
    "form": {
      "name": {
        "label": "供應商名稱",
        "placeholder": "請輸入供應商名稱"
      },
      "email": {
        "label": "電子郵件",
        "placeholder": "vendor@example.com"
      }
    }
  }
}
```

### Step 4: Validate Structure
```bash
pnpm validate:i18n
```

### Step 5: Test in Browser
- Start dev server: `pnpm dev`
- Navigate to the page
- Switch between English and Chinese
- Verify no MISSING_MESSAGE errors

---

## 🛡️ Prevention Best Practices

### 1. Use Validation Before Commit
Add to `.git/hooks/pre-commit` or `.husky/pre-commit`:
```bash
#!/bin/sh
pnpm validate:i18n || {
  echo "❌ Translation validation failed! Please fix issues before committing."
  exit 1
}
```

### 2. Code Review Checklist
When reviewing translation changes:
- [ ] Both `en.json` and `zh-TW.json` modified
- [ ] Same key structure in both files
- [ ] No duplicate keys
- [ ] No hardcoded Chinese in components
- [ ] Validation script passes

### 3. AI Assistant Guidelines
When using AI assistants (surgical-task-executor, etc.):
- Always specify to check existing structure before adding keys
- Require validation of both language files
- Ask assistant to run `pnpm validate:i18n` after changes

---

## 📊 Validation Script Details

### Location
```
scripts/validate-i18n.js
```

### Features

#### 1. Duplicate Key Detection
Uses line-by-line parsing with indentation tracking to detect duplicate keys that `JSON.parse()` would silently overwrite.

#### 2. Empty Value Detection
Warns about empty strings, null, or undefined values in translations.

#### 3. Locale Consistency Check
Compares `en.json` and `zh-TW.json` to ensure:
- Both have the same keys
- Reports missing keys in either file
- Reports extra keys in either file

#### 4. Exit Codes
- **0**: Success or warnings only
- **1**: Critical errors (duplicate keys, syntax errors)

### Configuration
Located in `scripts/validate-i18n.js`:

```javascript
const MESSAGES_DIR = path.join(__dirname, '../apps/web/src/messages');
const LOCALES = ['en', 'zh-TW'];
```

To add more locales, update the `LOCALES` array.

---

## 🔍 Troubleshooting

### Problem: MISSING_MESSAGE Error
**Error:**
```
IntlError: MISSING_MESSAGE: Could not resolve `vendors.form.name.label`
in messages for locale `zh-TW`.
```

**Solution:**
1. Run `pnpm validate:i18n` to check for issues
2. Verify the key exists in `zh-TW.json`
3. Check for duplicate keys that might overwrite it
4. Restart dev server to clear cache

### Problem: Key Exists But Still Shows Error
**Possible Causes:**
1. **Duplicate keys**: Check for duplicate objects in JSON
2. **Cache issue**: Clear `.next/` and restart dev server
3. **Typo in key path**: Verify exact key path spelling
4. **Wrong namespace**: Check component's `useTranslations()` parameter

**Debug:**
```javascript
// Test JSON parsing
node -e "
const data = JSON.parse(fs.readFileSync('apps/web/src/messages/zh-TW.json', 'utf8'));
console.log('Key value:', data.vendors?.form?.name?.label);
"
```

### Problem: Translation Not Updating
**Solution:**
1. Clear Next.js cache: Delete `.next/` directory
2. Restart dev server
3. Hard refresh browser (Ctrl+Shift+R)
4. Check if correct locale is active

---

## 📚 Additional Resources

### Related Files
- `apps/web/src/i18n/request.ts` - i18n configuration
- `apps/web/src/i18n/routing.ts` - Locale routing setup
- `middleware.ts` - Locale detection middleware

### Documentation
- [next-intl Documentation](https://next-intl-docs.vercel.app/)
- [Project I18N Implementation](../docs/i18n-implementation.md) (if exists)

### Validation Tools
- `pnpm validate:i18n` - Run translation validation
- `pnpm lint` - ESLint checks (may include i18n rules)
- `pnpm typecheck` - TypeScript validation

---

## ✨ Summary Checklist

When adding translation keys:

- [ ] Check existing keys first
- [ ] Add to both `en.json` and `zh-TW.json`
- [ ] Use consistent key structure
- [ ] No duplicate keys
- [ ] Run `pnpm validate:i18n`
- [ ] Test in both locales
- [ ] No hardcoded Chinese in components
- [ ] Clear `.next/` if changes don't appear
- [ ] Commit both language files together

---

**Last Updated:** 2025-11-06
**Maintained By:** Development Team
**Related:** FIX-074, FIX-075 (Duplicate Key Issues)

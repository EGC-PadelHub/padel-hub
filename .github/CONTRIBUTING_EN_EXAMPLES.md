# EXAMPLES REFERENCE - English commit/merge messages

This file contains examples with English messages as they should be written in real commits.

## ✅ Valid COMMITS (without #number)

```bash
git commit
# In editor:
feat: add notification system

Implemented because users need to know when there are new
updates to their datasets. Adds Notification model, API
endpoints and email sending system.
```

## ✅ Valid MERGES

```bash
# To trunk
git merge bugfix -m "fix: integrate login authentication fix #45"
git merge feature/notifications -m "feat: integrate notification system #46"

# To main  
git merge trunk -m "feat: release notification system v2.0.0. Closes #46"
git merge bugfix -m "fix: release authentication fix v1.1.0. Closes #45"
```

## 📋 Issue Examples

**Bug Report Title:**
```
Login fails with empty email field
```

**Feature Request Title:**
```
Email notification system for dataset updates
```

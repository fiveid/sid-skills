---
name: sid-pii-check
description: Scan staged files, codebases, and git diffs for personally identifiable information, local filesystem paths, client names, and exposed credentials before committing or publishing.
---

## Skill Behaviour

You are a security and privacy auditor specializing in pre-commit hygiene and information leakage prevention.

Your task is to scan changes or repositories to ensure developer identities, local machine paths, customer/client names, and credentials do not leak into public or shared version control.

## Process

### Step 1 — Run the Scanner Script

Run the bundled scanner from the repository root:

```bash
# Scan staged git files (default):
python .agents/skills/sid-pii-check/scripts/scan_pii.py

# Or scan specific path / custom client or author names:
python .agents/skills/sid-pii-check/scripts/scan_pii.py --path <directory_or_file> --names "ClientName" "ProjectAlias"
```

The script inspects targeted files for:
- Local machine paths (`/Users/...`, `/home/...`, Windows user profiles)
- Personal email addresses and internal IP addresses
- Git author names or specified client identifiers appearing in source code
- High-entropy tokens, private keys, and credential assignments

### Step 2 — Evaluate Findings

Review the JSON output:
1. **Filter false positives**: Legitimate test domains (`example.com`), public library docs, or intentional placeholder tokens.
2. **Flag actionable items**: Hardcoded personal names in mocks, client names in test data, machine paths in build scripts, and active credentials.
3. **Verify Git identity**: Check `git_identity` against the intended public profile (e.g., verifying whether GitHub privacy noreply email is configured).

### Step 3 — Format Output

Always present findings using the standardized two-part output format:

```markdown
### Scan Results

| Check Category | Status | Details |
| :--- | :---: | :--- |
| **Secrets & API Keys** | **Clean** / **Action Required** | [Summary of findings or clean confirmation] |
| **Absolute Local Paths** | **Clean** / **Flagged** | [Summary of machine paths found] |
| **Email Addresses** | **Clean** / **Flagged** | [Summary of emails found] |
| **Personal / Client Names** | **Clean** / **Flagged** | [Summary of author or client names found] |
| **Private IPs & Endpoints** | **Clean** / **Flagged** | [Summary of internal network findings] |

---

### Items Flagged For Your Review

1. **[Finding Category]**
   - **Location**: `path/to/file:line`
   - **Match**: `detected_value`
   - **Context**: `surrounding line snippet`
   - **Remediation**: [Suggested action, e.g. generalize to ProductCard, use relative path, move to .env]

2. **Git Committer Identity**
   - **Configured Name**: [user.name]
   - **Configured Email**: [user.email]
   - *Note*: [Confirmation if using noreply or alert if personal email is exposed]
```

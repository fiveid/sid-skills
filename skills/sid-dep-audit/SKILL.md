---
name: sid-dep-audit
description: Audit package dependencies for supply-chain risks, slopsquatting, age gating (packages < 30 days old), and unnecessary trivial packages.
---

## Skill Behaviour

You are a sceptical dependency auditor. Your job is to defend the codebase against dependency bloat, slopsquatting, and supply-chain vulnerabilities.

In accordance with project guidelines: **new dependencies require human sign-off**. Never add a package when a 3-line standard library function suffices, and never introduce unvetted or newly published packages without flagging them.

## Process

### Step 1 — Audit Dependencies

Run the bundled audit script from the repository root:

```bash
# Check dependencies newly added in git diff:
python .agents/skills/sid-dep-audit/scripts/audit_deps.py --diff

# Or audit specific package(s):
python .agents/skills/sid-dep-audit/scripts/audit_deps.py <package-name>
```

### Step 2 — Check Risk Factors

For each dependency under review:
1. **Age Gating**: Is the package or release version under 30 days old? (High risk window for account hijacking and slopsquatting).
2. **Triviality**: Is this a micro-utility (like `left-pad`, `is-plain-obj`, `clone-deep`) that modern TypeScript / JavaScript can do natively?
3. **Resolution / Slopsquatting**: Did the package resolve cleanly on npm, or does the name resemble a hallucinated package?

### Step 3 — Format Output

Present findings in this format:

```markdown
### Dependency Audit Summary

- **Total Audited**: X
- **Flagged**: Y (Pass / Warning / Action Required)

| Package | Version | Age (Days) | Status | Key Risk / Note |
| :--- | :--- | :---: | :---: | :--- |
| `pkg-name` | `1.2.0` | 12 | **AGE WARNING** | Published < 30 days ago |
| `is-number` | `7.0.0` | 1800 | **TRIVIAL** | Replace with native TypeScript check |

---

### In-House Alternatives & Recommendations

1. **[Package Name]**
   - **Risk**: [e.g. Unnecessary dependency for trivial operation]
   - **Native Alternative**: [Code snippet replacing the package]
   - **Recommendation**: [Drop package / Pin to previous version / Safe to proceed]
```

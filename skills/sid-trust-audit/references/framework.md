# The framework

## Contents

- The core rule
- Layer 1: always-on checks
- Layer 2: checkpoints
- Layer 3: milestones
- Data and stored formats
- Places to look

## The core rule

**You can ship code you haven't read, but not behaviour you can't vouch for.**

Treat generated code like a dependency. People ship frameworks, compilers and drivers they've never read, and trust them through interfaces, observed behaviour, tests and a limited blast radius.

Every piece of code is either understood by a human, or sits behind an interface a human understands and is checked by tests whose cases a human has decided. The human doesn't have to write the test code. But tests the agent both chose and judged are a closed loop. A second agent helps, but it isn't independence.

Vouching comes from two places: the owner checking behaviour themselves (owner-checked), and checks that run without anyone having to remember them (enforced). Each catches things the other can't, which is why the audit maps every top risk against both.

## Layer 1: always-on checks

The mechanical work goes to tooling: types, lint, format, static analysis, tests, project rules as lint rules (boundaries, banned calls), contracts at the edges (generated types, schemas, runtime validation), dependency and secret scanning.

What to check:

- **Does it run without anyone choosing to run it?** On CI, in the build, in the release script.
- **Does its failure block anything?** The useful gate is where code leaves the owner's hands: a deploy or release. CI on `main` without a gate is a loud signal, not a gate. That's fine if someone sees it, but say which it is.
- **Is it encoded as intent or as friction?** A rule that only makes the wrong thing awkward gets routed around by the obvious fix.
- **What does it actually prove?** Compare the message with what is checked.
- **Is the agent's verify routine complete?** It should run everything that exists, in the right order (e.g. code generation before type checking).

## Layer 2: checkpoints

A checkpoint is where a human stops and looks: using the product, interrogating the agent, reading the code, or a mix. Not every commit, not every line. The owner's own description of when and how they do this is the main evidence here.

Typical triggers (examples, not a list the owner must have written down):

- Before something becomes hard to undo: a schema change, a migration, a public API, a release.
- When work touches a risk area: auth, payments, user data, caching, file deletion, processes, external boundaries.
- When the agent does something unexpected.
- Before building on something new: a dependency, a pattern, a language the owner can't read.
- After a long uninterrupted run, or a very large PR.

What to check:

- **What does the owner already check?** From step 1. Label it owner-checked and attribute it. Don't mark it as a gap because nothing records it.
- **What can't those checks see?** Map them against the top risks. A risk the owner's checking can't reach needs an automated check.
- **Is anything triggered mechanically?** E.g. Clippy `disallowed-methods`, ESLint `no-restricted-imports`, snapshot tests of public surfaces. The tool doesn't judge the change; it makes sure a human looks.
- **Does interrogation end in evidence?** A rule that demonstrably bites, or a test that fails, rather than a reassuring paragraph.
- **Is there a readable table of behaviour for each top risk, and does it live in the code?** A table-driven test reads as a table and is the test. A Markdown table that tests read their expected values from makes the doc the source of truth instead of the code. Don't recommend one.

## Layer 3: milestones

Two milestones, each defined early and confirmed later.

**Feature complete:** project-specific, written down, with a "not in this version" list. Without that list, scope keeps moving.

**Production ready:** largely generic. Check each item:

- Error handling, empty and loading states, error reporting
- Input validation and security, including an adversarial pass on the top risks that ends in failing tests
- Secrets management
- Dependency monitoring
- Logging and backups
- Performance on real data, with a threshold that fails, not just a measurement
- Accessibility, checked with a tool or a screen reader
- Behaviour on a bad network
- Distribution concerns for the platform (signing, updates, store requirements, privacy documents)

Also: **claims are part of what is vouched for.** Every behavioural claim in docs or copy should point to a test.

## Data and stored formats

Models are good at conventional schemas, but data is where a mistake costs most once real data exists. Use the owner's answer from step 1 on whether there is any yet.

- **No real data yet:** the format can change freely. Keeping only the current shape, with no migrations or old versions, is a legitimate choice. Report the versioning drill result, but don't count it as a gap.
- **Data someone would mind losing:** the stored format needs a version, and a format change should force a migration the owner can look at. A cheap mechanism: commit a real current record as a test fixture and test that it still loads.

## Places to look

Earlier audits found problems in these places. Look there, but report what this project shows.

- **Code the owner doesn't read.** Risky operations (files, processes, network) often sit in the language or package the owner can't read.
- **Where the real gate is.** Free private repos can't protect `main`. The gate may be a deploy step, a release script or the owner's own build.
- **Type contracts versus effects.** Generated types show the shape of a call, not what it does (writes files, runs processes, uses the network).
- **Claims versus code.** The owner confirms an intent, the agent implements a narrower version, and the docs are written from the intent.
- **The agent's verify list.** "All green" is only as good as the list it ran.
- **The obvious fix.** Agents route around friction with whatever makes the error go away.
- **Versioning nothing forces**, once there is real data.
- **Unbuilt roadmap items.** Safeguards the owner asked about earlier may be sitting in a roadmap or issue list. Say which are still unbuilt.

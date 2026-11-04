# The framework

## Contents

- The core rule
- Layer 1: always-on checks
- Layer 2: checkpoints
- Layer 3: milestones
- Data and stored formats
- Patterns from earlier audits

## The core rule

Code review was never the goal; it was one way to get confidence in code. It was weak at conventions, finding bugs and reliably catching security flaws. It was strong at catching architectural drift, refining the approach and spotting gaps in business logic.

What's new with agents is the author: there may be nobody who understands every line. That isn't new in itself. People ship React, compilers and drivers they've never read, and trust them through interfaces, observed behaviour, tests and a limited blast radius. So treat generated code like a dependency:

**You can ship code you haven't read, but not behaviour you can't vouch for.**

Every piece of code is either understood by a human, or sits behind an interface a human understands and is checked by tests a human owns. Two caveats:

- Tests written and judged only by the agent that wrote the code are a closed loop. A second agent helps, but it isn't independence.
- Code nobody understands should be regenerated rather than patched. That favours small, well-bounded pieces.

## Layer 1: always-on checks

The things review was weak at are handed to tooling: types, lint, format, static analysis, tests, project rules as lint rules (boundaries, banned calls), contracts at the edges (generated types, schemas, runtime validation), dependency and secret scanning.

What to check:

- **Does it run without anyone choosing to run it?** On CI, in the build, in the release script.
- **Does its failure block anything?** The useful gate is where code leaves the owner's hands: a deploy or release. CI on `main` without a gate is a loud signal, not a gate. That's fine if someone sees it, but say which it is.
- **Is it encoded as intent or as friction?** A rule that only makes the wrong thing awkward gets routed around by the obvious fix.
- **What does it actually prove?** Compare the message with what is checked.
- **Is the agent's verify routine complete?** It should run everything that exists, in the right order (e.g. code generation before type checking).
- **Can the agent build on a red `main`?** If so, its routine should wait for CI and read the result.

## Layer 2: checkpoints

A checkpoint is where a human stops the build-up of unchecked assumptions: interrogating the agent, reading the code, or both. Not every commit, not every line.

Triggers:

- Before something becomes hard to undo: a schema change, a migration, a public API, a release.
- When work touches a risk area: auth, payments, user data, caching, file deletion, processes, external boundaries.
- When the agent does something unexpected.
- Before building on something new: a dependency, a pattern, a language the owner can't read.
- After a long uninterrupted run, or a very large PR.
- When an experiment becomes something the owner is keeping. Nothing marks this moment; it is usually missed.

What to check:

- **Is anything triggered mechanically?** E.g. Clippy `disallowed-methods`, ESLint `no-restricted-imports`, `CODEOWNERS` on key files, snapshot tests of public surfaces. The tool doesn't judge the change; it makes sure a human looks.
- **Does interrogation end in evidence?** A rule that demonstrably bites, or a test that fails, rather than a reassuring paragraph.
- **Do checkpoints leave a record?** A PR checkbox, a line in the description, a `Checked-by:` trailer, a decisions doc. Without one, they are unproven to anyone else.
- **Is there a small, human-readable table of behaviour** for each top risk?

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

AI can design the data structure, but a human should look at it, especially every migration. That rule needs a mechanism: stored data needs a version, and a frozen copy of a real current record committed as a test fixture, so any format change fails a test and forces a migration to exist. Without that, a format change can silently drop user data and nobody ever sees a migration to review.

## Patterns from earlier audits

These held across several projects. Check each one.

- **Risk collects where the owner's attention isn't:** in the language they can't read, the content they didn't inspect, the semantics behind features they specified.
- **Almost everything is "exists, not enforced" or a convention.** Free private repos often can't protect `main`. Find the real gate.
- **A type contract isn't an effect contract.** Generated types show the shape of a call, not what it does (writes files, runs processes, uses the network).
- **Claims run ahead of code.** The owner confirms an intent, the agent implements a narrower version, the docs are written from the intent.
- **An agent's "all green" is only as good as the list it ran.**
- **Agents take the obvious way around friction.**
- **Versioning that nothing forces is decoration.**
- **Human work is invisible.** Ask the owner; don't infer.
- **The owner usually did ask about safeguards, but ad hoc.** The answers became fixes and roadmap items rather than checks that run on their own. Look for those roadmap items and say which are still unbuilt.

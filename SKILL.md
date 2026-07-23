---
name: codex-surgical-engineering
description: Apply scope-safe engineering workflows to existing code repositories. Use when Codex is asked to implement a bug fix or feature, refactor code, review a proposed patch, or perform maintenance with minimal scope, risk-calibrated rigor, explicit success criteria, diff review, and evidence-based verification. Do not use for code explanation, repository orientation, brainstorming, or broad greenfield architecture and design.
---

# Codex Surgical Engineering

Make the smallest correct change, preserve what you do not understand, and prove what you claim.

## Core contract

1. **Never edit blind.** Read the target file and enough callers, tests, configuration, or documentation to understand the change surface.
2. **Define done before editing.** Convert the request into observable success criteria.
3. **Use the smallest coherent patch.** Change every location required for consistency, but nothing unrelated.
4. **Match the repository.** Reuse existing architecture, naming, dependencies, error patterns, and test tools.
5. **Verify with evidence.** Do not say “done,” “fixed,” or “should work” without reporting checks actually run.
6. **Protect existing work.** Never discard, overwrite, reset, or reformat unrelated user changes.

## Calibrate rigor

Choose the lightest tier that safely fits the task.

### Tier 0 — obvious and reversible

Examples: a typo, a literal value, a clearly isolated one-line defect.

- Inspect the target and local context.
- Make the direct change.
- Run the narrowest relevant check.
- Review the diff.
- Do not add ceremony or ask questions unless the request is contradictory.

### Tier 1 — standard repository change

Examples: normal bug fix, small feature, local refactor, API validation.

- Inspect relevant code, tests, and project instructions.
- State only assumptions that could change behavior.
- Define a short plan and success checks.
- Prefer a failing reproduction or existing test before implementation when practical.
- Implement, verify, and review the complete diff.

### Tier 2 — ambiguous, broad, risky, or hard to reverse

Examples: public API changes, migrations, authentication, payments, concurrency, destructive operations, cross-module redesign.

- Identify competing interpretations and material risks.
- Ask only when the answer changes public behavior, data safety, security, cost, or an irreversible decision.
- Otherwise choose the safest reversible interpretation and state it.
- Establish baseline behavior and rollback considerations before editing.
- Verify narrow checks first, then broader integration checks.

## Workflow

### 1. Load constraints

Before editing:

- Read applicable `AGENTS.md` and `AGENTS.override.md` files.
- Inspect repository status so unrelated user changes are visible.
- Locate the target implementation, its callers, tests, configuration, and generated boundaries.
- Do not modify a file you failed to read successfully.

### 2. Frame the change

Write a compact internal change contract:

- **Outcome:** observable behavior requested.
- **Allowed scope:** files or components expected to change.
- **Protected scope:** areas that must remain untouched.
- **Success checks:** commands or observations that demonstrate completion.
- **Material assumptions:** only unresolved facts that affect behavior.

Do not broaden the request into adjacent cleanup, modernization, or future-proofing.

### 3. Inspect before designing

Prefer evidence from the repository over generic best practices.

- Search for existing patterns before creating a new abstraction.
- Read the nearest tests before deciding how to implement a fix.
- Check dependency and build files before proposing a new package.
- For generated files, identify the source-of-truth file and regeneration command.
- For a bug, reproduce it first when a practical deterministic check exists.

### 4. Implement surgically

Every changed hunk must fit one of these reasons:

1. Directly implements the requested behavior.
2. Keeps callers, schemas, types, migrations, or documentation consistent.
3. Adds or updates verification for the requested behavior.
4. Removes an orphan created by this patch.

Anything else must be reverted or explicitly requested.

Rules:

- Do not refactor adjacent code merely because it looks improvable.
- Do not reformat untouched sections.
- Do not rename public symbols unless required.
- Do not add production dependencies unless existing tools cannot solve the task and the benefit is material.
- Do not create flexibility, configuration, plugin systems, wrappers, or extension points for hypothetical future needs.
- Keep comments that explain intent, invariants, constraints, or non-obvious behavior. Do not replace them with narration of obvious syntax.

### 5. Handle errors proportionally

Error handling belongs at realistic failure boundaries:

- Validate untrusted user, network, file, database, process, and external-service inputs.
- Preserve existing repository error conventions.
- Do not wrap deterministic internal code in broad `try/except` or catch-all handlers “just in case.”
- Never swallow errors merely to make tests pass.
- Add retries only for transient operations and only when retry safety is understood.

### 6. Verify from narrow to broad

Use existing project tooling. Do not invent a new test framework solely to validate one patch.

Choose applicable evidence:

1. Focused reproduction or unit test.
2. Nearby module or package tests.
3. Type checking or static analysis.
4. Lint and formatting checks that do not rewrite unrelated files.
5. Build, compile, parse, or asset validation.
6. Integration or end-to-end test.
7. Targeted smoke test or documented manual observation.

For refactors, establish passing behavior before and after when feasible.

For non-code work, use the appropriate proof:

- Documentation: links, examples, formatting, and referenced commands are valid.
- Configuration or CI: parser validation and a dry run where available.
- Database: migration generation review, upgrade/downgrade or dry-run checks, and compatibility notes.
- UI or game scenes: project parse/build plus a focused runtime or visual check when tools permit.

If a check cannot run, report the exact command not run and the blocking reason. Never convert “not run” into “passed.”

### 7. Re-read the diff

Before reporting completion:

- Run `git diff --check` when Git is available.
- Inspect `git diff --stat` and the full relevant diff.
- Confirm no secret, generated artifact, lock file, dependency file, or unrelated formatting change appeared unexpectedly.
- Justify each hunk using the four allowed reasons above.
- Revert scope drift, including “while I am here” cleanup.

Use `scripts/verify_change_scope.py` when an allowlist or denylist can make the scope check deterministic.

### 8. Report precisely

Return a compact completion report:

- **Changed:** files and observable behavior.
- **Verified:** exact commands or checks and results.
- **Unverified / risks:** only real remaining gaps, including checks that could not run.

Do not paste large code blocks already present in the patch unless the user asks.

## Overengineering smells

When any pattern appears, pause and simplify unless the repository already requires it:

| Smell | Default correction |
|---|---|
| Interface or abstract base with one implementation | Use the concrete implementation |
| Factory with one branch | Construct directly |
| Configuration for a fixed task constant | Keep a local constant |
| Wrapper that only forwards arguments | Call the underlying API directly |
| New service/helper layer duplicating an existing path | Extend the existing path |
| Custom retry, cache, logger, parser, or validator despite an existing project utility | Reuse the project utility |
| Broad exception handling around deterministic logic | Remove it or catch the real boundary error |
| Comments that narrate syntax | Remove them; document intent only |
| Refactor mixed into a bug fix | Split it or omit it |
| New generic framework for one use case | Implement the use case directly |

## Red-flag thoughts

Treat these thoughts as a signal to stop and re-check scope:

- “While I am here…”
- “This will be useful later…”
- “It should work now…”
- “I can clean this up too…”
- “A wrapper would be cleaner…”
- “Just in case…”
- “I probably do not need to read that file…”
- “The test is inconvenient, so I will skip it…”

## Push back or stop when

- The requested change conflicts with verified behavior, security requirements, or data integrity.
- A destructive or irreversible operation lacks explicit authorization.
- Required credentials, external approvals, or unavailable services block truthful verification.
- Two interpretations produce materially different public behavior and repository evidence cannot resolve them.

Do not stop for minor reversible choices. Use the existing project pattern and continue.

## Final self-check

Before the final response, answer internally:

- Did I read every file I modified?
- Can every diff hunk be traced to the request, required consistency, verification, or cleanup caused by my patch?
- Did I preserve unrelated user changes?
- Did I use existing patterns before inventing new ones?
- Did I run the strongest practical checks and report their real outcomes?
- Did I clearly distinguish passed, failed, and not-run checks?

If any answer is no, correct the work or report the limitation honestly.

# Repository Engineering Agreement

Use the `$codex-surgical-engineering` skill when changing existing code.

## Project context

- Primary language/runtime: `<fill in>`
- Package manager: `<fill in>`
- Architecture entry points: `<fill in>`
- Generated files and their sources: `<fill in or none>`

## Required commands

Run only the commands applicable to the touched area, from narrow to broad.

- Focused tests: `<command>`
- Full tests: `<command>`
- Type check: `<command>`
- Lint: `<command>`
- Build or parse check: `<command>`
- Smoke test: `<command or manual procedure>`

Do not report a command as passed unless it was executed successfully.

## Change boundaries

- Preserve existing architecture and naming unless the request requires a change.
- Do not add dependencies without explaining why existing tools are insufficient.
- Do not edit generated output directly; edit its source and regenerate it.
- Do not change lock files, schemas, migrations, public APIs, authentication, or deployment configuration unless required by the task.
- Do not reformat or clean up unrelated code.
- Never discard unrelated working-tree changes.

## Verification expectations

Before completion:

1. Run the focused check for the requested behavior.
2. Run relevant type, lint, build, or parse checks.
3. Review `git diff --check`, `git diff --stat`, and the relevant full diff.
4. Report passed, failed, and not-run checks separately.

## Code review rules

Flag changes that:

- alter behavior without tests or another concrete verification path;
- add speculative abstraction or configuration;
- catch or suppress errors too broadly;
- modify files unrelated to the stated goal;
- claim success without executed evidence;
- introduce a dependency where the standard library or an existing project utility is sufficient.

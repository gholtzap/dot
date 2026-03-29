# dot

A beginner-friendly CLI wrapper over git. UX layer that runs 100% native git commands under the hood.

## Mission

Make git feel obvious. If a new command requires explanation, it's too complex.

## Design principles

Never write any comments unless absolutely necessary.

- **New verbs, not new concepts.** `save` not `add + commit`. `push` not `add + commit + push`. Commands should map to what the user *wants to do*, not what git *needs to hear*.
- **Opinionated defaults, escape hatches for power users.** Rebase over merge. Stage everything over selective staging. But never block someone from doing it the git way.
- **Silent passthrough.** Any command dot doesn't own goes straight to git. No warnings, no banners, no "did you mean". The user should never feel trapped.
- **Friendly errors.** Catch git's cryptic output, translate it to plain English, suggest the fix. Never show a raw git error when we can do better.
- **No emojis, no color gimmicks, no cutesy output.** Minimal, informative, done.

## Architecture rules

- Every git invocation goes through `git.py`. No direct `subprocess` calls anywhere else.
- Error translation lives in `errors.py`. One function, pattern-matched. If no pattern matches, show the raw error — never swallow it.
- `.dot/` directory auto-creates on first use of a dot command, never on passthrough. It must stay in `.gitignore`.
- All dot metadata (undo stack, future config) lives in `.dot/`. Nothing outside it.
- Tests use real git repos in temp directories. No mocking git.

## Adding new commands

Before adding a command, answer:
1. Does this collapse multiple git steps into one obvious action?
2. Can a beginner understand what it does from the name alone?
3. Does it have a single, clear default behavior?

If any answer is no, it probably shouldn't be a dot command — let it passthrough to git.

## What not to do

- Don't add flags that replicate git's own flags. If someone needs `--force`, they can use `dot push --force` (passthrough).
- Don't add config/preferences in v1. Smart defaults only.
- Don't add interactive prompts unless the user *must* make a choice (like setting an upstream). Never prompt for confirmation of normal operations.
- Don't wrap commands that git already does well. `dot log` is just passthrough — don't reinvent it.
- Don't add dependencies beyond Click.

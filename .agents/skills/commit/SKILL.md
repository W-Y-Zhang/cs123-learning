---
name: commit
description: Stage changes and create a commit with emoji-prefixed conventional commit message
disable-model-invocation: true
argument-hint: "[optional message]"
allowed-tools: Bash, Read, Grep, Glob
---

# Emoji Commit

Stage relevant changes and create a commit following this project's emoji + conventional commit style.

## Steps

1. Run `git status` and `git diff` to understand current changes
2. Check `git remote -v` and `git branch -vv` before staging when the repository has both private and public remotes
3. Determine the commit type and choose the matching emoji
4. Write a concise Chinese commit message (1-2 sentences)
5. Stage the relevant files (prefer specific files over `git add -A`)
6. Commit with the format: `<emoji> <type>: <description>`

## Private / public repository policy

This repository can have two remotes:

- Private: `git@github.com:robots-hub/dive-into-embodied-ai.git` (`origin`)
- Public: `git@github.com:datawhalechina/dive-into-embodied-ai.git` (`public`)

Keep public-safe project changes synchronized across both repositories. AI collaboration traces must remain private-only and must not be included in commits intended for the public repository.

Treat these paths as private AI traces:

- `AGENTS.md`
- `CLAUDE.md`
- `.claude/`
- `.codex/`
- `.cursor/`
- `.cursor/skills/`
- `.agents/`
- `.agents/skills/`
- `.agents/skills/commit/`

If a working tree contains both public-safe changes and private AI traces, split them into separate commits. Stage public-safe files separately and keep that commit usable for both remotes. Stage private AI traces in a private-only commit and push it only to `origin`. Never push a commit containing the private AI trace paths above to the `public` remote.

## Emoji mapping

| Emoji | Type       | When to use                    |
|-------|------------|--------------------------------|
| ✨    | feat       | New feature                    |
| 🐛    | fix        | Bug fix                        |
| 📝    | docs       | Documentation changes          |
| 💄    | style      | Formatting, UI, cosmetic       |
| ♻️    | refactor   | Code restructure, no behavior change |
| ⚡    | perf       | Performance improvement        |
| ✅    | test       | Add or update tests            |
| 🔧    | chore      | Build, config, tooling         |
| 🚀    | deploy     | Deployment related             |
| 🔥    | remove     | Remove code or files           |

## Commit message rules

- Format: `<emoji> <type>: <description>`
- Description in Chinese, concise
- Do NOT append any Co-Authored-By line

## User hint

$ARGUMENTS

If the user provided a message hint above, use it to guide the commit message content. Otherwise, infer from the diff.

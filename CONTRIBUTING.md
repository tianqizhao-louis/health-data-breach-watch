# Contributing

Thanks for helping. A few rules keep this skill safe and small.

## Before you open a PR

```bash
make check   # Agent Skills format: name, description length, referenced files
make test    # script tests against the eval fixtures
```

## Changing the skill

- **Keep it read-only.** No change may let the agent send, click, label, delete or contact anyone. PRs that loosen the ground rules won't be merged.
- **Keep `SKILL.md` self-sufficient.** People paste it into chats on its own, so it must work without `references/` or `scripts/`.
- **Keep it short.** Put detail in `references/`, and keep the description under 1,024 characters.
- **Add a fixture for every new behavior.** Add a scenario to `evals/evals.json` with files in `evals/files/<name>/`, and a test in `tests/` if a script changed. Fixtures must be fictional: use 555 phone numbers and made-up names, codes and domains.
- **Bump `metadata.version`** in `SKILL.md` and `.claude-plugin/marketplace.json`, and add a `CHANGELOG.md` entry.

## Adding a skill for another breach

Copy `skills/health-breach-watch/` to a new folder, rename the `name` field to match the folder, edit the Configuration block, and add the folder to `.claude-plugin/marketplace.json`.

## Releasing

Push a tag such as `v3.0.0`. The release workflow runs the tests and attaches `health-breach-watch.zip` to a GitHub release, which the README's download link points to.

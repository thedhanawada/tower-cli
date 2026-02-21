# Tower CLI

Claude Code lets AI run tools on your machine — file reads, writes, bash commands, the lot. By default you're clicking "allow" on every single one, or you yolo it with `--dangerously-skip-permissions`. Neither is great.

Tower sits between Claude Code and tool execution as a [PreToolUse hook](https://docs.anthropic.com/en/docs/claude-code/hooks). You write rules in a YAML file — which tools to allow, which to block, which to still ask about — and Tower enforces them automatically. No more allow-fatigue, no more hoping Claude doesn't `rm -rf` something important.

## Install

```bash
pip install tower-cli
tower init
```

That's it. This creates `~/.claude/tower-rules.yml` and wires up the hook in `~/.claude/settings.json`. Works globally across all your projects.

If you want rules scoped to a single project:

```bash
cd your-project
tower init --local
```

If you skip `tower init` entirely and just start using Claude Code, Tower auto-creates a default config at `~/.claude/tower-rules.yml` the first time it evaluates a tool call.

## What the config looks like

```yaml
version: 1
default: ask  # what happens when no rule matches: allow | deny | ask

rules:
  # Reads and searches are safe, let them through
  - tool: Read
    action: allow
  - tool: Glob
    action: allow
  - tool: Grep
    action: allow

  # Allow harmless bash commands
  - tool: Bash
    command_pattern: "^(ls|cat|git status|git diff|npm test|pytest).*"
    action: allow

  # Block destructive bash commands outright
  - tool: Bash
    command_pattern: "rm -rf|git push --force|DROP TABLE"
    action: deny
    reason: "Destructive command blocked by Tower"

  # Allow writes only to code files
  - tool: Write
    path_pattern: "**/*.{py,js,ts,json,yml,yaml,md}"
    action: allow
```

Rules are evaluated top-to-bottom, first match wins. If nothing matches, the `default` action kicks in.

Tower looks for `tower-rules.yml` in this order:

1. `./tower-rules.yml` (project root)
2. `./.claude/tower-rules.yml` (project-local)
3. `~/.claude/tower-rules.yml` (global)

### Rule fields

| Field             | Required | Description                                    |
|-------------------|----------|------------------------------------------------|
| `tool`            | Yes      | Tool name (Bash, Read, Write, Edit, Glob, etc) |
| `action`          | Yes      | `allow`, `deny`, or `ask`                      |
| `command_pattern` | No       | Regex pattern for Bash commands                 |
| `path_pattern`    | No       | Glob pattern for file paths                     |
| `reason`          | No       | Message shown when a rule triggers              |

## Commands

| Command              | What it does                                       |
|----------------------|----------------------------------------------------|
| `tower init`         | Set up global config + hook in `~/.claude/`        |
| `tower init --local` | Set up project-local config + hook in `./.claude/` |
| `tower status`       | Show loaded rules and whether the hook is wired up |
| `tower config`       | Interactive TUI for editing rules                  |
| `tower evaluate`     | Evaluate a tool call from stdin (called by hook)   |

## Interactive config

Don't want to edit YAML by hand? `tower config` gives you a TUI.

You get a main menu, your current config info, and arrow-key navigation:

<p align="center">
  <img src="docs/menu.svg" alt="Tower Config main menu" width="700">
</p>

All your rules laid out in a table — green for allow, red for deny, yellow for ask:

<p align="center">
  <img src="docs/rules_table.svg" alt="Rules table view" width="750">
</p>

Adding a rule — pick a tool from the fuzzy-searchable list, choose an action, done:

<p align="center">
  <img src="docs/add_rule.svg" alt="Add rule flow" width="700">
</p>

Deleting a rule asks for confirmation so you don't accidentally nuke something:

<p align="center">
  <img src="docs/delete_confirm.svg" alt="Delete confirmation" width="700">
</p>

## How it works under the hood

1. Claude Code is about to run a tool (say, `Bash` with `rm -rf /tmp/stuff`)
2. The PreToolUse hook pipes the tool call to `tower evaluate` via stdin
3. Tower loads your rules, checks them top-to-bottom
4. First matching rule decides: `allow`, `deny`, or `ask`
5. If no rule matches, the `default` action is used
6. Tower sends the decision back to Claude Code

## Development

```bash
pip install -e ".[dev]"
pytest
```

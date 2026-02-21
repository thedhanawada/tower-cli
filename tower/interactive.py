"""Interactive configuration UI for Tower using InquirerPy and Rich."""

from InquirerPy import inquirer
from InquirerPy.separator import Separator
from InquirerPy.utils import InquirerPyStyle
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from tower.config import find_config_path, load_config, save_config

console = Console()

TOOL_CHOICES = [
    "Bash",
    "Read",
    "Write",
    "Edit",
    "Glob",
    "Grep",
    "NotebookEdit",
    "Task",
    "WebFetch",
    "WebSearch",
]

ACTION_CHOICES = ["allow", "deny", "ask"]

# InquirerPy theme: cyan pointer, green answer
THEME = InquirerPyStyle(
    {
        "questionmark": "#e5c07b",
        "answermark": "#e5c07b",
        "answer": "#98c379",
        "input": "#98c379",
        "question": "",
        "answered_question": "",
        "instruction": "#61afef",
        "long_instruction": "#5c6370",
        "pointer": "#56b6c2",
        "checkbox": "#98c379",
        "separator": "",
        "skipped": "#5c6370",
        "validator": "",
        "marker": "#e5c07b",
        "fuzzy_prompt": "#56b6c2",
        "fuzzy_info": "#5c6370",
        "fuzzy_border": "#56b6c2",
        "fuzzy_match": "#c678dd",
    }
)

ACTION_COLORS = {"allow": "green", "deny": "red", "ask": "yellow"}
ACTION_SYMBOLS = {"allow": "\u2713", "deny": "\u2717", "ask": "?"}


def _styled_action(action):
    """Return a rich-formatted action string."""
    color = ACTION_COLORS.get(action, "white")
    symbol = ACTION_SYMBOLS.get(action, " ")
    return f"[{color}]{symbol} {action.upper()}[/{color}]"


def _show_banner(config_path, config):
    """Show a styled banner with config info."""
    rule_count = len(config.get("rules", []))
    default = config.get("default", "ask")
    color = ACTION_COLORS.get(default, "white")

    content = (
        f"[bold]Tower Config[/bold]  [dim]v0.1.0[/dim]\n"
        f"[dim]{config_path}[/dim]\n"
        f"{rule_count} rules \u2022 default: [{color}]{default.upper()}[/{color}]"
    )
    console.print()
    console.print(Panel(content, border_style="cyan", padding=(0, 2)))
    console.print()


def run_interactive_config():
    """Launch the interactive Tower config menu."""
    config_path = find_config_path()
    if config_path is None:
        console.print("[red]No tower-rules.yml found. Run 'tower init' first.[/red]")
        return 1

    config = load_config(config_path)
    _dirty = False

    _show_banner(config_path, config)

    while True:
        action = inquirer.select(
            message="Tower Config",
            choices=[
                "View rules",
                "Add rule",
                "Edit rule",
                "Delete rule",
                "Change default action",
                "Reset to defaults",
                Separator(),
                "Save & exit",
                "Exit without saving",
            ],
            border=True,
            instruction="(arrow keys to navigate)",
            pointer="\u276f",
            style=THEME,
        ).execute()

        if action == "View rules":
            _view_rules(config)
        elif action == "Add rule":
            _add_rule(config)
            _dirty = True
        elif action == "Edit rule":
            if _edit_rule(config):
                _dirty = True
        elif action == "Delete rule":
            if _delete_rule(config):
                _dirty = True
        elif action == "Change default action":
            if _change_default(config):
                _dirty = True
        elif action == "Reset to defaults":
            if inquirer.confirm(
                message="Reset all rules to defaults?",
                default=False,
                style=THEME,
            ).execute():
                from tower.config import DEFAULT_CONFIG
                import yaml
                config = yaml.safe_load(DEFAULT_CONFIG)
                _dirty = True
                console.print("[green]Config reset to defaults.[/green]\n")
        elif action == "Save & exit":
            save_config(config, config_path)
            console.print(f"[bold green]\u2713 Saved to {config_path}[/bold green]")
            return 0
        elif action == "Exit without saving":
            if _dirty:
                if not inquirer.confirm(
                    message="You have unsaved changes. Exit anyway?",
                    default=False,
                    style=THEME,
                ).execute():
                    continue
            return 0


def _view_rules(config):
    """Display rules in a rich table."""
    default = config.get("default", "ask")
    color = ACTION_COLORS.get(default, "white")
    console.print(f"\n  Default action: [{color}][bold]{default.upper()}[/bold][/{color}]")

    rules = config.get("rules", [])
    if not rules:
        console.print("  [dim]No rules defined.[/dim]\n")
        return

    table = Table(
        box=box.ROUNDED,
        border_style="dim",
        title=f"{len(rules)} Rules",
        title_style="bold",
        padding=(0, 1),
    )
    table.add_column("#", style="dim", width=3, justify="right")
    table.add_column("Action", width=8)
    table.add_column("Tool", style="cyan")
    table.add_column("Pattern", style="dim")
    table.add_column("Reason", style="dim italic")

    for i, rule in enumerate(rules):
        action = rule["action"]
        action_color = ACTION_COLORS.get(action, "white")
        action_text = f"[{action_color}]{action.upper()}[/{action_color}]"

        pattern_parts = []
        if "command_pattern" in rule:
            pattern_parts.append(f"cmd:/{rule['command_pattern']}/")
        if "path_pattern" in rule:
            pattern_parts.append(f"path:{rule['path_pattern']}")
        pattern = " ".join(pattern_parts) if pattern_parts else "\u2014"

        reason = rule.get("reason", "\u2014")

        table.add_row(str(i + 1), action_text, rule["tool"], pattern, reason)

    console.print()
    console.print(table)
    console.print()


def _format_rule_colored(i, rule):
    """Format a rule for display in InquirerPy selection lists with action prefix."""
    action = rule["action"]
    symbol = ACTION_SYMBOLS.get(action, " ")
    desc = f"{symbol} {rule['action'].upper():5s} {rule['tool']}"
    if "command_pattern" in rule:
        desc += f"  cmd:/{rule['command_pattern']}/"
    if "path_pattern" in rule:
        desc += f"  path:{rule['path_pattern']}"
    return f"{i + 1}. {desc}"


def _add_rule(config):
    """Interactively add a new rule."""
    tool = inquirer.fuzzy(
        message="Tool name:",
        choices=TOOL_CHOICES,
        border=True,
        long_instruction="Type to filter tools",
        pointer="\u276f",
        style=THEME,
    ).execute()

    action = inquirer.select(
        message="Action:",
        choices=[
            {"name": "\u2713 Allow", "value": "allow"},
            {"name": "\u2717 Deny", "value": "deny"},
            {"name": "? Ask", "value": "ask"},
        ],
        long_instruction="What should Tower do when this tool is invoked?",
        pointer="\u276f",
        style=THEME,
    ).execute()

    rule = {"tool": tool, "action": action}

    if tool == "Bash":
        pattern = inquirer.text(
            message="Command pattern (regex, leave empty to match all):",
            long_instruction="e.g. ^(ls|git status).*",
            style=THEME,
        ).execute().strip()
        if pattern:
            rule["command_pattern"] = pattern

    if tool in ("Read", "Write", "Edit", "Glob", "Grep"):
        pattern = inquirer.text(
            message="Path pattern (glob, leave empty to match all):",
            long_instruction="e.g. **/*.py",
            style=THEME,
        ).execute().strip()
        if pattern:
            rule["path_pattern"] = pattern

    reason = inquirer.text(
        message="Reason (optional):",
        long_instruction="Shown when a rule matches",
        style=THEME,
    ).execute().strip()
    if reason:
        rule["reason"] = reason

    config.setdefault("rules", []).append(rule)
    console.print(f"[green]\u2713 Added: {action.upper()} {tool}[/green]\n")


def _edit_rule(config):
    """Interactively edit an existing rule. Returns True if a rule was edited."""
    rules = config.get("rules", [])
    if not rules:
        console.print("[dim]No rules to edit.[/dim]\n")
        return False

    choices = [_format_rule_colored(i, r) for i, r in enumerate(rules)]
    choices.append("Cancel")

    selected = inquirer.select(
        message="Select rule to edit:",
        choices=choices,
        border=True,
        pointer="\u276f",
        style=THEME,
    ).execute()

    if selected == "Cancel":
        return False

    idx = choices.index(selected)
    rule = rules[idx]

    rule["tool"] = inquirer.fuzzy(
        message="Tool name:",
        choices=TOOL_CHOICES,
        default=rule["tool"],
        border=True,
        long_instruction="Type to filter tools",
        pointer="\u276f",
        style=THEME,
    ).execute()

    rule["action"] = inquirer.select(
        message="Action:",
        choices=[
            {"name": "\u2713 Allow", "value": "allow"},
            {"name": "\u2717 Deny", "value": "deny"},
            {"name": "? Ask", "value": "ask"},
        ],
        default=rule["action"],
        long_instruction="What should Tower do when this tool is invoked?",
        pointer="\u276f",
        style=THEME,
    ).execute()

    if rule["tool"] == "Bash":
        current = rule.get("command_pattern", "")
        new_val = inquirer.text(
            message="Command pattern (regex):",
            default=current,
            long_instruction="e.g. ^(ls|git status).*",
            style=THEME,
        ).execute().strip()
        if new_val:
            rule["command_pattern"] = new_val
        else:
            rule.pop("command_pattern", None)
    else:
        rule.pop("command_pattern", None)

    if rule["tool"] in ("Read", "Write", "Edit", "Glob", "Grep"):
        current = rule.get("path_pattern", "")
        new_val = inquirer.text(
            message="Path pattern (glob):",
            default=current,
            long_instruction="e.g. **/*.py",
            style=THEME,
        ).execute().strip()
        if new_val:
            rule["path_pattern"] = new_val
        else:
            rule.pop("path_pattern", None)
    else:
        rule.pop("path_pattern", None)

    current_reason = rule.get("reason", "")
    new_reason = inquirer.text(
        message="Reason (optional):",
        default=current_reason,
        long_instruction="Shown when a rule matches",
        style=THEME,
    ).execute().strip()
    if new_reason:
        rule["reason"] = new_reason
    else:
        rule.pop("reason", None)

    console.print("[green]\u2713 Rule updated.[/green]\n")
    return True


def _delete_rule(config):
    """Interactively delete a rule. Returns True if a rule was deleted."""
    rules = config.get("rules", [])
    if not rules:
        console.print("[dim]No rules to delete.[/dim]\n")
        return False

    choices = [_format_rule_colored(i, r) for i, r in enumerate(rules)]
    choices.append("Cancel")

    selected = inquirer.select(
        message="Select rule to delete:",
        choices=choices,
        border=True,
        pointer="\u276f",
        style=THEME,
    ).execute()

    if selected == "Cancel":
        return False

    idx = choices.index(selected)
    removed = rules[idx]

    if not inquirer.confirm(
        message=f"Delete rule: {removed['action'].upper()} {removed['tool']}?",
        default=False,
        style=THEME,
    ).execute():
        return False

    rules.pop(idx)
    console.print(f"[red]\u2717 Deleted: {removed['action'].upper()} {removed['tool']}[/red]\n")
    return True


def _change_default(config):
    """Change the default action. Returns True if changed."""
    current = config.get("default", "ask")
    new_default = inquirer.select(
        message="Default action when no rule matches:",
        choices=[
            {"name": "\u2713 Allow", "value": "allow"},
            {"name": "\u2717 Deny", "value": "deny"},
            {"name": "? Ask", "value": "ask"},
        ],
        default=current,
        long_instruction="Applied when no specific rule matches a tool invocation",
        pointer="\u276f",
        style=THEME,
    ).execute()

    if new_default == current:
        return False

    config["default"] = new_default
    color = ACTION_COLORS.get(new_default, "white")
    console.print(f"Default action set to: [{color}][bold]{new_default.upper()}[/bold][/{color}]\n")
    return True

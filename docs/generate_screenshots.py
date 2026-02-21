"""Generate SVG screenshots of Tower Config UI components."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box


ACTION_COLORS = {"allow": "green", "deny": "red", "ask": "yellow"}


def render_banner(console):
    """Render the config banner."""
    content = (
        "[bold]Tower Config[/bold]  [dim]v0.1.0[/dim]\n"
        "[dim]/home/user/.claude/tower-rules.yml[/dim]\n"
        "7 rules \u2022 default: [yellow]ASK[/yellow]"
    )
    console.print()
    console.print(Panel(content, border_style="cyan", padding=(0, 2)))
    console.print()


def render_menu(console):
    """Render a simulated main menu."""
    console.print("[#e5c07b]?[/#e5c07b] Tower Config [#61afef](arrow keys to navigate)[/#61afef]")
    items = [
        ("View rules", True),
        ("Add rule", False),
        ("Edit rule", False),
        ("Delete rule", False),
        ("Change default action", False),
        ("Reset to defaults", False),
        (None, False),  # separator
        ("Save & exit", False),
        ("Exit without saving", False),
    ]
    for item, selected in items:
        if item is None:
            console.print("  [dim]──────────────────[/dim]")
        elif selected:
            console.print(f"  [#56b6c2]\u276f[/#56b6c2] [bold]{item}[/bold]")
        else:
            console.print(f"    [dim]{item}[/dim]")
    console.print()


def render_rules_table(console):
    """Render the rules table."""
    console.print("  Default action: [yellow][bold]ASK[/bold][/yellow]")
    console.print()

    rules = [
        {"tool": "Read", "action": "allow", "pattern": "\u2014", "reason": "\u2014"},
        {"tool": "Glob", "action": "allow", "pattern": "\u2014", "reason": "\u2014"},
        {"tool": "Grep", "action": "allow", "pattern": "\u2014", "reason": "\u2014"},
        {"tool": "Bash", "action": "allow", "pattern": "cmd:/^(ls|cat|git status|git diff|npm test|pytest).*/", "reason": "\u2014"},
        {"tool": "Bash", "action": "deny", "pattern": "cmd:/rm -rf|git push --force|DROP TABLE/", "reason": "Destructive command blocked by Tower"},
        {"tool": "Write", "action": "allow", "pattern": "path:**/*.{py,js,ts,json,yml,yaml,md}", "reason": "\u2014"},
        {"tool": "WebFetch", "action": "allow", "pattern": "\u2014", "reason": "\u2014"},
    ]

    table = Table(
        box=box.ROUNDED,
        border_style="dim",
        title="7 Rules",
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
        color = ACTION_COLORS.get(action, "white")
        action_text = f"[{color}]{action.upper()}[/{color}]"
        table.add_row(str(i + 1), action_text, rule["tool"], rule["pattern"], rule["reason"])

    console.print(table)
    console.print()


def render_add_rule(console):
    """Render a simulated add-rule flow."""
    console.print("[#e5c07b]?[/#e5c07b] Tool name: [dim]Type to filter tools[/dim]")
    console.print("  \u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510")
    tools = ["Bash", "Read", "Write", "Edit", "Glob", "Grep"]
    for i, t in enumerate(tools):
        if i == 0:
            console.print(f"  \u2502 [#56b6c2]\u276f[/#56b6c2] [bold]{t}[/bold]          \u2502")
        else:
            console.print(f"  \u2502   [dim]{t}[/dim]          \u2502")
    console.print("  \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518")
    console.print()
    console.print("[#e5c07b]?[/#e5c07b] Action:")
    console.print("  [#56b6c2]\u276f[/#56b6c2] [bold][green]\u2713 Allow[/green][/bold]")
    console.print("    [dim][red]\u2717 Deny[/red][/dim]")
    console.print("    [dim][yellow]? Ask[/yellow][/dim]")
    console.print()
    console.print("[green]\u2713 Added: ALLOW Bash[/green]")
    console.print()


def render_delete_confirm(console):
    """Render a simulated delete confirmation."""
    console.print("[#e5c07b]?[/#e5c07b] Delete rule: DENY Bash? [#61afef](y/N)[/#61afef] [#98c379]Yes[/#98c379]")
    console.print("[red]\u2717 Deleted: DENY Bash[/red]")
    console.print()


def render_save(console):
    """Render save message."""
    console.print("[bold green]\u2713 Saved to /home/user/.claude/tower-rules.yml[/bold green]")
    console.print()


def generate(name, render_fn, width=100):
    console = Console(record=True, width=width, force_terminal=True)
    render_fn(console)
    svg = console.export_svg(title="Tower Config")
    path = os.path.join(os.path.dirname(__file__), f"{name}.svg")
    with open(path, "w") as f:
        f.write(svg)
    print(f"Generated {path}")


if __name__ == "__main__":
    generate("banner", render_banner)
    generate("menu", lambda c: (render_banner(c), render_menu(c)))
    generate("rules_table", render_rules_table, width=110)
    generate("add_rule", render_add_rule)
    generate("delete_confirm", render_delete_confirm)
    generate("save", render_save)

    # Full flow composite
    def full_flow(c):
        render_banner(c)
        render_menu(c)

    generate("overview", full_flow)

"""Terminal setup command for configuring Shift+Enter multiline input."""

import os

import typer
from rich.console import Console
from rich.markdown import Markdown

app = typer.Typer(
    name="terminal-setup",
    help="Configure terminal for Shift+Enter multiline input",
    no_args_is_help=False,
)

console = Console(stderr=True)


def detect_terminal() -> str:
    """Detect terminal type from environment variables.

    Returns:
        Terminal identifier string (e.g., "vscode", "iterm2", "ghostty").
    """
    term_program = os.environ.get("TERM_PROGRAM", "").lower()
    term = os.environ.get("TERM", "").lower()

    if "vscode" in term_program:
        return "vscode"
    elif term_program == "iterm.app":
        return "iterm2"
    elif term_program == "ghostty":
        return "ghostty"
    elif term_program == "wezterm":
        return "wezterm"
    elif "kitty" in term:
        return "kitty"
    elif term_program == "apple_terminal":
        return "terminal_app"
    else:
        return "unknown"


# Terminal-specific configuration instructions
TERMINAL_INSTRUCTIONS: dict[str, str] = {
    "vscode": """
## VS Code Terminal Setup

Add to your **keybindings.json** (Cmd+Shift+P > "Preferences: Open Keyboard Shortcuts (JSON)"):

```json
{
  "key": "shift+enter",
  "command": "workbench.action.terminal.sendSequence",
  "args": { "text": "\\u001b[13;2u" },
  "when": "terminalFocus"
}
```

After adding, Shift+Enter will add newlines in jiro dream, and Enter will submit.
""",
    "iterm2": """
## iTerm2 Setup

1. Open **iTerm2 > Preferences > Keys > Key Mappings**
2. Click **+** to add a new mapping
3. Configure:
   - **Keyboard Shortcut**: Shift+Return
   - **Action**: Send Escape Sequence
   - **Esc+**: `[13;2u`

After configuration, Shift+Enter will add newlines in jiro dream, and Enter will submit.
""",
    "ghostty": """
## Ghostty Setup

Ghostty supports the CSI u protocol natively. Add to your Ghostty config:

```
keybind = shift+enter=text:\\x1b[13;2u
```

Or Ghostty may already send the correct sequence with modifyOtherKeys enabled.
Test by running `jiro dream` - Shift+Enter should add newlines automatically.
""",
    "wezterm": """
## WezTerm Setup

Add to your `~/.wezterm.lua`:

```lua
local wezterm = require 'wezterm'
local config = {}

config.keys = {
  {
    key = 'Enter',
    mods = 'SHIFT',
    action = wezterm.action.SendString '\\x1b[13;2u',
  },
}

return config
```

After configuration, Shift+Enter will add newlines in jiro dream, and Enter will submit.
""",
    "kitty": """
## Kitty Setup

Kitty supports the Kitty keyboard protocol natively. Add to your `~/.config/kitty/kitty.conf`:

```
map shift+enter send_text all \\x1b[13;2u
```

After configuration, Shift+Enter will add newlines in jiro dream, and Enter will submit.
""",
    "terminal_app": """
## macOS Terminal.app

Unfortunately, Terminal.app does not support custom key sequences for Shift+Enter.

**Alternatives:**
- Use **Meta+Enter** (Option+Enter) to submit instead
- Switch to iTerm2 or another terminal that supports key mapping

Current behavior: Enter adds newlines, Meta+Enter (Option+Enter) submits.
""",
    "unknown": """
## Unknown Terminal

Your terminal was not automatically detected.

**Current behavior** (fallback mode):
- **Enter** = add newline (continue typing)
- **Meta+Enter** (Alt/Option+Enter) = submit

If your terminal supports custom key mappings, configure Shift+Enter to send:
`\\x1b[13;2u` (ESC [ 1 3 ; 2 u)

Common terminals and their configuration:
- **VS Code**: Add keybinding to keybindings.json
- **iTerm2**: Preferences > Keys > Key Mappings
- **Ghostty**: Add keybind to config
- **WezTerm**: Add to ~/.wezterm.lua
- **Kitty**: Add map to kitty.conf

Run `jiro terminal-setup` again after switching terminals.
""",
}


@app.callback(invoke_without_command=True)
def terminal_setup_callback(ctx: typer.Context) -> None:
    """Configure terminal for Shift+Enter multiline input.

    Detects your terminal and provides configuration instructions
    to enable Shift+Enter for adding newlines in jiro dream.

    After configuration:
    - Shift+Enter = add newline (continue typing)
    - Enter = submit
    """
    if ctx.invoked_subcommand is not None:
        return

    terminal = detect_terminal()
    console.print(f"\nDetected terminal: [cyan]{terminal}[/cyan]\n")

    instructions = TERMINAL_INSTRUCTIONS.get(terminal, TERMINAL_INSTRUCTIONS["unknown"])
    console.print(Markdown(instructions))

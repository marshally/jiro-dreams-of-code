# ADR-010: Terminal Multiline Input with Shift+Enter

## Status

Accepted

## Context

Users expect Shift+Enter to add newlines while Enter submits, matching behavior in chat applications and Claude Code. However, standard terminal emulators cannot distinguish Shift+Enter from Enter at the protocol level—both send the same newline character.

Claude Code solves this via a `/terminal-setup` command that provides terminal-specific configuration instructions. Each terminal must be configured to send a special escape sequence when Shift+Enter is pressed.

## Decision

Implement a two-tier approach for multiline input in `jiro dream`:

### Tier 1: Fallback Behavior (No Configuration Required)

Using prompt_toolkit with `multiline=True`:

- **Enter** = add newline (continue typing)
- **Meta+Enter** (Alt/Option+Enter) or Escape+Enter = submit

This works out-of-the-box on all terminals.

### Tier 2: Configured Behavior (After Terminal Setup)

After running `jiro terminal-setup` and configuring the terminal:

- **Shift+Enter** = add newline (via CSI u escape sequence)
- **Enter** = submit

### Escape Sequence Handling

Terminals configured for Shift+Enter send one of these sequences:

| Protocol | Sequence | Terminals |
|----------|----------|-----------|
| CSI u | `\x1b[13;2u` | VS Code, WezTerm, Kitty |
| modifyOtherKeys | `\x1b[27;2;13~` | Ghostty |

prompt_toolkit key bindings parse these sequences and insert newlines:

```python
from prompt_toolkit.keys import Keys

bindings = KeyBindings()


# CSI u protocol: ESC [ 13 ; 2 u
@bindings.add(Keys.Escape, "[", "1", "3", ";", "2", "u")
def _insert_newline_csi_u(event):
    event.current_buffer.insert_text("\n")


# modifyOtherKeys: ESC [ 27 ; 2 ; 13 ~
@bindings.add(Keys.Escape, "[", "2", "7", ";", "2", ";", "1", "3", "~")
def _insert_newline_modify_other_keys(event):
    event.current_buffer.insert_text("\n")
```

### Terminal Setup Command

`jiro terminal-setup` detects the terminal via environment variables (`TERM_PROGRAM`, `TERM`) and displays configuration instructions:

- **VS Code**: Add keybinding to keybindings.json
- **iTerm2**: Preferences > Keys > Key Mappings
- **Ghostty**: Add keybind to config file
- **WezTerm**: Add to ~/.wezterm.lua
- **Kitty**: Add map to kitty.conf
- **Terminal.app**: Not supported (use fallback)

## Consequences

### Positive

- **Works everywhere**: Fallback behavior requires no setup
- **Matches user expectations**: After setup, Shift+Enter behaves like chat apps
- **Follows Claude Code pattern**: Users familiar with Claude Code will recognize the approach
- **Discoverable**: Messages in `jiro dream` mention the terminal-setup command

### Negative

- **Requires terminal configuration**: Users must run setup and configure their terminal
- **Not all terminals supported**: Terminal.app and some others can't be configured
- **Complex escape sequence parsing**: CSI u and modifyOtherKeys are different formats
- **prompt_toolkit dependency**: Added for multiline input handling

### Why Not Just Use Enter to Submit?

Single-line input (Enter = submit immediately) was considered but rejected because:

1. Users writing detailed feature descriptions need multiple lines
1. Refinement feedback often spans multiple paragraphs
1. Interview answers may include examples or lists

The multiline-first approach matches the conversational nature of `jiro dream`.

## Alternatives Considered

1. **Backslash+Enter**: Type `\` then Enter to add newline. Universal but awkward.
1. **Double-Enter to submit**: Blank line submits. Ambiguous when users want actual blank lines.
1. **Ctrl+D to submit**: Unix-style EOF. Less discoverable for non-Unix users.
1. **Single-line only**: Force users to write concise prompts. Poor UX for detailed specs.

Meta+Enter was chosen as the fallback because it's the standard prompt_toolkit pattern and matches IPython behavior.

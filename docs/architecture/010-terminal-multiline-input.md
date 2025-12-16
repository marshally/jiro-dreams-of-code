# ADR-010: Terminal Multiline Input with Shift+Enter

## Status

Accepted (Revised)

## Context

Users expect Shift+Enter to add newlines while Enter submits, matching behavior in chat applications and Claude Code. However, standard terminal emulators cannot distinguish Shift+Enter from Enter at the protocol level—both send the same newline character.

## Decision

Enable **modifyOtherKeys mode** automatically by sending escape sequences to the terminal. This allows Shift+Enter to work without manual configuration.

### How It Works

On startup, `jiro dream` sends `CSI > 4 ; 2 m` (`\x1b[>4;2m`) to enable modifyOtherKeys level 2. On exit, it sends `CSI > 4 ; 0 m` (`\x1b[>4;0m`) to disable it.

With modifyOtherKeys enabled:

- **Enter** = submit
- **Shift+Enter** = add newline

Terminals that don't support modifyOtherKeys will ignore the escape sequences, and users can fall back to **Meta+Enter** (Alt/Option+Enter) for newlines.

### Implementation

```python
@contextmanager
def _enhanced_keyboard_mode() -> Generator[None, None, None]:
    # Enable modifyOtherKeys level 2 (all keys)
    sys.stderr.write("\x1b[>4;2m")
    sys.stderr.flush()
    try:
        yield
    finally:
        # Disable modifyOtherKeys
        sys.stderr.write("\x1b[>4;0m")
        sys.stderr.flush()
```

### Escape Sequence Handling

Terminals send these sequences for Shift+Enter when modifyOtherKeys is enabled:

| Protocol | Sequence | Terminals |
|----------|----------|-----------|
| modifyOtherKeys | `\x1b[27;2;13~` | iTerm2, Ghostty, xterm |
| CSI u | `\x1b[13;2u` | VS Code, WezTerm, Kitty |

prompt_toolkit key bindings parse these sequences and insert newlines:

```python
from prompt_toolkit.keys import Keys

bindings = KeyBindings()


# modifyOtherKeys: ESC [ 27 ; 2 ; 13 ~
@bindings.add(Keys.Escape, "[", "2", "7", ";", "2", ";", "1", "3", "~")
def _insert_newline_modify_other_keys(event):
    event.current_buffer.insert_text("\n")


# CSI u protocol: ESC [ 13 ; 2 u
@bindings.add(Keys.Escape, "[", "1", "3", ";", "2", "u")
def _insert_newline_csi_u(event):
    event.current_buffer.insert_text("\n")
```

## Consequences

### Positive

- **Works automatically**: No manual terminal configuration required
- **Matches user expectations**: Shift+Enter behaves like chat apps
- **Graceful fallback**: Meta+Enter works on unsupported terminals
- **Clean restore**: Mode is disabled on exit

### Negative

- **Not all terminals supported**: Some terminals ignore modifyOtherKeys
- **Escape sequence complexity**: Different terminals use different formats
- **prompt_toolkit dependency**: Required for key binding parsing

### Terminal Support

| Terminal | modifyOtherKeys Support |
|----------|------------------------|
| iTerm2 | ✅ Yes |
| VS Code | ✅ Yes |
| Ghostty | ✅ Yes |
| WezTerm | ✅ Yes |
| Kitty | ✅ Yes |
| xterm | ✅ Yes (origin of feature) |
| Terminal.app | ⚠️ Partial |

## Revision History

- **Initial**: Two-tier approach with manual `jiro terminal-setup` command
- **Revised**: Automatic modifyOtherKeys mode via escape sequences (removed terminal-setup command)

## References

- [xterm Control Sequences](https://invisible-island.net/xterm/ctlseqs/ctlseqs.html)
- [Neovim modifyOtherKeys implementation](https://github.com/neovim/neovim/issues/15352)

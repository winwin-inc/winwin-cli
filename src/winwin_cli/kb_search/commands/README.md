# KB Search Commands Architecture

## Overview

The kb_search CLI uses a **plugin-based architecture** that makes it extremely easy to add new commands. Each command is a self-contained module that is automatically discovered and registered at runtime.

## Architecture Benefits

- **Zero configuration**: New commands are automatically discovered
- **Isolation**: Each command is in its own file
- **No modification needed**: Adding a command doesn't require editing `cli.py` or other commands
- **Testability**: Commands can be tested independently
- **Maintainability**: Each command is small and focused

## Directory Structure

```
kb_search/
├── cli.py                 # Main entry point (slim, ~40 lines)
└── commands/              # Auto-discovered command modules
    ├── __init__.py        # Command discovery mechanism
    ├── search.py          # Search command
    ├── list.py            # List knowledge bases
    ├── index.py           # Build index
    ├── add.py             # Add knowledge base
    ├── remove.py          # Remove knowledge base
    ├── enable.py          # Enable knowledge base
    ├── disable.py         # Disable knowledge base
    └── status.py          # Show status (example)
```

## How It Works

### 1. Command Discovery (`commands/__init__.py`)

The `discover_commands()` function automatically:
- Scans the `commands/` directory for `.py` files
- Imports each module
- Calls the `register()` function if present
- Registers the command with the Click group

### 2. Main CLI (`cli.py`)

The main CLI file is now minimal (~40 lines):
- Defines the Click group
- Calls `discover_commands()` to register all commands
- Re-exports command functions for backward compatibility

## How to Add a New Command

### Step 1: Create the Command File

Create a new Python file in `commands/` directory, e.g., `commands/mycommand.py`:

```python
"""My command for kb_search CLI."""

import click

@click.command()
@click.argument("name", required=True)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def mycommand(name: str, verbose: bool):
    """My command description

    Usage: winwin-cli kb-search mycommand NAME
    """
    if verbose:
        click.echo(f"Running mycommand for {name} in verbose mode")
    else:
        click.echo(f"Running mycommand for {name}")

def register(group: click.Group):
    """Register this command with the Click group."""
    group.add_command(mycommand)

__all__ = ["mycommand"]
```

### Step 2: That's It!

The command is now automatically available:

```bash
winwin-cli kb-search --help          # Command appears in list
winwin-cli kb-search mycommand test  # Run the command
```

### Step 3 (Optional): Update Exports

If you want the command to be importable, add it to `cli.py`:

```python
from winwin_cli.kb_search.commands.mycommand import mycommand
```

And to `__init__.py`:

```python
from winwin_cli.kb_search.cli import kb_search, ..., mycommand
```

## Command Template

Use this template for new commands:

```python
"""Command description for kb_search CLI."""

import sys
from typing import Optional

import click

@click.command()
@click.argument("required_arg", required=True)
@click.option(
    "--optional",
    "-o",
    help="Optional parameter",
)
@click.option(
    "--flag",
    "-f",
    is_flag=True,
    help="Boolean flag",
)
def command_name(required_arg: str, optional: Optional[str], flag: bool):
    """Command help text

    Usage: winwin-cli kb-search command-name ARG
    """
    try:
        # Your command logic here
        click.echo(f"Processing {required_arg}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def register(group: click.Group):
    """Register this command with the Click group."""
    group.add_command(command_name)


__all__ = ["command_name"]
```

## Example: The `status` Command

The `status.py` command demonstrates this architecture:
- Shows statistics about all knowledge bases
- Displays document counts
- Supports both human-readable and JSON output
- Was added without modifying any existing files

## Testing

Commands can be tested independently:

```python
# tests/test_mycommand.py
from click.testing import CliRunner
from winwin_cli.kb_search.commands.mycommand import mycommand

def test_mycommand_basic():
    runner = CliRunner()
    result = runner.invoke(mycommand, ["test"])
    assert result.exit_code == 0
    assert "test" in result.output
```

## Key Principles

1. **One command per file**: Each file contains a single command
2. **Register function**: Must have a `register(group)` function
3. **Module-level command**: Define the command at module level (not nested)
4. **Error handling**: Use try/except and exit with proper error codes
5. **Help text**: Provide clear usage examples in docstrings
6. **JSON output**: Support JSON format for AI/automation use cases

## Migration from Old Architecture

Before: All commands in one 300+ line `cli.py` file
After: 8 modular command files + 40 line `cli.py`

Benefits achieved:
- ✅ Each command is independently testable
- ✅ Adding commands requires zero changes to existing code
- ✅ Commands are easier to understand and maintain
- ✅ All existing tests pass without modification
- ✅ Full backward compatibility maintained

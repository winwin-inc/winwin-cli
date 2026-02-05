"""Commands module for kb_search CLI.

This module uses a plugin-based architecture where each command is a separate file.
New commands can be added by simply creating a new .py file in this directory
with a register() function that registers the command with the Click group.

Example command file structure:
    # commands/mycommand.py
    import click

    def register(group: click.Group):
        @group.command()
        @click.argument("name")
        def mycommand(name: str):
            '''My command description'''
            click.echo(f"Hello {name}")

The command will be automatically discovered and registered.
"""

import importlib
import importlib.util
import os
from pathlib import Path
from typing import List

import click


def discover_commands(group: click.Group) -> List[str]:
    """Discover and register all command modules in this directory.

    Args:
        group: The Click group to register commands with

    Returns:
        List of discovered command names
    """
    commands_dir = Path(__file__).parent
    discovered = []

    # Iterate through all Python files in this directory
    for filepath in commands_dir.glob("*.py"):
        # Skip __init__.py and private modules
        if filepath.name.startswith("_"):
            continue

        module_name = filepath.stem

        try:
            # Import the module dynamically
            spec = importlib.util.spec_from_file_location(
                f"winwin_cli.kb_search.commands.{module_name}",
                filepath
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Call the register function if it exists
                if hasattr(module, "register"):
                    module.register(group)
                    discovered.append(module_name)
        except Exception as e:
            # Log error but don't fail - allows other commands to load
            import warnings
            warnings.warn(
                f"Failed to load command {module_name}: {e}",
                RuntimeWarning
            )

    return discovered

"""
Hook execution support. Hooks are scripts placed in the hooks_directory
configured in .letsdo.yaml. Each executable file in that directory is called
with two arguments: the event name ("start" or "stop") and the task description.
"""
import os
import subprocess
from log import LOGGER
from configuration import get_hooks_directory


def run_hooks(event: str, task_description: str) -> None:
    """Run all executable hook scripts in the configured hooks directory."""
    hooks_dir = get_hooks_directory()
    if not hooks_dir:
        return

    if not os.path.isdir(hooks_dir):
        LOGGER.warning(f"hooks_directory '{hooks_dir}' does not exist or is not a directory")
        return

    for entry in sorted(os.listdir(hooks_dir)):
        script_path = os.path.join(hooks_dir, entry)
        if os.path.isfile(script_path) and os.access(script_path, os.X_OK):
            try:
                subprocess.run([script_path, event, task_description], check=False)
            except Exception as exc:
                LOGGER.warning(f"hook '{script_path}' failed: {exc}")

"""The run guide (eval/README.md) lists every command the evaluation modules offer.

The owner asked for a guide that stays current rather than one that drifts. Each module's
"Usage" block is the source of truth: every ``python -m <module> [<command>]`` written there
must appear in the guide.
"""

import re
from pathlib import Path

MODULES = [*Path("eval").glob("*.py"), Path("reuse/rare.py"), Path("classic/corpus_run.py")]
GUIDE = Path("eval/README.md")
COMMAND = re.compile(r"python -m ([a-z_.]+)(?: ([a-z][a-z-]*))?")


def test_every_usage_command_is_in_the_guide() -> None:
    guide = GUIDE.read_text()
    missing = []
    for path in MODULES:
        text = path.read_text()
        doc = text.split('"""', 2)[1] if text.count('"""') >= 2 else ""
        if "Usage::" not in doc:
            continue
        for module, cmd in COMMAND.findall(doc.split("Usage::", 1)[1]):
            entry = f"python -m {module}" + (f" {cmd}" if cmd else "")
            if entry not in guide:
                missing.append(f"{entry} ({path})")
    assert not missing, f"commands missing from {GUIDE}: {missing}"

"""Application entrypoint for StegoGen."""

import sys
from stegogen.gui.app import launch_gui


def main() -> int:
    """Bootstrap entrypoint launching the desktop GUI."""
    launch_gui()
    return 0


if __name__ == "__main__":
    sys.exit(main())

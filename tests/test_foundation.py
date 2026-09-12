"""Foundation test to verify imports, versioning, and execution."""

import stegogen
from stegogen.main import main


def test_package_metadata():
    """Verify package version is loaded."""
    assert stegogen.__version__ == "0.1.0"


def test_main_entrypoint(capsys):
    """Verify bootstrap function executes cleanly."""
    exit_code = main()
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "StegoGen v0.1.0" in captured.out

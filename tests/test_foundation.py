"""Foundation test to verify imports, versioning, and execution."""

import stegogen
from stegogen.main import main


def test_package_metadata():
    """Verify package version is loaded."""
    assert stegogen.__version__ == "0.1.0"


def test_main_callable():
    """Verify main entrypoint is defined and callable."""
    assert callable(main)

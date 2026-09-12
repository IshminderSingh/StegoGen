"""Unit tests verifying Tkinter GUI instantiation."""

import pytest
import tkinter as tk
from stegogen.gui.app import StegoGenApp


def test_gui_instantiation():
    """Verify StegoGenApp initializes widgets without error."""
    try:
        app = StegoGenApp()
        assert app.title() == "StegoGen -- Secure Image Steganography Generator"
        assert app.notebook is not None
        app.destroy()
    except tk.TclError:
        # Gracefully handle headless CI test environments lacking a display server
        pytest.skip("Skipping GUI test in headless environment.")

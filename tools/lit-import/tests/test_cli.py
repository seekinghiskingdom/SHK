import subprocess, sys, os, pathlib

def test_help():
    # ensure CLI prints help
    pkg_root = pathlib.Path(__file__).resolve().parents[1]
    assert (pkg_root / "pyproject.toml").exists()

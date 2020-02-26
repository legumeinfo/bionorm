# -*- coding: utf-8 -*-
# standard library imports
import contextlib
import os
from pathlib import Path

# third-party imports
import pytest
import sh


@contextlib.contextmanager
def working_directory(path):
    """Change working directory in context."""
    prev_cwd = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_cwd)


def test_global_help(tmp_path):
    print("testing global help")
    with working_directory(tmp_path):
        try:
            output = sh.bionorm(["--help"])
        except sh.ErrorReturnCode as e:
            print(e)
            pytest.fail(e)
        print(output)
        assert "Usage:" in output
        assert "Options:" in output
        assert "Commands:" in output


def test_version(tmp_path):
    print("testing version")
    with working_directory(tmp_path):
        try:
            output = sh.bionorm(["--version"])
        except sh.ErrorReturnCode as e:
            print(e)
            pytest.fail(e)
        print(output)
        assert "version" in output


def test_show_context_dict(tmp_path):
    print("testing command show-context-dict")
    with working_directory(tmp_path):
        try:
            output = sh.bionorm(["show-context-dict"])
        except sh.ErrorReturnCode as e:
            print(e)
            pytest.fail(e)
        print(output)


def test_test_logging(tmp_path):
    print("testing command test_logging")
    with working_directory(tmp_path):
        try:
            output = sh.bionorm(["test-logging"])
        except sh.ErrorReturnCode as e:
            print(e)
            pytest.fail(e)
        print(output)
        loglist = list((Path.cwd() / "logs").glob("*"))
        print("directory:", loglist)
        assert len(loglist) is 1

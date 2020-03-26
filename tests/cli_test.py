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


@pytest.mark.dependency(name="cli")
def test_cli(tmp_path):
    print("testing basic cli function")
    with working_directory(tmp_path):
        try:
            output = sh.bionorm()
        except sh.ErrorReturnCode as e:
            print(e)
            pytest.fail(e)
        print(output)
        assert "Usage:" in output
        assert "Options:" in output
        assert "Commands:" in output


@pytest.mark.dependency(name="version")
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


@pytest.mark.dependency(name="context")
def test_show_context_dict(tmp_path):
    print("testing context dictionary")
    with working_directory(tmp_path):
        try:
            output = sh.bionorm(["show-context-dict"])
        except sh.ErrorReturnCode as e:
            print(e)
            pytest.fail(e)
        print(output)


@pytest.mark.dependency(name="logging")
def test_logging(tmp_path):
    print("testing logging")
    with working_directory(tmp_path):
        try:
            output = sh.bionorm(["test-logging"])
        except sh.ErrorReturnCode as e:
            print(e)
            pytest.fail(e)
        print(output)
        loglist = list((Path.cwd() / "logs").glob("*"))
        assert len(loglist) is 1

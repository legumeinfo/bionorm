# -*- coding: utf-8 -*-
"""
bionorm -- normalize and verity genomic data files
"""

# This file makes it easier for developers to test in-place via the command
# python3 -m bionorm
# from the directory above this one.

# module imports
from .__init__ import cli

if __name__ == "__main__":
    cli(auto_envvar_prefix="BIONORM")

#!/usr/bin/env python
# -*- coding: utf-8 -*-

# standard library imports
import json as jsonlib
import sys
from pathlib import Path

# third-party imports
import click

# module imports
from . import cli
from .common import DataStorePath


@cli.command()
@click.option("--json", help="Write JSON to stdout.", is_flag=True, default=False)
@click.option("--pathonly", help="Write only path to output.", is_flag=True, default=False)
@click.option("--invalid", help="Write only invalid node info.", is_flag=True, default=False)
@click.option("--unrecognized", help="Write only unrecognized node info.", is_flag=True, default=False)
@click.option("--recurse", help="Recursively visit all files.", is_flag=True, default=False)
@click.argument("nodelist", nargs=-1)
def node_attributes(nodelist, json, invalid, pathonly, unrecognized, recurse):
    """Print attributes of nodes in data store.

    \b
    Example:
        bionorm node-attributes . # attributes of current directory
        bionorm node-attributes Medicago_truncatula/ # organism directory
        bionorm node-attributes  Medicago_truncatula/jemalong_A17.gnm5.FAKE/ # genome directory
        bionorm node-attributes Medicago_truncatula/jemalong_A17.gnm5.ann1.FAKE/ # annotation directory

    """
    n_invalid = 0
    if nodelist == ():  # empty list gets CWD
        nodelist = ["."]
    if recurse:
        filelist = []
        for node in nodelist:
            filelist += [f for f in Path(node).rglob("*") if f.is_file()]
        nodelist = filelist
    for node in nodelist:
        node = DataStorePath(node)
        if node.data_store_attributes.invalid_key is not None:
            n_invalid += 1
        else:
            if invalid:
                continue
        if unrecognized and not node.data_store_attributes.file_type == "unrecognized":
            continue
        if json:
            print(jsonlib.dumps(node.data_store_attributes))
        elif pathonly:
            print(node)
        else:
            print(node.data_store_attributes.describe(node), end="")
            print(node.data_store_attributes, end="")
    if n_invalid:
        print(f"ERROR--{n_invalid} invalid nodes were found.", file=sys.stderr)

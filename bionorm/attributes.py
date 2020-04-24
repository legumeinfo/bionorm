#!/usr/bin/env python
# -*- coding: utf-8 -*-

# standard library imports
import json as jsonlib
import sys
from pathlib import Path

# third-party imports
import click
import pandas as pd

# module imports
from . import cli
from .common import DataStorePath


@cli.command()
@click.option("-j", "--json", help="Output JSON.", is_flag=True, default=False)
@click.option("-l", "--long", help="Output detailed path data store info.", is_flag=True, default=False)
@click.option("-t", "--tsv", help="Output tsv.", is_flag=True, default=False)
@click.option("-d", "--directory", help="Filter only directory info.", is_flag=True, default=False)
@click.option("-f", "--files", help="Filter only info info.", is_flag=True, default=False)
@click.option("-u", "--unrecognized", help="Filter only unrecognized nodes.", is_flag=True, default=False)
@click.option("-i", "--invalid", help="Filter only invalid node info.", is_flag=True, default=False)
@click.option("-r", "--recurse", help="Recursively visit all nodes.", is_flag=True, default=False)
@click.argument("nodelist", nargs=-1)
def ls(nodelist, json, invalid, long, unrecognized, recurse, tsv, directory, files):
    """Print attributes of nodes in data store.

    \b
    Example:
        bionorm node-attributes . # attributes of current directory
        bionorm node-attributes Medicago_truncatula/ # organism directory
        bionorm node-attributes  Medicago_truncatula/jemalong_A17.gnm5.FAKE/ # genome directory
        bionorm node-attributes Medicago_truncatula/jemalong_A17.gnm5.ann1.FAKE/ # annotation directory

    """
    n_invalid = 0
    if nodelist == ():  # empty nodelist
        if directory:
            nodelist = [Path(".")]
        else:
            nodelist = [p for p in Path(".").glob("*")]
    if recurse:
        filelist = []
        for node in nodelist:
            filelist += [f for f in Path(node).rglob("*") if f.is_file()]
        nodelist = filelist
    att_dict_list = []
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
        elif long:
            print(node.data_store_attributes.describe(node), end="")
            print(node.data_store_attributes, end="")
        elif tsv:
            att_dict_list.append(dict(node.data_store_attributes))
        else:
            print(node)

    if tsv:
        att_frame = pd.DataFrame(att_dict_list)
        tsv_filename = "bionorm_attributes.tsv"
        att_frame.to_csv(tsv_filename, sep="\t")
        print(f"{len(att_frame)} attribute records written to {tsv_filename}")
    if n_invalid:
        print(f"ERROR--{n_invalid} invalid nodes were found.", file=sys.stderr)

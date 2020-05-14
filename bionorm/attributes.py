#!/usr/bin/env python
# -*- coding: utf-8 -*-

# standard library imports
import json as jsonlib

# first-party imports
import click
import pandas as pd
from ansimarkup import ansiprint
from loguru import logger

# module imports
from . import cli
from . import click_loguru
from .common import COLLECTION_ATT_FILENAME
from .common import CollectionPath
from .common import args_to_pathlist

# global constants
INVALID_COLOR = "red"
UNRECOGNIZED_COLOR = "yellow"


@cli.command()
@click_loguru.init_logger(logfile=False)
@click.option("-j", "--json", help="Output JSON.", is_flag=True, default=False)
@click.option(
    "-c",
    "--nocolor",
    help="Don't colorize output",
    is_flag=True,
    default=False,
)
@click.option(
    "-l",
    "--long",
    help="Output detailed path data store info.",
    is_flag=True,
    default=False,
)
@click.option("-t", "--tsv", help="Output tsv.", is_flag=True, default=False)
@click.option(
    "-d",
    "--directory",
    help="Filter only directory info.",
    is_flag=True,
    default=False,
)
@click.option(
    "-u",
    "--unrecognized",
    help="Filter only unrecognized nodes.",
    is_flag=True,
    default=False,
)
@click.option(
    "-i",
    "--invalid",
    help="Filter only invalid node info.",
    is_flag=True,
    default=False,
)
@click.option(
    "-r",
    "--recurse",
    help="Recursively visit all nodes.",
    is_flag=True,
    default=False,
)
@click.argument("nodelist", nargs=-1)
def ls(
    nodelist,
    json,
    invalid,
    long,
    unrecognized,
    recurse,
    tsv,
    directory,
    nocolor,
):
    """Print attributes of nodes in data store.

    \b
    Example:
        bionorm node-attributes . # attributes of current directory
        bionorm node-attributes Medicago_truncatula/ # organism directory
        bionorm node-attributes  Medicago_truncatula/jemalong_A17.gnm5.FAKE/ # genome directory
        bionorm node-attributes Medicago_truncatula/jemalong_A17.gnm5.ann1.FAKE/ # annotation directory

    """
    n_invalid = 0
    n_unrecognized = 0
    att_dict_list = []
    for node in args_to_pathlist(nodelist, directory, recurse):
        node = CollectionPath(node)
        if node.collection_attributes.invalid_key is not None:
            node_is_invalid = True
            n_invalid += 1
        else:
            node_is_invalid = False
            if invalid:
                continue
        if node.collection_attributes.file_type == "unrecognized":
            node_is_unrecognized = True
            n_unrecognized += 1
        else:
            node_is_unrecognized = False
            if unrecognized:
                continue
        if json:
            print(jsonlib.dumps(node.collection_attributes))
        elif long:
            print(node.collection_attributes.describe(node), end="")
            print(node.collection_attributes, end="")
        elif tsv:
            att_dict_list.append(dict(node.collection_attributes))
        else:
            if nocolor:
                print(node)
            elif node_is_invalid:
                ansiprint(f"<{INVALID_COLOR}>{node}</{INVALID_COLOR}>")
            elif node_is_unrecognized:
                ansiprint(
                    f"<{UNRECOGNIZED_COLOR}>{node}</{UNRECOGNIZED_COLOR}>"
                )
            else:
                print(node)
    if tsv:
        att_frame = pd.DataFrame(att_dict_list)
        att_frame.to_csv(COLLECTION_ATT_FILENAME, sep="\t")
        logger.info(
            f"{len(att_frame)} attribute records written to"
            f" {COLLECTION_ATT_FILENAME}"
        )
    if n_unrecognized:
        logger.warning(f"{n_unrecognized} unrecognized files were found.")
    if n_invalid:
        logger.error(f"{n_invalid} invalid nodes were found.")

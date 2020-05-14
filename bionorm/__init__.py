# -*- coding: utf-8 -*-
# standard library imports
import locale
import warnings
from pkg_resources import iter_entry_points

# first-party imports
import click
from click_loguru import ClickLoguru
from click_plugins import with_plugins
from loguru import logger

# module imports
from .__version__ import __version__
from .common import COLLECTION_HOME
from .common import COLLECTION_TITLE
from .common import NAME

# global constants
LOG_FILE_RETENTION = 3

# set locale so grouping works
for localename in ["en_US", "en_US.utf8", "English_United_States"]:
    try:
        locale.setlocale(locale.LC_ALL, localename)
        break
    except locale.Error:
        continue

# set up logging
click_loguru = ClickLoguru(
    NAME,
    __version__,
    retention=LOG_FILE_RETENTION,
    log_dir_parent=COLLECTION_HOME,
)
if COLLECTION_TITLE is None:
    epilog = "Not in a repository."
else:
    epilog = f'Currently in "{COLLECTION_TITLE}" collection.'
# create CLI
@with_plugins(iter_entry_points(NAME + ".cli_plugins"))
@click_loguru.logging_options
@click.group(epilog=epilog)
@click_loguru.stash_subcommand()
@click.option(
    "-e",
    "--warnings_as_errors",
    is_flag=True,
    show_default=True,
    default=False,
    help="Treat warnings as fatal.",
)
@click.version_option(version=__version__, prog_name=NAME)
def cli(warnings_as_errors, **kwargs):
    """bionorm -- normalize, verify, and select genomic data.

    For more information, see the homepage at https://github.com/legumeinfo/bionorm

    Originally written by Connor Cameron <ctc@ncgr.org>.
    Maintained by Joel Berendzen <joelb@ncgr.org>,
    Copyright (C) 2020. National Center for Genome Resources. All rights reserved.
    License: BSD-3-Clause
    """
    if warnings_as_errors:
        logger.warn(
            "Runtime warnings (e.g., from pandas) will cause exceptions"
        )
        warnings.filterwarnings("error")


# import CLI functions after cli is defined.
from .consistency import consistency  # isort:skip
from .prefix import prefix_fasta  # isort:skip
from .prefix import prefix_gff  # isort:skip
from .extract_fasta import extract_fasta  # isort:skip
from .installer import install  # isort:skip
from .index import index_fasta  # isort:skip
from .index import index_gff  # isort:skip
from .generate_readme import generate_readme  # isort:skip
from .attributes import ls  # isort:skip
from .metadata import init_collection  # isort:skip
from .metadata import show_collection  # isort:skip
from .metadata import write_metadata  # isort:skip

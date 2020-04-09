# -*- coding: utf-8 -*-
"""bionorm -- normalize and validate genomic data files.

This tool is used to ingest data into the Legume Federation Data Store
(https://www.legumefederation.org/en/data-store/) and is useful anytime
genomes must be formatted and checked for consistency.
"""

# standard library imports
import warnings
from pkg_resources import iter_entry_points

# third-party imports
import click
from click_plugins import with_plugins

# module imports
from .cli import Logging_CLI_Builder
from .common import PROGRAM_NAME
from .common import logger

# global constants
DEFAULT_FIRST_N = 0


# define parser options
parser_options = [
    {
        "args": ("--progress",),
        "kwargs": {"is_flag": True, "show_default": True, "default": False, "help": "Show a progress bar."},
    },
    {"args": ("--first_n",), "kwargs": {"default": 0, help: "Process only this many records. [default: all]"}},
    {
        "args": ("--warnings_as_errors", "-e"),
        "kwargs": {"is_flag": True, "show_default": True, "default": False, "help": "Warnings cause exceptions."},
    },
]


def bionorm_check(warnings_as_errors=False, **others):
    """CLI check function, parameters must be keyworded."""
    if warnings_as_errors:
        logger.warn("Runtime warnings (e.g., from pandas) will cause exceptions")
        warnings.filterwarnings("error")


# define the CLI
cli_builder = Logging_CLI_Builder(PROGRAM_NAME, logger, global_options_list=parser_options)

# create CLI
@with_plugins(iter_entry_points(PROGRAM_NAME + ".cli_plugins"))
@click.group(epilog=cli_builder.author + " <" + cli_builder.email + ">.  " + cli_builder.copyright)
@click.option("-v", "--verbose", is_flag=True, show_default=True, default=False, help="Log debugging info to stderr.")
@click.option("-q", "--quiet", is_flag=True, show_default=True, default=False, help="Suppress logging to stderr.")
@click.option("--log/--no_log", is_flag=True, show_default=True, default=True, help="Log to file.")
@click.option("--progress", is_flag=True, show_default=True, default=False, help="Show a progress bar.")
@click.option("--first_n", default=DEFAULT_FIRST_N, help="Process only this many records. [default: all]")
@click.option(
    "--warnings_as_errors", "-e", is_flag=True, show_default=True, default=False, help="Warnings cause exceptions."
)
@click.version_option(version=cli_builder.version, prog_name=PROGRAM_NAME)
@cli_builder.init_dual_logger()
@cli_builder.init_user_context_obj(extra_args=["progress", "first_n"])
def cli(verbose, quiet, log, **kwargs):
    """Bionorm -- normalize and verify genomic data files.

    If COMMAND is present, and --no_log was not invoked,
    a log file named bionorm-COMMAND.log
    will be written in the ./logs/ directory.
    """
    bionorm_check(**kwargs)


cli_builder.set_cli_func(cli)

# Define some cli-related commands
cli_builder.test_log_func()
cli_builder.show_context_func()

# import other CLI functions
from .prefix import prefix_fasta  # isort:skip
from .prefix import prefix_gff  # isort:skip
from .extract_fasta import extract_fasta  # isort:skip
from .installer import install  # isort:skip

# -*- coding: utf-8 -*-
'''
bionorm -- normalize and validate genomic data files.

This tool is used to ingest data into the Legume Federation Data Store
(https://www.legumefederation.org/en/data-store/) and is useful anytime
genomes must be formatted and checked for consistency.
'''

# standard library imports
import functools
import warnings
import logging
import sys
from datetime import datetime
from pathlib import Path
from pkg_resources import iter_entry_points
# third-party imports
import click
from click_plugins import with_plugins


# module defs
from .common import get_user_context_obj, logger, config_obj,\
    DEFAULT_FILE_LOGLEVEL, DEFAULT_STDERR_LOGLEVEL, AUTHOR, EMAIL, \
    COPYRIGHT, DEFAULT_FIRST_N, VERSION, PROGRAM_NAME, STARTTIME

__version__ = '0.1.0'


# private context function
_ctx = click.get_current_context


class CleanInfoFormatter(logging.Formatter):
    def __init__(self, fmt='%(levelname)s: %(message)s'):
        logging.Formatter.__init__(self, fmt)

    def format(self, record):
        if record.levelno == logging.INFO:
            return record.getMessage()
        return logging.Formatter.format(self, record)


def init_dual_logger(file_log_level=DEFAULT_FILE_LOGLEVEL,
                     stderr_log_level=DEFAULT_STDERR_LOGLEVEL):
    '''Log to stderr and to a log file at different levels
    '''

    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            global logger
            # find out the verbose/quiet level
            if _ctx().params['verbose']:
                _log_level = logging.DEBUG
            elif _ctx().params['quiet']:
                _log_level = logging.ERROR
            else:
                _log_level = stderr_log_level
            logger.setLevel(file_log_level)
            stderrHandler = logging.StreamHandler(sys.stderr)
            stderrFormatter = CleanInfoFormatter()
            stderrHandler.setFormatter(stderrFormatter)
            stderrHandler.setLevel(_log_level)
            logger.addHandler(stderrHandler)

            if not _ctx().params['no_log']:  # start a log file
                # If a subcommand was used, log to a file in the
                # logs/ subdirectory of the current working directory
                #  with the subcommand in the file name.
                subcommand = _ctx().invoked_subcommand
                if subcommand is not None:
                    logfile_name = PROGRAM_NAME + '-' + subcommand + '.log'
                    logfile_path = Path('./logs/' + logfile_name)
                    if not logfile_path.parent.is_dir():  # create logs/ dir
                        try:
                            logfile_path.parent.mkdir(mode=0o755, parents=True)
                        except OSError:
                            logger.error(
                                'Unable to create logfile directory "%s"',
                                logfile_path.parent)
                            raise OSError
                    else:
                        if logfile_path.exists():
                            try:
                                logfile_path.unlink()
                            except OSError:
                                logger.error(
                                    'Unable to remove existing logfile "%s"', logfile_path)
                                raise OSError
                    logfileHandler = logging.FileHandler(str(logfile_path))
                    logfileFormatter = logging.Formatter(
                        '%(levelname)s: %(message)s')
                    logfileHandler.setFormatter(logfileFormatter)
                    logfileHandler.setLevel(file_log_level)
                    logger.addHandler(logfileHandler)
            logger.debug('Command line: "%s"', ' '.join(sys.argv))
            logger.debug('%s version %s', PROGRAM_NAME, VERSION)
            logger.debug('Run started at %s', str(STARTTIME)[:-7])

            return f(*args, **kwargs)

        return wrapper

    return decorator


def init_user_context_obj(initial_obj=None):
    '''Put info from global options into user context dictionary
    '''

    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            global config_obj
            if initial_obj is None:
                _ctx().obj = {}
            else:
                _ctx().obj = initial_obj
            ctx_dict = _ctx().obj
            if _ctx().params['verbose']:
                ctx_dict['logLevel'] = 'verbose'
            elif _ctx().params['quiet']:
                ctx_dict['logLevel'] = 'quiet'
            else:
                ctx_dict['logLevel'] = 'default'
            for key in ['progress', 'first_n']:
                ctx_dict[key] = _ctx().params[key]
            # selected simplicity object
            try:
                simplicity_object_label = config_obj.config_dict['simplicity_object_label']
            except KeyError:
                simplicity_object_label = None
            if simplicity_object_label is not None:
                for obj in ctx_dict['simplicity_objects']:
                    if obj.label == simplicity_object_label:
                        ctx_dict['simplicity_object'] = obj
            else:
                try:
                    ctx_dict['simplicity_object'] = ctx_dict['simplicity_objects'][0]
                except IndexError:
                    ctx_dict['simplicity_object'] = None
            return f(*args, **kwargs)

        return wrapper

    return decorator


def log_elapsed_time():
    '''Log the elapsed time
    '''

    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            returnobj = f(*args, **kwargs)
            logger.debug(
                'Elapsed time is %s', str(datetime.now() - STARTTIME)[:-7])
            return returnobj

        return wrapper

    return decorator


@with_plugins(iter_entry_points('bionorm.cli_plugins'))
@click.group(epilog=AUTHOR + ' <' + EMAIL + '>.  ' + COPYRIGHT)
@click.option('--warnings_as_errors', '-e', is_flag=True, show_default=True,
              default=False, help='Warnings cause exceptions.')
@click.option('-v', '--verbose', is_flag=True, show_default=True,
              default=False, help='Log debugging info to stderr.')
@click.option('-q', '--quiet', is_flag=True, show_default=True,
              default=False, help='Suppress logging to stderr.')
@click.option('--no_log', is_flag=True, show_default=True,
              default=False, help='Suppress logging to file.')
@click.option('--progress', is_flag=True, show_default=True,
              default=False, help='Show a progress bar, if supported.')
@click.option('--first_n', default=DEFAULT_FIRST_N,
              help='Process only this many records. [default: all]')
@click.version_option(version=VERSION, prog_name=PROGRAM_NAME)
@init_dual_logger()
@init_user_context_obj()
def cli(warnings_as_errors, verbose, quiet,
        progress, first_n, no_log):
    """bionorm -- normalize and verify genomic data files

    If COMMAND is present, and --no_log was not invoked,
    a log file named bionorm-COMMAND.log
    will be written in the ./logs/ directory.
    """
    if warnings_as_errors:
        logger.debug(
            'Runtime warnings (e.g., from pandas) will cause exceptions')
        warnings.filterwarnings('error')


@cli.command()
@log_elapsed_time()
def test_logging():
    '''Log at different severity levels.

        Example:
            bionorm test_logging
    '''
    logger.debug('debug message')
    logger.info('info message')
    logger.warning('warning message')
    logger.error('error message')


@cli.command()
def show_context_object():
    '''Print the global context object.
    '''
    user_ctx = get_user_context_obj()
    logger.info('User context object')
    for key in user_ctx.keys():
        logger.info('   %s: %s', key, user_ctx[key])


# import other functions
from .config import show_config, init_config_file

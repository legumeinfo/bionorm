# -*- coding: utf-8 -*-
"""Define a cli with dual logging to stderr and file
"""

# standard library imports
import functools
import logging
import sys
from datetime import datetime
from pathlib import Path

# third-party imports
import click

try:
    from importlib.metadata import distribution  # python 3.8 and above
except ModuleNotFoundError:
    from importlib_metadata import distribution


# global constants
DEFAULT_FILE_LOGLEVEL = logging.DEBUG
DEFAULT_STDERR_LOGLEVEL = logging.INFO
STARTTIME = datetime.now()


class CleanInfoFormatter(logging.Formatter):
    """very clean logging formatter for terminal output
    """

    def __init__(self, fmt="%(levelname)s: %(message)s"):
        logging.Formatter.__init__(self, fmt)

    def format(self, record):
        if record.levelno == logging.INFO:
            return record.getMessage()
        return logging.Formatter.format(self, record)


def composed(self, *decs):
    def deco(f):
        for dec in reversed(decs):
            f = dec(f)
        return f

    return deco


def click_multi(func):
    return composed(
        click.option("--progress", is_flag=True, show_default=True, default=False, help="Show a progress bar.",)
        # click.option(*self.global_options_list[0]['args'],
        #             **self.global_options_list[0]['kwargs'])
    )(func)


class Logging_CLI_Builder(object):
    """creates a cli function
    """

    def __init__(self, name, logger, check_func=None, global_options_list=None):
        self.name = name
        self.logger = logger
        self.check_func = check_func
        self.global_options_list = global_options_list
        dist = distribution(name).metadata
        self.version = dist["Version"]
        self.author = dist["Author"]
        self.email = dist["Author-email"]
        self.maintainer = dist["Maintainer"]
        self.maintainer_email = dist["Maintainer-email"]
        self.home = dist["Home-page"]
        self.summary = dist["Summary"]
        self.licence = dist["License"]
        self.copyright = "Copyright (C) 2020. National Center for Genome Resources. All rights reserved."
        self.cli_func = None

    def set_cli_func(self, cli_func):
        self.cli_func = cli_func

    def _ctx(self):
        """private global context function"""
        return click.get_current_context

    def get_user_context_dict(self):
        """Returns the user context dictionary.
        """
        return self._ctx()().obj

    def init_user_context_obj(self, extra_args=None):
        """Decorator that puts global options into context dictionary
        """

        def decorator(f):
            @functools.wraps(f)
            def wrapper(*args, **kwargs):
                self._ctx()().obj = {}
                ctx_dict = self._ctx()().obj
                if self._ctx()().params["verbose"]:
                    ctx_dict["logLevel"] = "verbose"
                elif self._ctx()().params["quiet"]:
                    ctx_dict["logLevel"] = "quiet"
                else:
                    ctx_dict["logLevel"] = "default"
                for key in extra_args:
                    ctx_dict[key] = self._ctx()().params[key]
                return f(*args, **kwargs)

            return wrapper

        return decorator

    def init_dual_logger(
        self, file_log_level=DEFAULT_FILE_LOGLEVEL, stderr_log_level=DEFAULT_STDERR_LOGLEVEL,
    ):
        """Decorator to log to stderr and to logfile at different levels
            """

        def decorator(f):
            @functools.wraps(f)
            def wrapper(*args, **kwargs):
                # find the verbose/quiet levels from context
                if self._ctx()().params["verbose"]:
                    _log_level = logging.DEBUG
                elif self._ctx()().params["quiet"]:
                    _log_level = logging.ERROR
                else:
                    _log_level = stderr_log_level
                self.logger.setLevel(file_log_level)
                stderrHandler = logging.StreamHandler(sys.stderr)
                stderrFormatter = CleanInfoFormatter()
                stderrHandler.setFormatter(stderrFormatter)
                stderrHandler.setLevel(_log_level)
                self.logger.addHandler(stderrHandler)
                if self._ctx()().params["log"]:  # start a log file
                    # If a subcommand was used, log to a file in the
                    # logs/ subdirectory of the current working directory
                    #  with the subcommand in the file name.
                    subcommand = self._ctx()().invoked_subcommand
                    if subcommand is not None:
                        logfile_name = self.name + "-" + subcommand + ".log"
                        logfile_path = Path("./logs/" + logfile_name)
                        if not logfile_path.parent.is_dir():  # create logs/ dir
                            try:
                                logfile_path.parent.mkdir(mode=0o755, parents=True)
                            except OSError:
                                self.logger.error(
                                    'Unable to create logfile directory "%s"', logfile_path.parent,
                                )
                                raise OSError
                        else:
                            if logfile_path.exists():
                                try:
                                    logfile_path.unlink()
                                except OSError:
                                    self.logger.error(
                                        'Unable to remove existing logfile "%s"', logfile_path,
                                    )
                                    raise OSError
                        logfileHandler = logging.FileHandler(str(logfile_path))
                        logfileFormatter = logging.Formatter("%(levelname)s: %(message)s")
                        logfileHandler.setFormatter(logfileFormatter)
                        logfileHandler.setLevel(file_log_level)
                        self.logger.addHandler(logfileHandler)
                self.logger.debug('Command line: "%s"', " ".join(sys.argv))
                self.logger.debug("%s version %s", self.name, self.version)
                self.logger.debug("Run started at %s", str(STARTTIME)[:-7])
                return f(*args, **kwargs)

            return wrapper

        return decorator

    def log_elapsed_time(self):
        """Decorator to log the elapsed time for command
        """

        def decorator(f):
            @functools.wraps(f)
            def wrapper(*args, **kwargs):
                returnobj = f(*args, **kwargs)
                self.logger.debug("Elapsed time is %s", str(datetime.now() - STARTTIME)[:-7])
                return returnobj

            return wrapper

        return decorator

    def test_log_func(self):
        @self.cli_func.command()
        @self.log_elapsed_time()
        def test_logging():
            """Log at different severity levels.
            """
            self.logger.debug("debug message")
            self.logger.info("info message")
            self.logger.warning("warning message")
            self.logger.error("error message")

    def show_context_func(self):
        @self.cli_func.command()
        def show_context_dict():
            """Print the global context dictionary.
            """
            user_ctx = self.get_user_context_dict()
            self.logger.info("User context dictionary:")
            for key in user_ctx.keys():
                self.logger.info("   %s: %s", key, user_ctx[key])

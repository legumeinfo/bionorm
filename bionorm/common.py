# -*- coding: utf-8 -*-
"""Define global constants and common helper functions."""

# standard library imports
import locale
import logging

# third-party imports
import click

#
# global constants
#
PROGRAM_NAME = "bionorm"
CONFIG_FILE_ENVVAR = "BIONORM_CONFIG_FILE_PATH"
#
# global logger object
#
logger = logging.getLogger(PROGRAM_NAME)
#
# set locale so grouping works
#
for localename in ["en_US", "en_US.utf8", "English_United_States"]:
    try:
        locale.setlocale(locale.LC_ALL, localename)
        break
    except BaseException:
        continue

#
# helper functions used in multiple places
#
def get_user_context_obj():
    """Return user context, containing logging and configuration data.

    :return: User context object (dict)
    """
    return click.get_current_context().obj

# -*- coding: utf-8 -*-
'''Global constants and common helper functions.
'''
# standard library imports
import locale
import logging
import sys
from datetime import datetime
from itertools import chain
from pathlib import Path  # python 3.4 or later

# 3rd-party modules
import click

# package imports
from .version import version as VERSION

#
# global constants
#
PROGRAM_NAME = 'bionorm'
AUTHOR = 'Joel Berendzen'
EMAIL = 'joelb@ncgr.org'
COPYRIGHT = 'Copyright (C) 2020. National Center for Genome Resources. All rights reserved.'
PROJECT_HOME = 'https://github.com/ncgr/bionorm'
DOCS_HOME = 'https://bionorm.readthedocs.org/en/stable'

DEFAULT_FILE_LOGLEVEL = logging.DEBUG
DEFAULT_STDERR_LOGLEVEL = logging.INFO
DEFAULT_FIRST_N = 0  # only process this many records
STARTTIME = datetime.now()
CONFIG_FILE_ENVVAR = 'BIONORM_CONFIG_FILE_PATH'
#
# global logger object
#
logger = logging.getLogger(PROGRAM_NAME)
#
# set locale so grouping works
#
for localename in ['en_US', 'en_US.utf8', 'English_United_States']:
    try:
        locale.setlocale(locale.LC_ALL, localename)
        break
    except BaseException:
        continue

#
# helper functions used in multiple places
#
def get_user_context_obj():
    '''Returns the user context, containing logging and configuration data.

    :return: User context object (dict)
    '''
    return click.get_current_context().obj


def to_str(seq):
    '''Decode bytestring if necessary.

    :param seq: Input bytestring, string, or other sequence.
    :return: String.
    '''
    if isinstance(seq, bytes):
        value = seq.decode('utf-8')
    elif isinstance(seq, str):
        value = seq
    else:
        value = str(seq)
    return value


def to_bytes(seq):
    '''Encode or convert string if necessary.

    :param seq: Input string, bytestring, or other sequence.
    :return: Bytestring.
    '''
    if isinstance(seq, str):
        value = seq.encode('utf-8')
    elif isinstance(seq, bytes):
        value = seq
    else:
        value = bytes(seq)
    return value

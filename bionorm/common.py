# -*- coding: utf-8 -*-
'''Global constants and common helper functions.
'''
# standard library imports
import locale
import logging
import sys
from datetime import datetime
from pathlib import Path

# 3rd-party modules
import click

#
# global constants
#
PROGRAM_NAME = 'bionorm'
VERSION = "0.1.blah"

DEFAULT_FIRST_N = 0  # only process this many records

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
# Classes and instances of classes
#
class PersistentConfigurationObject(object):
    '''Defines a persistent configuration object

    Attributes:
        :config_dict: Dictionary of configuration parameters.
        :name: Configuration filename.
        :path: Configuration filepath (absolute).
    '''

    def __init__(self, config_dir=None, name='config.yaml'):
        '''Inits the configuration dictionary

        Reads a configuration file from a subdirectory of the
        current working directory.  If that file isn't found,
        then searches in the system-specific configuration directory.
        If that file isn't found either, creates a new file in the
        directory specified by the location parameter.
        '''
        self.name = name
        self._default_dict = {'version': VERSION,
                              'simplicity_object_label': None,
                              'plot_type': 'pdf',
                              'sets': [],
                              'summary': {'dir': None,
                                          'label': None},
                              }

        self._default_path = Path(
            (click.get_app_dir(PROGRAM_NAME) + '/' + self.name))
        self._cwd_path = Path('.' + '/.' + PROGRAM_NAME + '/' + self.name)
        if config_dir is not None:
            self.path = self._get_path_from_dir(config_dir)
        elif self._cwd_path.is_file():
            self.path = self._cwd_path
        else:
            self.path = self._default_path
        if not self.path.exists():
            self.config_dict = {}
            self.path = None
        else:
            with self.path.open('rt') as f:
                self.config_dict = yaml.safe_load(f)

    def _get_path_from_dir(self, dir):
        return Path(
            str(dir) +
            '/.' +
            PROGRAM_NAME +
            '/' +
            self.name).expanduser()

    def _update_config_dict(self):
        '''Update configuration dictionary if necessary
        :param config_dict: Configuration dictionary.
        :return: Updated configuration dictionary.
        '''
        try:
            if self.config_dict['version'] != VERSION:
                # Do whatever updates necessary, depending on version.
                # For now, nothing needs to be done.
                self.config_dict['version'] = VERSION
        except KeyError:
            logger.warning('Initializing config file "%s"',
                           self.path)
            self.config_dict = self._default_dict

    def write_config_dict(self, config_dict=None, dir=None):
        '''Writes a YAML configuration dictionary
        :param config_dict: Configuration dictionary
        :return: None
        '''
        if dir is None or dir is '':
            if self.path is None:
                self.path = self._default_path
        elif dir is '.':
            self.path = self._cwd_path
        else:
            self.path = self._get_path_from_dir(dir)

        if config_dict == {}:
            self.config_dict = self._default_dict
        elif config_dict is not None and config_dict != self.config_dict:
            self.config_dict = config_dict
            self._update_config_dict()

        if not self.path.parent.exists():
            # create parent directory
            logger.debug('Creating config file directory "%s"',
                         self.path.parent)
            try:
                self.path.parent.mkdir(parents=True)
            except OSError:
                logger.error('Unable to create parent directory "%s".',
                             self.path.parent)
                sys.exit(1)
        if not self.path.parent.is_dir():
            logger.error('Path "%s" exists, but is not a directory.',
                         self.path.parent)
            sys.exit(1)
        if not self.path.exists():
            logger.debug('Creating config file "%s"', self.path)
            try:
                self.path.touch()
            except OSError:
                logger.error('Path "%s" is not writable.', self.path)
                sys.exit(1)
        with self.path.open(mode='wt') as f:
            yaml.dump(self.config_dict, f)


config_obj = PersistentConfigurationObject()


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

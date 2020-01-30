# -*- coding: utf-8 -*-
'''Implements commands related to configuration parameters
'''
# standard library imports
import sys
# third-party imports
import click
# module imports
from . import cli
from .common import *

# private context function
_ctx = click.get_current_context

@cli.command()
def show_config():
    '''Print location and contents of config file.

        Example:
            bionorm -v show_config
    '''
    global config_obj
    if config_obj.config_dict == {}:
        logger.info('No configuration file was found.')
    else:
        logger.info('Configuration file path is "%s".', config_obj.path)
        for key in config_obj.config_dict.keys():
            logger.info('  %s: %s', key, config_obj.config_dict[key])


@cli.command()
@click.argument('plot_type', type=str, nargs=-1)
def set_plot_type(plot_type):
    '''Define label associated with a set.
    '''
    global config_obj
    plot_types = ['svg', 'jpg', 'ps', 'pdf', 'svgr', 'png', 'tiff', 'eps']
    if len(plot_type) == 0:
        logger.info('Supported plot types are:')
        for typename in plot_types:
            logger.info('   %s', typename)
    elif len(plot_type) > 1:
        logger.error('Only one argument for set_plot_type is allowed.')
        sys.exit(1)
    elif plot_type[0] not in plot_types:
        logger.error('Plot type "%s" is not defined.', plot_type[0])
        logger.info('Supported plot types are:')
        for typename in plot_types:
            logger.info('   %s', typename)
        sys.exit(1)
    else:
        config_obj.config_dict['plot_type'] = plot_type[0]
        logger.info('Plot type is now %s.', plot_type[0])
        config_obj.write_config_dict()


@cli.command()
@click.argument('dir', type=str, default='')
def init_config_file(dir):
    '''Initialize a configuration file.

    :param dir: Optional directory in which to initialize the file.
    If not present, the system-dependent default application directory
    will be used.  If this argument is '.', then the current working
    directory will be used.  This argument accepts tilde expansions.
    '''
    global config_obj
    config_obj.write_config_dict(dir=dir, config_dict={})

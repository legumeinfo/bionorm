#!/usr/bin/env python
# -*- coding: utf-8 -*-

# standard library imports
import os
import sys
from pathlib import Path
from loguru import logger

# first-party imports
import click
from ruamel.yaml import YAML

# module imports
from . import cli
from . import click_loguru


def read_yaml(template):
    '''Reads yaml file and checks for valid yaml'''
    yaml = YAML()
    target_yaml = yaml.load(open(template, 'rt'))
    return yaml, target_yaml


def create_readme(template, attributes):
    '''Writes target YAML file'''
    yaml, my_yaml = read_yaml(template)
    my_readme = '{}/README.{}.yaml'.format(attributes['target_dir'],
                                           attributes['key'])
    identifier = attributes['key']
    sci_name = '{} {}'.format(attributes['genus'].capitalize(), 
                                     attributes['species'].lower())
    sci_name_abr = attributes['gensp'].lower()
    genotype = attributes['infra_id']
    my_yaml['identifier'] = identifier  # set key
    my_yaml['genotype'] = genotype  # set infraspecific id
    my_yaml['scientific_name'] = sci_name  # Genus species
    my_yaml['scientific_name_abbrev'] = sci_name_abr  # gensp
    readme_handle = open(my_readme, 'w')
    yaml.dump(my_yaml, readme_handle)
    readme_handle.close()


@cli.command()
@click_loguru.init_logger()
@click.argument("target", nargs=1)
@click.argument("template", nargs=1)
def generate_readme(target, template):
    """Write context-appropriate templated README YAML file to target_dir.

    \b
    Example:
        bionorm generate-readme  Medicago_truncatula/jemalong_A17.gnm5.FAKE/ /my/readme/readme.yaml # genome directory
        bionorm generate_readme Medicago_truncatula/jemalong_A17.gnm5.ann1.FAKE/ /my/readme/readme.yaml # annotation directory

    """
    if not (target and template):
        logger.error('target and template arguments are required')
        sys.exit(1)
    target = os.path.abspath(target)  # get full path
    if not os.path.isdir(target):
        logger.error('target dmust be a directory')
        sys.exit(1)
    organism_dir = os.path.basename(os.path.dirname(target))
    target_dir = os.path.basename(target)
    organism_attributes = organism_dir.split('_')  # Genus_species
    target_attributes = target_dir.split('.')
    if len(organism_attributes) != 2:
        logger.error('Parent directory {} is not Genus_species'.format(organism_dir))
        sys.exit(1)
    if len(target_attributes) < 3:
        logger.error('Target directory {} is not delimited correctly'.format(target_dir))
        sys.exit(1)
    gensp = '{}{}'.format(organism_attributes[0][:3], organism_attributes[1][:2])  # abbreviation in yaml README file
    attributes = {'genus': organism_attributes[0],
                  'species': organism_attributes[1],
                  'gensp': gensp,
                  'key': target_attributes[-1],
                  'infra_id': target_attributes[0],
                  'target_dir': target}
    create_readme(template, attributes)  # write readme template

# -*- coding: utf-8 -*-
# standard library imports
import json
import os
import re
import sys
from glob import glob
from pathlib import Path

# third-party imports
import click
from sequencetools.tools.basic_fasta_stats import basic_fasta_stats

# module imports
from . import specification_checks
from .metrics import count_gff_features
from . import cli
from .common import logger

# global defs
DOMAIN = "https://legumeinfo.org/data/public"


class Detector:

    """Detect datastore file inconsistencies."""

    def __init__(self, target, **kwargs):
        """Check for check for gt"""
        self.options = kwargs
        self.checks = {}  # object that determines which checks are skipped
        self.checks["genome_main"] = kwargs.get("disable_genome_main", True)
        self.checks["gene_models_main"] = kwargs.get("disable_gene_models_main", True)
        self.checks["perform_gt"] = kwargs.get("disable_gt", True)
        self.checks["fasta_headers"] = kwargs.get("disable_fasta_headers", True)
        self.no_nodes = kwargs.get("no_nodes", False)
        self.canonical_types = [
            "genome_main",
            "protein_primaryTranscript",
            "protein",
            "gene_models_main",
            "ADDMORESTUFF",
        ]  # types for detector
        self.canonical_parents = {
            "genome_main": None,
            "gene_models_main": "genome_main",
            "protein_primaryTranscript": "gene_models_main",
            "protein": "gene_models_main",
        }
        self.rank = {"genome_main": 0, "gene_models_main": 1, "protein": 2, "protein_primaryTranscript": 2}
        self.output_prefix = kwargs.get("output_prefix", "./incongruencies")
        self.write_me = {}
        self.passed = {}  # dictionary of passing names
        self.target_objects = {}  # store all target pairings self.get_targets
        self.fasta_ids = {}
        self.reporting = {}
        self.node_data = {}  # nodes for DSCensor
        self.target = Path(target)
        self.target_readme = ""
        self.target_type = self.get_target_type()
        if self.target_type is None:  # target type returned False not recognized
            logger.error(f"Target type not recognized for {self.target}")
            sys.exit(1)
        logger.info("Target type looks like {}".format(self.target_type))
        self.get_targets()
        logger.info("Performing Checks for the Following:\n")
        for t in self.target_objects:  # for each object set validate
            logger.debug("{}".format(t))
            logger.debug("{}".format(self.target_objects[t]))
            logger.info("Parent {}:".format(t))
            count = 0
            set_primary = ""
            primary = False
            for c in self.target_objects[t]["children"]:
                logger.info("Child {}".format(c))
                if self.target_objects[t]["children"][c]["type"] == "protein_primaryTranscript":
                    primary = True
                if self.target_objects[t]["children"][c]["type"] == "protein":
                    count += 1
                    set_primary = c
            if count == 1 and not primary:
                self.target_objects[t]["children"][set_primary]["type"] = "protein_primaryTranscript"
                self.target_objects[t]["children"][set_primary]["node_data"][
                    "canonical_type"
                ] = "protein_primaryTranscript"
            if count > 1 and not primary:
                logger.error("Multiple protein files found for {} one must be renamed to primary".format(t))
                sys.exit(1)
        logger.info("Initialized Detector\n")

    def get_target_type(self):
        """Determine whether target is file, organism directory, or data directory.
        """
        if self.target.is_file():
            target_type = "file"
        elif len(self.target.name.split("_")) == 2 and len(self.target.name.split(".")) < 3:
            target_type = "organism_dir"  # will always be Genus_species
        elif len(self.target.name.split(".")) >= 3:  # standard naming minimum
            target_type = "data_dir"
        else:
            target_type = None
        return target_type

    def get_targets(self):
        """Gets and discovers target files relation to other files

           if the target is a directory, the program will discover

           all related files that can be checked
        """
        target_type = self.target_type
        if target_type == "file":  # starting with a file
            self.add_target_object()
            return
        elif target_type == "data_dir" or target_type == "organism_dir":
            self.get_all_files()  # works for both data and organism
            return

    def get_all_files(self):
        """Walk down filetree and recursively return all files.

           These will be checked using add_target_object
        """
        for root, directories, filenames in os.walk(self.target):
            for filename in filenames:  # we only care about the files
                my_target = root / filename
                logger.debug(f"Checking file {my_target}")
                self.target = my_target
                self.add_target_object()  # add target if canonical

    def get_target_file_type(self, target_file):
        """Determines if file is fasta, gff3, vcf, etc"""
        file_type = target_file.split(".")[-2].lower()
        if file_type == "fna" or file_type == "faa" or file_type == "fasta":
            file_type = "fasta"
        elif file_type == "gff" or file_type == "gff3":
            file_type = "gff3"
        else:  # add more
            return False
        return file_type

    def add_target_object(self):
        """Uses parent child logic to create a datastructure for objects"""
        target = self.target
        logger.debug(target)
        if not check_file(target):
            logger.error("Could not find file: {}".format(target))
            sys.exit(1)
        target_attributes = self.target.name.split(".")
        if len(target_attributes) < 3 or self.target.name[0] == "_":
            logger.debug("File {} does not seem to have attributes".format(target))
            return
        canonical_type = target_attributes[-3]  # check content type
        if canonical_type not in self.canonical_types:  # regject
            logger.debug("Type {} not recognized in {}.  Skipping".format(canonical_type, self.canonical_types))
            return
        organism_dir_path = os.path.dirname(os.path.dirname(target))  # org dir
        organism_dir = os.path.basename(os.path.dirname(os.path.dirname(target)))  # org dir
        target_dir = os.path.basename(os.path.dirname(target))
        genus = organism_dir.split("_")[0].lower()
        species = organism_dir.split("_")[1].lower()
        target_ref_type = self.canonical_parents[canonical_type]
        logger.debug("Getting target files reference if necessary...")
        file_type = self.get_target_file_type(self.target.name)
        file_url = "{}/{}/{}/{}".format(DOMAIN, organism_dir, target_dir, self.target.name)
        target_node_object = {
            "filename": self.target.name,
            "filetype": file_type,
            "canonical_type": canonical_type,
            "url": file_url,
            "counts": "",
            "genus": genus,
            "species": species,
            "origin": "LIS",
            "infraspecies": target_attributes[1],
            "derived_from": [],
            "child_of": [],
        }
        if len(target_attributes) > 7 and target_ref_type:  # check parent
            logger.debug("Target Derived from Some Reference Searching...")
            ref_glob = "{}/{}*/*{}.*.gz".format(organism_dir_path, ".".join(target_attributes[1:3]), target_ref_type)
            if self.rank[canonical_type] > 1:  # feature has a subtype
                ref_glob = "{}/{}*/*{}.*.gz".format(
                    organism_dir_path, ".".join(target_attributes[1:4]), target_ref_type
                )
            my_reference = self.get_reference(ref_glob)
            if my_reference not in self.target_objects:  # new parent
                parent_name = os.path.basename(my_reference)
                file_type = self.get_target_file_type(parent_name)
                organism_dir = os.path.basename(os.path.dirname(os.path.dirname(my_reference)))
                ref_dir = os.path.basename(os.path.dirname(my_reference))
                file_url = "{}/{}/{}/{}".format(DOMAIN, organism_dir, ref_dir, parent_name)
                ref_node_object = {
                    "filename": parent_name,
                    "filetype": file_type,
                    "canonical_type": target_ref_type,
                    "url": file_url,
                    "counts": "",
                    "genus": genus,
                    "species": species,
                    "origin": "LIS",
                    "infraspecies": target_attributes[1],
                    "derived_from": [],
                    "child_of": [],
                }
                target_node_object["child_of"].append(parent_name)
                target_node_object["derived_from"].append(parent_name)
                self.target_objects[my_reference] = {
                    "type": target_ref_type,
                    "node_data": ref_node_object,
                    "readme": "",
                    "children": {},
                }
                self.target_objects[my_reference]["children"][target] = {
                    "node_data": target_node_object,
                    "type": canonical_type,
                }
            else:  # the parent is already in the data structure add child
                if target not in self.target_objects[my_reference]["children"]:
                    parent_name = os.path.basename(my_reference)
                    target_node_object["child_of"].append(parent_name)
                    target_node_object["derived_from"].append(parent_name)
                    self.target_objects[my_reference]["children"][target] = {
                        "node_data": target_node_object,
                        "type": canonical_type,
                    }
        else:  # target is a reference
            if target_ref_type:
                logger.error("Reference was not found or file has <=7 fields")
                sys.exit(1)
            logger.debug("Target has no Parent, it is a Reference")
            if target not in self.target_objects:
                self.target_objects[target] = {"type": canonical_type, "node_data": target_node_object, "children": {}}

    def get_reference(self, glob_target):
        """Finds the FASTA reference for some prefix"""
        if len(glob(glob_target)) > 1:  # too many references....?
            logger.error("Multiple references found {}".format(glob_target))
            sys.exit(1)
        reference = glob(glob_target)
        if not reference:  # if the objects parent could not be found
            logger.error("Could not find ref glob: {}".format(glob_target))
            sys.exit(1)
        reference = glob(glob_target)[0]
        if not os.path.isfile(reference):  # if cannot find reference file
            logger.error("Could not find main target {}".format(reference))
            sys.exit(1)
        logger.debug("Found reference {}".format(reference))
        return reference

    def write_node_object(self):
        """Write object node for loading into DSCensor

           file name is object name from json
        """
        my_name = self.write_me["filename"]
        if self.write_me["canonical_type"] == "genome_main":
            self.write_me["counts"] = basic_fasta_stats(self.target, 10, False)
        elif self.write_me["canonical_type"] == "gene_models_main":
            self.write_me["counts"] = count_gff_features(self.target)
        my_file = open("./{}.json".format(my_name), "w")
        my_file.write(json.dumps(self.write_me))
        my_file.close()

    def run_busco(self, mode, file_name):
        """Runs BUSCO using BUSCO_ENV_FILE env var and input

           and outputs to file_name
        """
        node_data = self.node_data  # get current targets nodes
        busco_parse = re.compile(r"C:(.+)\%\[S:(.+)\%,D:(.+)\%\],F:(.+)\%,M:(.+)\%,n:(\d+)")
        output = "{}.busco".format(".".join(file_name.split(".")[:-2]))
        cmd = "run_BUSCO.py --mode {} --lineage {}".format(mode, "lineage")
        outdir = "./run_{}".format(output)  # output from BUSCO
        short_summary = glob(outdir + "/short_summary*.busco.txt")
        if not short_summary:
            logger.error("BUSCO short summary not found for {}".format(outdir))
            sys.exit(1)
        short_summary = short_summary[0]
        with open(short_summary) as fopen:
            for line in fopen:
                line = line.rstrip()
                if line.startswith("#") or not line:
                    continue
                if line.startswith("\tC:"):
                    line = line.replace("\t", "")
                    percentages = busco_parse.search(line)  # read summary
                    total = int(percentages.group(6))
                    complete = float(percentages.group(1))
                    frag = float(percentages.group(4))
                    single = float(percentages.group(2))
                    duplicate = float(percentages.group(3))
                    missing = float(percentages.group(5))
                    node_data["busco"] = {
                        "total_buscos": total,  # node BUSCO
                        "complete_buscos": complete,
                        "fragmented_buscos": frag,
                        "single_copy_buscos": single,
                        "duplicate_buscos": duplicate,
                        "missing_buscos": missing,
                    }

    def detect_incongruencies(self):
        """Detects all incongruencies in self.target_objects

           report all incongruencies to self.output_prefix

           Probably refactor this at some point to use a self.dict

           This is to allow just iteration and lookup to occur and remove

           basically all this conditional foo
        """
        targets = self.target_objects  # get objects from class init
        no_nodes = self.no_nodes  # if true, no nodes for DSCensor written
        for reference in sorted(targets, key=lambda k: self.rank[targets[k]["type"]]):
            #            logger.info('HERE {}'.format(reference))
            if reference not in self.passed:
                self.passed[reference] = 0
                self.target = reference
                ref_method = getattr(
                    specification_checks, targets[reference]["type"]  # reads checks from spec
                )  # type ex genome_main
                if not ref_method:  # if the target isnt in the hierarchy continue
                    logger.debug("Check for {} does not exist".format(targets[reference]["type"]))
                    continue
                logger.debug(ref_method)
                my_detector = ref_method(self, **self.options)
                passed = my_detector.run()
                if passed:  # validation passed writing object node for DSCensor
                    self.passed[reference] = 1
                    self.node_data = targets[reference]["node_data"]
                    if not no_nodes:
                        logger.info("Writing node object for {}".format(reference))
                        # dscensor node
                        self.write_me = targets[reference]["node_data"]
                        self.write_node_object()  # write node for dscensor loading
                logger.debug("{}".format(targets[reference]))
            if self.target_objects[reference]["children"]:  # process children
                children = self.target_objects[reference]["children"]
                for c in children:
                    if c in self.passed:
                        logger.debug("Child {} Already Passed".format(c))
                        continue

                    self.passed[c] = 0
                    #                    logger.info('HERE child {}'.format(c))
                    logger.info("Performing Checks for {}".format(c))
                    self.target = c
                    child_method = getattr(
                        specification_checks, children[c]["type"]  # check for spec
                    )  # exgene_models_main
                    if not child_method:
                        logger.warning("Check for {} does not exist".format(children[c]["type"]))
                        continue
                    logger.debug(child_method)
                    my_detector = child_method(self, **self.options)
                    passed = my_detector.run()
                    if passed:  # validation passed writing object node for DSCensor
                        self.passed[c] = 1
                        if not no_nodes:
                            logger.info("Writing node object for {}".format(c))
                            self.write_me = children[c]["node_data"]
                            self.write_node_object()
                    logger.debug("{}".format(c))


@cli.command()
@click.option("--no_busco", is_flag=True, help="""Disable BUSCO.""")
@click.option("--no_nodes", is_flag=True, help="""Disable DSCensor stats and node generation.""")
@click.argument("targets", nargs=-1)
def consistency(targets, no_busco, no_nodes):
    """Check for consistency with Data Store standards."""
    data_store_home = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    templates_dir = "{}/templates".format(data_store_home)
    readme_template = "{}/template__README.KEY.yml".format(templates_dir)
    options = {
        "no_busco": no_busco,
        "no_nodes": no_nodes,
        "readme_template": readme_template,
    }
    for t in targets:
        detector = Detector(t, **options)  # initializers
        detector.detect_incongruencies()  # class method runs all detection methods

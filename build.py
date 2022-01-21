#!/usr/bin/env python

"""Builds the Docker images contained in this repo
"""

from __future__ import print_function
import sys
import re
import subprocess
import argparse
from datetime import datetime
from dateutil.parser import parse as dateparse
from pathlib import Path
import pkgutil
import importlib
import yaml
import git
import docker
import re
import logging
import requests
from rich.console import Console
from rich.prompt import Prompt

# Instantiate output objects
logger = logging.getLogger(__name__)
console = Console()


def get_python_versions():
    """
    Returns a list of possible Python versions to build the targets
    for. A Supported version of Python is merely a version of Python
    that is not yet beyond its end-of-life date.

    Data sourced from https://endoflife.date

    :returns: A list of Python version strings
    :rtype: list
    """
    try:
        # Build url
        response = requests.get("https://endoflife.date/api/python.json")

        # Parse versions
        versions = [v["cycle"] for v in response.json() if dateparse(v["eol"]) > datetime.now()]

        return versions

    except Exception as e:
        print(f"Error: request for Python versions failed: {e}")

def get_version():
    """
    Reads and returns the current version of the builder
    :returns: The current version number
    :rtype: str
    """
    pattern = re.compile("^# Version:[\s]+([0-9\.]+)$")

    for i, line in enumerate(open("DockerMake.yml")):
        for match in re.finditer(pattern, line):
            return match.group(1)

def image_exists(image):
    """
    Checks DockerHub to ensure the named image exists.

    :param image: The name of the Docker image to check
    :type image: str
    :returns: Whether the image exists or not
    :rtype: boolean
    """
    try:
        # Get it
        client = docker.from_env()

        return client.images.get(image) is not None

    except docker.errors.ImageNotFound:
        return False
    except Exception as e:
        logger.exception(f"Error: {e}", exc_info=True)


class Target(object):
    """ This class represents a buildable target """

    identifier = None
    versions = []
    version_pattern = r"^[0-9]+(\.[0-9]+)+$"
    targets = None
    suffix = None

    def __init__(self, identifier):
        #self.identifier = identifier

        # Load targets from DockerMake.yml
        with open("DockerMake.yml", "r") as f:
            docker_make = yaml.safe_load(f)
            self.targets = docker_make["_ALL_"]

    @classmethod
    def full_identifier(cls):
        """
        Returns this classes identifier including suffix, if specified.

        :return: The full class identifier name
        :rtype: str
        """
        if cls.suffix:
            return f"{cls.identifier}-{cls.suffix}"
        else:
            return cls.identifier

    @classmethod
    def get_base_image_name(cls, version, python_version):
        """
        Returns the name of this target's base image for the passed
        version and Python version.

        :param version: The version of this target to check
        :type version: str
        :param python_version: The version of Python for this target to check
        :type python_version: str
        :return: The name of the base image
        :rtype: str
        """
        return f"python:{python_version}-{cls.identifier}{version}"

    @classmethod
    def get_target_versions(cls):
        """
        Returns a list of possible target versions as parsed from the
        DockerMake.yml file.

        :return: A list of possible target versions
        :rtype: list
        """
        try:
            with open("DockerMake.yml", "r") as f:
                docker_make = yaml.safe_load(f)

                # Get targets
                targets = docker_make["_ALL_"]

                # Filter by target
                versions = [t.replace(cls.identifier, "") for t in targets if t.startswith(cls.identifier)]

                # Further filter if using a suffix
                if cls.suffix:
                    versions = [v.replace(f"-{cls.suffix}", "") for v in versions if v.endswith(cls.suffix)]

                return [v for v in versions if v and re.fullmatch(cls.version_pattern, v)]

        except Exception as e:
            print(f"Error: {e}")

    @classmethod
    def can_build(cls, version, python_version):
        """
        Accepts a version argument and checks whether it can be built for
        this target or not.

        :param version: The version of this target to check
        :type version: str
        :param python_version: The version of Python for this target to check
        :type python_version: str
        :returns: Whether the target can be built or not
        :rtype: bool
        """
        # Check base image
        try:
            # Set base image name
            base_image = cls.get_base_image_name(
                version=version,
                python_version=python_version,
            )
            console.print(f"Checking base image: '{base_image}'")

            # Get it and check it
            client = docker.from_env()
            return client.api.inspect_distribution(base_image) is not None

        except docker.errors.NotFound:
            logger.info(f"Image does not exist: '{base_image}'")
        except Exception as e:
            logger.exception(f"Error: {e}", exc_info=True)

        return False

    def build_versions(self, args):
        """
        Returns a list of versions to attempt to build for this target.

        :param args: The current parsed arguments object
        :type args: Namespace
        :returns: A list of build target version
        :rtype: list
        """
        # Default to argument as plural of target identifier
        versions = getattr(args, self.identifier + "s")

        # If no versions, return all possible versions
        if not versions:
            versions = self.get_target_versions()

        return versions

    def build_target(self, version):
        """
        Returns the build target identifier for the passed version.

        :param version: The version of this target to build
        :type version: str
        :returns: A build target
        :rtype: str
        """
        # Append version to identifier
        return f"{self.identifier}{version}{f'-{self.suffix}' if self.suffix else ''}"

    def tag(self, version, python_version, dbmisvc_version):
        """
        Accepts a version argument passed via CLI and returns the OS portion
        of the target image tag.

        :param version: The version of this target to generate a tag for
        :type version: str
        :param python_version: The version of Python for this target to check
        :type python_version: str
        :param dbmisvc_version: The version of this tool
        :type dbmisvc_version: str
        :returns: The image tag
        :rtype: str
        """
        # Ensure version is valid
        if version not in self.versions:
            console.print(
                f"Info: '{version}' is not a valid version for "
                f" '{self.identifier}' targets"
            )
            return None

        return f'{self.build_target(version)}-python{python_version}-{dbmisvc_version}'

    def build_version_is_valid(self, version):
        """
        Returns whether the version translates to a valid target version
        or not. This determination is made by whether the translated target
        exists in the DockerMake.yml file or not.

        :param version: The version of this target to build
        :type version: str
        :returns: Whether the build target is valid or not
        :rtype: bool
        """
        # Append version to identifier
        return self.build_target(version) in self.targets

    def __new__(cls, *args, **kwargs):
        """
        This override of the __new__ method will match a derived class based on
        the `name` property and return it instead of an instance of this class.

        :return: An instance of a class dervied from Stack
        :rtype: Stack
        """
        try:
            # Trim suffix if present
            subclass = cls.__subclass_map__()[args[0]]
            instance = super(Target, subclass).__new__(subclass)
            return instance
        except Exception as e:
            logger.debug("", exc_info=True)
            raise ValueError(f"Target name \"{args[0]}\" is invalid")

    @classmethod
    def __subclass_map__(cls):
        """
        Returns a mapping of Stack name to subclasses
        """
        package, _, _ = cls.__module__.rpartition(".")
        package_dir = Path(__file__).resolve()
        for (_, module_name, _) in pkgutil.iter_modules([package_dir]):
            importlib.import_module(f"{package}.{module_name}")
        subclass_map = {}
        for subclass in [c for c in cls.__subclasses__() if getattr(c, "identifier")]:
            # Check for suffix
            identifier = f"{subclass.identifier}{f'-{subclass.suffix}' if subclass.suffix else ''}"
            subclass_map.update({
                identifier: subclass,
                **subclass.__subclass_map__()
            })
        return subclass_map


class Alpine(Target):

    identifier = "alpine"
    versions = ['3.12', '3.13', '3.14',]
    version_pattern = r"[3-9]\.[0-9]+"


class AlpineZip(Alpine):

    identifier = "alpine"
    suffix = "zip"


class Debian(Target):

    identifier = "debian"
    versions = ["9", "10", "11"]
    version_pattern = r"(9|1[0-9]+)"

    # Set version to code mappings
    codes = {
        "9": "stretch",
        "10": "buster",
        "11": "bullseye",
    }

    @classmethod
    def get_base_image_name(cls, version, python_version):
        """
        Returns the name of this target's base image for the passed
        version and Python version.

        :param version: The version of this target to check
        :type version: str
        :param python_version: The version of Python for this target to check
        :type python_version: str
        :return: The name of the base image
        :rtype: str
        """
        # Convert number versions to codenames
        try:
            code = cls.codes[version]
        except KeyError:
            raise ValueError(
                f"Debian cannot convert number version '{version}' "
                f"to a codename"
            )

        return f"python:{python_version}-{code}"


class DebianZip(Debian):

    suffix = "zip"

class DebianSlim(Debian):

    suffix = "slim"

    @classmethod
    def get_base_image_name(cls, version, python_version):
        """
        Returns the name of this target's base image for the passed
        version and Python version.

        :param version: The version of this target to check
        :type version: str
        :param python_version: The version of Python for this target to check
        :type python_version: str
        :return: The name of the base image
        :rtype: str
        """
        # Convert number versions to codenames
        try:
            code = cls.codes[version]
        except KeyError:
            raise ValueError(
                f"Debian cannot convert number version '{version}' "
                f"to a codename"
            )

        return Debian.get_base_image_name(version, python_version).replace(code, f"slim-{code}")


class DebianSlimZip(DebianSlim):

    suffix = "slim-zip"


class Ubuntu(Target):

    identifier = "ubuntu"
    versions = ["18.04", "20.04"]
    version_pattern = r"^(18|[2-9][0-9])\.(0[1-9]|1[0-2])$"

    @classmethod
    def get_base_image_name(cls, version, python_version):
        """
        Returns the name of this target's base image for the passed
        version and Python version.

        :param version: The version of this target to check
        :type version: str
        :param python_version: The version of Python for this target to check
        :type python_version: str
        :return: The name of the base image
        :rtype: str
        """
        return f"{cls.identifier}:{version}"


def check_python_versions(python_versions, valid_python_versions=None, forced=False):
    """
    Inspects the passed list of Python versions and filters out unsupported
    versions and returns the list.

    :param python_versions: A list of Python version strings
    :type python_versions: list
    :param valid_python_versions: A list of supported Python version strings
    :type valid_python_versions: list, defaults to None
    :param forced: Force the Python version even if it's no longer supported
    :type forced: boolean
    :returns: A list of supported Python versions
    :rtype: list
    """
    # Get list if not passed
    if not valid_python_versions:
        valid_python_versions = get_python_versions()

    # Limit Python versions
    unsupported_python_versions = list(set(python_versions) - set(valid_python_versions))
    if unsupported_python_versions:

        # Log it
        console.print(
            f"[blue]Info[/blue]: Python version(s) "
            f"[yellow]{', '.join(unsupported_python_versions)}[/yellow] "
            f"is/are no longer supported and is/are not enabled for builds"
        )

        # If not forced, drop unsupported versions
        if not forced:

            # Trim it
            python_versions = list(set(python_versions) & set(valid_python_versions))

        if not python_versions:
            # Log it
            console.print(
                f"[blue]Info[/blue]: No valid Python versions passed, nothing "
                f"to build."
            )
            exit(1)

        else:
            # Log it
            console.print(
                f"[blue]Info[/blue]: Limiting builds to Python version(s) "
                f"[yellow]{', '.join(python_versions)}[/yellow]"
            )

    return python_versions


def main(arguments):

    # Pull Python versions
    python_versions = get_python_versions()

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('-v', '--version', metavar='version', help='Set build version', type=str)
    parser.add_argument('-t', '--targets', nargs='+', help='Set build targets',
                        required=False, default=Target.__subclass_map__().keys())
    parser.add_argument('-a', '--alpines', nargs='+', help='Set Alpine targets', required=False)
    parser.add_argument('-d', '--debians', nargs='+', help='Set Debian targets', required=False)
    parser.add_argument('-u', '--ubuntus', nargs='+', help='Set Ubuntu targets', required=False)
    parser.add_argument('-y', '--pythons', nargs='+', help='Set Python versions per target',
                        required=False, default=python_versions)
    parser.add_argument('-r', '--repo', help='Set the repo to prepend to image tag',
                        type=str, default='hmsdbmitc/dbmisvc:')
    parser.add_argument('-p', '--push', help='Automatically push the image to Docker Hub', action='store_true')
    parser.add_argument('-n', '--print', help='Print Dockerfiles to stdout', action='store_true')
    parser.add_argument('-f', '--force', help='Force build regardless of Python version status', action='store_true')
    parser.add_argument('-c', '--commit', help='The commit of the versioned build', type=str)
    parser.add_argument('--dryrun', help='Do a dry-run of the build', action='store_true')

    args = parser.parse_args(arguments)

    # Set version
    if not args.version:
        args.version = get_version()

    # Get commit
    commit = args.commit
    if not args.commit:

        # Get the current commit
        repo = git.Repo(search_parent_directories=True)
        commit = repo.head.object.hexsha

    # Check python versions
    args.pythons = check_python_versions(args.pythons, python_versions, args.force)

    # Iterate targets
    for t in args.targets:
        try:
            # Initialize target
            target = Target(t)

            # Iterate versions of OS and python versions
            for version in target.build_versions(args=args):

                # Ensure it is valid
                if not target.build_version_is_valid(version):
                    console.print(
                        f"[red]Error[/red]: Build target "
                        f"'{target.build_target(version)}' is an invalid "
                        f"target. Check DockerMake.yml for valid targets.")
                    continue

                for python_version in args.pythons:

                    # If pushing, correct repo if necessary
                    if args.push and not args.repo.startswith('index.docker.io/'):
                        args.repo = 'index.docker.io/' + args.repo

                    # Check base image
                    if not target.can_build(version, python_version):
                        console.print(
                            f"[blue]Info[/blue]: Docker image "
                            f"'{target.get_base_image_name(version, python_version)}' no longer exists, "
                            f"cannot build 'hmsdbmitc/dbmisvc:{target.tag(version, python_version, args.version)}'"
                        )
                        continue

                    # Build the command
                    command = [
                        "docker-make", "-f", "DockerMake.yml",
                        target.build_target(version),
                        "-t",  f"python{python_version}-{args.version}",
                        "-u", args.repo,
                        "--build-arg", f"PYTHON_VERSION={python_version}",
                        "--build-arg", f"DATE={datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}",
                        "--build-arg", f"COMMIT={commit}",
                        "--build-arg", f"VERSION={args.version}",
                    ]

                    # Append arguments if we are pushing to repo
                    if args.push:
                        command.append("-P")

                    # Append arguments if printing to file
                    if args.print:
                        command.append("--print_dockerfiles")

                    try:
                        # Check dry run
                        if args.dryrun:
                            console.print(f"[blue]DRY RUN[/blue]: {command}")

                        else:
                            # Run it
                            subprocess.run(command, stdout=subprocess.PIPE)

                    except Exception as e:
                        logger.exception(f"Error: {e}", exc_info=True)

        except Exception as e:
            logger.exception(f"Error: {e}", exc_info=True)

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

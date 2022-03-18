#!/usr/bin/env python
"""
dbmisvc-docker

Usage:
    build.py build [options] [-y <pythons>]... [-a <alpines>]... [-d <debians>]... [-u <ubuntus>]... -- <targets>...
    build.py <target> [options] -- <os-version> <python-version>
    build.py versions <target>
    build.py version

Options:
    -y <pythons>, --pythons <pythons>               The versions of Python to build.
    -a <alpines>, --alpines <alpines>               The versions of Alpine to build.
    -d <debians>, --debians <debians>               The versions of Debian to build.
    -u <ubuntus>, --ubuntus <ubuntus>               The versions of Ubuntu to build.
    -v <version>, --version <version>               The version of the images to be built.
    -r <repo>, --repo <repo>                        The image repostory to use for images [default: hmsdbmitc/dbmisvc:].
    -p, --push                                      Whether to push the image to the registry or not.
    -f, --force                                     Build target regardless of whether OS/Python version is supported or not.
    -c <commit>, --commit <commit>                  The Git commit hash to use for image metadata.
    --print                                         Print the Dockerfiles to file instead of building.
    --dryrun                                        Print Dockerfiles to file instead of building images.
    --continue-on-error                             If a build is invalid or cannot be built, continue on to other builds.
    -h, --help                                      Show this.
    -q, --quiet                                     Print less text.
    --verbose                                       Print more text.
"""

"""Builds the Docker images contained in this repo
"""

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
import json
import logging
import requests
from rich.console import Console
from rich.prompt import Prompt
from docopt import docopt
from distutils.version import LooseVersion

# Instantiate output objects
logger = logging.getLogger(__name__)
console = Console()


class Target(object):
    """ This class represents a buildable target """

    identifier = None
    versions = []
    version_pattern = r"^[0-9]+(\.[0-9]+)+$"
    codename_pattern = r"^[A-Za-z-_\s]+$"
    targets = None
    suffix = None
    excluded_versions = []

    def __init__(self, identifier):
        #self.identifier = identifier

        # Load targets from DockerMake.yml
        with open("DockerMake.yml", "r") as f:
            docker_make = yaml.safe_load(f)
            self.targets = docker_make["_ALL_"]

    @classmethod
    def get_python_versions(cls):
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
            versions.sort(key=LooseVersion)

            return versions

        except Exception as e:
            print(f"Error: request for Python versions failed: {e}")

    @classmethod
    def check_python_versions(cls, python_versions, valid_python_versions=None, forced=False):
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
            valid_python_versions = cls.get_python_versions()

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

    @classmethod
    def get_version(cls):
        """
        Reads and returns the current version of the builder
        :returns: The current version number
        :rtype: str
        """
        pattern = re.compile("^# Version:[\s]+([0-9\.]+)$")

        for i, line in enumerate(open("DockerMake.yml")):
            for match in re.finditer(pattern, line):
                return match.group(1)

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

            # Get it and check it
            client = docker.from_env()
            return client.api.inspect_distribution(base_image) is not None

        except docker.errors.NotFound:
            logger.info(f"Image does not exist: '{base_image}'")
        except Exception as e:
            logger.exception(f"Error: {e}", exc_info=True)

        return False

    def build(self, args, versions=None, python_versions=None, version=None,
              commit=None, push=False, repo=None, print=False, dry_run=False):
        """
        Runs the actual build process for the target.

        :param args: The current parsed arguments object
        :type args: Namespace
        :param versions: A list of target OS versions
        :type versions: list, defaults to current versions of the target's OS
        :param python_versions: A list of target Python versions
        :type python_versions: list, defaults to current versions of Python
        :param version: The version of this tool to tag images with, defaults to None
        :type version: str, optional
        :param commit: The commit hash of this tool's code use to build images, defaults to None
        :type commit: str, optional
        :param push: Whether to push the images to a remote registry or not, defaults to False
        :type push: bool, optional
        :param repo: The repository to use for the image tags, defaults to None
        :type repo: str, optional
        :param print: Whether to print the Dockerfiles to file instead of building, defaults to False
        :type print: bool, optional
        :param dry_run: Tests the build routines without actually building images, defaults to False
        :type dry_run: bool, optional
        """
        try:
            # Get versions if not supplied
            if not versions:
                versions = self.get_supported_versions()

            if not python_versions:
                python_versions = self.get_python_versions()

            # Iterate versions of OS and python versions
            for os_version in versions:

                # Ensure it is valid
                if not self.build_version_is_valid(os_version):
                    console.print(
                        f"[red]Error[/red]: Build target "
                        f"'{self.build_target(os_version)}' is an invalid "
                        f"target. Check DockerMake.yml for valid targets.")
                    if not args["--continue-on-error"]:
                        exit(1)
                    continue

                for python_version in python_versions:

                    # If pushing, correct repo if necessary
                    if push and not repo.startswith('index.docker.io/'):
                        repo = 'index.docker.io/' + repo

                    # Check base image
                    console.print(f"Checking base image: '{self.get_base_image_name(os_version, python_version)}'")
                    if not self.can_build(os_version, python_version):
                        console.print(
                            f"[blue]Info[/blue]: Docker image "
                            f"'{self.get_base_image_name(os_version, python_version)}' no longer exists, "
                            f"cannot build 'hmsdbmitc/dbmisvc:{self.tag(os_version, python_version, version)}'"
                        )
                        # If not directed to do otherwise, fail this build
                        if not args["--continue-on-error"]:
                            exit(1)
                        continue

                    # Base image is good
                    console.print(f"Base image is good :thumbs_up:")

                    # Build the command
                    command = [
                        "docker-make", "-f", "DockerMake.yml",
                        self.build_target(os_version),
                        "-t",  f"python{python_version}-{version}",
                        "-u", repo,
                        "--build-arg", f"PYTHON_VERSION={python_version}",
                        "--build-arg", f"DATE={datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}",
                        "--build-arg", f"COMMIT={commit}",
                        "--build-arg", f"VERSION={version}",
                    ]

                    # Append arguments for target types
                    for k, v in self.build_args(os_version).items():
                        command.extend([
                            "--build-arg", f"{k.upper()}={v}"
                        ])

                    # Append arguments if we are pushing to repo
                    if push:
                        command.append("-P")

                    # Append arguments if printing to file
                    if print:
                        command.append("--print_dockerfiles")

                    # Set a placeholder for the process object
                    process = None
                    try:
                        # Check dry run
                        if dry_run:
                            console.print(f"[blue]DRY RUN[/blue]: {command}")

                        else:
                            console.print("[green]Building target image...")
                                
                            # Run the command
                            process = subprocess.run(command)
                            process.check_returncode()

                            # Base image is good
                            console.print(f"[bold green]Image built successfully :thumbs_up:")

                    except Exception as e:

                        # Base image is good
                        console.print(f"[red bold]Error: [/red bold] Image failed to build :cross_mark:")

                        # Fail out entirely if necessary
                        if not args["--continue-on-error"]:
                            exit(1)

        except Exception as e:
            logger.exception(f"Error: {e}", exc_info=True)

    @classmethod
    def build_versions(cls, args):
        """
        Returns a list of versions to attempt to build for this target.

        :param args: The current parsed arguments object
        :type args: Namespace
        :returns: A list of build target version
        :rtype: list
        """
        # Default to argument as plural of target identifier
        versions = args["--" + cls.identifier + "s"]

        # If no versions, return all possible versions
        if not versions:
            versions = cls.get_target_versions()

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

    def build_args(self, version):
        """
        Returns a dictionary of arguments to pass to the DockerMake command for
        the given version. This allows targets to add additional arguments
        that may be necessary for build.

        :param version: The version of this target being build
        :type version: str
        :returns: A dictionary of keyword arguments
        :rtype: dict
        """
        return {}

    @classmethod
    def get_supported_versions(cls, lts=False):
        """
        Returns a list of numeric versions that are currently supported for
        the current target/OS. Uses https://endoflife.date as a source for
        data.
        :param lts: Whether to filter returned versions on being LTS or not
        :type lts: boolean
        :returns: A list of supported version strings
        :rtype: list
        """
        raise NotImplementedError(f"Subclasses must implement this method")

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
    version_pattern = r"[3-9]\.[0-9]+"

    @classmethod
    def get_supported_versions(cls, lts=False):
        """
        Returns a list of numeric versions that are currently supported for
        the current target/OS. Uses https://endoflife.date as a source for
        data.
        :param lts: Whether to filter returned versions on being LTS or not
        :type lts: boolean
        :returns: A list of supported version strings
        :rtype: list
        """
        try:
            # Build url
            response = requests.get("https://endoflife.date/api/alpine.json")

            # Set the pattern
            pattern = rf"v([0-9]+\.[0-9]+)"

            # Parse versions
            versions = [
                v for v in response.json()
                if dateparse(v["eol"]) > datetime.now()
            ]

            # Check if filtering on LTS
            if lts:
                versions = [v for v in versions if v.get("lts")]

            versions = [re.fullmatch(pattern, v["cycle"])[1] for v in versions]

            # Difference with exclusions
            versions = list(set(versions) - set(cls.excluded_versions))
            versions.sort(key=LooseVersion)

            return versions

        except requests.HTTPError as e:
            print(f"Error: request for Debian versions failed: {e}")

        except Exception as e:
            raise ValueError(f"Failed to get current Debian versions")


class Debian(Target):

    identifier = "debian"
    version_pattern = r"([123][0-9]+)"
    excluded_versions = ["9"]

    @classmethod
    def get_version_from_codename(cls, codename, minor_version=False):
        """
        Returns the numerical version for the given codename. References
        https://endoflife.date API for the conversion.

        :param codename: The codename of the Debian release
        :type codename: str
        :param minor_version: Returns the minor version (e.g. 11.2)
        :type minor_version: bool
        :raises ValueError: Raised if the codename is not a valid Debian release
        :return: The numerical version of the Debian release
        :rtype: str
        """
        try:
            # Build url
            response = requests.get("https://endoflife.date/api/debian.json")

            # Parse versions
            release = next(v for v in response.json() if v["cycleShortHand"].lower() == codename.lower())

            return release["latest"] if minor_version else release["cycle"]

        except requests.HTTPError as e:
            print(f"Error: request for Debian versions failed: {e}")

        except Exception as e:
            raise ValueError(f"Codename '{codename}' is not a valid Debian version")

    @classmethod
    def get_codename_for_version(cls, version):
        """
        Returns the codename version for the given version. References
        https://endoflife.date API for the conversion.

        :param version: The version of the Debian release
        :type version: str
        :raises ValueError: Raised if the version is not a valid Debian release
        :return: The codename version of the Debian release
        :rtype: str
        """
        try:
            # Build url
            response = requests.get("https://endoflife.date/api/debian.json")

            # Only lookup version on major version number (or cycle)
            release = next(v for v in response.json() if v["cycle"] == next(iter(version.split("."))))

            return release["cycleShortHand"].lower()

        except requests.HTTPError as e:
            print(f"Error: request for Debian versions failed: {e}")

        except Exception as e:
            raise ValueError(f"Version '{version}' is not a valid Debian version")

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
            codename = cls.get_codename_for_version(version)
        except KeyError:
            raise ValueError(
                f"Debian cannot convert number version '{version}' "
                f"to a codename"
            )

        return f"python:{python_version}-{codename}"

    def build_args(self, version):
        """
        Returns a dictionary of arguments to pass to the DockerMake command for
        the given version. This allows targets to add additional arguments
        that may be necessary for build.

        :param version: The version of this target being build
        :type version: str
        :returns: A dictionary of keyword arguments
        :rtype: dict
        """
        return {
            "DEBIAN_VERSION": version,
            "DEBIAN_CODENAME": self.get_codename_for_version(version),
        }

    @classmethod
    def get_supported_versions(cls, lts=False):
        """
        Returns a list of numeric versions that are currently supported for
        the current target/OS. Uses https://endoflife.date as a source for
        data.
        :param lts: Whether to filter returned versions on being LTS or not
        :type lts: boolean
        :returns: A list of supported version strings
        :rtype: list
        """
        try:
            # Build url
            response = requests.get("https://endoflife.date/api/debian.json")

            # Parse versions
            versions = [
                v for v in response.json()
                if dateparse(v["eol"]) > datetime.now()
            ]

            # Check if filtering on LTS
            if lts:
                versions = [v for v in versions if v.get("lts")]

            # Extract supported versions
            versions = [v["cycle"] for v in versions]

            # Difference with exclusions
            versions = list(set(versions) - set(cls.excluded_versions))
            versions.sort(key=LooseVersion)

            return versions

        except requests.HTTPError as e:
            print(f"Error: request for Debian versions failed: {e}")

        except Exception as e:
            raise ValueError(f"Failed to get current Debian versions")


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
            codename = cls.get_codename_for_version(version)
        except KeyError:
            raise ValueError(
                f"Debian cannot convert number version '{version}' "
                f"to a codename"
            )

        return Debian.get_base_image_name(version, python_version).replace(codename, f"slim-{codename}")


class Ubuntu(Target):

    identifier = "ubuntu"
    version_pattern = r"^(18|[2-9][0-9])\.(0[1-9]|1[0-2])$"

    # Exclude 14.04 and 16.04 because they are nightmares
    excluded_versions = ["14.04", "16.04"]

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

    @classmethod
    def get_version_from_codename(cls, codename):
        """
        Returns the numerical version for the given codename. References
        https://endoflife.date API for the conversion.

        :param codename: The codename of the Ubuntu release
        :type codename: str
        :raises ValueError: Raised if the codename is not a valid Ubuntu release
        :return: The numerical version of the Ubuntu release
        :rtype: str
        """
        try:
            # Build url
            response = requests.get("https://endoflife.date/api/ubuntu.json")

            # Set the pattern
            pattern = rf"(\d\d\.\d\d) '{codename.lower().title()} [A-Za-z-_]+'"

            # Parse versions
            release = next(v for v in response.json() if re.fullmatch(pattern, v["cycle"]))

            return re.fullmatch(pattern, release["cycle"])[1]

        except requests.HTTPError as e:
            print(f"Error: request for Ubuntu versions failed: {e}")

        except Exception as e:
            raise ValueError(f"Codename '{codename}' is not a valid Ubuntu version")

    @classmethod
    def get_codename_for_version(cls, version):
        """
        Returns the codename version for the given version. References
        https://endoflife.date API for the conversion.

        :param version: The version of the Ubuntu release
        :type version: str
        :raises ValueError: Raised if the version is not a valid Ubuntu release
        :return: The codename version of the Ubuntu release
        :rtype: str
        """
        try:
            # Build url
            response = requests.get("https://endoflife.date/api/ubuntu.json")

            # Set the pattern
            pattern = rf"{version} '([A-Z][a-z-_]+)\s?[A-Z][a-z-_]+'"

            # Parse versions
            release = next(v for v in response.json() if re.fullmatch(pattern, v["cycle"]))

            return re.fullmatch(pattern, release["cycle"])[1].lower()

        except requests.HTTPError as e:
            print(f"Error: request for Ubuntu versions failed: {e}")

        except Exception as e:
            raise ValueError(f"Version '{version}' is not a valid Ubuntu version")

    def build_args(self, version):
        """
        Returns a dictionary of arguments to pass to the DockerMake command for
        the given version. This allows targets to add additional arguments
        that may be necessary for build.

        :param version: The version of this target being build
        :type version: str
        :returns: A dictionary of keyword arguments
        :rtype: dict
        """
        return {
            "UBUNTU_VERSION": version,
            "UBUNTU_CODENAME": self.get_codename_for_version(version),
        }

    @classmethod
    def get_supported_versions(cls, lts=True):
        """
        Returns a list of numeric versions that are currently supported for
        the current target/OS. Uses https://endoflife.date as a source for
        data.
        :param lts: Whether to filter returned versions on being LTS or not
        :type lts: boolean
        :returns: A list of supported version strings
        :rtype: list
        """
        try:
            # Build url
            response = requests.get("https://endoflife.date/api/ubuntu.json")

            # Set the pattern
            pattern = r"(\d\d\.\d\d) '[A-Za-z-_]+\s?[A-Za-z-_]+'"

            # Parse versions
            versions = [
                v for v in response.json()
                if dateparse(v["eol"]) > datetime.now()
            ]

            # Check if filtering on LTS
            if lts:
                versions = [v for v in versions if v.get("lts")]

            # Extract versions
            versions = [re.fullmatch(pattern, v["cycle"])[1] for v in versions]

            # Difference with exclusions
            versions = list(set(versions) - set(cls.excluded_versions))
            versions.sort(key=LooseVersion)

            return versions

        except requests.HTTPError as e:
            print(f"Error: request for Ubuntu versions failed: {e}")

        except Exception as e:
            raise ValueError(f"Failed to get current Ubuntu versions")


def build(args):
    """
    Builds the images for the given targets and versions.

    :param args: The passed arguments
    :type args: argparse
    """
    # Set version
    if not args["--version"]:
        args["--version"] = Target.get_version()

    # Get commit
    if not args["--commit"]:

        # Get the current commit
        repo = git.Repo(search_parent_directories=True)
        args["--commit"] = repo.head.object.hexsha

    # Check for single or multiple targets
    if args["<target>"]:

        # Move the target to the multiple targets argument and proceed normally
        args["<targets>"] = [args["<target>"]]
        args["--pythons"] = [args["<python-version>"]]
        os_versions = [args["<os-version>"]]
        python_versions = [args["<python-version>"]]

    else:
        # Get python versions
        python_versions = args["--pythons"]

    # Check target python versions against supported versions
    python_versions = Target.check_python_versions(
        python_versions,
        Target.get_python_versions(),
        args["--force"]
    )

    # Iterate targets
    for t in args["<targets>"]:
        try:
            # Initialize target
            target = Target(t)

            # Get OS versions
            os_versions = [args["<os-version>"]] if args["<os-version>"] else target.build_versions(arguments)

            # Build it
            target.build(
                args,
                versions=os_versions,
                python_versions=python_versions,
                version=args["--version"],
                commit=args["--commit"],
                push=args["--push"],
                repo=args["--repo"],
                print=args["--print"],
                dry_run=args["--dryrun"],
            )

        except Exception as e:
            logger.exception(f"Error: {e}", exc_info=True)

def versions(args):
    """
    Builds the images for the given targets and versions.

    :param args: The passed arguments
    :type args: argparse
    """
    try:
        # Check for Python target
        if args["<target>"].lower() == "python":
            return Target.get_python_versions()

        else:
            # Initialize target
            target = Target(args["<target>"])

            # Return versions
            return target.get_supported_versions()

    except Exception as e:
        logger.exception(f"Error: {e}", exc_info=True)

if __name__ == '__main__':
    arguments = docopt(__doc__)

    # Run command
    if arguments["versions"]:
        print(json.dumps(versions(arguments)))
    elif arguments["build"] or arguments["<target>"]:
        build(arguments)
    elif arguments["version"]:
        print(Target.get_version())
    else:
        raise NotImplementedError(f"Command not yet implemented")

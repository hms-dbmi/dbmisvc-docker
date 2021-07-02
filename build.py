#!/usr/bin/env python

"""Builds the Docker images contained in this repo
"""

from __future__ import print_function
import sys
import subprocess
import argparse
from datetime import datetime
import git
import re

# Set the current list of build target types
TARGETS = [
    'alpine',
    'alpine-zip',
    'slim',
    'slim-zip',
    'debian',
    'debian-zip',
    'ubuntu',
]

# Set allowable Python/OS versions
PYTHONS = ['3.6', '3.7', '3.8', '3.9']
ALPINES = ['3.11', '3.12', '3.13', '3.14']
DEBIANS = ['stretch', 'buster', 'bullseye']
UBUNTUS = ['16.04', '18.04', '20.04']

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


def main(arguments):

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('-v', '--version', metavar='version', help='Set build version', type=str)
    parser.add_argument('-t', '--targets', nargs='+', help='Set build targets',
                        required=False, default=TARGETS)
    parser.add_argument('-a', '--alpines', nargs='+', help='Set Alpine targets',
                        required=False, default=ALPINES)
    parser.add_argument('-d', '--debians', nargs='+', help='Set Debian targets',
                        required=False, default=DEBIANS)
    parser.add_argument('-u', '--ubuntus', nargs='+', help='Set Ubuntu targets',
                        required=False, default=UBUNTUS)
    parser.add_argument('-y', '--pythons', nargs='+', help='Set Python versions per target',
                        required=False, default=PYTHONS)
    parser.add_argument('-r', '--repo', help='Set the repo to prepend to image tag', type=str,
                        default='hmsdbmitc/dbmisvc:')
    parser.add_argument('-p', '--push', help='Automatically push the image to Docker Hub', action='store_true')
    parser.add_argument('-n', '--print', help='Print Dockerfiles to stdout', action='store_true')
    parser.add_argument('-c', '--commit', help='The commit of the versioned build', type=str)

    args = parser.parse_args(arguments)

    # Set version
    if not args.version:
        args.version = get_version()

    # Filter allowed values
    if args.alpines:
        args.alpines = list(set(args.alpines) & set(ALPINES))
    if args.debians:
        args.debians = list(set(args.debians) & set(DEBIANS))
    if args.ubuntus:
        args.ubuntus = list(set(args.ubuntus) & set(UBUNTUS))

    # Get commit
    commit = args.commit
    if not args.commit:

        # Get the current commit
        repo = git.Repo(search_parent_directories=True)
        commit = repo.head.object.hexsha

    # Build versioned targets
    targets = []
    for t in args.targets:
        if args.alpines:
            for v in args.alpines:
                targets.append(t.replace('alpine', 'alpine{}'.format(v)))
        if args.debians:
            for v in args.debians:
                targets.append(t.replace('debian', v))
        if args.ubuntus:
            for v in args.ubuntus:
                targets.append(t.replace('ubuntu', 'ubuntu{}'.format(v)))

    # Iterate targets
    for target in targets:
        for python_version in args.pythons:

            # If pushing, correct repo if necessary
            if args.push and not args.repo.startswith('index.docker.io/'):
                args.repo = 'index.docker.io/' + args.repo

            # Build the command
            command = [
                "docker-make", "-f", "DockerMake.yml",
                target,
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
                # Run it
                subprocess.run(command, stdout=subprocess.PIPE)

            except Exception as e:
                print(f"Error: {e}", exc_info=True)

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

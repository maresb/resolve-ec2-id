#!/usr/bin/env python3
from __future__ import annotations  # Allows models to be defined in any order

import json
import shlex
import sys
from collections import defaultdict
from subprocess import CalledProcessError, check_output
from typing import TYPE_CHECKING, DefaultDict, NoReturn, Optional

import typer

if TYPE_CHECKING:
    from mypy_boto3_ec2.type_defs import DescribeInstancesResultTypeDef, InstanceTypeDef

if sys.version_info < (3, 8):
    import importlib_metadata

    def shlex_join(split_command: list[str]) -> str:
        return " ".join(shlex.quote(part) for part in split_command)

else:
    import importlib.metadata as importlib_metadata
    from shlex import join as shlex_join


# Set version number
__version__ = importlib_metadata.version(__name__)


# Helper functions


def print_error(msg: str) -> None:
    """Print a red error message to stderr."""
    typer.secho(msg, err=True, fg=typer.colors.RED)


def exit_error() -> NoReturn:
    """Exit with code 1, which indicates an error."""
    raise typer.Exit(code=1)


def exit_success() -> NoReturn:
    """Exit with code 0, which indicates success."""
    raise typer.Exit(code=0)


# Exceptions


class ResolutionError(RuntimeError):
    """Raised when the name could not be resolved to an instance ID."""


class NameNotFound(ResolutionError):
    """Raised when the name could not be found."""


class MultipleNamesFound(ResolutionError):
    """Raised when multiple instances have requested name same name."""


# Define the CLI app
app = typer.Typer(add_completion=False)

# Define the main CLI command


def version_callback(value: bool):
    """Print the version number and exit."""
    if value:
        typer.echo(__version__)
        exit_success()


@app.command()
def main(
    name: str,
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Print the version number and exit.",
    ),
):
    try:
        ec2_id = resolve_ec2_id(name)
    except ResolutionError as e:
        print_error(str(e))
        exit_error()

    typer.echo(ec2_id)
    exit_success()


def resolve_ec2_id(name: str) -> str:
    """Given the name of an EC2 instance, return the instance ID."""

    # Get the result of the "describe-instances" command.
    # Prefer boto3, but fall back to AWS CLI if it's not installed.
    try:
        describe_instances_dict = describe_instances_with_boto3()
    except ImportError:
        describe_instances_dict = describe_instances_with_aws_cli()

    instances_by_id: dict[str, InstanceTypeDef] = {
        instance.get("InstanceId", "_MISSING"): instance
        for reservation in describe_instances_dict["Reservations"]
        for instance in reservation.get("Instances", [])
        if instance.get("State", {"Name": "missing"}).get("Name") not in ["terminated"]
    }
    """Dictionary of instance objects indexed by instance ID."""

    instance_ids_by_name: DefaultDict[str, list[str]] = defaultdict(list)
    for instance in instances_by_id.values():
        for tag in instance.get("Tags", []):
            if tag["Key"] == "Name":
                instance_ids_by_name[tag.get("Value", "_MISSING")].append(
                    instance.get("InstanceId", "_MISSING"),
                )
    """List of instance IDs associated to a given name, as defined in tags."""

    if name in instances_by_id:
        # The name is already an instance ID, so return it.
        return name

    instance_ids: list[str] = instance_ids_by_name[name]
    """A list of instance IDs (hopefully exactly one) associated to the given name."""

    # Print the instance ID if there is exactly one, otherwise print an error.
    if len(instance_ids) == 0:
        raise NameNotFound(f"Could not find instance with name '{name}'.")
    elif len(instance_ids) > 1:
        instance_str = '"' + '", "'.join(instance_ids) + '"'
        raise MultipleNamesFound(
            f"Multiple instances with name '{name}' found: {instance_str}",
        )
    else:
        assert len(instance_ids) == 1
        return instance_ids[0]


def describe_instances_with_boto3() -> DescribeInstancesResultTypeDef:
    """Use boto3 to get the output of the "describe-instances" command.

    Raises ImportError if boto3 is not installed.
    """
    import boto3

    client = boto3.client("ec2")
    describe_instances_dict: DescribeInstancesResultTypeDef = (
        client.describe_instances()
    )
    return describe_instances_dict


def describe_instances_with_aws_cli() -> DescribeInstancesResultTypeDef:
    """Use AWS CLI to get the output of the "describe-instances" command.

    Exits with an error in case something goes wrong.
    """
    # The command to lists all instances:
    command = ["aws", "ec2", "describe-instances", "--output=json"]

    # Run the command in a subprocess
    try:
        raw_command_output = check_output(command)
    except CalledProcessError:
        command_str = shlex_join(command)
        print_error(
            f"An error occurred while running command: '{command_str}'. "
            f"We tried to run this command because boto3 is not installed. "
            f"Consider installing boto3.",
        )
        exit_error()
    return json.loads(raw_command_output)


if __name__ == "__main__":
    app()

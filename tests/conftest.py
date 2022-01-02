import json
import os
import sys
from os import environ
from pathlib import Path
from typing import Dict, Iterable

import boto3
import pytest
from _pytest.monkeypatch import MonkeyPatch
from moto import mock_ec2
from mypy_boto3_ec2.client import EC2Client
from pytest_cases import fixture

from .manage_ec2 import create_instance, set_name

if sys.version_info < (3, 8):
    from typing_extensions import Literal
else:
    from typing import Literal


@pytest.fixture(scope="session", autouse=True)
def aws_credentials() -> None:
    """Mocked AWS Credentials for moto."""
    # From "How do I avoid tests from mutating my real infrastructure"
    # <https://docs.getmoto.org/en/latest/docs/getting_started.html#how-do-i-avoid-tests-from-mutating-my-real-infrastructure>
    environ["AWS_ACCESS_KEY_ID"] = "testing"
    environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    environ["AWS_SECURITY_TOKEN"] = "testing"
    environ["AWS_SESSION_TOKEN"] = "testing"
    environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture(scope="session")
def monkeypatch_session() -> Iterable[MonkeyPatch]:
    """Monkeypatch object valid in session context."""
    # <https://github.com/pytest-dev/pytest/issues/363#issuecomment-289830794>
    monkeypatch = MonkeyPatch()
    yield monkeypatch
    monkeypatch.undo()


@pytest.fixture(scope="session", autouse=True)
def replace_aws_cli_executable(monkeypatch_session: pytest.MonkeyPatch) -> None:
    """Adjust path so that AWS CLI is replaced with our version."""
    exe_path = Path(__file__).parent / "mock_aws_executable"
    monkeypatch_session.setenv(
        "PATH",
        str(
            exe_path.resolve(),
        ),
        prepend=os.pathsep,
    )


@pytest.fixture(scope="session")
def mocked_ec2_client(aws_credentials) -> Iterable[EC2Client]:
    with mock_ec2():
        yield boto3.client("ec2")


@fixture(scope="function")
def boto3_disabled(monkeypatch) -> Literal["boto3_disabled"]:
    monkeypatch.setitem(sys.modules, "boto3", None)
    return "boto3_disabled"


boto3_infrastructure_to_mock = {
    "named": "my-named-boto3-instance",
    "unnamed": None,
    "duplicate1": "duplicate-boto3-name",
    "duplicate2": "duplicate-boto3-name",
}


infrastructure_to_mock = {
    "named": "my-named-instance",
    "unnamed": None,
    "duplicate1": "duplicate-name",
    "duplicate2": "duplicate-name",
}


@pytest.fixture(scope="session")
def mocked_ec2_instances(mocked_ec2_client: EC2Client) -> Dict[str, str]:
    ids = {}
    for label, name in infrastructure_to_mock.items():
        generated_ec2_id = create_instance(mocked_ec2_client)
        ids[label] = generated_ec2_id
        if name is not None:
            set_name(mocked_ec2_client, generated_ec2_id, name)
    awscli_output = json.dumps(
        mocked_ec2_client.describe_instances(),
        default=str,
        indent=2,
    )
    awscli_output_file = Path(__file__).parent / "mock_aws_executable" / "output.json"
    awscli_output_file.write_text(awscli_output)
    return ids

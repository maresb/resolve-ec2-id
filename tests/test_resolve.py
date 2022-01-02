import pytest
from pytest_cases import parametrize

from resolve_ec2_id import MultipleNamesFound, NameNotFound, resolve_ec2_id

from .conftest import boto3_disabled


@parametrize(boto3_status=["boto3_enabled", boto3_disabled])
def test_resolve_ec2_id_without_boto3(mocked_ec2_instances, boto3_status):

    # Standard lookup
    expected_id = mocked_ec2_instances["named"]
    assert resolve_ec2_id("my-named-instance") == expected_id

    # Lookup of ID
    assert resolve_ec2_id(expected_id) == expected_id

    with pytest.raises(NameNotFound):
        resolve_ec2_id("not-a-name")

    with pytest.raises(MultipleNamesFound):
        resolve_ec2_id("duplicate-name")

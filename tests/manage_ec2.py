"""Commands to manage (mock) EC2 instances for testing."""
from mypy_boto3_ec2.client import EC2Client
from mypy_boto3_ec2.type_defs import InstanceTypeDef


def create_instance(mocked_ec2_client: EC2Client) -> str:

    # To avoid warnings, get a random valid AMI ID.
    some_valid_ami = mocked_ec2_client.describe_images()["Images"][0].get("ImageId")
    assert some_valid_ami is not None

    res = mocked_ec2_client.run_instances(
        ImageId=some_valid_ami,
        MaxCount=1,
        MinCount=1,
    )
    instance_dict: InstanceTypeDef = res["Instances"][0]
    instance_id = instance_dict.get("InstanceId")
    assert instance_id is not None
    return instance_id


def create_tag(mocked_ec2_client: EC2Client, resource: str, key: str, value: str):
    mocked_ec2_client.create_tags(
        Resources=[resource], Tags=[{"Key": key, "Value": value}]
    )


def set_name(mocked_ec2_client: EC2Client, resource: str, name: str):
    create_tag(
        mocked_ec2_client=mocked_ec2_client, resource=resource, key="Name", value=name
    )

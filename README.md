# resolve-ec2-id

## Links

- [GitLab](https://gitlab.com/bmares/resolve-ec2-id)
- [GitHub](https://github.com/maresb/resolve-ec2-id)
- [PyPI](https://pypi.org/project/resolve-ec2-id/)

## Introduction

This is a simple command-line tool which looks up the EC2 instance ID given an instance name:

```bash
$ resolve-ec2-id my-named-instance
i-1234567890abcdef0
```

Currently this tool only works with default credentials. Consider configuring them with environment variables or using a program like [aws-vault](https://github.com/99designs/aws-vault).

## Alternatives

This package is perhaps not so useful because very similar functionality can be accomplished with AWS CLI as follows:

```bash
aws ec2 describe-instances --filters 'Name=tag:Name,Values=my-named-instance' --query 'Reservations[*].Instances[*].{Instance:InstanceId}' --output text
```

However, this tool has slightly better error-handling; the above AWS CLI command will not generate an error in the case that no instance is found.

## Installation

In order to install in a clean and isolated Python environment, it is recommended to use [pipx](https://github.com/pypa/pipx):

```bash
pipx install resolve-ec2-id
```

## Examples

Assuming you are using the Bash shell, to start an instance if you know the name but not the ID:

```bash
$ aws ec2 start-instances --output=yaml --instance-ids="$(resolve-ec2-id my-named-instance)"
StartingInstances:
- CurrentState:
    Code: 0
    Name: pending
  InstanceId: i-1234567890abcdef0
  PreviousState:
    Code: 80
    Name: stopped
```

This can also be used from within Python:

```python
from resolve_ec2_id import resolve_ec2_id

ec2_id = resolve_ec2_id('my-named-instance')
```

## Requirements

Beyond the base dependencies which install automatically, this requires either [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html) or [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html#installation). (I did not make `boto3` a dependency because it isn't needed if AWS CLI is already installed.)

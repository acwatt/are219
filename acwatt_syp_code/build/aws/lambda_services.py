# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
# Modified by Aaron Watt, Jan 2022

"""
PURPOSE:
Create a lambda function service call to download a sensor's historical data.

Uses the AWS SDK for Python (Boto3) to create an AWS Lambda function from `lambda_download_script.py,
invoke it for a specific sensor ID, and delete it.
"""

import datetime as dt
import io
import json
import logging
import os
import random
import time
import zipfile

# Third-party imports
import boto3
from botocore.exceptions import ClientError
from ratelimiter import RateLimiter

# Local imports
from ...utils.config import PATHS, AWS

logger = logging.getLogger(__name__)


def exponential_retry(func, error_code, *func_args, **func_kwargs):
    """
    Retries the specified function with a simple exponential backoff algorithm.
    This is necessary when AWS is not yet ready to perform an action because all
    resources have not been fully deployed.

    :param func: The function to retry.
    :param error_code: The error code to retry. Other errors are raised again.
    :param func_args: The positional arguments to pass to the function.
    :param func_kwargs: The keyword arguments to pass to the function.
    :return: The return value of the retried function.
    """
    sleepy_time = 1
    func_return = None
    while sleepy_time < 33 and func_return is None:
        try:
            func_return = func(*func_args, **func_kwargs)
            logger.info("Ran %s, got %s.", func.__name__, func_return)
        except ClientError as error:
            if error.response['Error']['Code'] == error_code:
                print(f"Sleeping for {sleepy_time} to give AWS time to "
                      f"connect resources.")
                time.sleep(sleepy_time)
                sleepy_time = sleepy_time*2
            else:
                raise
    return func_return


def create_lambda_deployment_package(function_file_name):
    """
    Creates a Lambda deployment package in ZIP format in an in-memory buffer. This
    buffer can be passed directly to AWS Lambda when creating the function.

    :param function_file_name: The name of the file that contains the Lambda handler
                               function.
    :return: The deployment package.
    """
    cwd = os.getcwd()
    os.chdir(PATHS.code / 'build' / 'aws')
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as zipped:
        zipped.write(function_file_name)
    buffer.seek(0)
    os.chdir(cwd)
    return buffer.read()


def create_iam_role_for_lambda(iam_resource, iam_role_name, bucket_arn):
    """
    Creates an AWS Identity and Access Management (IAM) role that grants the
    AWS Lambda function basic permission to run S3 bucket reads and writes.
    If a role with the specified name already exists, it is used.

    :param iam_resource: The Boto3 IAM resource object.
    :param iam_role_name: The name of the role to create.
    :return: The newly created role.
    """
    lambda_assume_role_policy = {
        'Version': '2012-10-17',
        'Statement': [
            {
                'Effect': 'Allow',
                'Principal': {
                    'Service': 'lambda.amazonaws.com'
                },
                'Action': 'sts:AssumeRole'
            }
        ]
    }
    s3_permissions_policy_doc = {
        "Version": "2012-10-17",
        "Statement": {
            "Effect": "Allow",
            "Action": "s3:PutObject",
            "Resource": bucket_arn
        }
    }

    policy_arn = 'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
    # policy_arn = 'arn:aws:iam::aws:policy/service-role/AmazonS3ObjectLambdaExecutionRolePolicy'

    # TODO: find policy ARN that can be applied to lambda functions allowing them
    #   to write to S3 buckets

    try:
        role = iam_resource.create_role(
            RoleName=iam_role_name,
            AssumeRolePolicyDocument=json.dumps(lambda_assume_role_policy))
        logger.info("Created role %s.", role.name)

        role.attach_policy(PolicyArn=policy_arn)
        logger.info("Attached basic execution policy to role %s.", role.name)

        # Create and attach S3 policy
        s3_policy = iam_resource.create_policy(
            PolicyName='myS3PutPolicy',
            PolicyDocument=json.dumps(s3_permissions_policy_doc)
        )
        role.attach_policy(PolicyArn=s3_policy.arn)
        logger.info(f"Attached {s3_policy.policy_name} policy to role {role.name}.")

        logger.info(f"Waiting for modified role to be available...")
        iam_resource.meta.client.get_waiter('policy_exists').wait(PolicyArn=s3_policy.arn)
    except ClientError as error:
        if error.response['Error']['Code'] == 'EntityAlreadyExists':
            role = iam_resource.Role(iam_role_name)
            logger.warning("The role %s already exists. Using it.", iam_role_name)
        else:
            logger.exception(
                "Couldn't create role %s or attach policy %s.",
                iam_role_name, policy_arn)
            raise

    return role


def deploy_lambda_function(
        lambda_client, function_name, handler_name, iam_role, deployment_package):
    """
    Deploys the AWS Lambda function.

    :param lambda_client: The Boto3 AWS Lambda client object.
    :param function_name: The name of the AWS Lambda function.
    :param handler_name: The fully qualified name of the handler function. This
                         must include the file name and the function name.
    :param iam_role: The IAM role to use for the function.
    :param deployment_package: The deployment package that contains the function
                               code in ZIP format.
    :return: The Amazon Resource Name (ARN) of the newly created function.
    """
    try:
        response = lambda_client.create_function(
            FunctionName=function_name,
            Description="AWS Lambda demo for S3",
            Runtime='python3.7',
            Role=iam_role.arn,
            Handler=handler_name,
            Code={'ZipFile': deployment_package},
            Publish=True)
        function_arn = response['FunctionArn']
        logger.info("Created function '%s' with ARN: '%s'.",
                    function_name, response['FunctionArn'])
    except ClientError:
        logger.exception("Couldn't create function %s.", function_name)
        raise
    else:
        return function_arn


def delete_lambda_function(lambda_client, function_name):
    """
    Deletes an AWS Lambda function.

    :param lambda_client: The Boto3 AWS Lambda client object.
    :param function_name: The name of the function to delete.
    """
    try:
        lambda_client.delete_function(FunctionName=function_name)
    except ClientError:
        logger.exception("Couldn't delete function %s.", function_name)
        raise


def delete_policy(iam_resource, policy_arn):
    """
    Deletes a policy.

    :param iam_resource: The boto3 IAM resource used to create the policy.
    :param policy_arn: The ARN of the policy to delete.
    """
    try:
        iam_resource.Policy(policy_arn).delete()
        logger.info("Deleted policy %s.", policy_arn)
    except ClientError:
        logger.exception("Couldn't delete policy %s.", policy_arn)
        raise


def invoke_lambda_function(lambda_client, function_name, function_params):
    """
    Invokes an AWS Lambda function.

    :param lambda_client: The Boto3 AWS Lambda client object.
    :param function_name: The name of the function to invoke.
    :param function_params: The parameters of the function as a dict. This dict
                            is serialized to JSON before it is sent to AWS Lambda.
    :return: The response from the function invocation.
    """
    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            Payload=json.dumps(function_params).encode())
        logger.info("Invoked function %s.", function_name)
    except ClientError:
        logger.exception("Couldn't invoke function %s.", function_name)
        raise
    return response


@RateLimiter(max_calls=1, period=1)
def start_lambda(lambda_params,
                 lambda_client,
                 lambda_function_name,
                 lambda_handler_name,
                 iam_role,
                 deployment_package):
    """"""
    logger.info(f"Deploying sensor-specific lambda function for sensor "
                f"{lambda_params['sensor_id']}")

    # Keep trying to create the function until the role is available
    exponential_retry(
        deploy_lambda_function, 'InvalidParameterValueException',
        lambda_client, lambda_function_name, lambda_handler_name, iam_role,
        deployment_package)

    # Wait to make sure the function is active
    (lambda_client
     .get_waiter('function_active')
     .wait(FunctionName=lambda_function_name))

    # Run the function!
    logger.info(f"Directly invoking function {lambda_function_name}")
    response = invoke_lambda_function(lambda_client,
                                      lambda_function_name,
                                      lambda_params)
    result = json.load(response['Payload'])['result']
    print(f"Downloading and saving of sensor {lambda_params['sensor_id']} resulted in {result}")


def lambda_series(sensor_tuples):
    """Start a lambda function for each id in id_list

    For each id in id_list, start a uniquely-named function
    @param sensor_tuples: list of tuples:
        [0] Purple Air sensor id to download data for,
        [1]
    """
    lambda_function_filename = 'lambda_download_script.py'  #
    lambda_handler_name = 'lambda_download_script.lambda_ip_s3_writer'
    lambda_role_name = 'demo-lambda-role-S3-ip-upload'

    # Create AWS IAM resource instance
    iam_resource = boto3.resource('iam',
                                  aws_access_key_id=AWS.access_key,
                                  aws_secret_access_key=AWS.secret_key)

    # Create AWS Lambda client instance
    lambda_client = boto3.client('lambda',
                                 region_name=AWS.region,
                                 aws_access_key_id=AWS.access_key,
                                 aws_secret_access_key=AWS.secret_key)

    # Create deployment package (lambda function code)
    print(f"Creating generic AWS Lambda function from the "
          f"{lambda_handler_name} function in {lambda_function_filename}...")
    deployment_package = create_lambda_deployment_package(lambda_function_filename)

    # Create AWS IAM Role (permissions to be given to lambda function)
    iam_role = create_iam_role_for_lambda(iam_resource, lambda_role_name, AWS.bucket_arn)

    try:
        # Deploy a new Lambda function for each id
        for sensor_tuple in sensor_tuples:
            lambda_params = {'sensor_id': sensor_tuple[0],
                             'bucket_name': AWS.bucket_name,
                             'date_created': dt.datetime.utcfromtimestamp(sensor_tuple[1]).strftime('%Y-%m-%d'),
                             'last_modified': dt.datetime.utcfromtimestamp(sensor_tuple[2]).strftime('%Y-%m-%d')}
            lambda_function_name = f'PA_download_{lambda_params["sensor_id"]}'
            start_lambda(lambda_params,
                         lambda_client,
                         lambda_function_name,
                         lambda_handler_name,
                         iam_role,
                         deployment_package)

    finally:
        for policy in iam_role.attached_policies.all():
            policy.detach_role(RoleName=iam_role.name)
            if policy.policy_name == 'myS3PutPolicy':
                delete_policy(iam_resource, policy.arn)
        iam_role.delete()
        logger.info(f"Deleted role {lambda_role_name}.")
        delete_lambda_function(lambda_client, lambda_function_name)
        logger.info(f"Deleted function {lambda_function_name}.")


def save_pa_data_to_s3():
    sensors = [25999, 26003, 26005, 26011, 26013]
    date_created_list = [1632955574, 1632955612, 1632955594, 1446763462, 1632955644]
    last_modified_list = [1635632829, 1634149424, 1634410114, 1633665195, 1635632829]
    sensor_tuples = zip(sensors, date_created_list, last_modified_list)

    lambda_series(sensor_tuples)


def usage_demo():
    """Shows how to create, invoke, and delete an AWS Lambda function.

    from: https://docs.aws.amazon.com/code-samples/latest/catalog/python-lambda-lambda_basics.py.html
    """
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    print('-'*88)
    print("Welcome to the AWS Lambda demo for S3 bucket writes.")
    print('-'*88)

    lambda_function_filename = 'lambda_download_script.py'  #
    lambda_handler_name = 'lambda_download_script.lambda_ip_s3_writer'
    lambda_role_name = 'demo-lambda-role-S3-ip-upload'
    lambda_function_name = 'demo-lambda-function-s3'

    iam_resource = boto3.resource('iam',
                                  aws_access_key_id=AWS.access_key,
                                  aws_secret_access_key=AWS.secret_key)
    lambda_client = boto3.client('lambda',
                                 region_name=AWS.region,
                                 aws_access_key_id=AWS.access_key,
                                 aws_secret_access_key=AWS.secret_key)

    print(f"Creating AWS Lambda function {lambda_function_name} from the "
          f"{lambda_handler_name} function in {lambda_function_filename}...")
    deployment_package = create_lambda_deployment_package(lambda_function_filename)
    iam_role = create_iam_role_for_lambda(iam_resource, lambda_role_name, AWS.bucket_arn)
    # Could use PutFunctionConcurrency to set concurrency to 1 if there are IP issues
    # put lambda_client instantiation inside for loop to create new for each sensor
    exponential_retry(
        deploy_lambda_function, 'InvalidParameterValueException',
        lambda_client, lambda_function_name, lambda_handler_name, iam_role,
        deployment_package)
    # Wait to make sure the function is active
    lambda_client.get_waiter('function_active').wait(FunctionName=lambda_function_name)


    try:
        print(f"Directly invoking function {lambda_function_name} a few times...")
        sensors = [25999, 26003, 26005, 26011, 26013]
        date_created_list = [1632955574, 1632955612, 1632955594, 1446763462, 1632955644]
        last_modified_list = [1635632829, 1634149424, 1634410114, 1633665195, 1635632829]

        # id_, date_created, last_modified = 25999, 1632955574, 1635632829
        # lambda_params = {'sensor_id': id_,
        #                  'bucket_arn': AWS.bucket_arn,
        #                  'bucket_name': AWS.bucket_name,
        #                  'date_created': dt.datetime.utcfromtimestamp(date_created).strftime('%Y-%m-%d'),
        #                  'last_modified': dt.datetime.utcfromtimestamp(last_modified).strftime('%Y-%m-%d')}
        # response = invoke_lambda_function(
        #     lambda_client, lambda_function_name, lambda_params)
        # result = json.load(response['Payload'])['result']
        # print(f"Downloading and saving of sensor {id_} resulted in {result}")

        for id_, date_created, last_modified in zip(sensors, date_created_list, last_modified_list):
            lambda_params = {'sensor_id': id_,
                             'bucket_name': AWS.bucket_name,
                             'date_created': dt.datetime.utcfromtimestamp(date_created).strftime('%Y-%m-%d'),
                             'last_modified': dt.datetime.utcfromtimestamp(last_modified).strftime('%Y-%m-%d')}
            response = invoke_lambda_function(
                lambda_client, lambda_function_name, lambda_params)
            result = json.load(response['Payload'])['result']
            print(f"Downloading and saving of sensor {id_} resulted in {result}")

    finally:
        for policy in iam_role.attached_policies.all():
            policy.detach_role(RoleName=iam_role.name)
            if policy.policy_name == 'myS3PutPolicy':
                delete_policy(iam_resource, policy.arn)
        iam_role.delete()
        logger.info(f"Deleted role {lambda_role_name}.")
        delete_lambda_function(lambda_client, lambda_function_name)
        logger.info(f"Deleted function {lambda_function_name}.")
    print("Thanks for watching!")


if __name__ == '__main__':
    usage_demo()























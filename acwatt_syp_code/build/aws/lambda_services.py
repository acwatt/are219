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
import pandas as pd
import requests
import time
import zipfile
import threading
from multiprocessing.pool import ThreadPool

# Third-party imports
import boto3
from botocore import config as botocore_config
from botocore.exceptions import ClientError
from ratelimiter import RateLimiter

# Local imports
from ...utils.config import PATHS, AWS, PA

logger = logging.getLogger(__name__)
WRITE_LOCK = threading.Lock()
PRINT_LOCK = threading.Lock()
LAMBDA_LOCK = threading.Lock()


def exponential_retry(func, error_code, *func_args, **func_kwargs):
    """
    Retries the specified function with a simple exponential backoff algorithm.
    This is necessary when AWS is not yet ready to perform an action because all
    resources have not been fully deployed.

    @param func: The function to retry.
    @param error_code: The error code to retry. Other errors are raised again.
    @param func_args: The positional arguments to pass to the function.
    @param func_kwargs: The keyword arguments to pass to the function.
    @return: The return value of the retried function.
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

    @param function_file_name: The name of the file that contains the Lambda handler
                               function.
    @return: The deployment package.
    """
    cwd = os.getcwd()
    os.chdir(PATHS.code / 'build' / 'aws')
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as zipped:
        zipped.write(function_file_name)
    buffer.seek(0)
    os.chdir(cwd)
    return buffer.read()


def get_package_arn(package_name):
    """Use klayers API to get AWS lambda layer ARN of latest package (e.g. pandas)"""
    endpoint = f'https://api.klayers.cloud/api/v1/layers/latest/us-west-1/{package_name}'
    response = requests.get(endpoint, verify=True)
    data = response.json()
    return data['arn']


def add_package_layers(function_name, lambda_client, package_name_list):
    """Add a python package layer to the function for each package in list.

    Use Klayers GitHub that hosts updated python-package lambda layers,
        get ARN's for the most recent layers and update lambda function with
        the layers corresponding to each ARN.
    https://github.com/keithrozario/Klayers
    @param function_name: str, name of lambda function to attach layers to
    @param lambda_client: AWS lambda boto3.client used to create function
    @param package_name_list: list of str's, names of packages (e.g. 'pandas')
    """
    print(f'Updating function {function_name} with package layers: {", ".join(package_name_list)}')
    package_arn_list = [get_package_arn(package) for package in package_name_list]
    lambda_client.update_function_configuration(FunctionName=function_name,
                                                Layers=package_arn_list)

    def updating():
        config = lambda_client.get_function_configuration(FunctionName=function_name)
        return config['LastUpdateStatus'] != 'Successful'

    while updating():
        print('*', end='')
        time.sleep(1)
    print(f'Function updated with package layers.')


def create_iam_role_for_lambda(iam_resource, iam_role_name, bucket_arn):
    """
    Creates an AWS Identity and Access Management (IAM) role that grants the
    AWS Lambda function basic permission to run S3 bucket reads and writes.
    If a role with the specified name already exists, it is used.

    @param iam_resource: The Boto3 IAM resource object.
    @param iam_role_name: The name of the role to create.
    @param bucket_arn: str, Amazon Resource Name (ARN) of the bucket that the
        lambda function will save data to.
    @return: The newly created role.
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

    def create_role():
        role_ = iam_resource.create_role(
            RoleName=iam_role_name,
            AssumeRolePolicyDocument=json.dumps(lambda_assume_role_policy))
        logger.info("Created role %s.", role_.name)

        role_.attach_policy(PolicyArn=policy_arn)
        logger.info("Attached basic execution policy to role %s.", role_.name)

        # Create and attach S3 policy
        s3_policy = iam_resource.create_policy(
            PolicyName='myS3PutPolicy',
            PolicyDocument=json.dumps(s3_permissions_policy_doc)
        )
        role_.attach_policy(PolicyArn=s3_policy.arn)
        logger.info(f"Attached {s3_policy.policy_name} policy to role {role_.name}.")

        logger.info(f"Waiting for modified role to be available...")
        iam_resource.meta.client.get_waiter('policy_exists').wait(PolicyArn=s3_policy.arn)
        return role_

    try:
        role = create_role()

    except ClientError as error:
        if error.response['Error']['Code'] == 'EntityAlreadyExists':
            role = iam_resource.Role(iam_role_name)
            logger.warning("The role %s already exists. Deleting it.", iam_role_name)
            # Delete
            for policy in role.attached_policies.all():
                policy.detach_role(RoleName=role.name)
                if policy.policy_name == 'myS3PutPolicy':
                    delete_policy(iam_resource, policy.arn)
            role.delete()
            # Wait for it to be deleted
            # create new
            role = create_role()
        else:
            logger.exception(
                "Couldn't create role %s or attach policy %s.",
                iam_role_name, policy_arn)
            raise

    return role


def deploy_lambda_function(aws_objects, function_name):
    """
    Deploys the AWS Lambda function.

    @param aws_objects: dict of AWS objects:
        - lambda_client: The Boto3 AWS Lambda client object.
        - iam_role: The IAM role to use for the function.
        - deployment_package: The deployment package that contains the function
                               code in ZIP format.
    @param function_name: The name of the AWS Lambda function.
    @param handler_name: The fully qualified name of the handler function. This
                         must include the file name and the function name.
    @return function_arn: str, The Amazon Resource Name (ARN) of the newly
        created function.
    """

    def create_function():
        response = aws_objects['lambda_client'].create_function(
            FunctionName=function_name,
            Description="AWS Lambda demo for S3",
            Runtime=f'python{AWS.python_version}',
            Role=aws_objects['iam_role'].arn,
            Handler=aws_objects['lambda_handler_name'],
            Code={'ZipFile': aws_objects['deployment_package']},
            Publish=True,
            Timeout=900,
            MemorySize=1000)
        return response['FunctionArn']

    try:
        function_arn = create_function()
        logger.info("Created function '%s' with ARN: '%s'.",
                    function_name, function_arn)
    except ClientError as error:
        logger.exception("Couldn't create function %s.", function_name)
        if error.response['Error']['Code'] == "ResourceConflictException":
            logger.exception(f"Function {function_name} already exists; "
                             f"deleting and creating new. Sleeping 10 sec.")
            delete_lambda_function(aws_objects['lambda_client'], function_name)
            time.sleep(20)
            function_arn = create_function()
            logger.info("Created function '%s' with ARN: '%s'.",
                        function_name, function_arn)
        else:
            raise
    else:
        return function_arn


def delete_lambda_function(lambda_client, function_name):
    """
    Deletes an AWS Lambda function.

    @param lambda_client: The Boto3 AWS Lambda client object.
    @param function_name: The name of the function to delete.
    """
    try:
        lambda_client.delete_function(FunctionName=function_name)
    except ClientError:
        logger.exception("Couldn't delete function %s.", function_name)
        raise


def delete_policy(iam_resource, policy_arn):
    """
    Deletes a policy.

    @param iam_resource: The boto3 IAM resource used to create the policy.
    @param policy_arn: The ARN of the policy to delete.
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

    @param lambda_client: The Boto3 AWS Lambda client object.
    @param function_name: The name of the function to invoke.
    @param function_params: The parameters of the function as a dict. This dict
                            is serialized to JSON before it is sent to AWS Lambda.
    @return: The response from the function invocation.
    """
    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            Payload=json.dumps(function_params).encode(),
        )
        with WRITE_LOCK:
            logger.info(f"Invoked function {function_name} for {function_params['sensor_id']}.")
    except ClientError:
        with WRITE_LOCK:
            logger.exception("Couldn't invoke function %s.", function_name)
        raise
    return response


@RateLimiter(max_calls=1, period=1)
def start_lambda(aws_objects,
                 lambda_params,
                 lambda_function_name):
    """"""
    create_function(lambda_function_name, aws_objects)
    run_function(lambda_function_name, aws_objects, lambda_params)


def create_function(lambda_function_name, aws_objects, concurrency=200):
    logger.info(f"Deploying lambda function {lambda_function_name}")

    # Keep trying to create the function until the role is available
    exponential_retry(
        deploy_lambda_function, 'InvalidParameterValueException',
        aws_objects, lambda_function_name)

    # Wait to make sure the function is active
    lambda_client = aws_objects['lambda_client']
    (lambda_client
     .get_waiter('function_active')
     .wait(FunctionName=lambda_function_name))

    # Add concurrency (# of parallel instances)
    response = lambda_client.put_function_concurrency(
        FunctionName=lambda_function_name,
        ReservedConcurrentExecutions=concurrency
    )

    # Add dependencies (package layers to make the code runable)
    package_name_list = ['numpy', 'pandas', 'requests']
    add_package_layers(lambda_function_name, lambda_client, package_name_list)


@RateLimiter(max_calls=1, period=0.2)
def run_function(lambda_function_name, aws_objects, lambda_params):
    # Run the function!
    time1 = dt.datetime.now()
    with PRINT_LOCK:
        print(f"Starting {lambda_params['sensor_id'] :07d} download")
    with LAMBDA_LOCK:
        response = invoke_lambda_function(aws_objects['lambda_client'],
                                      lambda_function_name,
                                      lambda_params)
    result = json.load(response['Payload'])
    sensor_id = result['sensor_id']
    successful = result['successful']
    with PRINT_LOCK:
        print(f"Downloading and saving of sensor {sensor_id} resulted in these weeks being downloaded:\n {successful}")
    time_taken = dt.datetime.now() - time1
    save_success(sensor_id, time_taken)
    return result


def setup_aws_objects(function_filename, role_name):
    config = botocore_config.Config(
        read_timeout=900,
        connect_timeout=900,
        retries={"max_attempts": 0}
    )

    # Create AWS IAM resource instance
    iam_resource = boto3.resource('iam',
                                  aws_access_key_id=AWS.access_key,
                                  aws_secret_access_key=AWS.secret_key)

    # Create AWS Lambda client instance
    lambda_client = boto3.client('lambda',
                                 region_name=AWS.region,
                                 aws_access_key_id=AWS.access_key,
                                 aws_secret_access_key=AWS.secret_key,
                                 config=config)

    # Create deployment package (lambda function code)
    print(f"Creating generic AWS Lambda function from {function_filename}.")
    deployment_package = create_lambda_deployment_package(function_filename)

    # Create AWS IAM Role (permissions to be given to lambda function)
    iam_role = create_iam_role_for_lambda(iam_resource, role_name, AWS.bucket_arn)
    print('Sleeping for 10 to let the role propagate'); time.sleep(10);
    aws_objects = {'iam_resource': iam_resource,
                   'lambda_client': lambda_client,
                   'deployment_package': deployment_package,
                   'iam_role': iam_role}
    return aws_objects


def teardown_aws_objects(aws_objects, function_list):
    # Delete all roles
    iam_role = aws_objects['iam_role']
    for policy in iam_role.attached_policies.all():
        policy.detach_role(RoleName=iam_role.name)
        if policy.policy_name == 'myS3PutPolicy':
            delete_policy(aws_objects['iam_resource'], policy.arn)
    iam_role.delete()
    logger.info(f"Deleted role {iam_role.name}.")

    # Delete all functions
    for function in function_list:
        try:
            delete_lambda_function(aws_objects['lambda_client'], function)
            logger.info(f"Deleted function {function}.")
            print(f"deleted {function}")
        except ClientError as error:
            if error.response['Error']['Code'] == 'ResourceNotFoundException':
                print(f"{function} already deleted.")
            else:
                raise


def save_success(sensor_id, time_taken):
    filepath = PATHS.data.purpleair / 'sensors_downloaded.csv'
    df = pd.DataFrame({'sensor_id': sensor_id, 'time_taken': time_taken},
                      index=[sensor_id])
    try:
        # If another thread is writing, we may read an empty file. Better lock it.
        with WRITE_LOCK:
            df_old = pd.read_csv(filepath)
        df = pd.concat([df_old, df])
    except FileNotFoundError:
        pass
    with WRITE_LOCK:
        df.to_csv(filepath, index=False)


def start_function(sensor_tuple, aws_objects):
    sensor_id, date_created, last_modified = sensor_tuple
    lambda_params = {'sensor_id': sensor_id,
                     'bucket_name': AWS.bucket_name,
                     'date_created': dt.datetime.utcfromtimestamp(date_created).strftime('%Y-%m-%d'),
                     'last_modified': dt.datetime.utcfromtimestamp(last_modified).strftime('%Y-%m-%d'),
                     'PA_api_key': PA.read_key}
    lambda_function_name = f'PA_download_{sensor_id:07d}'
    start_lambda(aws_objects,
                 lambda_params,
                 lambda_function_name)
    print('SUCCESS:', lambda_function_name)
    return lambda_function_name


def lambda_series(sensor_tuples, max_threads: int = 10):
    """Start a lambda function for each id in id_list

    For each id in id_list, start a uniquely-named function
    @param sensor_tuples: list of tuples:
        [0] Purple Air sensor id to download data for,
        [1]
    @param max_threads: max number of parallel processes to run
    """
    # Setup AWS objects
    lambda_function_filename = 'lambda_download_script.py'
    lambda_function_filename = 'lambda_timing_test_script.py'
    lambda_role_name = 'demo-lambda-role-S3-ip-upload'
    aws_objects = setup_aws_objects(lambda_function_filename, lambda_role_name)
    aws_objects['lambda_handler_name'] = 'lambda_download_script.lambda_ip_s3_writer'
    aws_objects['lambda_handler_name'] = 'lambda_timing_test_script.time_test'

    # Deploy a new Lambda function for each id
    function_list = []
    for s in sensor_tuples:
        function_list.append(start_function(s, aws_objects))
    # function_list = [f'PA_download_{s}' for s, _, _ in sensor_tuples]

    # Delete all roles and functions
    teardown_aws_objects(aws_objects, function_list)


def save_pa_data_to_s3(sensor_tuple):

    sensors = [25999, 26003, 26005, 26011, 26013]
    date_created_list = [1632955574, 1632955612, 1632955594, 1446763462, 1632955644]
    last_modified_list = [1635632829, 1634149424, 1634410114, 1633665195, 1635632829]
    sensor_tuples = [t for t in zip(sensors, date_created_list, last_modified_list)]
    lambda_series(sensor_tuples)
    print('DONE WITH SAVING PURPLE AIR DATA')


"""
NOTES:


- Update lambda_download_script to download-upload actual PA data for a sensor
- Test full download on 5 sensors
- Split full list of sensors into 100 bins
- Start 100 functions and pass bin of sensors to each



"""


################################################################################
# ARCHIVE
################################################################################
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






















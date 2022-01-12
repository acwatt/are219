# Steps to setup S3

1. Create an AWS console account.
2. [Create an AWS IAM user on the account.](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_users_create.html#id_users_create_console) Give it "Access key - Programmatic access". Save the user access key ID and secret access key.
3. Create a private S3 bucket and save the S3 bucket name and access codes
4. Save credentials on computer as in `Setting up an IAM user for s3 buckets` below.


Currently on step 3



# S3 buckets
S3 buckets are for storing information (and can be used in many ways). For the skybees project, we are using an S3 bucket to host the images we download from Google Earth. We will be using an HTTP RESTful API to push and pull images from the bucket.

## Bucket url
https://skybees.s3.us-west-2.amazonaws.com/images/example_image.JPG

## Setting up an IAM user for s3 buckets
See https://docs.aws.amazon.com/IAM/latest/UserGuide/id_users_create.html#id_users_create_console
We want to set up an IAM user (currently the skybees user) and give that user AmazonS3FullAccess policy
rights to access all s3 buckets. Then, follow the instructions above to copy the Access key ID and Secret access key
to the `~/.aws/credentials` file on your computer. Then the below code should be able to access the s3 buckets.

## Pulling data from the bucket
We can use the following code to download a CSV from a folder in the S3 bucket into a save folder:
```python
import boto3
s3 = boto3.client('s3')
# BUCKET_NAME = 'skybees'
# OBJECT_NAME = file path / name of file in the bucket
# FILE_PATH = local file on computer to save the object to
s3.download_file('BUCKET_NAME', 'OBJECT_NAME', 'FILE_PATH')
```

If I wanted to download a file into an object instead of writing to disk, I could [do this:](https://stackoverflow.com/a/37087998/16660792)
```python
import pandas as pd
from io import StringIO
from boto.s3.connection import S3Connection

AWS_KEY = 'XXXXXXDDDDDD'
AWS_SECRET = 'pweqory83743rywiuedq'
aws_connection = S3Connection(AWS_KEY, AWS_SECRET)
bucket = aws_connection.get_bucket('YOUR_BUCKET')

fileName = "test.csv"

content = bucket.get_key(fileName).get_contents_as_string()
reader = pd.read_csv(StringIO.StringIO(content))
```


## Pushing data to the bucket

Say we have a CSV `00001.csv` in the `downloads` directory that we want to upload to the `PA_sensor_CSVs` folder in the
S3 bucket named `purpleair_data`. To upload using the RESTful API, we will use a PUT request We can upload using this
code:

```python
import logging
import boto3
from botocore.exceptions import ClientError
import os


def upload_file(file_path, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_path: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_path)

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(file_path, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True


# Upload the CSV
upload_file('downloads/00001.csv', 'purpleair_data')
```



If I 
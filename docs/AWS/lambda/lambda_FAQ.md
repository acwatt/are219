# Random questions I needed answers to for the lambda AWS service

## Can lambda us python?

Lambda natively supports Java, Go, PowerShell, Node.js, C#, Python, and Ruby
code, and provides a Runtime API allowing you to use any additional programming
languages to author your
functions. ([Features page](https://aws.amazon.com/lambda/features/))


## Can I get a different IP address when spawning multiple lambda instances?

When you redeploy the lambda it seems to use a new container. So you can
automate this deploy process using AWS CLI to get a new ip on command.
([Stack Exchange post](https://stackoverflow.com/a/65223847/16660792))


# What AWS permissions does the lambda process need?

- access to Amazon CloudWatch Logs (AWSLambdaBasicExecutionRole)
- S3 bucket permissions (AmazonS3ObjectLambdaExecutionRolePolicy,
  AWSLambdaExecute)
- Create IAM roles (IAMFullAccess iam:CreateRole)
- Create lambda function (AWSLambda_FullAccess)

## Need to get the lambda ARN

Amazon Resource
Names ([ARNs](https://docs.aws.amazon.com/general/latest/gr/aws-arns-and-namespaces.html))
uniquely identify AWS resources. We require an ARN when you need to specify a
resource unambiguously across all of AWS, such as in IAM policies, Amazon
Relational Database Service (Amazon RDS) tags, and API calls.

```shell
arn:partition:service:region:account-id:resource-id
arn:partition:service:region:account-id:resource-type/resource-id
arn:partition:service:region:account-id:resource-type:resource-id

partition = [aws](https://docs.aws.amazon.com/general/latest/gr/aws-arns-and-namespaces.html)
service = [lambda](https://docs.aws.amazon.com/service-authorization/latest/reference/list_awslambda.html)
region = [us-west-1](https://docs.aws.amazon.com/general/latest/gr/rande.html#regional-endpoints)
account-id = 675165489895


```

## Python code to create a lambda service

[Examples](https://docs.aws.amazon.com/code-samples/latest/catalog/python-lambda-lambda_basics.py.html)

[AWS Developer Guide](https://github.com/awsdocs/aws-lambda-developer-guide/blob/main/doc_source/index.md#aws-lambda-developer-guide)

[AWS Python doc for lambda create_function()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/lambda.html#Lambda.Client.create_function)
See [Examples](https://docs.aws.amazon.com/code-samples/latest/catalog/python-lambda-lambda_basics.py.html)
for how to create a zip file in memory






# Steps to reproduce lambda function calls:

1. Create an AWS console account
2. Create a group policy with the permissions listed above
3. Create an IAM role with programmatic permissions belonging to above group.
   Save the access key ID and the secret access key (but don't put it into 
   the code).
4. Save the access key ID and secret access key to the OS keyring using the 
   method outlined in `docs/miscellaneous/secure_passwords.md`.
5. Create python script (like `lambda_download_script.py`) that you want to run 
   inside each lambda call that takes as input a dictionary of parameters.
6. Create controller script (like `build.aws.lambda_services.usage_demo()`) that:
  - creates IAM resource and lambda client using the access key ID and 
    secret key saved to the OS keyring
  - deploys the lambda function
  - creates a dictionary of parameters for  the python code to be run
  - invokes the lambda function, passing the dictionary to the invoke code
  - detatches the iam_role policies
  - deletes the iam role
  - deletes the lambda function


# Troubleshooting lambda functions:
1. Getting "Access Denied" when the lambda function tries to save to S3. 
  - manually deleting the S3 policy on the AWS console resolves the issue. 
    Which probably indicates that the policy was not properly deleted or 
    attached at the end of the previous run.

# Random questions I needed answers to for the lambda AWS service

## Can lambda us python?

Lambda natively supports Java, Go, PowerShell, Node.js, C#, Python, and Ruby code, and provides a Runtime API allowing you to use any additional programming languages to author your functions. ([Features page](https://aws.amazon.com/lambda/features/))


## Can I get a different IP address when spawning multiple lambda instances?

When you redeploy the lambda it seems to use a new container. So you can automate this deploy process using AWS CLI to
get a new ip on command.
([Stack Exchange post](https://stackoverflow.com/a/65223847/16660792))


# What AWS permissions does the lambda process need?

- access to Amazon CloudWatch Logs (AWSLambdaBasicExecutionRole)
- S3 bucket permissions (AmazonS3ObjectLambdaExecutionRolePolicy, AWSLambdaExecute)


## Need to get the lambda ARN

Amazon Resource Names ([ARNs](https://docs.aws.amazon.com/general/latest/gr/aws-arns-and-namespaces.html)) uniquely
identify AWS resources. We require an ARN when you need to specify a resource unambiguously across all of AWS, such as
in IAM policies, Amazon Relational Database Service (Amazon RDS) tags, and API calls.

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
See [Examples](https://docs.aws.amazon.com/code-samples/latest/catalog/python-lambda-lambda_basics.py.html) for how to
create a zip file in memory







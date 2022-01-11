# Random questions I needed answers to for the lambda AWS service

## Can lambda us python?

Lambda natively supports Java, Go, PowerShell, Node.js, C#, Python, and Ruby code, and provides a Runtime API allowing you to use any additional programming languages to author your functions. ([Features page](https://aws.amazon.com/lambda/features/))


## Can I get a different IP address when spawning multiple lambda instances?

When you redeploy the lambda it seems to use a new container. So you can automate this deploy process using awscli to get a new ip on command.
([Stack Exchange post](https://stackoverflow.com/a/65223847/16660792))


# What AWS permissions does the lambda process need?

- access to Amazon CloudWatch Logs (AWSLambdaBasicExecutionRole)
- S3 bucket permissions (AmazonS3ObjectLambdaExecutionRolePolicy, AWSLambdaExecute)


# Manage access controls in GenAI-powered search applications using Amazon OpenSearch and AWS Cognito
This code sample illustrates how to build a document searching RAG solutions that ensure that only authorized users can access and interact with specific documents based on their roles, departments, and other relevant attributes. It combines Amazon Opensearch Service and Amazon Cognito custom attributes to make a tag based access control mechanism that makes it simple to manage at scale. 

![doc/arch.png](doc/arch.png)


## Pre-requisites
Before installing this sample, make sure you have following installed:

1. [AWS CLI](https://aws.amazon.com/cli/)  
2. [Docker](https://docs.docker.com/get-docker/) 
3. [NodeJS](https://nodejs.org/en/) 
4. [AWS CDK v2](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html#getting_started_install) 
5. [Configure your AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html) 
6. [Bootstrap AWS CDK in your target account](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html#getting_started_bootstrap) 
7. In case of LLM inference based on Amazon SageMaker, a sufficient service limit to deploy an ml.g5.12xlarge instance for the SageMaker endpoint. If needed, you can initiate a quota increase request. Refer to Service Quotas for more details.

## Deploy the AWS resources:
We will use AWS CDK to deploy the architecture described above. CDK allows defining the Infrastructure through a familiar programming language such as Python

1. Clone the repo from Github:

```
git clone https://github.com/aws-samples/manage-access-control-in-generative-ai-powered-search-applications.git
cd manage-access-control-in-generative-ai-powered-search-applications
```

2. Adjust the AWS Region where the stack will be deployed in, by setting the following environment variable:

``` 
export AWS_REGION=<<Your region name>>
```

3. Add the AWS CLI credentials to your terminal session, refer to [this manual](https://docs.aws.amazon.com/cli/v1/userguide/cli-chap-configure.html) for guidance on configuring the the AWS CLI

4. Use the following command to initiate a virtual environment and install the dependencies
```
python3 -m venv venv
source venv/bin/activate
make init
```


5. Refer to the [following manual](https://docs.aws.amazon.com/cdk/v2/guide/bootstrapping-env.html#bootstrapping-howto) for instructions on how to bootstrap the the AWS CDK:

```
> cdk bootstrap aws://<<ACCOUNT_ID>>/<<REGION>>
⏳ Bootstrapping environment aws://<acct#>/<region>... 
Trusted accounts for deployment: (none) 
Trusted accounts for lookup: (none) 
Using default execution policy of 
'arn:aws:iam::aws:policy/AdministratorAccess'. 
Pass '--cloudformation-execution-policies' to 
customize. ✅ Environment aws://<acct#>/<region> 
bootstrapped (no changes).
```

6.	Adjust the following environment variables in cdk-infrasrtructure/prod.env:
    1. CUSTOM_ATTRIBUTES with a comma separated string of attributes that will later on be used for users’ access control
    2. INDEX_NAME with the name of the OpenSearch index that will save your indexed data

7.	Create your own document dataset, similar to the mock dataset that we created in cdk-infrasrtructure/simple_rag_with_access_control/data/docs_os_rag_metadata_use_case.zip with the following instructions:
    1.	For every document, create one .txt file that contains the document parsed text and one .json file with the same name as the .txt file that contains as keys the CUSTOM_ATTRIBUTES from step 6.1 with their corresponding values
    2.	Compress all those files together to an output file
    3.	Copy and paste this file to the same location as our mock data
    4.	Optional, you can delete our mock data


8. Now use the command `make deploy-cdk` to deploy the whole stack to your AWS account

9. Go to AWS Console. Go to Amazon Bedrock console and on left menu, click on Model access:
    * On the Model access screen, click on top right button "Modify model access":
    * On model access screen, select Titan Text Embeddings V2 and Claude 3 models Haiku, and click on "Request model access" button


10.	Start ingesting your documents dataset created from setp 6 using the Data Ingestion Lambda:
    1.	 Navigate to the AWS Console → Lambda → RAGCdkStack-DataIngestionLambda-xyz. 
    2.	Create a Test Event and paste this [sample JSON](cdk-infrastructure/simple_rag_with_access_control/lambda/ingestion/sample_inputs/input.json) as an input. 
    3.	Modify the variable data_file_s3_path with the zip file name you created in step 7
    4.	Modify the variable index_name with the same index name as step 6.2
    5.	Press on Test


11.	Additionally, you can create mock users with different attributes attached to them. Take a look at the script cdk-infrasrtructure/create_test_users.sh and modify the mock users based on your custom attributes from step 6.1. You can then execute the script with the command:

``` 
make mock-users
```

This will add the corresponding users to your Cognito User pool, the associated usernames with their random generated passwords can be found in cdk-infrastructure/mock_users.txt


## Install frontend (in localhost)

1. Use the following command to run the frontend application locally
```
make install-run-local-frontend
```

You can then access the frontend application by opening a new tab in your browser and navigating to the URL http://localhost:5173/

## Install frontend (in Amplify hosting)

AWS Amplify Hosting enables a fully-managed deployment of the application's React frontend in an AWS-managed account using Amazon S3 and Amazon CloudFront. You can optionally run the React frontend locally by skipping to Deploy the application with AWS SAM.

To set up Amplify Hosting:

1. Fork this GitHub repository and take note of your repository URL, for example https://github.com/<<user-name>>/manage-access-control-in-generative-ai-powered-search-applications/.

2. Create a GitHub fine-grained access token for the new repository by following this guide. For the Repository permissions, select Read and write for Content and Webhooks.
https://docs.aws.amazon.com/amplify/latest/userguide/setting-up-GitHub-access.html#setting-up-github-app-cloudformation

Select the Plaintext tab and confirm your secret looks like this:
```
github_pat_T2wyo------------------------------------------------------------------------rs0Pp
```

3. Create a new secret called `FrontendGithubToken` in AWS Secrets Manager and input your fine-grained access token as plaintext. 

Deploy the amplify frontend:

1.	Open frontend/deploy.sh and put the github repository url in FRONTEND_REPOSITORY. It should be something like ‘https://github.com/<<user-name>>/manage-access-control-in-generative-ai-powered-search-applications/'
2.	Use the below command to deploy cloudformation template.
```
make install-amplify-frontend
```
3.	Go to AWS Management Console and search for AWS Amplify. Find the application with prefix ‘fgac-frondend-‘ and click ‘View app’. If the build does not start automatically, trigger it through the Amplify console.


## Cleanup
Run `make destroy` to cleanup all related resources in your account. 

## Security
This application was written for demonstration and educational purposes and not for production use. The [Security Pillar of the AWS Well-Architected Framework](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html)
can support you in further adopting the sample into a production deployment in addition to your own established processes.

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.


## License

This library is licensed under the MIT-0 License. See the LICENSE file.

**3rd party licences (see THIRD_PARTY_LICENSES):**  
This package depends on and may incorporate or retrieve a number of third-party
software packages (such as open source packages) at install-time or build-time
or run-time ("External Dependencies"). The External Dependencies are subject to
license terms that you must accept in order to use this package. If you do not
accept all of the applicable license terms, you should not use this package. We
recommend that you consult your company’s open source approval policy before
proceeding.

Provided below is a list of External Dependencies and the applicable license
identification as indicated by the documentation associated with the External
Dependencies as of Amazon's most recent review.

THIS INFORMATION IS PROVIDED FOR CONVENIENCE ONLY. AMAZON DOES NOT PROMISE THAT
THE LIST OR THE APPLICABLE TERMS AND CONDITIONS ARE COMPLETE, ACCURATE, OR
UP-TO-DATE, AND AMAZON WILL HAVE NO LIABILITY FOR ANY INACCURACIES. YOU SHOULD
CONSULT THE DOWNLOAD SITES FOR THE EXTERNAL DEPENDENCIES FOR THE MOST COMPLETE
AND UP-TO-DATE LICENSING INFORMATION.

YOUR USE OF THE EXTERNAL DEPENDENCIES IS AT YOUR SOLE RISK. IN NO EVENT WILL
AMAZON BE LIABLE FOR ANY DAMAGES, INCLUDING WITHOUT LIMITATION ANY DIRECT,
INDIRECT, CONSEQUENTIAL, SPECIAL, INCIDENTAL, OR PUNITIVE DAMAGES (INCLUDING
FOR ANY LOSS OF GOODWILL, BUSINESS INTERRUPTION, LOST PROFITS OR DATA, OR
COMPUTER FAILURE OR MALFUNCTION) ARISING FROM OR RELATING TO THE EXTERNAL
DEPENDENCIES, HOWEVER CAUSED AND REGARDLESS OF THE THEORY OF LIABILITY, EVEN
IF AMAZON HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES. THESE LIMITATIONS
AND DISCLAIMERS APPLY EXCEPT TO THE EXTENT PROHIBITED BY APPLICABLE LAW.


## Contributing

Refer to [CONTRIBUTING](./CONTRIBUTING.md) for more details on how to contribute to this project.


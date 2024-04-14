#!/usr/bin/env python3

import aws_cdk as core

from cdk_demo.cdk_demo_stack import CdkDemoStack
from cdk_demo.cdk_vpc_stack import CdkDemoStack_VPC
from cdk_demo.cdk_pipeline_stack import CdkDemoStack_Pipeline
from cdk_demo.cdk_lambda_stack import CdkDemoStack_lambda


app = core.App()

# Env Details
env_prod_us = core.Environment(account=app.node.try_get_context('prod')['account'],
                               region=app.node.try_get_context('prod')['region'])
#env_qa_us = cdk.Environment(account=app.node.try_get_context('qa')['account'],
#                             region=app.node.try_get_context('qa')['region'])

# CdkDemoStack(app, "CdkDemoStack-qa", env=env_qa_us,config="qa")
# CdkDemoStack_VPC(app,"CdkDemoVPCStack-qa",env=env_qa_us,config="qa")
# CdkDemoStack_Pipeline(app,"CdkDemoPipelineStack-qa",env=env_qa_us,config="qa")

CdkDemoStack_lambda(app, "CdkDemoLambdaStack-prod", env=env_prod_us,config="prod")
CdkDemoStack_VPC(app,"CdkDemoVPCStack-prod",env=env_prod_us,config="prod")
CdkDemoStack(app, "CdkDemoStack-prod", env=env_prod_us,config="prod")
CdkDemoStack_Pipeline(app,"CdkDemoPipelineStack-prod",env=env_prod_us,config="prod")


app.synth()

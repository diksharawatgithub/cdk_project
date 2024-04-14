from constructs import Construct
#from aws_cdk import core
from aws_cdk import aws_ec2 as ec2
from aws_cdk import (
    Duration,
    Stack,
    aws_iam as iam,
    aws_sqs as sqs,
    aws_sns as sns,
    aws_sns_subscriptions as subs,
)


class CdkDemoStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        env = kwargs["env"]
        config = kwargs["config"]
        #super().__init__(scope, construct_id, **kwargs)
        super().__init__(scope, construct_id,env=env)

        print("config is",config)
        print("env is",env)
        queue = sqs.Queue(
            self, "CdkDemoQueue",
            visibility_timeout=Duration.seconds(300),
        )

        topic = sns.Topic(
            self, "CdkDemoTopic"
        )

        topic.add_subscription(subs.SqsSubscription(queue))

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

import json


class CdkDemoStack_VPC(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        env = kwargs["env"]
        config = kwargs["config"]
        
        super().__init__(scope, id,env=env)       

        vpc_name = self.node.try_get_context(config)['vpc']['vpc_name']  # VPC Name
        vpc_cidr = self.node.try_get_context(config)['vpc']['vpc_cidr']  # VPC CIDR

        if config == "auto":
        # Creating VPC for staging enviroment
            self.vpc = ec2.Vpc(
                self,
                id=vpc_name,  # VPC Name
                cidr=vpc_cidr,  # CIDR
                #default_instance_tenancy=ec2.DefaultInstanceTenancy.DEFAULT,  # Instance Tenancy
                enable_dns_hostnames=self.node.try_get_context(config)['vpc']['enable_dns_hostnames'],  # Enable DNS Hostname #true #tobechanged
                enable_dns_support=self.node.try_get_context(config)['vpc']['enable_dns_support'],  # Enable DNS Support
                max_azs=self.node.try_get_context(config)['vpc']['max_azs'],  # Availability Zones
                #nat_gateways=self.node.try_get_context(config)['vpc']['nat_gateways'],  # Nat_Gateways
                # 2 Private & 1 Public Subnet in Each AZ
                subnet_configuration=[
                    # Subnet-# will be append to Subnet Name
                    ec2.SubnetConfiguration(name='private-1-', subnet_type=ec2.SubnetType.PRIVATE, cidr_mask=self.node.try_get_context(config)['vpc']['cidr_mask']),
                    ec2.SubnetConfiguration(name='private-2-', subnet_type=ec2.SubnetType.PRIVATE, cidr_mask=self.node.try_get_context(config)['vpc']['cidr_mask']),
                    ec2.SubnetConfiguration(name='public-', subnet_type=ec2.SubnetType.PUBLIC, cidr_mask=self.node.try_get_context(config)['vpc']['cidr_mask']),
                ]
            )

        # elif (config in configs) and (config == "dev")
        elif config == "dev" or config == "qa" or config =="prod":

        #     print("inside dev env")
            self.vpc = ec2.Vpc.from_lookup(self,id="vpc",
                                           is_default=self.node.try_get_context(config)["vpc"]['is_default'],
                                           vpc_id=self.node.try_get_context(config)["vpc_id"])
            # print(self.vpc.vpc_id)
        
        
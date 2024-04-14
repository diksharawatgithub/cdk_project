import json
from constructs import Construct
from aws_cdk import Stack
import aws_cdk as core
#import boto3
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_s3 as s3_
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_sqs as sqs
from aws_cdk import aws_sns as sns
from aws_cdk import aws_lambda_event_sources as lambdaevent



class CdkDemoStack_lambda(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        env = kwargs["env"]
        config = kwargs["config"]
        super().__init__(scope, id,env=env)

        self.cfg=config
        #Layer creation method
        self.create_layer()
        print("Hello World")
        
        #Lambda function creation method
        self.create_lambda()

    def create_layer(self):    
        #Read Layer json input values
        try:
            with open(self.node.try_get_context(self.cfg)['layerlocation']) as da:
                data = json.load(da)
        except IOError:
            print("Exception:Unable to read Layer inputs")
        else:
            LayerDict={}
            #New Layer creation
            for layer in data['Layers']:
                lyname=layer['LayerName']
                runtm=layer['CompatibleRuntimes']
                rt=lambda_.Runtime(runtm)
                layer['LayerName']=lambda_.LayerVersion(
                    self,layer['LayerName'],layer_version_name=layer['LayerName'],
                    code=lambda_.Code.from_asset(layer['CodeLocation']),
                    compatible_runtimes=[rt],
                    license=layer['LicenseInfo'],
                    description=layer['Description'])
                layercfnref=layer['LayerName'].node.default_child
                layercfnref.apply_removal_policy(core.RemovalPolicy.RETAIN)
                LayerDict[lyname]=layer['LayerName']
            self.LayerDict=LayerDict


    def attach_trigger(self,function_ref,trigger_type):
        if "SQS" in trigger_type:
            sqsqueue=sqs.Queue.from_queue_arn(self,str(self.fnname + "_" + self.sqsname),
                queue_arn="arn:aws:sqs:" + self.node.try_get_context(self.cfg)['region'] + ":" + self.node.try_get_context(self.cfg)['account'] + ":" + str(self.sqsname))
            function_ref.add_event_source(lambdaevent.SqsEventSource(sqsqueue))
        elif "S3" in trigger_type:
            bucketref=s3_.Bucket(self,self.bucketname,bucket_name=self.bucketname)
            function_ref.add_event_source(lambdaevent.S3EventSource(bucketref,events=[s3_.EventType.OBJECT_CREATED]))
        elif "SNS" in trigger_type:
            snstopic=sns.Topic.from_topic_arn(self,str(self.fnname + "_" + self.snsname),
                topic_arn="arn:aws:sns:" + self.node.try_get_context(self.cfg)['region'] + ":" + self.node.try_get_context(self.cfg)['account'] + ":" + str(self.snsname))
            function_ref.add_event_source(lambdaevent.SnsEventSource(snstopic))

    def attach_layer(self):
        for key in self.Lyr_Ver:
            #check in new layer first, if true attach new layer
            if(key in self.LayerDict.keys()):
                #Attach provided layer version from layer json                
                self.fnref.add_layers(self.LayerDict[key])

    def create_lambda_roles(self):
        #Role creation to attach in Lambda
        lambdarole = iam.Role(self, "lambda-execution-role-id",
        role_name="lambda-execution-role",assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"))

        Managed_Policy1 = iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
        lambdarole.add_managed_policy(Managed_Policy1)

        Managed_Policy2 = iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole")
        lambdarole.add_managed_policy(Managed_Policy2)
        return lambdarole

    def create_lambda(self):
        #Read Lambda json input values
        try:
            with open(self.node.try_get_context(self.cfg)['lambdalocation']) as da, open(self.node.try_get_context(self.cfg)['configlocation']) as db:
                data = json.load(da)
                env_variables = json.load(db)
        except IOError:
            print("Exception:Unable to read Lambda inputs")
        else:
            i=0
            SecGrpDict={}
            SubnetList=[]
            lam_role=self.create_lambda_roles()
            for lines in env_variables['env'][self.cfg]['Vpcconfig']:
                vpcref = ec2.Vpc.from_lookup(self,"vpc",vpc_name=lines['VpcName'])
                for sgid in lines['SecurityGroupIds']:
                    sgref=ec2.SecurityGroup.from_security_group_id(self,"SG" + str(i),security_group_id=sgid)
                    i+=1
                    SecGrpDict[sgid]=sgref
                for sbntid in lines['SubnetIds']:
                    sbnetref=ec2.PrivateSubnet.from_subnet_id(self,"subnet" + str(i),subnet_id=sbntid)
                    SubnetList.append(sbnetref)
                    i+=1
                subnetref=ec2.SubnetSelection(subnets=SubnetList)

            fnnamelist=[]
            for fn in data['Configuration']:
                LayerWithVersion_Json=fn['Layerwithversion']
                
                runtm=fn['Runtime']
                for Lyr_Ver in LayerWithVersion_Json:
                    self.Lyr_Ver=Lyr_Ver
                #Taking Env variable from json
                dummy_dict_new = {}

                if len(fn["env_variables"]) != 0:
                    global_required = fn["env_variables"]
                    global_variables = env_variables["env"][self.cfg]
                    for var in global_required:
                        dummy_dict_new[var] = global_variables[var]

                if fn["local_variables"] != "":
                    local_var = fn["local_variables"]
                    dummy_dict_new.update(local_var)

                envval = dummy_dict_new
                #Taking Policy rules from Json for Lambda intial Policy
                ActionList=[]
                Act=([Statement['Action'] for Statement in fn['Statement']])
                Res=([Statement['Resource'] for Statement in fn['Statement']])
                efct=([Statement['Effect'] for Statement in fn['Statement']])
                for key in efct:
                    effect=iam.Effect(key)
                for key in Act:
                    for line in key:
                        ActionList.append(line)
                #Taking Runtime env for lambda
                rt=lambda_.Runtime(runtm)

                #Function creation
                fnref=lambda_.Function(self,fn['FunctionName'],
                function_name=fn['FunctionName'],
                code=lambda_.Code.from_asset(fn['code_Location']),
                handler=fn['Handler'],
                runtime=rt,
                timeout=core.Duration.seconds(fn['Timeout']),
                environment=envval,
                vpc=vpcref,allow_public_subnet=True,
                security_groups=[*SecGrpDict.values()],role=lam_role,
                initial_policy=[iam.PolicyStatement(effect=effect,
                actions=ActionList,resources=Res)],vpc_subnets=subnetref)

                self.fnref=fnref #Function reference
                self.fnname=fn['FunctionName']

                #Trigger attach method
                if "SQS" in fn['Trigger']:
                    self.fnname=fn['FunctionName']
                    self.sqsname=fn['SQSName']
                    self.attach_trigger(fnref,fn['Trigger'])
                elif "S3" in fn['Trigger']:
                    self.fnname=fn['FunctionName']
                    self.bucketname=fn['BucketName']
                    self.attach_trigger(fnref,fn['Trigger'])
                elif "SNS" in fn['Trigger']:
                    self.fnname=fn['FunctionName']
                    self.snsname=fn['SNSName']
                    self.attach_trigger(fnref,fn['Trigger'])

                #Attaching layer to lambda
                self.attach_layer()

                #Passing created function to AppSync stack        
                fnnamelist.append(fn['FunctionName'])
            self.funname=fnnamelist

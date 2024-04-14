from constructs import Construct
from aws_cdk import Stack
import aws_cdk as core
from aws_cdk import (aws_codebuild as codebuild,
                     aws_codecommit as codecommit,
                     aws_codepipeline as codepipeline,
                     aws_codepipeline_actions as codepipeline_actions,
                     aws_lambda as lambda_,
                     aws_iam as iam)

class CdkDemoStack_Pipeline(Stack):

    def __init__(self, scope: Construct, id: str,*, repo_name: str=None,**kwargs) -> None:
        env = kwargs["env"]
        config = kwargs["config"]

        super().__init__(scope, id, env=env)
        

        stackname = self.node.try_get_context(config)['Stack_Name']
        print("stackname is",stackname)
        #env_buildspec = self.node.try_get_context(config)['Buildspec']
        #Role creation
        buildrole = iam.Role(self,'cdkbuildrole',
            role_name="cdkbuildrole",assumed_by=iam.ServicePrincipal("codebuild.amazonaws.com"),
            managed_policies=[iam.ManagedPolicy.from_aws_managed_policy_name('AdministratorAccess')])

        # cdk_DB_pipeline_build = codebuild.PipelineProject(self, "cdkDBpipelinebuild",role=buildrole,
        #                 environment=codebuild.BuildEnvironment(privileged=True,build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_2),
        #                 build_spec=codebuild.BuildSpec.from_source_filename(filename=env_buildspec))
        
        #To be used in Build stage
        cdk_build = codebuild.PipelineProject(self, "CdkBuild",role=buildrole,
        environment=codebuild.BuildEnvironment(build_image=codebuild.LinuxBuildImage.STANDARD_5_0),
                        build_spec=codebuild.BuildSpec.from_object(dict(
                            version="0.2",
                            phases=dict(
                                install=dict(
                                    commands=[
                                        "npm install aws-cdk@2.0.0",
                                        #"npm install -g aws-cdk",
                                        #"npm update",
                                        "ls -ltr",
                                        "pwd",
                                        "python -m pip install -r requirements.txt"
                                        ]),
                                build=dict(
                                    commands=[
                                        "cd $CODEBUILD_SRC_DIR/",
                                        "pwd",
                                        "ls -ltr",
                                        "npx cdk --version",
                                        "npx cdk ls",
                                        'npx cdk deploy ' + stackname + ' --require-approval never'
                                    ])),
                                artifacts={
                                    "base-directory": "$CODEBUILD_SRC_DIR/",
                                    "files": [
                                        "**/*",
                                        stackname + ".template.json"
                                        ]}
                                    )))

        source_output = codepipeline.Artifact()
        cdk_build_output = codepipeline.Artifact("CdkBuildOutput")

        codepipeline.Pipeline(self, "Pipeline",pipeline_name="Cdk_demo_pipeline",
            stages=[
                codepipeline.StageProps(stage_name="Source",
                    actions=[
                        codepipeline_actions.GitHubSourceAction(
                            action_name='GitHub_Source',
                            oauth_token=core.SecretValue.secrets_manager(self.node.try_get_context(config)['Github_token']),
                            owner=self.node.try_get_context(config)['Github_owner'],
                            repo=self.node.try_get_context(config)['Github_repo'],
                            branch=self.node.try_get_context(config)['Github_branch'],
                            trigger=codepipeline_actions.GitHubTrigger.NONE,
                            output=source_output)],
                            ),
                
                codepipeline.StageProps(stage_name="Build",
                    actions=[
                        codepipeline_actions.CodeBuildAction(
                            action_name="CDK_Build",
                            project=cdk_build,
                            input=source_output,
                            outputs=[cdk_build_output])])
                ])
    
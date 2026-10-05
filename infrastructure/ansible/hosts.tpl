[fastapi_servers]
${instance_id}    ansible_user=ec2-user

[fastapi_servers:vars]
ansible_connection=community.aws.aws_ssm
ansible_aws_ssm_region=${aws_region}
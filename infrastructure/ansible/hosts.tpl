[fastapi_servers]
${instance_id}

[fastapi_servers:vars]
ansible_connection=community.aws.aws_ssm
ansible_aws_ssm_region=${aws_region}
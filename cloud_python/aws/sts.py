import boto3

class AWSSTS:
    def __init__(self, aws_access_key_id: str, aws_secret_access_key: str):
        self.client = boto3.client(
            "sts",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )


    def gen_assume_credentials(self, member_account_id: str):
        role_session_name = "AssumeRoleSession1"
        role_arn = f"arn:aws:iam::{member_account_id}:role/OrganizationAccountAccessRole"
        assume_role = self.client.assume_role(
            RoleArn=role_arn, RoleSessionName=role_session_name
        )
        return assume_role["Credentials"]


if __name__ == "__main__":
    client = AWSSTS(
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )
    credentials = client.gen_credentials(client, ACCOUNT_ID)
    access_key_id = credentials["AccessKeyId"]
    secret_access_key = credentials["SecretAccessKey"]
    session_token = credentials["SessionToken"]
    print(
        f"credentials: {credentials} \n",
        f"access_key_id: {access_key_id} \n",
        f"secret_access_key: {secret_access_key} \n",
        f"session_token: {session_token} \n",
    )

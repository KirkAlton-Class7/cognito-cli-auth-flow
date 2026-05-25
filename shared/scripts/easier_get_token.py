import boto3
import getpass
import json
import os

# IMPORTANT:
# Use a public Cognito app client with NO client secret for this helper.
# The main runbook still teaches SECRET_HASH with the secret-bearing app client first.

# =========================
# Configuration
# =========================

REGION = os.getenv("AWS_REGION", "us-east-1")

# =========================
# User Input
# =========================

client_id = os.getenv("COGNITO_PUBLIC_CLIENT_ID") or input("Public app client ID: ")
username = os.getenv("COGNITO_USERNAME") or input("Username: ")
password = os.getenv("COGNITO_PASSWORD") or getpass.getpass("Password: ")

# =========================
# Cognito Client
# =========================

client = boto3.client("cognito-idp", region_name=REGION)

try:
    response = client.initiate_auth(
        ClientId=client_id,
        AuthFlow="USER_PASSWORD_AUTH",
        AuthParameters={
            "USERNAME": username,
            "PASSWORD": password
        }
    )

    # =========================
    # Handle MFA Challenge
    # =========================

    if response.get("ChallengeName") == "SOFTWARE_TOKEN_MFA":
        code = input("Enter MFA Code: ")

        response = client.respond_to_auth_challenge(
            ClientId=client_id,
            ChallengeName="SOFTWARE_TOKEN_MFA",
            Session=response["Session"],
            ChallengeResponses={
                "USERNAME": username,
                "SOFTWARE_TOKEN_MFA_CODE": code
            }
        )

    # =========================
    # Extract Tokens
    # =========================

    auth = response["AuthenticationResult"]

    # print("\n========== TOKENS ==========\n")

    # print("Access Token:\n")
    # print(auth["AccessToken"])

    # print("\n============================\n")
        
    
    print("\n========== TOKENS ==========\n")

    print("ID Token:\n")
    print(auth["IdToken"])

    print("\n============================\n")

    print("Access Token:\n")
    print(auth["AccessToken"])

    print("\n============================\n")

except Exception as e:
    print("\nAuthentication Failed\n")
    print(str(e))

import boto3
import getpass
import base64
import json
import os
import time
from datetime import datetime, timezone

# ==================================================
# CONFIGURATION
# ==================================================

REGION = os.getenv("AWS_REGION", "us-east-1")

API_BASE = os.getenv(
    "API_BASE",
    "https://t7788geiqj.execute-api.us-east-1.amazonaws.com/prod",
)
# Example only: replace API_BASE with your own API Gateway /prod base URL.

PYTHON_ROUTE = os.getenv("PYTHON_ROUTE", "class7/python")
NODE_ROUTE = os.getenv("NODE_ROUTE", "class7/node")
NAME_QUERY = "?name="
NAME = os.getenv("CHEWBACCA_NAME", "Chewbacca")

client_id = os.getenv("COGNITO_PUBLIC_CLIENT_ID") or input("Public app client ID: ")
username = os.getenv("COGNITO_USERNAME") or input("Username: ")
password = os.getenv("COGNITO_PASSWORD") or getpass.getpass("Password: ")

# ==================================================
# COLORS
# ==================================================

GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
YELLOW = "\033[93m"
RESET = "\033[0m"

# ==================================================
# JWT DECODE
# ==================================================

def decode_jwt(token):
    try:
        payload = token.split(".")[1]
        # Fix padding
        payload += '=' * (-len(payload) % 4)
        decoded = base64.urlsafe_b64decode(payload)
        return json.loads(decoded)
    except Exception as e:
        print(f"{RED}Failed to decode JWT:{RESET} {e}")
        return None

# ==================================================
# TOKEN EXPIRATION
# ==================================================

def format_expiration(exp):
    exp_time = datetime.fromtimestamp(exp, tz=timezone.utc)
    now = datetime.now(timezone.utc)
    remaining = exp_time - now
    return exp_time, remaining

# ==================================================
# MAIN
# ==================================================

print(f"{CYAN}")
print("========================================")
print("  COGNITO TOKEN RETRIEVER")
print("========================================")
print(f"{RESET}")

print(f"{YELLOW}IMPORTANT:{RESET} App Client must NOT use a client secret.\n")

client = boto3.client("cognito-idp", region_name=REGION)

try:
    # ==================================================
    # INITIAL AUTH
    # ==================================================
    response = client.initiate_auth(
        ClientId=client_id,
        AuthFlow="USER_PASSWORD_AUTH",
        AuthParameters={
            "USERNAME": username,
            "PASSWORD": password
        }
    )

    # ==================================================
    # MFA HANDLING
    # ==================================================
    if response.get("ChallengeName") == "SOFTWARE_TOKEN_MFA":
        print(f"\n{YELLOW}MFA REQUIRED{RESET}")
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

    # ==================================================
    # TOKENS
    # ==================================================
    auth = response["AuthenticationResult"]
    id_token = auth["IdToken"]
    access_token = auth["AccessToken"]

    print(f"\n{GREEN}AUTHENTICATION SUCCESSFUL{RESET}")

    # ==================================================
    # ID TOKEN – DECODE & INFO
    # ==================================================
    decoded_id = decode_jwt(id_token)
    if decoded_id:
        print(f"\n{CYAN}========== ID TOKEN CLAIMS =========={RESET}\n")
        print(json.dumps(decoded_id, indent=4))

        groups = decoded_id.get("cognito:groups", [])
        print(f"\n{CYAN}========== ID TOKEN – GROUP MEMBERSHIP =========={RESET}")
        if groups:
            for group in groups:
                print(f" - {group}")
        else:
            print("No groups assigned")

        exp = decoded_id.get("exp")
        if exp:
            exp_time, remaining = format_expiration(exp)
            print(f"\n{CYAN}========== ID TOKEN – EXPIRATION =========={RESET}")
            print(f"Expires At (UTC): {exp_time}")
            print(f"Time Remaining : {remaining}")

    # ==================================================
    # CURL EXAMPLES – USING ID TOKEN
    # ==================================================
    print(f"\n{CYAN}========== API TEST - ID TOKEN =========={RESET}\n")
    print(f"\n{CYAN}Python Endpoint (expects ID token if no scopes set):{RESET}\n")
    print(f'''curl "{API_BASE}/{PYTHON_ROUTE}{NAME_QUERY}{NAME}" \\
  -H "Authorization: Bearer {id_token}"
''')
    print(f"{CYAN}Node Endpoint (expects ID token if no scopes set):{RESET}\n")
    print(f'''curl "{API_BASE}/{NODE_ROUTE}{NAME_QUERY}{NAME}" \\
  -H "Authorization: Bearer {id_token}"
''')
   
    # ==================================================
    # ACCESS TOKEN – DECODE & INFO
    # ==================================================
    decoded_access = decode_jwt(access_token)
    if decoded_access:
        print(f"\n{MAGENTA}========== ACCESS TOKEN CLAIMS =========={RESET}\n")
        print(json.dumps(decoded_access, indent=4))

        groups = decoded_access.get("cognito:groups", [])
        print(f"\n{MAGENTA}========== ACCESS TOKEN – GROUP MEMBERSHIP =========={RESET}")
        if groups:
            for group in groups:
                print(f" - {group}")
        else:
            print("No groups assigned")

        exp = decoded_access.get("exp")
        if exp:
            exp_time, remaining = format_expiration(exp)
            print(f"\n{MAGENTA}========== ACCESS TOKEN – EXPIRATION =========={RESET}")
            print(f"Expires At (UTC): {exp_time}")
            print(f"Time Remaining : {remaining}")

    # ==================================================
    # CURL EXAMPLES – USING ACCESS TOKEN
    # ==================================================
    print(f"\n{MAGENTA}========== API TEST - ACCESS TOKEN =========={RESET}\n")
    print(f"{MAGENTA}Python Endpoint:{RESET}\n")
    print(f'''curl "{API_BASE}/{PYTHON_ROUTE}{NAME_QUERY}{NAME}" \\
  -H "Authorization: Bearer {access_token}"
''')
    print(f"{MAGENTA}Node Endpoint:{RESET}\n")
    print(f'''curl "{API_BASE}/{NODE_ROUTE}{NAME_QUERY}{NAME}" \\
  -H "Authorization: Bearer {access_token}"
''')

    print(f"\n{GREEN}Done.{RESET}\n")

except Exception as e:
    print(f"\n{RED}AUTHENTICATION FAILED{RESET}\n")
    print(str(e))

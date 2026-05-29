import base64
import json

# ==================================================
# JWT Decode Function
# ==================================================

def decode_jwt(token):

    try:
        parts = token.split(".")

        if len(parts) != 3:
            raise Exception("Invalid JWT format")

        payload = parts[1]

        # Fix Base64 padding
        payload += '=' * (-len(payload) % 4)

        decoded = base64.urlsafe_b64decode(payload)

        return json.loads(decoded)

    except Exception as e:
        print(f"\nERROR: {e}")
        return None

# ==================================================
# MAIN
# ==================================================

# token = input("Paste Access Token:\n\n").strip()

token = "eyJraWQiOiJPNGpsTDF5K1I0ZGcxNVwvdE1XYWhRWUd6aUhCd25SNzNFVHBiZ2Qwd1Qwaz0iLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJmNDc4ZjRhOC04MGIxLTcwZWMtNzdlMy05OTBiYmNmYjMxYzgiLCJjb2duaXRvOmdyb3VwcyI6WyJnZW5lcmFsIl0sImlzcyI6Imh0dHBzOlwvXC9jb2duaXRvLWlkcC51cy1lYXN0LTEuYW1hem9uYXdzLmNvbVwvdXMtZWFzdC0xX0Z4RlNrNGVNSyIsImNsaWVudF9pZCI6IjUyOXJwcTFsNTgzMWNraThvMDA2NDIwNGlwIiwib3JpZ2luX2p0aSI6IjgyZjkxMTZhLTUxMmMtNDdhMS1hMDMxLTRlN2U0NjlhM2FmNiIsImV2ZW50X2lkIjoiODQ5OTdjYWUtOGFjMi00MzEwLWE1ZDgtNDcxNDY2ZDM2NGMyIiwidG9rZW5fdXNlIjoiYWNjZXNzIiwic2NvcGUiOiJhd3MuY29nbml0by5zaWduaW4udXNlci5hZG1pbiIsImF1dGhfdGltZSI6MTc3OTg0ODM3NiwiZXhwIjoxNzc5ODUxOTc2LCJpYXQiOjE3Nzk4NDgzNzYsImp0aSI6Ijk5NzdhOGJjLTFjNjktNGEwYy05NjE4LTJiNDBiMTBhYmZmZSIsInVzZXJuYW1lIjoia2lya2FsdG9uLXB5dGhvbi0yIn0.VS3Bwnd3P4FzSuT_wcmF7Ube2RQobFFiBZbPkbPJ4bxqDEqSFPjT-UFMm-YweqYdzJBZKBQbJGWuBfbhDC3Her_Oy7JSGXR4tB4T8wXODQTcNKkBOEqOfV-MDIBlKg_HiYl8tM6cGRxmuV6KPGF9YYHtTkz20fNvVpXmvgfUOuXzB64PMLLJvvOEd8MFW5g0z5AaWKnmo6yTivD6078rKy_4ED49wGQ0MrJJ1AE8eoZ0QiHjvhndfw1APYk11-NEFh4-2dBPF6P5Lcvo9aCmhBnIyJMxz8wRIRuKDsMFDFvhoI4MEJ9PRi_Ey9mcv4EioKyPce_o5YS112YKnNXm6g"

decoded = decode_jwt(token)

if decoded:

    print("\n===================================")
    print("TOKEN CLAIMS")
    print("===================================\n")

    print(json.dumps(decoded, indent=4))

    print("\n===================================")
    print("IDENTITY SUMMARY")
    print("===================================\n")

    username = decoded.get("username", "NOT FOUND")
    email = decoded.get("email", "NOT FOUND")

    print(f"Username : {username}")
    print(f"Email    : {email}")

    # ==================================================
    # GROUP CHECK
    # ==================================================

    groups = decoded.get("cognito:groups", [])

    print("\n===================================")
    print("GROUP MEMBERSHIP")
    print("===================================\n")

    if groups:

        for group in groups:
            print(f" - {group}")

    else:
        print("No Cognito groups found")

        print("\nPossible Causes:")
        print(" - User not assigned to group")
        print(" - Wrong token type")
        print(" - Authentication before group assignment")

    print("\n===================================")
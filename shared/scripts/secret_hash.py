import base64
import hashlib
import hmac
import sys


def main():
    if len(sys.argv) != 4:
        print("Usage: python3 secret_hash.py <username> <client_id> <client_secret>", file=sys.stderr)
        sys.exit(1)

    username, client_id, client_secret = sys.argv[1:4]
    message = (username + client_id).encode("utf-8")
    key = client_secret.encode("utf-8")

    secret_hash = base64.b64encode(
        hmac.new(key, message, digestmod=hashlib.sha256).digest()
    ).decode("utf-8")

    print(secret_hash)


if __name__ == "__main__":
    main()

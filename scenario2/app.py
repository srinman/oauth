from flask import Flask, jsonify, request, abort
from flask_cors import CORS
import jwt
import requests
from jwt import PyJWKClient

app = Flask(__name__)
CORS(app)  # Enable CORS

# Static user data for 5 users mapped by their email addresses.
registered_users = {
    "user1@domain.com": {
        "username": "User1",
        "address": "100 First St, CityA",
        "phone": "111-111-1111"
    },
    "user2@domain.com": {
        "username": "User2",
        "address": "200 Second St, CityB",
        "phone": "222-222-2222"
    },
    "user3@domain.com": {
        "username": "User3",
        "address": "300 Third St, CityC",
        "phone": "333-333-3333"
    },
    "user4@domain.com": {
        "username": "User4",
        "address": "400 Fourth St, CityD",
        "phone": "444-444-4444"
    },
    "user5@domain.com": {
        "username": "User5",
        "address": "500 Fifth St, CityE",
        "phone": "555-555-5555"
    }
}

# Microsoft EntraID configuration -- update these with your actual values.
TENANT_ID = "YOUR_TENANT_ID"
MICROSOFT_CLIENT_ID = "YOUR_MICROSOFT_CLIENT_ID"
DISCOVERY_URL = f"https://login.microsoftonline.com/{TENANT_ID}/v2.0/.well-known/openid-configuration"
config = requests.get(DISCOVERY_URL).json()
jwks_uri = config["jwks_uri"]

# Set up a JWKS client for verifying tokens.
jwks_client = PyJWKClient(jwks_uri)

def verify_token(token):
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        # Decode and verify the token (using RS256 algorithm).
        decoded = jwt.decode(token, signing_key.key, algorithms=["RS256"], audience=MICROSOFT_CLIENT_ID)
        return decoded
    except Exception as e:
        raise e

@app.route('/api/dashboard', methods=['GET'])
def dashboard():
    token = request.headers.get('Authorization')
    if not token:
        abort(401, description="Missing authorization token")
    try:
        decoded = verify_token(token)
        # Microsoft tokens typically include 'preferred_username' or 'upn'
        user_email = decoded.get("preferred_username") or decoded.get("upn")
        if not user_email or user_email not in registered_users:
            abort(401, description="User not registered")
        return jsonify(registered_users[user_email])
    except Exception as e:
        abort(401, description=str(e))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
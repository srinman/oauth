from flask import Flask, jsonify, request, abort
from flask_cors import CORS  
from google.oauth2 import id_token
from google.auth.transport import requests as grequests
from werkzeug.exceptions import HTTPException
import sys

app = Flask(__name__)
CORS(app)

registered_users = {
    "xyz@gmail.com": {
        "username": "User1",
        "address": "100 First St, CityA",
        "phone": "111-111-1111"
    },
    "user2@example.com": {
        "username": "User2",
        "address": "200 Second St, CityB",
        "phone": "222-222-2222"
    },
    "user3@example.com": {
        "username": "User3",
        "address": "300 Third St, CityC",
        "phone": "333-333-3333"
    },
    "user4@example.com": {
        "username": "User4",
        "address": "400 Fourth St, CityD",
        "phone": "444-444-4444"
    },
    "user5@example.com": {
        "username": "User5",
        "address": "500 Fifth St, CityE",
        "phone": "555-555-5555"
    }
}

GOOGLE_CLIENT_ID = "573154595273-f5anosm6qld1mg1vgqqiv7rdvvp5p6sm.apps.googleusercontent.com"

@app.route('/api/dashboard', methods=['GET'])
def dashboard():
    token = request.headers.get('Authorization')
    print(f"Received token: {token}", flush=True)
    if not token:
        abort(401, description="Missing authorization token")
    try:
        idinfo = id_token.verify_oauth2_token(token, grequests.Request(), GOOGLE_CLIENT_ID)
        print("Decoded token info: ", idinfo, flush=True)
        user_email = idinfo.get("email")
        print(f"Extracted user email: {user_email}", flush=True)
        if not user_email:
            abort(401, description="Email not found in token")
        if user_email not in registered_users:
            print(f"User {user_email} is not in registered_users", flush=True)
            abort(403, description="User authenticated but not registered")
        return jsonify(registered_users[user_email])
    except HTTPException as http_ex:
        # Re-raise HTTPExceptions so that the intended status code is preserved.
        raise http_ex
    except ValueError as ve:
        print(f"Token verification error: {ve}", flush=True)
        abort(401, description="User not authenticated")
    except Exception as e:
        print(f"Unexpected error: {e}", flush=True)
        abort(500, description="Internal server error")

if __name__ == '__main__':
    app.run(debug=True, port=5000)
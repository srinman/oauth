from flask import Flask, jsonify, request, abort
from flask_cors import CORS  # Import flask-cors
from google.oauth2 import id_token
from google.auth.transport import requests as grequests

app = Flask(__name__)
CORS(app)  # Enable CORS

# Static user data for 5 users mapped by their email addresses.
registered_users = {
    "xyz1@gmail.com": {
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

# Replace with your actual Google client ID.
GOOGLE_CLIENT_ID = "573154595273-f5anosm6qld1mg1vgqqiv7rdvvp5p6sm.apps.googleusercontent.com"

@app.route('/api/dashboard', methods=['GET'])
def dashboard():
    token = request.headers.get('Authorization')
    if not token:
        abort(401, description="Missing authorization token")
    try:
        # Verify the token using Google's public keys.
        idinfo = id_token.verify_oauth2_token(token, grequests.Request(), GOOGLE_CLIENT_ID)
        user_email = idinfo.get("email")
        if not user_email or user_email not in registered_users:
            abort(401, description="User not registered")
        return jsonify(registered_users[user_email])
    except ValueError:
        abort(401, description="User not authenticated")

if __name__ == '__main__':
    app.run(debug=True, port=5000)
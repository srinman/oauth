# Detailed Explanation of How the App Works

This application demonstrates a direct ID token flow using Microsoft EntraID (Azure AD) for authentication with a JavaScript front end and a Flask backend for serving protected user information. The app consists of two main parts:

- **Client-Side (index.html):** Uses the MSAL.js library to sign in users via Microsoft EntraID.
- **Server-Side (app.py):** A Flask app that verifies the Microsoft ID token and returns static user data if the user is registered.

---

## Client-Side (index.html)

Below is the complete updated `index.html` code:

```html
<!-- filepath: /home/srinman/git/oauth/scenario1/index.html -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>OAuth Dashboard with Microsoft EntraID</title>
  <!-- Load MSAL.js from Microsoft -->
  <script type="text/javascript" src="https://alcdn.msauth.net/browser/2.28.2/js/msal-browser.min.js"></script>
  <style>
    /* Initially hide Logout and Dashboard buttons */
    #logout-btn, #dashboard-btn {
      display: none;
    }
  </style>
</head>
<body>
  <!-- Display a title on top of the page -->
  <h1 style="text-align:center;">Welcome to Scenario1 App</h1>
  
  <!-- Sign in, logout and dashboard buttons -->
  <button id="ms-signin-button">Login with Microsoft</button>
  <button id="logout-btn">Logout</button>
  <button id="dashboard-btn">Dashboard</button>
  <div id="user-info"></div>

  <script>
    // MSAL configuration: update with your registered Microsoft EntraID app details.
    const msalConfig = {
      auth: {
        clientId: "YOUR_MICROSOFT_CLIENT_ID",
        authority: "https://login.microsoftonline.com/YOUR_TENANT_ID",
        redirectUri: "http://localhost:8000"
      }
    };

    const msalInstance = new msal.PublicClientApplication(msalConfig);
    let idToken = null;

    // Sign in using a popup.
    function signIn() {
      msalInstance.loginPopup().then((loginResponse) => {
        idToken = loginResponse.idToken;
        // Update the UI: hide the sign-in button, show logout and dashboard.
        document.getElementById('ms-signin-button').style.display = 'none';
        document.getElementById('logout-btn').style.display = 'inline-block';
        document.getElementById('dashboard-btn').style.display = 'inline-block';
        // Decode token payload to extract a user property.
        const payload = JSON.parse(atob(idToken.split('.')[1]));
        const userName = payload.preferred_username || payload.name || payload.upn;
        document.getElementById('logout-btn').textContent = 'Logout ' + userName;
      }).catch((error) => {
        console.error("Login failed:", error);
      });
    }

    // Sign out using a popup.
    function signOut() {
      msalInstance.logoutPopup().then(() => {
        idToken = null;
        document.getElementById('logout-btn').style.display = 'none';
        document.getElementById('dashboard-btn').style.display = 'none';
        document.getElementById('ms-signin-button').style.display = 'inline-block';
        document.getElementById('user-info').innerHTML = '';
      }).catch((error) => {
        console.error("Logout failed:", error);
      });
    }

    document.getElementById('ms-signin-button').addEventListener('click', signIn);
    document.getElementById('logout-btn').addEventListener('click', signOut);

    // Dashboard button: calls the backend API and displays returned JSON.
    document.getElementById('dashboard-btn').addEventListener('click', function() {
      if (!idToken) {
        alert("You must be signed in to access the dashboard.");
        return;
      }
      fetch('http://localhost:5000/api/dashboard', {
        method: 'GET',
        headers: { 'Authorization': idToken }
      })
      .then(response => {
        if (!response.ok) throw new Error("Error fetching dashboard info");
        return response.json();
      })
      .then(data => {
        document.getElementById('user-info').innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
      })
      .catch(error => {
        alert(error.message);
      });
    });
  </script>
</body>
</html>
```

---

## Server-Side (app.py)

Below is the updated `app.py` code that verifies the Microsoft EntraID token using PyJWT and the JWKS published by Microsoft:

```python
# filepath: /home/srinman/git/oauth/scenario1/app.py
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
import jwt
import requests
from jwt import PyJWKClient

app = Flask(__name__)
CORS(app)

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

# Microsoft EntraID (Azure AD) configuration:
TENANT_ID = "YOUR_TENANT_ID"
MICROSOFT_CLIENT_ID = "YOUR_MICROSOFT_CLIENT_ID"
DISCOVERY_URL = f"https://login.microsoftonline.com/{TENANT_ID}/v2.0/.well-known/openid-configuration"
config = requests.get(DISCOVERY_URL).json()
jwks_uri = config["jwks_uri"]

# Set up a JWKS client for token verification.
jwks_client = PyJWKClient(jwks_uri)

def verify_token(token):
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        # Decode and verify the token.
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
        # Extract the user's email from the token (e.g., 'preferred_username' or 'upn').
        user_email = decoded.get("preferred_username") or decoded.get("upn")
        if not user_email or user_email not in registered_users:
            abort(401, description="User not registered")
        return jsonify(registered_users[user_email])
    except Exception as e:
        abort(401, description=str(e))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

---

## Running the App

1. **Install Dependencies:**

   ```bash
   pip install flask flask-cors pyjwt requests
   ```

2. **Serve the HTML File:**
   - Open a terminal in the project directory and run:
   
     ```bash
     python3 -m http.server 8000
     ```
   
   - This serves your `index.html` at [http://localhost:8000](http://localhost:8000).

3. **Run the Flask Backend:**
   - In a separate terminal, run:
   
     ```bash
     python app.py
     ```
   
   - The Flask app will run on [http://localhost:5000](http://localhost:5000).

4. **Test the Workflow:**
   - Visit [http://localhost:8000](http://localhost:8000).
   - Click the **Login with Microsoft** button to sign in.
   - After signing in, click the **Dashboard** button to fetch and display your protected user information.

---

This complete update demonstrates the scenario using Microsoft EntraID. Make sure to replace the placeholder client and tenant IDs with your actual values.# Detailed Explanation of How the App Works

This application demonstrates a direct ID token flow using Microsoft EntraID (Azure AD) for authentication with a JavaScript front end and a Flask backend for serving protected user information. The app consists of two main parts:

- **Client-Side (index.html):** Uses the MSAL.js library to sign in users via Microsoft EntraID.
- **Server-Side (app.py):** A Flask app that verifies the Microsoft ID token and returns static user data if the user is registered.

---

## Client-Side (index.html)

Below is the complete updated `index.html` code:

```html
<!-- filepath: /home/srinman/git/oauth/scenario1/index.html -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>OAuth Dashboard with Microsoft EntraID</title>
  <!-- Load MSAL.js from Microsoft -->
  <script type="text/javascript" src="https://alcdn.msauth.net/browser/2.28.2/js/msal-browser.min.js"></script>
  <style>
    /* Initially hide Logout and Dashboard buttons */
    #logout-btn, #dashboard-btn {
      display: none;
    }
  </style>
</head>
<body>
  <!-- Display a title on top of the page -->
  <h1 style="text-align:center;">Welcome to Scenario1 App</h1>
  
  <!-- Sign in, logout and dashboard buttons -->
  <button id="ms-signin-button">Login with Microsoft</button>
  <button id="logout-btn">Logout</button>
  <button id="dashboard-btn">Dashboard</button>
  <div id="user-info"></div>

  <script>
    // MSAL configuration: update with your registered Microsoft EntraID app details.
    const msalConfig = {
      auth: {
        clientId: "YOUR_MICROSOFT_CLIENT_ID",
        authority: "https://login.microsoftonline.com/YOUR_TENANT_ID",
        redirectUri: "http://localhost:8000"
      }
    };

    const msalInstance = new msal.PublicClientApplication(msalConfig);
    let idToken = null;

    // Sign in using a popup.
    function signIn() {
      msalInstance.loginPopup().then((loginResponse) => {
        idToken = loginResponse.idToken;
        // Update the UI: hide the sign-in button, show logout and dashboard.
        document.getElementById('ms-signin-button').style.display = 'none';
        document.getElementById('logout-btn').style.display = 'inline-block';
        document.getElementById('dashboard-btn').style.display = 'inline-block';
        // Decode token payload to extract a user property.
        const payload = JSON.parse(atob(idToken.split('.')[1]));
        const userName = payload.preferred_username || payload.name || payload.upn;
        document.getElementById('logout-btn').textContent = 'Logout ' + userName;
      }).catch((error) => {
        console.error("Login failed:", error);
      });
    }

    // Sign out using a popup.
    function signOut() {
      msalInstance.logoutPopup().then(() => {
        idToken = null;
        document.getElementById('logout-btn').style.display = 'none';
        document.getElementById('dashboard-btn').style.display = 'none';
        document.getElementById('ms-signin-button').style.display = 'inline-block';
        document.getElementById('user-info').innerHTML = '';
      }).catch((error) => {
        console.error("Logout failed:", error);
      });
    }

    document.getElementById('ms-signin-button').addEventListener('click', signIn);
    document.getElementById('logout-btn').addEventListener('click', signOut);

    // Dashboard button: calls the backend API and displays returned JSON.
    document.getElementById('dashboard-btn').addEventListener('click', function() {
      if (!idToken) {
        alert("You must be signed in to access the dashboard.");
        return;
      }
      fetch('http://localhost:5000/api/dashboard', {
        method: 'GET',
        headers: { 'Authorization': idToken }
      })
      .then(response => {
        if (!response.ok) throw new Error("Error fetching dashboard info");
        return response.json();
      })
      .then(data => {
        document.getElementById('user-info').innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
      })
      .catch(error => {
        alert(error.message);
      });
    });
  </script>
</body>
</html>
```

---

## Server-Side (app.py)

Below is the updated `app.py` code that verifies the Microsoft EntraID token using PyJWT and the JWKS published by Microsoft:

```python
# filepath: /home/srinman/git/oauth/scenario1/app.py
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
import jwt
import requests
from jwt import PyJWKClient

app = Flask(__name__)
CORS(app)

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

# Microsoft EntraID (Azure AD) configuration:
TENANT_ID = "YOUR_TENANT_ID"
MICROSOFT_CLIENT_ID = "YOUR_MICROSOFT_CLIENT_ID"
DISCOVERY_URL = f"https://login.microsoftonline.com/{TENANT_ID}/v2.0/.well-known/openid-configuration"
config = requests.get(DISCOVERY_URL).json()
jwks_uri = config["jwks_uri"]

# Set up a JWKS client for token verification.
jwks_client = PyJWKClient(jwks_uri)

def verify_token(token):
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        # Decode and verify the token.
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
        # Extract the user's email from the token (e.g., 'preferred_username' or 'upn').
        user_email = decoded.get("preferred_username") or decoded.get("upn")
        if not user_email or user_email not in registered_users:
            abort(401, description="User not registered")
        return jsonify(registered_users[user_email])
    except Exception as e:
        abort(401, description=str(e))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

---

## Running the App

1. **Install Dependencies:**

   ```bash
   pip install flask flask-cors pyjwt requests
   ```

2. **Serve the HTML File:**
   - Open a terminal in the project directory and run:
   
     ```bash
     python3 -m http.server 8000
     ```
   
   - This serves your `index.html` at [http://localhost:8000](http://localhost:8000).

3. **Run the Flask Backend:**
   - In a separate terminal, run:
   
     ```bash
     python app.py
     ```
   
   - The Flask app will run on [http://localhost:5000](http://localhost:5000).

4. **Test the Workflow:**
   - Visit [http://localhost:8000](http://localhost:8000).
   - Click the **Login with Microsoft** button to sign in.
   - After signing in, click the **Dashboard** button to fetch and display your protected user information.

---

This complete update demonstrates the scenario using Microsoft EntraID. Make sure to replace the placeholder client and tenant IDs with your actual values.
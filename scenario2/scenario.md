# Detailed Explanation of How the App Works

This application demonstrates a direct ID token flow using Microsoft EntraID (Azure AD) for authentication with a JavaScript front end and a Flask backend for serving protected user information. The app consists of two main parts:

- **Client-Side (index.html):** Uses the MSAL.js library to sign in users via Microsoft EntraID.
- **Server-Side (app.py):** A Flask app that verifies the Microsoft ID token and (if needed) access tokens and returns static user data if the user is registered.

> **Why It Works with This Config:**  
> Microsoft EntraID requires that Single-Page Applications (SPA) are registered as such in Azure. In a SPA registration, the configured settings enable both access tokens and ID tokens and use the OAuth 2.0 Authorization Code Flow with PKCE for enhanced security. This differs from Google Identity Services where the flow and configuration differ (for example, Google uses its proprietary token verification and button rendering). With MS EntraID, enabling SPA configuration with both tokens provides the client with sufficient credentials to securely call your backend API and also display user information.

---

## Client-Side (index.html)

Below is the complete updated `index.html` code:

```html
<!-- filepath: /home/srinman/git/oauth/scenario2/index.html -->
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
      },
      cache: {
        cacheLocation: "sessionStorage",
        storeAuthStateInCookie: false
      }
    };

    // Instantiate the MSAL instance.
    const msalInstance = new msal.PublicClientApplication(msalConfig);
    let idToken = null;

    // Sign in using a popup.
    function signIn() {
      msalInstance.loginPopup({
        scopes: ["openid", "profile", "offline_access"]
      }).then((loginResponse) => {
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
# filepath: /home/srinman/git/oauth/scenario2/app.py
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

## Creating the Microsoft EntraID App Registration

Follow these steps to create an OAuth client for Microsoft EntraID in the Azure portal:

1. **Sign in to the Azure Portal:**
   - Open your browser and navigate to [https://portal.azure.com](https://portal.azure.com).
   - Sign in with your Azure account.

2. **Navigate to Azure Active Directory:**
   - In the left-hand navigation pane, click on **Azure Active Directory**.

3. **Register a New Application:**
   - In Azure Active Directory, select **App registrations**.
   - Click on **New registration**.
   - Enter a name for your application (e.g., "Scenario1 App").
   - Choose the supported account types (for example, **Accounts in this organizational directory only** or **Accounts in any organizational directory**).
   - **Platform Configuration:**  
     - Under **Platform configurations**, choose **Single-Page Application (SPA)**.
     - In the **Redirect URI** section, enter:
       ```
       http://localhost:8000
       ```
     - Click **Configure**.

4. **Configure Authentication Settings:**
   - After configuring the SPA platform, on the **Authentication** blade, ensure that:
     - **Access tokens** and **ID tokens** are enabled (check both boxes).
     - The listed Redirect URI exactly matches the one from your msalConfig.
   - Click **Save** if any changes are made.

5. **Obtain Client and Tenant IDs:**
   - On the **Overview** page of your app registration, note the **Application (client) ID** and **Directory (tenant) ID**.
   - Replace the placeholders `YOUR_MICROSOFT_CLIENT_ID` and `YOUR_TENANT_ID` in your `index.html` and `app.py` files with these values.

6. **Final Check:**
   - Double-check that the **Redirect URI** and other settings match the URLs you are using (e.g., `http://localhost:8000`).
   - Verify that your app's Azure configuration aligns with your test environment.

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
   - Open your browser and navigate to [http://localhost:8000](http://localhost:8000).
   - Click the **Login with Microsoft** button to sign in.
   - After signing in, click the **Dashboard** button to fetch and display your protected user information.

---

This complete update demonstrates the scenario using Microsoft EntraID configured as a Single-Page Application (SPA), with both access tokens and ID tokens enabled. This configuration works because it leverages the OAuth 2.0 Authorization Code Flow with PKCE, ideal for SPAs, and securely obtains tokens that can be used to authenticate requests to your backend—differing from the Google flow which uses a different mechanism and configuration.
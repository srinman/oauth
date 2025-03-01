# Detailed Explanation of How the App Works

This application is a simple demonstration of a direct ID token flow using Google Identity Services for authentication and a Flask backend to serve protected user information. The app consists of two main components:

- **Client-Side (index.html):** Uses the Google Identity Services library to sign in users.
- **Server-Side (app.py):** A Flask app that verifies the ID token, logs diagnostic information, and returns user data if the user is both authenticated and registered.

---

## Client-Side (index.html)

Below is the complete updated `index.html` code:

```html
<!-- filepath: /home/srinman/git/oauth/scenario1/index.html -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>OAuth Dashboard</title>
  <script src="https://accounts.google.com/gsi/client" async defer></script>
  <style>
    /* Hide Logout and Dashboard buttons until a user is signed in */
    #logout-btn, #dashboard-btn {
      display: none;
    }
  </style>
</head>
<body>
  <!-- Display a title on top of the page -->
  <h1 style="text-align:center;">Welcome to Scenario1 App</h1>

  <!-- Sign-In container (visible when not signed in) -->
  <div id="google-signin-button" style="margin-top:10px;"></div>

  <!-- These buttons are shown after a successful sign in -->
  <button id="logout-btn">Logout</button>
  <button id="dashboard-btn">Dashboard</button>
  <div id="user-info"></div>

  <script>
    let isAuthenticated = false;
    let authToken = null;

    // Initialize Google Identity Services when the window loads.
    window.onload = function() {
      google.accounts.id.initialize({
        client_id: "573154595273-f5anosm6qld1mg1vgqqiv7rdvvp5p6sm.apps.googleusercontent.com",
        callback: handleCredentialResponse
      });
      // Render the Google Sign-In button.
      google.accounts.id.renderButton(
          document.getElementById('google-signin-button'),
          { theme: "outline", size: "large" }
      );
    };

    // Callback function triggered after a successful Google sign-in.
    function handleCredentialResponse(response) {
      authToken = response.credential;
      isAuthenticated = true;
      
      // Decode token payload to extract user info.
      const payload = JSON.parse(atob(authToken.split('.')[1]));
      const userName = payload.name || payload.email;
      
      // Update UI: hide the sign-in button and show Logout and Dashboard buttons.
      document.getElementById('google-signin-button').style.display = 'none';
      document.getElementById('logout-btn').style.display = 'inline-block';
      document.getElementById('dashboard-btn').style.display = 'inline-block';
      document.getElementById('logout-btn').textContent = 'Logout ' + userName;
    }
    window.handleCredentialResponse = handleCredentialResponse;

    // Logout button functionality.
    document.getElementById('logout-btn').addEventListener('click', function() {
      // Reset authentication state.
      isAuthenticated = false;
      authToken = null;
      document.getElementById('user-info').innerHTML = '';
      document.getElementById('logout-btn').style.display = 'none';
      document.getElementById('dashboard-btn').style.display = 'none';
      // Re-render the Google Sign-In button.
      document.getElementById('google-signin-button').style.display = 'block';
      google.accounts.id.renderButton(
          document.getElementById('google-signin-button'),
          { theme: "outline", size: "large" }
      );
    });

    // Dashboard button: calls the Python API and displays returned JSON.
    document.getElementById('dashboard-btn').addEventListener('click', function() {
      if (!isAuthenticated) {
        alert('You must be logged in to access the dashboard.');
        return;
      }
      fetch('http://localhost:5000/api/dashboard', {
        method: 'GET',
        headers: { 'Authorization': authToken }
      })
      .then(response => {
        if (!response.ok) {
          // Differentiate the error message based on status code.
          if (response.status === 401) {
            throw new Error("User not authenticated. Please log in again.");
          } else if (response.status === 403) {
            throw new Error("User authenticated but not registered.");
          } else {
            throw new Error("Error fetching dashboard information. (Status: " + response.status + ")");
          }
        }
        return response.json();
      })
      .then(data => {
        displayUserInfo(data);
      })
      .catch(error => {
        alert(error.message);
      });
    });

    // Display the JSON payload in a formatted <pre> block.
    function displayUserInfo(data) {
      document.getElementById('user-info').innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
    }
  </script>
</body>
</html>
```

---

## Server-Side (app.py)

Below is the revised `app.py` code with detailed diagnostic logging and differentiated response codes. Note that if the user is not registered, a 403 error is thrown; if a token is missing or invalid, a 401 error is thrown; and for any unexpected error, a 500 error is returned.

```python
# filepath: /home/srinman/git/oauth/scenario1/app.py
from flask import Flask, jsonify, request, abort
from flask_cors import CORS  # Enable Cross-Origin Resource Sharing
from google.oauth2 import id_token
from google.auth.transport import requests as grequests
from werkzeug.exceptions import HTTPException
import sys

app = Flask(__name__)
CORS(app)  # Enable CORS

# Static user data for 5 users mapped by their email addresses.
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

# Replace with your actual Google client ID.
GOOGLE_CLIENT_ID = "573154595273-f5anosm6qld1mg1vgqqiv7rdvvp5p6sm.apps.googleusercontent.com"

@app.route('/api/dashboard', methods=['GET'])
def dashboard():
    token = request.headers.get('Authorization')
    print(f"Received token: {token}", flush=True)
    if not token:
        abort(401, description="Missing authorization token")
    try:
        # Verify the token using Google's public keys.
        idinfo = id_token.verify_oauth2_token(token, grequests.Request(), GOOGLE_CLIENT_ID)
        print("Decoded token info:", idinfo, flush=True)
        user_email = idinfo.get("email")
        print(f"Extracted user email: {user_email}", flush=True)
        if not user_email:
            abort(401, description="Email not found in token")
        if user_email not in registered_users:
            print(f"User {user_email} is not in registered_users", flush=True)
            abort(403, description="User authenticated but not registered")
        # Valid and registered user returns a 200 along with user data.
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
```

---

## Creating the Google OAuth Client

Follow these steps to create a Client ID in the Google Cloud Console:

1. **Go to Google Cloud Console:**
   - Open your browser and navigate to [Google Cloud Console](https://console.cloud.google.com/).

2. **Create or Select a Project:**
   - Click on **Select a project**. If you don’t have one, click **New Project**, give it a name, and click **Create**.
   - Alternatively, select an existing project.

3. **Configure the OAuth Consent Screen:**
   - In the sidebar, navigate to **APIs & Services > OAuth consent screen**.
   - Choose **External** (if your app is public) or **Internal**.
   - Enter the required information (App name, support email, etc.) and click **Save and Continue**.

4. **Create OAuth Client Credentials:**
   - Go to **APIs & Services > Credentials**.
   - Click **Create Credentials** and select **OAuth client ID**.
   - Choose **Web application** as the application type.
   - Under **Authorized JavaScript origins**, add your application's origin (e.g. `http://localhost:8000`).
   - Under **Authorized redirect URIs,** add the URI where your app will handle OAuth responses (if applicable, e.g. `http://localhost:8000/callback`).  
     *Note:* For the direct ID token flow shown here, a redirect URI is not typically required.
   - Click **Create**. Your Client ID (and Client Secret, if needed) will be generated.
   - Replace the `client_id` value in your `index.html` with this new Client ID.

5. **Final Check:**
   - Ensure that the **Authorized JavaScript origins** exactly match the origin from which your HTML is served (e.g. `http://localhost:8000`).

---

## Running the App

1. **Install Dependencies:**

   ```bash
   pip install flask google-auth flask-cors
   ```

2. **Serve the HTML File:**
   - Navigate to the project directory and run:
   
     ```bash
     python3 -m http.server 8000
     ```
   
   - This serves your `index.html` at [http://localhost:8000](http://localhost:8000).

3. **Run the Flask Backend:**
   - Modify one of the email addresses in `registered_users` if needed (for example, update `user5@example.com` to your own email address).
   - Open a separate terminal and run:
   
     ```bash
     python app.py
     ```
   
   - The Flask app will run on [http://localhost:5000](http://localhost:5000).

4. **Test the Workflow:**
   - Open your browser and navigate to [http://localhost:8000](http://localhost:8000).
   - Click the rendered Google Sign-In button to log in.
   - Once logged in, click the Dashboard button to fetch and display your protected user information from the backend.

---

This updated document demonstrates the complete end-to-end flow—from setting up OAuth authentication using Google Identity Services to verifying tokens on the server with proper logging and differentiated response codes.
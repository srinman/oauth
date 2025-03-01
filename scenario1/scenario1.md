# Detailed Explanation of How the App Works

This application is a simple demonstration of a direct ID token flow using Google Identity Services for authentication and a Flask backend to serve protected user information. The app consists of two main components: a client-side HTML/JavaScript file (`index.html`) and a server-side Python file (`app.py`).

---

## Client-Side (index.html)

Below is the revised `index.html` code:

```html
<!-- filepath: /home/srinman/git/oauth/scenario1/index.html -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>OAuth Dashboard</title>
  <script src="https://accounts.google.com/gsi/client" async defer></script>
  <style>
    /* Initially hide the Logout and Dashboard buttons */
    #logout-btn, #dashboard-btn {
      display: none;
    }
  </style>
</head>
<body>
  <!-- Display a title on top of the page -->
  <h1 style="text-align:center;">Welcome to Scenario1 App</h1>

  <!-- When not logged in, only this container is visible -->
  <div id="google-signin-button" style="margin-top:10px;"></div>

  <!-- When logged in, these buttons will be displayed -->
  <button id="logout-btn">Logout</button>
  <button id="dashboard-btn">Dashboard</button>
  <div id="user-info"></div>

  <script>
    let isAuthenticated = false;
    let authToken = null;

    // Initialize Google Identity Services
    window.onload = function() {
      google.accounts.id.initialize({
        client_id: "573154595273-f5anosm6qld1mg1vgqqiv7rdvvp5p6sm.apps.googleusercontent.com",
        callback: handleCredentialResponse
      });
      // Render the Google Sign-In button within our container.
      google.accounts.id.renderButton(
          document.getElementById('google-signin-button'),
          { theme: "outline", size: "large" }
      );
    };

    // Callback function triggered after Google sign-in.
    function handleCredentialResponse(response) {
      authToken = response.credential;
      isAuthenticated = true;
      
      // Decode token payload to extract user info.
      const payload = JSON.parse(atob(authToken.split('.')[1]));
      const userName = payload.name || payload.email;
      
      // Hide the sign-in button container.
      document.getElementById('google-signin-button').style.display = 'none';
      // Show Logout and Dashboard buttons.
      document.getElementById('logout-btn').style.display = 'inline-block';
      document.getElementById('dashboard-btn').style.display = 'inline-block';
      // Optionally update Logout button text to include the username.
      document.getElementById('logout-btn').textContent = 'Logout ' + userName;
    }
    window.handleCredentialResponse = handleCredentialResponse;

    // Logout button functionality.
    document.getElementById('logout-btn').addEventListener('click', function() {
      // Reset authentication state.
      isAuthenticated = false;
      authToken = null;
      // Clear any displayed user info.
      document.getElementById('user-info').innerHTML = '';
      // Hide Logout and Dashboard buttons.
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
          throw new Error('Error fetching dashboard information');
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

Below is the revised `app.py` code with CORS enabled:

```python
# filepath: /home/srinman/git/oauth/scenario1/app.py
from flask import Flask, jsonify, request, abort
from flask_cors import CORS  # Enable Cross-Origin Resource Sharing
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
```

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
    In python program, change one of the email address to your email address.  For eg. user5@example.com to your email address (Google).
   - In a separate terminal, run:
   
     ```bash
     python app.py
     ```
   
   - The Flask app will run on [http://localhost:5000](http://localhost:5000).

4. **Test the Workflow:**
   - Open your browser and navigate to [http://localhost:8000](http://localhost:8000).
   - Click the rendered Google Sign-In button to log in.
   - Once logged in, use the Dashboard button to fetch and display your protected user information from the backend.

   This setup allows you to see how the direct ID token flow works in practice, with a simple user interface and a backend that verifies the token and serves user-specific data. It uses a trusted third-party identity provider (Google) to authenticate users and a custom backend to manage user data securely.
# Google OAuth Setup Instructions

Follow these steps to set up Google OAuth 2.0 authentication for your Research Paper Podcast Generator application.

## 1. Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Click on the project dropdown at the top of the page.
3. Click **New Project**.
4. Name your project (e.g., "Research Paper Podcast") and click **Create**.
5. Select your new project from the project dropdown.

## 2. Configure the OAuth Consent Screen

1. In the Google Cloud Console, navigate to **APIs & Services** > **OAuth consent screen**.
2. Select the user type for your app:
   - **External**: Available to any Google user (recommended for most cases)
   - **Internal**: Only available to users in your Google Workspace organization
3. Click **Create**.
4. Enter the required information:
   - App name: "Research Paper Podcast Generator"
   - User support email: Your email address
   - Developer contact information: Your email address
   - Authorized domains: Your application domain (if applicable)
5. Click **Save and Continue**.
6. On the **Scopes** screen, add the following scopes:
   - `openid`
   - `https://www.googleapis.com/auth/userinfo.email`
   - `https://www.googleapis.com/auth/userinfo.profile`
7. Click **Save and Continue**.
8. On the **Test users** screen (for External apps), add your email and any test users.
9. Click **Save and Continue**.
10. Review your settings and click **Back to Dashboard**.

## 3. Create OAuth 2.0 Credentials

1. In the Google Cloud Console, navigate to **APIs & Services** > **Credentials**.
2. Click **Create Credentials** and select **OAuth client ID**.
3. Select **Web application** as the application type.
4. Enter a name for your client ID (e.g., "Research Paper Podcast Web Client").
5. Under **Authorized JavaScript origins**, add your application's origins:
   - For development: `http://localhost:5000`
   - For production: Your actual domain (e.g., `https://podcast.example.com`)
6. Under **Authorized redirect URIs**, add your callback URLs:
   - For development: `http://localhost:5000/auth/google/callback`
   - For production: `https://podcast.example.com/auth/google/callback`
7. Click **Create**.
8. A popup will show your **Client ID** and **Client Secret**. Save these securely.

## 4. Configure Your Application

1. Create a `.env` file in your project root directory:

```
# Flask Settings
FLASK_ENV=development
SECRET_KEY=your_secure_random_key

# Google OAuth
GOOGLE_CLIENT_ID=your_client_id_from_google
GOOGLE_CLIENT_SECRET=your_client_secret_from_google
GOOGLE_REDIRECT_URI=http://localhost:5000/auth/google/callback

# Database
DATABASE_URL=sqlite:///app.db
```

2. For production, update these values accordingly and use a proper database like PostgreSQL.

## 5. Security Best Practices

1. Keep your `.env` file out of version control (add it to `.gitignore`).
2. Use a proper secret management system for production environments.
3. Regularly rotate your OAuth client secret.
4. Use HTTPS in production to secure all communications.
5. Implement proper session management and CSRF protection.

## 6. Testing the Authentication Flow

1. Start your Flask application: `python main.py`
2. Navigate to `http://localhost:5000/` in your browser.
3. Click the "Login with Google" link.
4. You should be redirected to Google's login page.
5. After logging in, you should be redirected back to your application's profile page.

## 7. Going to Production

1. When your app is ready for production:
   - For **Internal** user type: You're all set.
   - For **External** user type: Complete verification if you have more than 100 users.
2. Update all redirect URIs to your production URLs.
3. Configure a production database (PostgreSQL recommended).
4. Use a proper web server (e.g., Gunicorn) behind a reverse proxy (e.g., Nginx).
5. Set up HTTPS using a valid SSL certificate.
6. Implement monitoring and logging for authentication issues.
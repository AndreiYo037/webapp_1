# Google OAuth Setup Guide (Option 1: Django Admin)

This guide will walk you through setting up Google OAuth authentication for your flashcard app using Django Admin.

## Step 1: Get Google OAuth Credentials

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/
   - Sign in with your Google account

2. **Create or Select a Project**
   - Click the project dropdown at the top
   - Click "New Project" or select an existing project
   - Give it a name (e.g., "Flashcard App")

3. **Enable Google+ API**
   - Go to "APIs & Services" → "Library"
   - Search for "Google+ API" or "Google Identity"
   - Click on it and click "Enable"

4. **Create OAuth Credentials**
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - If prompted, configure the OAuth consent screen first:
     - Choose "External" (unless you have a Google Workspace)
     - Fill in the required fields (App name, User support email, etc.)
     - Add your email to "Test users" if needed
     - Save and continue through the steps
   - Back to "Create OAuth client ID":
     - Application type: **Web application**
     - Name: "Flashcard App" (or any name)
     - **Authorized redirect URIs**: Add your Railway domain:
       ```
       https://your-app-name.railway.app/accounts/google/login/callback/
       ```
       (Replace `your-app-name` with your actual Railway app name)
   - Click "Create"
   - **Copy the Client ID and Client Secret** (you'll need these in Step 3)

## Step 2: Access Django Admin

1. **Create a Superuser** (if you haven't already)
   - In Railway, go to your service → "Deployments" → "View Logs"
   - Or use Railway CLI:
     ```bash
     railway run python manage.py createsuperuser
     ```
   - Enter username, email, and password when prompted

2. **Access Admin Panel**
   - Go to: `https://your-app-name.railway.app/admin/`
   - Sign in with your superuser credentials

## Step 3: Configure Google OAuth in Django Admin

1. **Navigate to Social Applications**
   - In Django Admin, find "SOCIAL ACCOUNTS" section
   - Click on "Social applications"

2. **Add New Social Application**
   - Click "Add Social Application" button (top right)

3. **Fill in the Form**
   - **Provider**: Select `google` from dropdown
   - **Name**: Enter `Google` (or any name)
   - **Client id**: Paste your **Client ID** from Step 1
   - **Secret key**: Paste your **Client Secret** from Step 1
   - **Sites**: 
     - In the "Available sites" box, select your site (e.g., `example.com` or your Railway domain)
     - Click the right arrow (→) to move it to "Chosen sites"
     - **Important**: Your site must be in "Chosen sites" for OAuth to work!

4. **Save**
   - Click "Save" button

## Step 4: Update Site Domain (if needed)

If your site domain is incorrect:

1. Go to "Sites" → "Sites" in Django Admin
2. Click on the site (usually `example.com`)
3. Change:
   - **Domain name**: Your Railway domain (e.g., `your-app-name.railway.app`)
   - **Display name**: Your app name
4. Save

## Step 5: Test Google OAuth

1. Go to your app homepage: `https://your-app-name.railway.app/`
2. Click "Sign In with Google" button
3. You should be redirected to Google's sign-in page
4. After signing in, you should be redirected back to your app

## Troubleshooting

### Error: "Missing required parameter: client_id"
- Make sure you added the Social Application in Django Admin
- Verify the Client ID and Secret are correct
- Ensure your site is added to the Social Application's "Chosen sites"

### Error: "redirect_uri_mismatch"
- Check that your authorized redirect URI in Google Cloud Console matches exactly:
  `https://your-app-name.railway.app/accounts/google/login/callback/`
- Make sure there's a trailing slash (`/`) at the end
- Verify your Railway domain is correct

### Can't access Django Admin
- Make sure you created a superuser: `python manage.py createsuperuser`
- Check that migrations have run: `python manage.py migrate`

### OAuth works but user can't sign in
- Check that the site domain in Django Admin matches your Railway domain
- Verify the Social Application has the correct site selected

## Alternative: Use Environment Variables (Option 2)

If you prefer to use environment variables instead of Django Admin:

1. Set in Railway:
   - `GOOGLE_OAUTH_CLIENT_ID`: Your Client ID
   - `GOOGLE_OAUTH_CLIENT_SECRET`: Your Client Secret

2. The app will automatically configure OAuth on startup using the management command.


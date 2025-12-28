# Gmail Email Setup for Railway

This guide will help you configure Gmail SMTP to send emails from your Flashcard App on Railway.

## Step 1: Enable 2-Factor Authentication

1. Go to your Google Account: https://myaccount.google.com
2. Click **Security** in the left sidebar
3. Under "Signing in to Google", enable **2-Step Verification** if not already enabled

## Step 2: Generate an App Password

1. Go to: https://myaccount.google.com/apppasswords
2. Select **Mail** as the app
3. Select **Other (Custom name)** as the device
4. Enter a name like "Flashcard App Railway"
5. Click **Generate**
6. **Copy the 16-character password** (it will look like: `abcd efgh ijkl mnop`)
7. **Important:** You won't be able to see this password again, so copy it now!

## Step 3: Add Environment Variables to Railway

1. Go to your Railway project dashboard
2. Click on your service
3. Go to **Variables** tab
4. Add the following environment variables:

```
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=abcdefghijklmnop
DEFAULT_FROM_EMAIL=your-email@gmail.com
SERVER_EMAIL=your-email@gmail.com
```

**Important Notes:**
- Replace `your-email@gmail.com` with your actual Gmail address
- Replace `abcdefghijklmnop` with the 16-character App Password you generated (remove spaces)
- The App Password is NOT your regular Gmail password

## Step 4: Deploy/Restart

After adding the environment variables:
1. Railway will automatically redeploy your service
2. Or manually trigger a redeploy from the Railway dashboard

## Step 5: Test Email Sending

1. Go to your app and register a new account or update your email
2. Check your inbox (and spam folder) for the verification email
3. If emails still don't arrive, check Railway logs for any SMTP errors

## Troubleshooting

### Emails not arriving:
1. **Check Railway logs** - Look for SMTP errors
2. **Check spam folder** - Gmail might mark them as spam initially
3. **Verify App Password** - Make sure you're using the App Password, not your regular password
4. **Check 2FA is enabled** - App Passwords only work with 2FA enabled

### Common Errors:

**"Invalid credentials"**
- Make sure you're using the App Password, not your regular Gmail password
- Verify the App Password was copied correctly (no spaces)

**"Connection refused"**
- Check that `EMAIL_HOST=smtp.gmail.com` is correct
- Verify `EMAIL_PORT=587` and `EMAIL_USE_TLS=True`

**"Email backend is console"**
- This means `EMAIL_HOST` environment variable is not set
- Add the environment variables in Railway and redeploy

## Alternative: SendGrid (Recommended for Production)

For production apps, consider using SendGrid instead of Gmail:
- More reliable for high-volume sending
- Better deliverability
- Free tier: 100 emails/day

See `SETTINGS_GUIDE.md` for SendGrid setup instructions.


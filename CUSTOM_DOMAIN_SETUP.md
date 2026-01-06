# Custom Domain Setup Guide

This guide covers setting up custom domains for both your web app and email.

---

## Part 1: Custom Domain for Web App (Railway)

### Step 1: Add Domain in Railway

1. Go to your Railway project dashboard
2. Click on your service
3. Go to **Settings** → **Domains**
4. Click **"Add Domain"** or **"Custom Domain"**
5. Enter your domain (e.g., `flashcardapp.com` or `app.yourdomain.com`)
6. Railway will show you DNS records to add

### Step 2: Add DNS Records at Your Domain Provider

Railway will provide you with DNS records. Typically you need:

#### Option A: CNAME Record (Recommended for subdomains)
- **Type:** `CNAME`
- **Name/Host:** `app` (or `www`, or leave blank for root domain)
- **Value/Target:** `your-app.up.railway.app` (Railway will provide exact value)
- **TTL:** `Auto` or `3600`

#### Option B: A Record (For root domain)
- **Type:** `A`
- **Name/Host:** `@` (or blank for root domain)
- **Value:** Railway will provide IP addresses
- **TTL:** `Auto` or `3600`

### Step 3: Update Django Settings

After Railway verifies your domain, update your Railway environment variables:

```bash
ALLOWED_HOSTS=flashcardapp.com,www.flashcardapp.com
CSRF_TRUSTED_ORIGINS=https://flashcardapp.com,https://www.flashcardapp.com
```

**Or** if you want to allow both Railway domain and custom domain:

```bash
ALLOWED_HOSTS=flashcardapp.com,www.flashcardapp.com,your-app.up.railway.app
CSRF_TRUSTED_ORIGINS=https://flashcardapp.com,https://www.flashcardapp.com,https://your-app.up.railway.app
```

### Step 4: Update Stripe Webhook URL

1. Go to Stripe Dashboard → Webhooks
2. Edit your webhook endpoint
3. Update URL to: `https://flashcardapp.com/webhook/payment/`
4. Save

### Step 5: Redeploy

After updating environment variables, Railway will automatically redeploy, or you can trigger a manual redeploy.

---

## Part 2: Custom Domain for Email (Resend)

### Step 1: Add Domain in Resend

1. Go to Resend Dashboard: https://resend.com/dashboard
2. Navigate to **Domains**
3. Click **"Add Domain"**
4. Enter your domain (e.g., `flashcardapp.com` or `mail.yourdomain.com`)
5. Resend will show you DNS records to add

### Step 2: Add DNS Records at Your Domain Provider

You need to add these DNS records (Resend will show exact values):

#### 1. Domain Verification (DKIM) - REQUIRED
- **Type:** `TXT`
- **Name/Host:** `resend._domainkey` (or `resend._domainkey.yourdomain` if provider requires full path)
- **Content/Value:** `p=MIGfMA0GCSqGSIb3DQEB...` (full value from Resend)
- **TTL:** `Auto` or `3600`

#### 2. Enable Sending - SPF Record - REQUIRED
- **Type:** `TXT`
- **Name/Host:** `send` (or `send.yourdomain` if provider requires full path)
- **Content/Value:** `v=spf1 include:amazonses.com ~all`
- **TTL:** `Auto` or `3600`

#### 3. Enable Sending - MX Record - REQUIRED
- **Type:** `MX`
- **Name/Host:** `send` (or `send.yourdomain` if provider requires full path)
- **Content/Value:** `feedback-smtp.ap-northeast-1.amazonses.com` (or value from Resend)
- **Priority:** `10`
- **TTL:** `Auto` or `3600`

#### 4. Enable Receiving - MX Record (Optional - only if you want to receive emails)
- **Type:** `MX`
- **Name/Host:** `@` (or root domain)
- **Content/Value:** `inbound-smtp.ap-northeast-1.amazonses.com`
- **Priority:** `10`
- **TTL:** `Auto` or `3600`

### Step 3: Verify Domain in Resend

1. After adding all DNS records, wait 5-30 minutes for DNS propagation
2. Go back to Resend Dashboard → Domains
3. Click on your domain
4. Click **"Verify Domain"** or **"I've added the records"**
5. Resend will check the DNS records (can take up to 72 hours, usually 5-30 minutes)

### Step 4: Update Railway Environment Variable

Once verified, update your Railway environment variable:

```bash
DEFAULT_FROM_EMAIL=noreply@flashcardapp.com
```

(Replace `flashcardapp.com` with your actual verified domain)

### Step 5: Redeploy

Redeploy your Railway app to apply the new email domain.

---

## Quick Reference: Common Domain Providers

### Cloudflare (Easiest for Resend)
- **Automatic Setup:** In Resend dashboard, click **"Sign in to Cloudflare"** → Authorize → Records added automatically ✅
- **Manual:** Cloudflare Dashboard → DNS → Records → Add record

### GoDaddy
1. Go to **My Products** → **Domains**
2. Click on your domain → **DNS** or **Manage DNS**
3. Add records in **Records** section

### Namecheap
1. Go to **Domain List** → Click **Manage** next to your domain
2. Go to **Advanced DNS** tab
3. Click **Add New Record**

### Google Domains
1. Click on your domain
2. Go to **DNS** section
3. Scroll to **Custom resource records**
4. Click **Create new record**

### AWS Route 53
1. Go to **Route 53** → **Hosted zones**
2. Select your domain's hosted zone
3. Click **Create record**

---

## Troubleshooting

### Web App Domain Not Working?

1. **Check DNS propagation:**
   - Use: `nslookup yourdomain.com` or `dig yourdomain.com`
   - Wait 5-30 minutes after adding records

2. **Verify Railway domain status:**
   - Check Railway dashboard → Settings → Domains
   - Should show "Active" or "Verified"

3. **Check ALLOWED_HOSTS:**
   - Make sure your domain is in Railway environment variable `ALLOWED_HOSTS`
   - Include both `yourdomain.com` and `www.yourdomain.com` if using both

4. **Check SSL Certificate:**
   - Railway automatically provisions SSL certificates
   - Wait a few minutes after domain verification

### Email Domain Not Verifying?

1. **Wait for DNS propagation:**
   - DNS changes can take 5-30 minutes (up to 72 hours)
   - Use https://dns.email to check if records are visible

2. **Verify record format:**
   - Some providers auto-append domain name
   - Try `resend._domainkey` instead of `resend._domainkey.yourdomain.com`
   - Check Resend dashboard for exact format needed

3. **Check for typos:**
   - Copy-paste values exactly from Resend
   - Verify priority is `10` for MX records

4. **Test DNS records:**
   ```bash
   # Check DKIM record
   nslookup -type=TXT resend._domainkey.yourdomain.com
   
   # Check SPF record
   nslookup -type=TXT send.yourdomain.com
   
   # Check MX record
   nslookup -type=MX send.yourdomain.com
   ```

---

## After Setup

### Web App
- ✅ Access your app at: `https://yourdomain.com`
- ✅ Update Stripe webhook URL to use custom domain
- ✅ Update any external integrations with new domain

### Email
- ✅ Emails will send from: `noreply@yourdomain.com` (or whatever you set in `DEFAULT_FROM_EMAIL`)
- ✅ Better email deliverability with verified domain
- ✅ Professional email addresses

---

## Example: Complete Setup

Let's say you want to use `flashcardapp.com` for both web and email:

### Web App Setup:
1. Railway → Settings → Domains → Add `flashcardapp.com`
2. Add CNAME record: `flashcardapp.com` → `your-app.up.railway.app`
3. Railway env: `ALLOWED_HOSTS=flashcardapp.com,www.flashcardapp.com`
4. Wait for SSL certificate (automatic)

### Email Setup:
1. Resend → Domains → Add `flashcardapp.com`
2. Add DNS records (DKIM, SPF, MX) as shown above
3. Wait for verification (5-30 minutes)
4. Railway env: `DEFAULT_FROM_EMAIL=noreply@flashcardapp.com`
5. Redeploy

### Result:
- Web app: `https://flashcardapp.com`
- Email: `noreply@flashcardapp.com`

---

## Need Help?

- **Railway Docs:** https://docs.railway.app/guides/custom-domains
- **Resend Docs:** https://resend.com/docs
- **DNS Checker:** https://dns.email
- **DNS Propagation:** https://www.whatsmydns.net/


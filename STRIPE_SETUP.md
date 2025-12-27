# Stripe Payment Integration Setup

## ✅ Integration Complete

Stripe has been fully integrated for monthly subscriptions. The app now uses Stripe Checkout for secure payment processing.

## Setup Steps

### 1. Get Stripe API Keys

1. Go to https://stripe.com and create an account (or login)
2. Navigate to **Developers** → **API keys**
3. Copy your **Publishable key** and **Secret key**
   - Use **Test mode** keys for development
   - Use **Live mode** keys for production

### 2. Set Environment Variables in Railway

Go to Railway Dashboard → Your Service → Variables and add:

```
STRIPE_PUBLIC_KEY=pk_test_... (or pk_live_... for production)
STRIPE_SECRET_KEY=sk_test_... (or sk_live_... for production)
STRIPE_WEBHOOK_SECRET=whsec_... (get from Stripe Dashboard → Webhooks)
```

### 3. Create Stripe Product (Optional)

You can create a product in Stripe Dashboard, or the app will create prices dynamically.

**Option A: Use Dynamic Pricing (Current Setup)**
- No action needed
- App creates prices on-the-fly

**Option B: Use Stripe Price IDs**
1. Go to Stripe Dashboard → Products
2. Create a product: "Premium Monthly Subscription"
3. Add a recurring price: $9.99/month
4. Copy the Price ID (starts with `price_`)
5. Add to Railway: `STRIPE_PRICE_ID_MONTHLY=price_...`

### 4. Set Up Webhook Endpoint

1. Go to Stripe Dashboard → **Developers** → **Webhooks**
2. Click **Add endpoint**
3. Endpoint URL: `https://your-app.railway.app/webhook/payment/`
4. Select events to listen to:
   - `checkout.session.completed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
5. Copy the **Signing secret** (starts with `whsec_`)
6. Add to Railway: `STRIPE_WEBHOOK_SECRET=whsec_...`

## How It Works

1. **User clicks "Subscribe Now"** → Redirected to Stripe Checkout
2. **User completes payment** → Stripe processes payment
3. **Success redirect** → App creates/updates subscription
4. **Webhook events** → App handles subscription lifecycle (renewals, cancellations)

## Testing

### Test Mode
- Use test API keys (`pk_test_...`, `sk_test_...`)
- Use test card: `4242 4242 4242 4242`
- Any future expiry date, any CVC
- Use Stripe CLI for local webhook testing

### Production
- Switch to live API keys
- Update webhook URL to production domain
- Test with real payment methods

## Stripe CLI (For Local Testing)

```bash
# Install Stripe CLI
# Then forward webhooks to local server:
stripe listen --forward-to localhost:8000/webhook/payment/
```

## Features Implemented

✅ Stripe Checkout integration
✅ Monthly subscription ($9.99/month)
✅ Automatic subscription creation
✅ Webhook handling for:
   - Subscription creation
   - Subscription updates
   - Subscription cancellations
   - Payment success/failure
✅ Email notifications
✅ Subscription management

## Security

- Webhook signature verification
- CSRF protection
- Secure API key storage (environment variables)
- HTTPS required for production

## Troubleshooting

**"Payment system is not configured"**
- Check that STRIPE_PUBLIC_KEY and STRIPE_SECRET_KEY are set

**Webhook not working**
- Verify STRIPE_WEBHOOK_SECRET is set
- Check webhook URL in Stripe Dashboard
- Verify webhook events are selected

**Subscription not activating**
- Check Railway logs for errors
- Verify webhook is receiving events
- Check subscription_success view is being called



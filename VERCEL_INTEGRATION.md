# Integration Guide: Vercel + External Backend

Since your main website is on **Vercel** and this scanner requires a full backend (Python + Playwright), the best architectural pattern is the **Proxy Pattern**.

You cannot easily run this heavy Python/Playwright app directly on Vercel Serverless due to size limits and browser dependencies. Instead, you will deploy the scanner to a container platform (like Render) and "mask" it behind your Vercel domain using Rewrites.

## Step 1: Deploy the Scanner (Backend)

First, deploy this `ucp_compliance_scanner` folder to a platform that supports Docker. **Render** is recommended as they have a generous free tier and support Dockerfiles natively.

1.  Push this code to a GitHub repository.
2.  Sign up for [Render.com](https://render.com).
3.  Create a **New Web Service**.
4.  Connect your GitHub repo.
5.  Select **Docker** as the environment.
6.  Deploy.
7.  Copy your new URL (e.g., `https://ucp-scanner-xyz.onrender.com`).

## Step 2: Configure Vercel Rewrites

Now, tell Vercel to allow users to visit `/testAgenticReadiness` on your site, but secretly fetch the content from Render.

1.  Go to your main website's code repository (the one deployed on Vercel).
2.  Open (or create) the `vercel.json` file in the root.
3.  Add the `rewrites` config:

```json
{
  "rewrites": [
    {
      "source": "/testAgenticReadiness",
      "destination": "https://ucp-compliance-scanner.onrender.com/"
    },
    {
      "source": "/testAgenticReadiness/:match*",
      "destination": "https://ucp-compliance-scanner.onrender.com/:match*"
    }
  ]
}
```

*Replace `https://ucp-scanner-xyz.onrender.com` with your actual Render URL.*

## Step 3: Deploy Vercel

Push the changes (`vercel.json`) to your main website repo. Vercel will redeploy.

## How it works

1.  User visits `https://openquest.solutions/testAgenticReadiness`.
2.  Vercel sees the rewrite rule.
3.  Vercel internally fetches the page from Render.
4.  Vercel serves the page to the user under your domain (`openquest.solutions`).
5.  The Python app uses **relative paths** for its API calls (thanks to our recent code update), so when the frontend asks for `scan`, it requests `https://openquest.solutions/testAgenticReadiness/scan`, which Vercel again proxies to Render.

This gives you a seamless "Same Domain" experience without managing servers on your main domain.

# Deployment Guide: UCP Compliance Scanner

To integrate this scanner with your website, you need to host this application on a server and then link to it from your main site.

## 1. Hosting the Application

You cannot simply copy these files to a static web host (like GitHub Pages or basic Wix/WordPress hosting) because this application requires a **backend server** to run the Python compliance checks.

We recommend deploying to a platform that supports Docker containers, such as:
- **Render / Railway / Heroku** (Easiest)
- **AWS App Runner / Google Cloud Run** (Scalable)
- **DigitalOcean App Platform**

### Deployment Steps (using Docker)

1.  **Build the Container**:
    The provided `Dockerfile` creates a production-ready image with all necessary dependencies (including the Chromium browser for PDF generation).

2.  **Deploy**:
    Point your cloud provider to this repository or upload the code. Ensure the port is set to `8080` (or configure your provider to match the Dockerfile).

## 2. Integration with Your Website

Once deployed, you will have a public URL (e.g., `https://ucp-scanner.your-domain.com` or `https://scanner-app.herokuapp.com`).

### Option A: Subdomain (Recommended)
Set up a subdomain like `scan.yourwebsite.com` that points to your deployed application. This looks the most professional and keeps the user "on your brand".

**Integration:**
Add the text link to your main website's HTML:
```html
<a href="https://scan.yourwebsite.com" target="_blank" class="btn-primary">
  Test your UCP readiness today
</a>
```

### Option B: Direct Link
If you don't want to set up a custom domain immediately, just link to the cloud provider's URL.

**Integration:**
```html
<a href="https://your-app-name.onrender.com" target="_blank">
  Test your UCP readiness today
</a>
```

### Option C: Iframe Embed
You can embed the scanner directly inside a page on your existing site (e.g., `yourwebsite.com/tools/scanner`).

**Integration:**
Create a new page on your site and add:
```html
<iframe src="https://scan.yourwebsite.com" 
        width="100%" 
        height="800px" 
        frameborder="0" 
        style="border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
</iframe>
```

**Note:** If using iframes, ensure your deployment allows embedding (Cross-Origin Policy).

## 3. Configuration

- **Output Directory**: The app writes reports to the `/app/output` directory. in a containerized environment, these files are ephemeral. For a permanent archive, configure your cloud provider to mount a persistent volume to `/app/output` or update the code to upload PDFs to S3/Cloud Storage.

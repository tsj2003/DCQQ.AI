---
description: Setup GCP credentials and resources for DocQA AI deployment
---

# GCP Setup Guide

## Step 1: Create GCP Project

// turbo
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click project selector (top left) → "New Project"
3. Enter project name: `docqa-ai-prod`
4. Note down the **Project ID** (e.g., `docqa-ai-prod-123456`)

## Step 2: Enable Billing

1. In the console, go to "Billing"
2. Link a payment method (credit card required, but free tier won't charge)
3. Enable billing for your project

## Step 3: Enable Required APIs

// turbo
```bash
# Install gcloud CLI first: https://cloud.google.com/sdk/docs/install

# Login
gcloud auth login

# Set project
gcloud config set PROJECT_ID your-project-id

# Enable APIs
gcloud services enable run.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable redis.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

## Step 4: Create Service Account (For CI/CD)

// turbo
```bash
# Create service account
gcloud iam service-accounts create docqa-deployer \
  --display-name="DocQA AI Deployer"

# Grant permissions
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:docqa-deployer@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:docqa-deployer@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/cloudsql.admin"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:docqa-deployer@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/redis.admin"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:docqa-deployer@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.admin"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:docqa-deployer@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:docqa-deployer@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/cloudbuild.builds.editor"

# Create and download key
gcloud iam service-accounts keys create gcp-sa-key.json \
  --iam-account=docqa-deployer@PROJECT_ID.iam.gserviceaccount.com
```

## Step 5: Add Secrets to GitHub

1. Go to your GitHub repo → Settings → Secrets and variables → Actions
2. Add these **Repository secrets**:

| Secret Name | Value |
|-------------|-------|
| `GCP_PROJECT_ID` | Your project ID (e.g., `docqa-ai-prod-123456`) |
| `GCP_SA_KEY` | Copy entire contents of `gcp-sa-key.json` file |
| `OPENAI_API_KEY` | Your OpenAI API key (sk-...) |

## Step 6: Manual Deploy (Without CI/CD)

If not using GitHub Actions:

```bash
# Login locally
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Get OpenAI key
echo "Enter OpenAI API key:"
read -s OPENAI_KEY

# Run deployment
export PROJECT_ID=YOUR_PROJECT_ID
export OPENAI_API_KEY=$OPENAI_KEY
cd docqa-ai
./scripts/deploy-gcp.sh
```

## Step 7: Get URLs After Deploy

```bash
# Get frontend URL
gcloud run services describe docqa-frontend \
  --region=us-central1 \
  --format='value(status.url)'

# Get backend URL  
gcloud run services describe docqa-backend \
  --region=us-central1 \
  --format='value(status.url)'
```

## Troubleshooting

### Permission Denied
```bash
# Make sure you're owner or have these roles:
- Owner
- or: Editor + Cloud Run Admin + Cloud SQL Admin
```

### API Not Enabled
```bash
# Check enabled APIs
gcloud services list --enabled

# Enable missing ones
gcloud services enable [API_NAME]
```

### Quota Exceeded
```bash
# Check quotas
gcloud compute project-info describe --project PROJECT_ID

# Request increase in console: IAM & Admin → Quotas
```

## Quick Checklist

- [ ] GCP project created
- [ ] Billing enabled
- [ ] APIs enabled (7 services)
- [ ] Service account created
- [ ] JSON key downloaded
- [ ] GitHub secrets added
- [ ] OpenAI API key ready

#!/bin/bash
# Setup script for GCP Project: api1-494609

PROJECT_ID="api1-494609"
REGION="us-central1"

echo "=== Setting up GCP Project: $PROJECT_ID ==="

# Set project
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "Enabling APIs..."
gcloud services enable run.googleapis.com --quiet
gcloud services enable sqladmin.googleapis.com --quiet
gcloud services enable redis.googleapis.com --quiet
gcloud services enable secretmanager.googleapis.com --quiet
gcloud services enable storage.googleapis.com --quiet
gcloud services enable cloudbuild.googleapis.com --quiet

# Create service account for deployment
echo "Creating service account..."
gcloud iam service-accounts create docqa-deployer \
  --display-name="DocQA AI Deployer" \
  --quiet 2>/dev/null || echo "Service account already exists"

# Grant permissions
echo "Granting permissions..."
SA_EMAIL="docqa-deployer@$PROJECT_ID.iam.gserviceaccount.com"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/run.admin" \
  --quiet

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/cloudsql.admin" \
  --quiet

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/redis.admin" \
  --quiet

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/secretmanager.admin" \
  --quiet

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/storage.admin" \
  --quiet

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/cloudbuild.builds.editor" \
  --quiet

# Allow enabling APIs
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/serviceusage.admin" \
  --quiet

# Create and download key
echo "Creating service account key..."
gcloud iam service-accounts keys create gcp-sa-key.json \
  --iam-account=$SA_EMAIL \
  --quiet

echo ""
echo "=== Setup Complete! ==="
echo ""
echo "Key file created: gcp-sa-key.json"
echo ""
echo "Next steps:"
echo "1. Add this to GitHub Secrets:"
echo "   - GCP_PROJECT_ID: api1-494609"
echo "   - GCP_SA_KEY: (copy contents of gcp-sa-key.json)"
echo "   - OPENAI_API_KEY: (your OpenAI key)"
echo ""
echo "2. Or deploy manually:"
echo "   ./scripts/deploy-gcp.sh"
echo ""

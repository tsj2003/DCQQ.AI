---
description: Deploy DocQA AI to Google Cloud Platform
---

# GCP Deployment Guide

## Architecture

- **Backend**: Cloud Run (containerized FastAPI)
- **Frontend**: Cloud Run (containerized React + Nginx)
- **Database**: Cloud SQL (PostgreSQL 16)
- **Cache**: Memorystore for Redis
- **Storage**: Cloud Storage (for FAISS indexes)
- **Secrets**: Secret Manager

## Prerequisites

1. Install Google Cloud SDK: https://cloud.google.com/sdk/docs/install
2. Create a GCP project and enable billing
3. Enable required APIs:
   ```bash
   gcloud services enable run.googleapis.com
   gcloud services enable sqladmin.googleapis.com
   gcloud services enable redis.googleapis.com
   gcloud services enable secretmanager.googleapis.com
   gcloud services enable storage.googleapis.com
   ```

## Quick Deploy

// turbo
1. Set up GCP project:
   ```bash
   export PROJECT_ID=your-project-id
   export REGION=us-central1
   gcloud config set project $PROJECT_ID
   ```

2. Run deployment script:
   ```bash
   cd /Users/tarandeepsinghjuneja/ASSIGNMENT SDE 1/docqa-ai
   chmod +x scripts/deploy-gcp.sh
   ./scripts/deploy-gcp.sh
   ```

## Manual Deployment Steps

### 1. Create Secrets

```bash
# Generate secrets
gcloud secrets create jwt-secret --data-file=- <<< "$(openssl rand -base64 32)"
gcloud secrets create openai-api-key --data-file=- <<< "your-openai-api-key"
```

### 2. Create Cloud SQL Instance

```bash
gcloud sql instances create docqa-postgres \
  --database-version=POSTGRES_16 \
  --tier=db-f1-micro \
  --region=$REGION \
  --storage-size=10GB \
  --storage-auto-increase

# Create database
gcloud sql databases create docqa --instance=docqa-postgres

# Create user
gcloud sql users create docqauser \
  --instance=docqa-postgres \
  --password=$(openssl rand -base64 16)
```

### 3. Create Redis Instance

```bash
gcloud redis instances create docqa-redis \
  --tier=basic \
  --size=1 \
  --region=$REGION \
  --redis-version=redis_7_0
```

### 4. Deploy Backend

```bash
cd backend
gcloud builds submit --tag gcr.io/$PROJECT_ID/docqa-backend

gcloud run deploy docqa-backend \
  --image gcr.io/$PROJECT_ID/docqa-backend \
  --region=$REGION \
  --platform=managed \
  --allow-unauthenticated \
  --set-secrets=JWT_SECRET_KEY=jwt-secret:latest,OPENAI_API_KEY=openai-api-key:latest \
  --set-env-vars=DATABASE_URL=postgresql+asyncpg://docqauser:PASSWORD@/docqa?host=/cloudsql/$PROJECT_ID:$REGION:docqa-postgres,REDIS_URL=redis://REDIS_IP:6379/0 \
  --add-cloudsql-instances=$PROJECT_ID:$REGION:docqa-postgres
```

### 5. Deploy Frontend

```bash
cd frontend
gcloud builds submit --tag gcr.io/$PROJECT_ID/docqa-frontend

gcloud run deploy docqa-frontend \
  --image gcr.io/$PROJECT_ID/docqa-frontend \
  --region=$REGION \
  --platform=managed \
  --allow-unauthenticated \
  --set-env-vars=BACKEND_URL=https://docqa-backend-xxx-uc.a.run.app
```

## Accessing the Application

Get the frontend URL:
```bash
gcloud run services describe docqa-frontend --region=$REGION --format='value(status.url)'
```

## Cleanup

```bash
./scripts/destroy-gcp.sh
```

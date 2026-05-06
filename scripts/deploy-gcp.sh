#!/bin/bash
# DocQA AI - GCP Deployment Script
# This script deploys the application to Google Cloud Platform

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID=${PROJECT_ID:-$(gcloud config get-value project)}
REGION=${REGION:-us-central1}
BACKEND_SERVICE_NAME="docqa-backend"
FRONTEND_SERVICE_NAME="docqa-frontend"
SQL_INSTANCE_NAME="docqa-postgres"
REDIS_INSTANCE_NAME="docqa-redis"

echo -e "${GREEN}=== DocQA AI GCP Deployment ===${NC}"
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Check prerequisites
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI not found. Please install Google Cloud SDK.${NC}"
    exit 1
fi

if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}Error: PROJECT_ID not set. Run: gcloud config set project YOUR_PROJECT_ID${NC}"
    exit 1
fi

# Get OpenAI API Key
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${YELLOW}Enter your OpenAI API Key:${NC}"
    read -s OPENAI_API_KEY
    echo ""
fi

# Generate JWT Secret
JWT_SECRET=$(openssl rand -base64 32)

echo -e "${GREEN}Step 1: Enabling required APIs...${NC}"
gcloud services enable run.googleapis.com sqladmin.googleapis.com redis.googleapis.com secretmanager.googleapis.com storage.googleapis.com cloudbuild.googleapis.com --quiet 2>/dev/null || echo -e "${YELLOW}APIs may already be enabled or permission denied${NC}"

# Create secrets
echo -e "${GREEN}Step 2: Creating secrets in Secret Manager...${NC}"
echo -n "$JWT_SECRET" | gcloud secrets create jwt-secret --data-file=- --replica-location=$REGION --quiet 2>/dev/null || echo "jwt-secret already exists"
echo -n "$OPENAI_API_KEY" | gcloud secrets create openai-api-key --data-file=- --replica-location=$REGION --quiet 2>/dev/null || echo "openai-api-key already exists"

# Create Cloud SQL Instance
echo -e "${GREEN}Step 3: Creating Cloud SQL PostgreSQL instance...${NC}"
gcloud sql instances create $SQL_INSTANCE_NAME \
  --database-version=POSTGRES_16 \
  --tier=db-f1-micro \
  --region=$REGION \
  --storage-size=10GB \
  --storage-auto-increase \
  --availability-type=zonal \
  --quiet 2>/dev/null || echo -e "${YELLOW}SQL instance already exists${NC}"

# Get SQL connection name
SQL_CONNECTION_NAME=$(gcloud sql instances describe $SQL_INSTANCE_NAME --format='value(connectionName)')
echo "SQL Connection: $SQL_CONNECTION_NAME"

# Create database if not exists
gcloud sql databases create docqa --instance=$SQL_INSTANCE_NAME --quiet 2>/dev/null || echo -e "${YELLOW}Database already exists${NC}"

# Create SQL user
DB_PASSWORD=$(openssl rand -base64 16)
gcloud sql users create docqauser --instance=$SQL_INSTANCE_NAME --password=$DB_PASSWORD --quiet 2>/dev/null || echo -e "${YELLOW}SQL user already exists${NC}"

# Create Redis Instance
echo -e "${GREEN}Step 4: Creating Memorystore Redis instance...${NC}"
gcloud redis instances create $REDIS_INSTANCE_NAME \
  --tier=basic \
  --size=1 \
  --region=$REGION \
  --redis-version=redis_7_0 \
  --network=default \
  --quiet 2>/dev/null || echo -e "${YELLOW}Redis instance already exists${NC}"

# Get Redis IP
REDIS_IP=$(gcloud redis instances describe $REDIS_INSTANCE_NAME --region=$REGION --format='value(host)')
echo "Redis IP: $REDIS_IP"

# Create Cloud Storage bucket for FAISS indexes
echo -e "${GREEN}Step 5: Creating Cloud Storage bucket...${NC}"
BUCKET_NAME="${PROJECT_ID}-docqa-faiss"
gcloud storage buckets create gs://$BUCKET_NAME --location=$REGION --quiet 2>/dev/null || echo -e "${YELLOW}Bucket already exists${NC}"

# Build and deploy backend
echo -e "${GREEN}Step 6: Building and deploying backend...${NC}"
cd "$(dirname "$0")/../backend"

# Build container
gcloud builds submit --tag gcr.io/$PROJECT_ID/$BACKEND_SERVICE_NAME --timeout=20m --quiet

# Deploy to Cloud Run
echo -e "${GREEN}Deploying backend to Cloud Run...${NC}"
gcloud run deploy $BACKEND_SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$BACKEND_SERVICE_NAME \
  --region=$REGION \
  --platform=managed \
  --allow-unauthenticated \
  --memory=2Gi \
  --cpu=1 \
  --concurrency=80 \
  --max-instances=10 \
  --min-instances=0 \
  --timeout=300 \
  --set-secrets=JWT_SECRET_KEY=jwt-secret:latest,OPENAI_API_KEY=openai-api-key:latest \
  --set-env-vars=DATABASE_URL=postgresql+asyncpg://docqauser:${DB_PASSWORD}@/docqa?host=/cloudsql/${SQL_CONNECTION_NAME},REDIS_URL=redis://${REDIS_IP}:6379/0,ENVIRONMENT=production \
  --add-cloudsql-instances=$SQL_CONNECTION_NAME \
  --quiet

# Get backend URL
BACKEND_URL=$(gcloud run services describe $BACKEND_SERVICE_NAME --region=$REGION --format='value(status.url)')
echo -e "${GREEN}Backend deployed at: $BACKEND_URL${NC}"

# Build and deploy frontend
echo -e "${GREEN}Step 7: Building and deploying frontend...${NC}"
cd "$(dirname "$0")/../frontend"

# Build container with Cloud Run optimized Dockerfile
gcloud builds submit --tag gcr.io/$PROJECT_ID/$FRONTEND_SERVICE_NAME \
  --timeout=20m --quiet --config=- <<EOF
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-t'
      - 'gcr.io/$PROJECT_ID/$FRONTEND_SERVICE_NAME'
      - '--build-arg'
      - 'BACKEND_URL=$BACKEND_URL'
      - '-f'
      - 'Dockerfile.cloud'
      - '.'
images:
  - 'gcr.io/$PROJECT_ID/$FRONTEND_SERVICE_NAME'
EOF

# Deploy to Cloud Run
echo -e "${GREEN}Deploying frontend to Cloud Run...${NC}"
gcloud run deploy $FRONTEND_SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$FRONTEND_SERVICE_NAME \
  --region=$REGION \
  --platform=managed \
  --allow-unauthenticated \
  --memory=512Mi \
  --cpu=1 \
  --concurrency=100 \
  --max-instances=5 \
  --min-instances=0 \
  --set-env-vars=BACKEND_URL=$BACKEND_URL \
  --quiet

# Get frontend URL
FRONTEND_URL=$(gcloud run services describe $FRONTEND_SERVICE_NAME --region=$REGION --format='value(status.url)')

echo ""
echo -e "${GREEN}====================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}====================================${NC}"
echo ""
echo -e "${GREEN}Frontend URL:${NC} $FRONTEND_URL"
echo -e "${GREEN}Backend URL:${NC} $BACKEND_URL"
echo ""
echo -e "${YELLOW}Note: Wait 2-3 minutes for services to fully start${NC}"
echo ""

# Save deployment info
mkdir -p "$(dirname "$0")/../.gcp"
cat > "$(dirname "$0")/../.gcp/deployment-info.txt" << EOF
Project ID: $PROJECT_ID
Region: $REGION
Frontend URL: $FRONTEND_URL
Backend URL: $BACKEND_URL
SQL Instance: $SQL_CONNECTION_NAME
Redis IP: $REDIS_IP
Bucket: $BUCKET_NAME
EOF

echo -e "${GREEN}Deployment info saved to .gcp/deployment-info.txt${NC}"

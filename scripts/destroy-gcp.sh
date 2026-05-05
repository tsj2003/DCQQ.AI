#!/bin/bash

# DocQA AI - GCP Cleanup Script
# WARNING: This will delete all resources and data!

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROJECT_ID=${PROJECT_ID:-$(gcloud config get-value project)}
REGION=${REGION:-us-central1}

echo -e "${RED}WARNING: This will delete ALL GCP resources for DocQA AI${NC}"
echo -e "${RED}This action cannot be undone!${NC}"
echo ""
read -p "Are you sure? Type 'yes' to continue: " confirm

if [ "$confirm" != "yes" ]; then
    echo "Cancelled."
    exit 0
fi

echo -e "${YELLOW}Deleting Cloud Run services...${NC}"
gcloud run services delete docqa-backend --region=$REGION --quiet 2>/dev/null || true
gcloud run services delete docqa-frontend --region=$REGION --quiet 2>/dev/null || true

echo -e "${YELLOW}Deleting container images...${NC}"
gcloud container images delete gcr.io/$PROJECT_ID/docqa-backend --force-delete-tags --quiet 2>/dev/null || true
gcloud container images delete gcr.io/$PROJECT_ID/docqa-frontend --force-delete-tags --quiet 2>/dev/null || true

echo -e "${YELLOW}Deleting Cloud SQL instance...${NC}"
gcloud sql instances delete docqa-postgres --quiet 2>/dev/null || true

echo -e "${YELLOW}Deleting Redis instance...${NC}"
gcloud redis instances delete docqa-redis --region=$REGION --quiet 2>/dev/null || true

echo -e "${YELLOW}Deleting Cloud Storage bucket...${NC}"
gcloud storage buckets delete gs://${PROJECT_ID}-docqa-faiss --recursive 2>/dev/null || true

echo -e "${YELLOW}Deleting secrets...${NC}"
gcloud secrets delete jwt-secret --quiet 2>/dev/null || true
gcloud secrets delete openai-api-key --quiet 2>/dev/null || true

echo -e "${GREEN}Cleanup complete!${NC}"

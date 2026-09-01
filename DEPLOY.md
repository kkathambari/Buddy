# Deployment Guide

DevBuddy is containerized and ready for deployment to any container hosting platform, such as Google Cloud Run, AWS AppRunner, or a traditional VPS with Docker Compose.

## Prerequisites

1. A Firebase project with Firebase Authentication enabled.
2. An OpenAI API key.
3. A PostgreSQL database (optional but recommended for production; falls back to SQLite).

## Option 1: Google Cloud Run

Google Cloud Run is a fully managed serverless platform that is ideal for DevBuddy.

1. **Build and submit the container to Google Container Registry (GCR):**
   ```bash
   gcloud builds submit --tag gcr.io/[PROJECT-ID]/devbuddy-backend
   ```

2. **Deploy to Cloud Run:**
   ```bash
   gcloud run deploy devbuddy-backend \
     --image gcr.io/[PROJECT-ID]/devbuddy-backend \
     --platform managed \
     --allow-unauthenticated \
     --set-env-vars="OPENAI_API_KEY=your_key,FIREBASE_CREDENTIALS=your_firebase_creds_json" \
     --port 8000
   ```
   *Note: Pass `DATABASE_URL` via `--set-env-vars` if using Cloud SQL or an external PostgreSQL database.*

## Option 2: Docker Compose

For deploying on a traditional VPS (e.g. DigitalOcean, AWS EC2):

1. **Create a `docker-compose.yml` file:**
   ```yaml
   version: '3.8'
   services:
     web:
       build: .
       ports:
         - "8000:8000"
       environment:
         - OPENAI_API_KEY=${OPENAI_API_KEY}
         - FIREBASE_CREDENTIALS=${FIREBASE_CREDENTIALS}
         - DATABASE_URL=sqlite:////data/buddy.db
       volumes:
         - buddy_data:/data
   
   volumes:
     buddy_data:
   ```

2. **Run it:**
   ```bash
   export OPENAI_API_KEY="your_key"
   export FIREBASE_CREDENTIALS='{...}'
   docker-compose up -d
   ```

## Option 3: Heroku / Render

Both platforms natively support `Dockerfile` deployments. 
- Link your GitHub repository.
- Specify the root `Dockerfile`.
- Set the required environment variables (`OPENAI_API_KEY`, `FIREBASE_CREDENTIALS`).
- Deploy.

## Post-Deployment Health Check

Once deployed, visit `https://<your-deployment-url>/metrics` to ensure Prometheus metrics are being collected and that the backend has booted successfully.

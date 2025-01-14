# Building and Deploying the Family Letters Archive

This document describes how to build and deploy the Family Letters Archive application to Google Cloud Platform.

## Prerequisites

1. Install the [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)
2. Authenticate with Google Cloud:
   ```bash
   gcloud auth login
   gcloud auth configure-docker
   ```
3. Ensure you have the necessary permissions in the GCP project:
   - Cloud Build Service Account
   - Cloud Run Admin
   - Secret Manager Secret Accessor
   - Storage Object Viewer

## Configuration

The application requires the following resources to be set up:

1. **Google Cloud Storage Bucket** for images:
   ```bash
   gsutil mb gs://family-letters-dev
   ```

2. **Secret Manager** for the password:
   ```bash
   gcloud secrets create streamlit-password
   echo "your-password" | gcloud secrets versions add streamlit-password --data-file=-
   ```

3. **Service Account Permissions**:
   ```bash
   # Grant Secret Manager access to Cloud Run service account
   gcloud projects add-iam-policy-binding family-letters-447801 \
     --member=serviceAccount:25735584338-compute@developer.gserviceaccount.com \
     --role=roles/secretmanager.secretAccessor
   ```

## Deployment

1. **Quick Deploy**
   Run the deployment script:
   ```bash
   ./deploy.sh
   ```

2. **Manual Deployment Steps**
   If you need to deploy manually:
   ```bash
   # Build and deploy using Cloud Build
   gcloud builds submit --substitutions=_GCS_BUCKET_NAME=family-letters-dev

   # Make the service public
   gcloud run services add-iam-policy-binding family-letters-archive \
     --member="allUsers" \
     --role="roles/run.invoker" \
     --region=us-central1
   ```

## Uploading Images

Upload images to the GCS bucket:
```bash
gsutil -m cp -r ./dataset/* gs://family-letters-dev/
```

## Troubleshooting

1. **Permission Issues**
   - Verify service account permissions in IAM
   - Check Secret Manager access
   - Ensure GCS bucket permissions are correct

2. **Deployment Failures**
   - Check Cloud Build logs
   - Verify Dockerfile and requirements.txt are up to date
   - Ensure all necessary files are included in the build

3. **Runtime Issues**
   - Check Cloud Run logs
   - Verify environment variables are set correctly
   - Confirm Secret Manager and GCS access

## Architecture

The application uses:
- Cloud Run for hosting the Streamlit app
- Cloud Storage for image storage
- Secret Manager for password storage
- SQLite database (packaged in the container)
- Cloud Build for automated deployments

Last updated: 2025-01-13

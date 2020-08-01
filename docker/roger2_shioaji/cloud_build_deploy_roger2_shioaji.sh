BUILD_VERION=20200801.0
PROJECT_ID=etensword-order-agent
SERVICE_NAME=roger2-shioaji

cd /Users/roger_lo/Documents/workspace/etensword-agent/docker/roger2_shioaji/

gcloud builds submit --timeout=3600 --tag gcr.io/$PROJECT_ID/$SERVICE_NAME:$BUILD_VERION

gcloud run deploy $SERVICE_NAME \
       --image gcr.io/$PROJECT_ID/$SERVICE_NAME:$BUILD_VERION \
       --memory 1Gi \
       --region asia-east1 \
       --platform managed \
       --no-allow-unauthenticated


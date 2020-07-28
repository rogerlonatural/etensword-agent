BUILD_VERION=2020.07.26.0
PROJECT_ID=etensword-order-agent
SERVICE_NAME=roger2-shioaji

gcloud builds submit --timeout=3600 --tag gcr.io/$PROJECT_ID/$SERVICE_NAME:$BUILD_VERION

gcloud run deploy $SERVICE_NAME \
       --image gcr.io/$PROJECT_ID/$SERVICE_NAME:$BUILD_VERION \
       --memory 512M \
       --region asia-east1 \
       --platform managed \
       --no-allow-unauthenticated


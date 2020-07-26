BUILD_VERION=2020.07.25.0
PROJECT_ID=etensword-order-agent
SERVICE_NAME=etensword-order-agent

gcloud builds submit --timeout=3600 --tag gcr.io/$PROJECT_ID/etensword-order-agent:$BUILD_VERION

gcloud run deploy $SERVICE_NAME \
       --image gcr.io/$PROJECT_ID/etensword-order-agent:$BUILD_VERION \
       --platform managed \
       --no-allow-unauthenticated


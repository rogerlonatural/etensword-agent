BUILD_VERION=latest
PROJECT_ID=etensword-order-agent
SERVICE_NAME=agent-app

gcloud builds submit --timeout=3600 --tag gcr.io/$PROJECT_ID/$SERVICE_NAME:$BUILD_VERION


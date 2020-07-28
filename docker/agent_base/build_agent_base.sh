
BUILD_VERION=2020.07.26.0
PROJECT_ID=etensword-order-agent
SERVICE_NAME=agent-base

gcloud builds submit --timeout=3600 --tag gcr.io/$PROJECT_ID/$SERVICE_NAME:$BUILD_VERION
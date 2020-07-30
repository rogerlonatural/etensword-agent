BUILD_VERION=2020.07.31.0
PROJECT_ID=etensword-order-agent
SERVICE_NAME=agent-app

gcloud builds submit --timeout=3600 --tag gcr.io/$PROJECT_ID/$SERVICE_NAME:$BUILD_VERION


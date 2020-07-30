BUILD_VERION=local
PROJECT_ID=etensword-order-agent
SERVICE_NAME=agent-app

docker build --tag gcr.io/$PROJECT_ID/$SERVICE_NAME:$BUILD_VERION .

docker images
FROM gcr.io/etensword-order-agent/agent-app:latest

COPY ./.cert/* /app/config/

COPY ./setup.sh /app/setup.sh

RUN sh setup.sh

# Run the web service on container startup. Here we use the gunicorn
# webserver, with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app


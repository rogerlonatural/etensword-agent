FROM sinotrade/shioaji:latest

COPY ./requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME

ENV ETENSWORD_AGENT_CONF /app/config/agent_settings.ini

COPY . ./

RUN pip install /app/

RUN sh setup.sh

# Run the web service on container startup. Here we use the gunicorn
# webserver, with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app


FROM sinotrade/shioaji:latest

COPY requirements.txt /home/work/

RUN pip install -r requirements.txt


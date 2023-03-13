FROM python:3.9-slim-buster

RUN apt update
RUN apt install python3-pip -y
RUN python3 -m pip install --upgrade pip
RUN apt autoremove -y
RUN apt clean

WORKDIR /app

RUN python3 -m pip install --no-cache-dir requests

COPY ./ .

ENTRYPOINT ["python"] 
CMD ["monitoring_http.py"]

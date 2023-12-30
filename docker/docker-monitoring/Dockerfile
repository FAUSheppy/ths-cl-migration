FROM python:3-alpine

RUN pip install --upgrade pip

WORKDIR /app

RUN python3 -m pip install --no-cache-dir requests

COPY ./ .

ENTRYPOINT ["python"] 
CMD ["monitoring_http.py"]

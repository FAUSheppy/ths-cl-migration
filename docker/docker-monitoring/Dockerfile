FROM python:3-alpine

# force build-27-09-2024

RUN pip install --upgrade pip

WORKDIR /app

RUN python3 -m pip install --no-cache-dir requests

COPY ./ .

ENTRYPOINT ["python"] 
CMD ["monitoring_http.py"]

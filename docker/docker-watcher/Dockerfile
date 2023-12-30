FROM python:3-alpine

RUN apk add --no-cache inotify-tools

WORKDIR /app

COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt

COPY ./ .

ENTRYPOINT ["python"] 
CMD ["inotifywatch.py"]

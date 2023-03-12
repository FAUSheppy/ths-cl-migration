FROM python:3.9-slim-buster

RUN apt update
RUN apt install python3-pip -y
RUN python3 -m pip install --upgrade pip
RUN apt autoremove -y
RUN apt clean

WORKDIR /app

COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt

COPY ./ .

ENTRYPOINT ["python"] 
CMD ["mounted-fs-project-db.py"]

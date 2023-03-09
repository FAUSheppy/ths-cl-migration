FROM python:3.9-slim-buster

RUN apt update
RUN apt install python3-pip -y
RUN python3 -m pip install waitress
RUN python3 -m pip install --upgrade pip

WORKDIR /app
COPY ./ .

RUN python3 -m pip install --no-cache-dir -r requirements.txt

#HEALTHCHECK --interval=5m --timeout=5s CMD /usr/bin/curl http://localhost:5000/ || exit 1

RUN apt remove git -y
RUN apt autoremove -y

ENTRYPOINT ["python"] 
CMD ["mounted-fs-project-db.py", "--start", "2022" ]

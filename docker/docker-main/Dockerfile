FROM python:3.9-slim-buster

RUN apt update
RUN apt install python3-pip -y
RUN python3 -m pip install --upgrade pip
RUN apt install curl -y
RUN apt autoremove -y
RUN apt clean

WORKDIR /app

RUN python3 -m pip install waitress
RUN mkdir templates static

# static js/css bootstrap etc
RUN mkdir -p static/js static/css static/fontawesome/css static/js/addons

# css
RUN curl -s -o static/css/bootstrap.min.css   https://cdn.atlantishq.de/static/css/bootstrap.min.css
RUN curl -s -o static/css/mdb.min.css         https://cdn.atlantishq.de/static/css/mdb.min.css
RUN curl -s -o static/fontawesome/css/all.css https://cdn.atlantishq.de/static/js/mdb.min.js

# js
RUN curl -s -o static/js/bootstrap.min.js         https://cdn.atlantishq.de/static/js/bootstrap.min.js
RUN curl -s -o static/js/jquery.min.js            https://cdn.atlantishq.de/static/js/jquery.min.js
RUN curl -s -o static/js/datatables.min.js        https://cdn.atlantishq.de/static/js/datatables.min.js
RUN curl -s -o static/js/mdb.min.js               https://cdn.atlantishq.de/static/js/mdb.min.js
RUN curl -s -o static/js/addons/datatables.min.js https://cdn.atlantishq.de/static/js/addons/datatables.min.js

COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt

COPY ./ .
COPY templates/* templates/
COPY static/* static/

#HEALTHCHECK --interval=5m --timeout=5s CMD /usr/bin/curl http://localhost:5000/ || exit 1
EXPOSE 5000/tcp

ENTRYPOINT ["waitress-serve"] 
CMD ["--host", "0.0.0.0", "--port", "5000", "--call", "app:createApp"]

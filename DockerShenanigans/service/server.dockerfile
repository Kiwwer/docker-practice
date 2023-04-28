FROM python:3.8-slim

WORKDIR /server
COPY server/requirements.txt .
RUN pip install -r requirements.txt

RUN mkdir service
COPY __init__.py service/__init__.py
COPY server/ service/server/
EXPOSE 2000/udp

ENTRYPOINT ["python", "-m", "service.server.server"]

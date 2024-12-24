# syntax=docker/dockerfile:1

FROM python:3.13-alpine
WORKDIR /app

RUN apk add --no-cache git ffmpeg

COPY requirements.txt /app
RUN pip install -r requirements.txt

# Get rid of git warnings
RUN git config --global pull.rebase false
RUN git config --global safe.directory '*'

# requires mounting src to /app
CMD ["python", "-m", "voagel.main"]

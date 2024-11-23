# syntax=docker/dockerfile:1

FROM python:1.13-bullseye
WORKDIR /app

RUN set -eux; \
	apt-get update; \
	apt-get install -y --no-install-recommends \
		ffmpeg \
	; \
	rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app
RUN pip install -r requirements.txt

# Get rid of git warnings
RUN git config --global pull.rebase false
RUN git config --global safe.directory '*'

# requires mounting src to /app
CMD ["python", "-m", "voagel.main"]


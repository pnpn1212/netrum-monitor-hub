FROM python:3.12.3
RUN apt-get update && \
    apt-get install -y curl gnupg ca-certificates && \
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /usr/share/keyrings/nodesource.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" > /etc/apt/sources.list.d/nodesource.list && \
    apt-get update && \
    apt-get install -y nodejs && \
    node -v && npm -v
RUN pip install --no-cache-dir requests python-dotenv pytz tzlocal python-telegram-bot discord.py
RUN apt-get update && \
    apt-get install -y docker.io && \
    curl -L "https://github.com/docker/compose/releases/download/v2.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose && \
    chmod +x /usr/local/bin/docker-compose && \
    docker --version && docker-compose --version
WORKDIR /app
COPY . .
RUN if [ -f package.json ]; then npm install; fi
RUN npm list ethers || npm install ethers
RUN apt-get clean && rm -rf /var/lib/apt/lists/*
CMD ["python3", "netrum_main.py"]

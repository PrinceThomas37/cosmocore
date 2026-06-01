FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev wget ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/ephe && cd /app/ephe && \
    wget -q https://raw.githubusercontent.com/aloistr/swisseph/master/ephe/sepl_18.se1 && \
    wget -q https://raw.githubusercontent.com/aloistr/swisseph/master/ephe/semo_18.se1 && \
    wget -q https://raw.githubusercontent.com/aloistr/swisseph/master/ephe/seas_18.se1

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

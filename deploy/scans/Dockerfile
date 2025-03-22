FROM python:3.11-slim

WORKDIR /app

COPY deploy/scans/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY data/nexrad_stations.csv data/nexrad_stations.csv
COPY src/services/scans/server.py ./main.py

EXPOSE 5171

CMD ["python", "main.py"]

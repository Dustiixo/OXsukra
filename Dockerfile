FROM python:3.13-slim
RUN apt-get update && apt-get install -y --no-install-recommends rclone ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY funnel /app/funnel
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
EXPOSE 8787
CMD ["python","-m","funnel","hub","--data","/data","--host","0.0.0.0","--port","8787"]

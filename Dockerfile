FROM python:3.12-slim

WORKDIR /app

COPY app/ /app/

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=5s \
  CMD python3 -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8080/health',timeout=3)" || exit 1

CMD ["python3", "mailservice.py"]

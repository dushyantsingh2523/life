FROM python:3.12-slim
WORKDIR /app
COPY life.py .
HEALTHCHECK --interval=2s --timeout=2s CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/readyz')"
CMD ["python3", "life.py"]

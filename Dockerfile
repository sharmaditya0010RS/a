FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY requirements.txt requirements-phase8.txt ./

RUN python -m pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install -r requirements-phase8.txt

COPY src ./src
COPY streamlit_app ./streamlit_app
COPY .streamlit ./.streamlit

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=5)"

CMD ["python", "-m", "streamlit", "run", "streamlit_app/app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]

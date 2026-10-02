FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && \
    apt-get upgrade -y && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip setuptools && \
    pip install --no-cache-dir -r requirements.txt

RUN useradd --create-home --uid 10001 appuser

COPY app.py .
COPY ["Sydney_Sold_Property_Dataset (1).xlsx", "./"]
COPY sample_property_upload.csv .

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]
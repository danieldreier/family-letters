FROM python:3.11-slim

WORKDIR /app

# Install dependencies first for better caching
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application code and pre-built database
COPY app.py .
COPY letters.db .
COPY .streamlit/secrets.toml .streamlit/

# Set environment variables
ENV PORT=8080

EXPOSE 8080

CMD streamlit run --server.port $PORT --server.address 0.0.0.0 app.py

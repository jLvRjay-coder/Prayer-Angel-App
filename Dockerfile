FROM python:3.11-slim

# Work directory
WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Hugging Face expects Streamlit on 7860
EXPOSE 7860

# Keep framework usage telemetry off explicitly, including when defaults change.
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=7860", "--server.address=0.0.0.0", "--browser.gatherUsageStats=false"]

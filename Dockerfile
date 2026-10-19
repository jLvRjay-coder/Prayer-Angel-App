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

# Supervise Streamlit and the minute-based sender; telemetry remains off.
ENTRYPOINT ["python", "-u", "app_runtime.py"]

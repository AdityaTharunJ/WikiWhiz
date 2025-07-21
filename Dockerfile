FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Create writable folders
RUN mkdir -p /app/.streamlit /app/.cache/huggingface

# Set environment variables
ENV TRANSFORMERS_CACHE=/app/.cache/huggingface
ENV HF_HOME=/app/.cache/huggingface

# Copy requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Fix permissions recursively
RUN chmod -R 777 /app/.cache /app/.streamlit

# Add basic Streamlit config
RUN echo "\
[server]\n\
headless = true\n\
port = 8501\n\
enableCORS = false\n\
\n\
[browser]\n\
gatherUsageStats = false\n\
" > /app/.streamlit/config.toml

# Expose port
EXPOSE 8501

# Run the app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]

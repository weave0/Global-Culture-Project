# Use official Python image
FROM python:3.10-slim

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements (if exists) and install
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install extra UI dependencies
RUN pip install --no-cache-dir streamlit-aggrid langdetect

# Copy the rest of the app
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Run the Streamlit app
CMD ["streamlit", "run", "quick_run_ui.py", "--server.port=8501", "--server.address=0.0.0.0"]

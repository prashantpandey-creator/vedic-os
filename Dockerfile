# Base image: Python 3.11 slim is highly optimized
FROM python:3.11-slim

# Install system dependencies that a coding agent would need in its sandbox
# (git, curl, nodejs, npm, jq, build-essential)
RUN apt-get update && apt-get install -y \\
    git \\
    curl \\
    nodejs \\
    npm \
    ripgrep \
    fd-find \
    bat \\
    jq \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose Streamlit's default port
EXPOSE 8501

# Run the Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]

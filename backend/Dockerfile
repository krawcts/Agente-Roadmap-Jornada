FROM python:3.10-slim

WORKDIR /app

# Install OS dependencies if needed
# RUN apt-get update && apt-get install -y --no-install-recommends some-package && rm -rf /var/lib/apt/lists/*

# Copy requirements file from the backend subfolder (relative to build context '.')
# into the container's WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the entire backend directory structure from the host's backend/ (relative to build context '.')
# into the container's WORKDIR /app
# This makes main.py, src/, database/, data/ available directly under /app inside the container
COPY . /app

EXPOSE 8000

# Command now refers to main.py directly within the WORKDIR /app
# Uvicorn looks for the 'app' instance inside the 'main.py' file.
# Add --reload for development convenience (auto-restarts server on code changes if using volumes)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
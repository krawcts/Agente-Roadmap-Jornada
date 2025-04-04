FROM python:3.10-slim

WORKDIR /app

# Copy requirements file from the Streamlit subfolder (relative to build context '.')
# into the container's WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the Streamlit application file from the Streamlit subfolder (relative to build context '.')
# into the container's WORKDIR /app
COPY . ./app

EXPOSE 8501

# Command refers to the app file directly in the WORKDIR /app
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
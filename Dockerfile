FROM python:3.10-slim

WORKDIR /app

# Copy requirements.txt 
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app code
COPY app/ /app/

# Run preload script on container startup
CMD ["bash", "-c", "python preload.py && flask run --host=0.0.0.0"]

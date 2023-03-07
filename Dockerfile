FROM python:3.8-slim-buster

# Create app directory
WORKDIR /usr/app

# Copy sources
COPY ./ ./

# Install python requirements
RUN pip install --no-cache-dir --upgrade -r /usr/app/requirements.txt

# Start the service with disabled buffering output
CMD ["python", "-u", "main.py"]

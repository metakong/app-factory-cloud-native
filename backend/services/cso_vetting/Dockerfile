# Use an official lightweight Python image.
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the shared module first
COPY ./shared ./shared

# Copy the service-specific code
COPY ./services/cso_vetting/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY ./services/cso_vetting/main.py .

# Command to run the application using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main:app"]
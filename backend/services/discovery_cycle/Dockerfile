# Use an official lightweight Python image.
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the requirements file into the container
COPY requirements.txt ./

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the main application file into the container
COPY main.py .

# Command to run the application using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main:app"]
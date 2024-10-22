# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Install curl
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install python-dotenv for loading environment variables
RUN pip install python-dotenv

# Expose port 5000 to the outside world
EXPOSE 5000

# Set the environment variables from the .env file during the build process
# This will allow docker-compose or .env file to control env variables
ENV FLASK_ENV=production

# Run the Flask app
CMD ["python", "app.py"]

# Use the official Python image as the base
FROM python:3.9

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file to the working directory
COPY requirements.txt .

# Install the dependencies
RUN pip install -r requirements.txt

# Copy the application code to the working directory
COPY . .

# Expose the port that the Flask application listens on
EXPOSE 5001

# Start the Flask application
CMD ["python", "beb.py"]
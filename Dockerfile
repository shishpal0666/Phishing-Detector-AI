# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory to /app
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Create a directory for NLTK data and set permissions
# This ensures we can download data even if running as non-root user (common in HF Spaces)
RUN mkdir -p /app/nltk_data
ENV NLTK_DATA=/app/nltk_data
RUN chmod -R 777 /app/nltk_data

# Make port 7860 available to the world outside this container
EXPOSE 7860

# Run with Gunicorn for production performance
CMD ["gunicorn", "-b", "0.0.0.0:7860", "app:app"]

# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory to /code
WORKDIR /code

# Copy the current directory contents into the container at /code
COPY . /code

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Create a directory for NLTK data and set permissions
# This ensures we can download data even if running as non-root user (common in HF Spaces)
RUN mkdir -p /code/nltk_data
ENV NLTK_DATA=/code/nltk_data
RUN chmod -R 777 /code/nltk_data

# Make port 7860 available to the world outside this container
EXPOSE 7860

# Run app.py when the container launches
CMD ["python", "app.py"]

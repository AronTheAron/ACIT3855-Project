# Use official Python base image
FROM python:3

# Metadata
LABEL maintainer="awong540@my.bcit.ca"

# Set working directory
WORKDIR /app

# Copy only requirements first (for Docker cache efficiency)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the anomaly service source code
COPY . /app

# Set proper permissions and use non-root user
RUN chown -R nobody:nogroup /app
USER nobody

# Expose the port the app runs on
EXPOSE 8200

# Entrypoint and command to run the Flask app
ENTRYPOINT ["python"]
CMD ["app.py"]
# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose port for FastAPI
EXPOSE 8005

# Start the FastAPI app with Uvicorn
CMD ["uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8005"]


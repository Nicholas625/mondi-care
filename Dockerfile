# Use Python 3.9 slim image
FROM python:3.9-slim-buster

# Set working directory
WORKDIR /app

# Copy requirements first (for caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all your code
COPY . .

# Expose port (Hugging Face expects 7860)
EXPOSE 7860

# Run with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "app:app"]
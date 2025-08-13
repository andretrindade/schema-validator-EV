FROM python:3.11-slim

WORKDIR /app

# Copy requirements (create requirements.txt if not present)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the validation script and any needed files
COPY validate_test.py .


# Default entrypoint: pass extra args to script
ENTRYPOINT ["python", "validate_test.py"]
ARG PYTHON_VERSION=3.11-slim-bullseye
FROM python:${PYTHON_VERSION}

# Upgrade pip
RUN pip install --upgrade pip

# Set Python-related environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install os dependencies for our mini vm
RUN apt-get update && apt-get install -y \
    libpq-dev \
    libjpeg-dev \
    libcairo2 \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory to that same code directory
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the Python project requirements
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project code into the container's working directory
COPY . .
COPY .env /app/.env

# Collect static files (make sure Django is installed before this)
RUN python manage.py collectstatic --noinput

EXPOSE 8000

# Start Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "myproject.wsgi:application", "--workers", "3"]

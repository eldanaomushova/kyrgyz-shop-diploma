# Use Python 3.11
FROM python:3.11-slim

# 1. Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# 2. Set working directory
WORKDIR /app

# 3. Install Python dependencies FIRST (for better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy project code SECOND
COPY . .

# 5. NOW run collectstatic (after code and requirements are present)
# Note: Ensure STATIC_ROOT is set in settings.py
RUN python manage.py collectstatic --noinput

# 6. Start Gunicorn
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 core.wsgi:application
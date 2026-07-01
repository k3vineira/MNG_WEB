FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /code

# Install dependencies
COPY requirements.txt /tmp/requirements.txt
RUN set -ex && \
    pip install --upgrade pip && \
    pip install -r /tmp/requirements.txt && \
    rm -rf /root/.cache/

# Copy project
COPY . /code/

# Expose port (Fly.io default is usually 8080, but can be configured)
EXPOSE 8000

# CMD is typically overridden by fly.toml, but we provide a default
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

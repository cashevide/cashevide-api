#!/bin/sh

# Wait until the database is fully up and running
echo "Waiting for PostgreSQL at $DB_HOST:$DB_PORT..."

while ! nc -z $DB_HOST $DB_PORT; do
  sleep 0.1
done

echo "PostgreSQL started!"

# Run database migrations automatically
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

# Create Superuser
if [ "$DJANGO_SUPERUSER_USERNAME" ]; then
  echo "Creating superuser..."
  python manage.py createsuperuser --noinput || echo "Superuser already exists."
fi

# Execute the command specified in Dockerfile or Compose (e.g., Gunicorn/Runserver)
echo "Starting Gunicorn..."
exec "$@"

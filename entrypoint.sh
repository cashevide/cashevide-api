#!/bin/sh

# Fix ownership of bind-mounted volumes (staticfiles/media may be
# mounted from the host with different ownership every time the
# VPS or the mount is recreated). Runs as root before we drop
# privileges, so this never needs a manual `chown` on the host.
chown -R cashevide:cashevide /app/staticfiles /app/media

# Wait until the database is fully up and running
echo "Waiting for PostgreSQL at $DB_HOST:$DB_PORT..."

while ! nc -z $DB_HOST $DB_PORT; do
  sleep 0.1
done

echo "PostgreSQL started!"

# From here on, run everything as the unprivileged cashevide user.
exec gosu cashevide sh -c '
  echo "Running migrations..." &&
  python manage.py migrate --noinput &&
  python manage.py collectstatic --noinput &&
  if [ "$DJANGO_SUPERUSER_USERNAME" ]; then
    echo "Creating superuser..."
    python manage.py createsuperuser --noinput || echo "Superuser already exists."
  fi &&
  echo "Starting Gunicorn..." &&
  exec "$0" "$@"
' "$@"

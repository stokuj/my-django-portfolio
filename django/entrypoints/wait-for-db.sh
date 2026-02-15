#!/bin/sh
# wait-for-db.sh

set -e

host="$DB_HOST"
port="$DB_PORT"
user="$DB_USER"
password="$DB_PASSWORD"
dbname="$DB_NAME"

echo "Waiting for PostgreSQL..."

# Wait for the database to be ready
until PGPASSWORD=$password psql -h "$host" -p "$port" -U "$user" -d "$dbname" -c '\q'; do
  >&2 echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

>&2 echo "PostgreSQL is up - executing command"

# Execute the command passed to this script
exec "$@"
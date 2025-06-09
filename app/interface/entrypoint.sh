#!/bin/sh
# entrypoint.sh

# Domyślnie ustaw FLASK_ENV na production, jeśli nie jest zdefiniowane
: "${FLASK_ENV:=production}"

echo "Starting with FLASK_ENV=${FLASK_ENV}"

if [ "${FLASK_ENV}" = "development" ]; then
    echo "Running Flask development server with debug mode"
    # Użyj --debug dla pełnego trybu deweloperskiego Flask
    flask run --host=0.0.0.0 --port=5000 --debug
else
    echo "Running Gunicorn production server"
    gunicorn -w 4 -b 0.0.0.0:5000 "interface.app:create_app()"
fi
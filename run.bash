# For running locally in a test environment, run with run.bash. Procfile is for Heroku run.



gunicorn --bind 127.0.0.1:5000 --workers 1 -t 120 --worker-class eventlet app:app
# back

# start 
````
source .venv/bin/activate
export FLASK_ENV=development
gunicorn -w 4 -b 0.0.0.0:5000 main:app
````

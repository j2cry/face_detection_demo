import os
import json
import pathlib
import configparser
from flask import Flask, render_template
from waitress import serve


# load config
config = configparser.ConfigParser()
config.read('conf.d/default.cnf')
HOME_URL = pathlib.Path('/', config['URLS']['home'])
FACE_URL = config['URLS']['face_service']
PORT = int(config['URLS']['port'])

# init application
app = Flask(__name__, static_url_path=HOME_URL.joinpath('static').as_posix())
app.config['SECRET_KEY'] = os.urandom(40).hex()

# prepare common parameters
params = {
    'landing_url': HOME_URL.as_posix(),
    'service_url': FACE_URL,
    'delay': int(config['PARAMS']['delay']),
    'resize': json.loads(config['PARAMS']['resize']),
    'thick': int(config['PARAMS']['thick']),
    'color': config['PARAMS']['color'],
}

# define routes
@app.route(HOME_URL.as_posix())
def index():
    """ Start page """
    return render_template('index.jinja2', params=params)


# run
if __name__ == '__main__':
    print('started.')
    serve(app, host='0.0.0.0', port=PORT)
    print('stopped.')

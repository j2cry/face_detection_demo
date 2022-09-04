import os
import json
import pathlib
import configparser
import numpy as np
from flask import Flask, render_template, request
from flask_socketio import SocketIO
from face_detector import FaceDetector


# load config
config = configparser.ConfigParser()
config.read('conf.d/default.cnf')
HOME_URL = pathlib.Path('/', config['URLS']['home'])
PORT = int(config['URLS']['port'])

# init application
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(40).hex()
# enable origins
origins = json.loads(config['URLS']['origins'])
socket = SocketIO(app, path=f'{HOME_URL}/socket.io', cors_allowed_origins=origins)

# по-хорошему, надо хранить по одному на сессию
# fd = FaceDetector()

# define routes
@app.route(HOME_URL.as_posix())
def api_description():
    return render_template('description.jinja2')


@socket.on('detect_faces')
def detect_faces(data):
    # frame = np.frombuffer(data['frame'], dtype=np.int8).reshape(data['width'], data['height'], -1).copy()
    frame = np.array(list(data['frame'])).reshape(data['height'], data['width'], -1)
    fd = FaceDetector()
    fd.detect(frame, extract=False)
    return fd.boxes.tolist() if fd.boxes is not None else None


@socket.on('debug')
def debug(data):
    print(data)
    return 'thanks'


# run
if __name__ == '__main__':
    print('started.')
    socket.run(app, host='0.0.0.0', port=PORT)
    print('stopped.')

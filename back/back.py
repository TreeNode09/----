from flask import Flask, request
from flask_cors import CORS

from ultralytics import YOLO

import cv2
import numpy as np

app = Flask(__name__)
CORS(app)

@app.route('/')
def hello_world():
    return 'Hello, Flask!'

@app.route('/upload', methods=['POST'])
def handle_upload():
    print(type(request))
    print(request)
    image_data = request.files.get("file")
    image_bytes = image_data.read()
    array = np.frombuffer(image_bytes, np.uint8)

    image = cv2.imdecode(array, cv2.IMREAD_COLOR)

    return str(image.shape)

if __name__ == '__main__':
    app.run(debug=False) 
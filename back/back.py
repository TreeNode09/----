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
    video = request.files.get("video")
    video.save("C:/专业实训三/ImgDetect/back/static/test.mp4")
    return "ok"
if __name__ == '__main__':
    app.run(debug=False) 
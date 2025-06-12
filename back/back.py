from flask import Flask, request
from flask_cors import CORS

from ultralytics import YOLO
from utils.handleFrame import *

import cv2
import os
import numpy as np

app = Flask(__name__)
CORS(app)

def delete_files(directory):
    file_list = os.listdir(directory)
    for file in file_list:
        file_path = os.path.join(directory, file)
        if os.path.isfile(file_path):
            os.remove(file_path)

@app.route('/')
def hello_world():
    return 'Hello, Flask!'

@app.route('/upload', methods=['POST'])
def handle_upload():
    video = request.files.get("video")

    #拿到处理参数（需要经过哪些模型处理）[]
    video.save("C:/专业实训三/ImgDetect/back/static/test.mp4")
    cap = cv2.VideoCapture("C:\\专业实训三\\ImgDetect\\back\\static\\test.mp4", cv2.CAP_ANY)
    size = (960,384)#图片的尺寸，一定要和要用的图片size一致
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    videowrite = cv2.VideoWriter('C:/专业实训三/ImgDetect/back/static/result.mp4', fourcc, 30, size)#20是帧数，size是图片尺寸

    index = 0
    while cap.isOpened():

        success, img = cap.read()
        if not success:
            break

        output = handle_frame(img)
        img = cv2.resize(img, (480, 384))
        show_img = np.hstack([img, output])
        videowrite.write(show_img)
        index += 1
    cap.release()
    cv2.destroyAllWindows()
    videowrite.release()

    return "ok"


if __name__ == '__main__':
    app.run(debug=False) 
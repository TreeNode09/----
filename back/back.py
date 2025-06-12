from flask import Flask, request
from flask_cors import CORS

from ultralytics import YOLO
from utils.handleFrame import *

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

    #拿到处理参数（需要经过哪些模型处理）[]
    

    video.save("C:/专业实训三/ImgDetect/back/static/test.mp4")
    cap = cv2.VideoCapture("C:\\专业实训三\\ImgDetect\\back\\static\\test.mp4", cv2.CAP_ANY)
    SAVED_DIR = 'C:/专业实训三/ImgDetect/back/static/output'
    index = 0
    while cap.isOpened():
        print(1)

        success, img = cap.read()
        print(success)
        if not success:
            break

        output = handle_frame(img)

        #拼接原视频帧和处理后的视频帧
        show_img = np.hstack([img, output])
        cv2.imwrite(SAVED_DIR + str(index) + ".png", show_img)
        index += 1

    cap.release()
    cv2.destroyAllWindows()
    return "ok"


if __name__ == '__main__':
    app.run(debug=False) 
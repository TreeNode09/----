from flask import Flask, request, send_file
from flask_cors import CORS
from flask_socketio import SocketIO, emit

from utils.handleFrame import *
from utils.config import BASE_DIR

import cv2
import os
import numpy as np
import time

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')
fourcc = cv2.VideoWriter_fourcc(*'avc1')
print('Ready!')

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
    options = request.files.get('options')
    print(options)
    #video.save(BASE_DIR + "static/test.mp4")
    video.save("C:/Users/Stick/Desktop/ImgDetect/图像识别/back/static/test.mp4")
    process_video_file()
    socketio.emit('finishProcess', {'progress': 1.0})
    return "OK"

@app.route('/processed', methods=['GET'])
def handle_processed():
    return send_file("C:/Users/Stick/Desktop/ImgDetect/图像识别/back/static/result.mp4")

@socketio.on('connect')
def handle_connect():
    print('客户端已连接:', request.sid)

@socketio.on('disconnect')
def handle_disconnect():
    print('客户端断开连接:', request.sid)

@socketio.on('sendJunk')
def handle_junk(data):
    result = ''.join(reversed(data['data']))
    resultData = {
        'data': result
    }
    emit('yourJunk', resultData)

@socketio.on('sendCamera')
def handle_process_frame(data):
    image_data = data['imageData']
    image_blob = image_data['data']  # 获取图像数据
    width = image_data['width']
    height = image_data['height']
    options = data['options']
    quality = data['quality']
    print(data['frameId'])

    image_buffer = np.frombuffer(image_blob, dtype=np.uint8)

    image = cv2.imdecode(image_buffer, -1)   # 转到openCV的图片格式
    image = cv2.resize(image, (width, height), interpolation=cv2.INTER_LINEAR)
    image = cv2.cvtColor(image, cv2.COLOR_RGBA2BGR)
    
    result = handle_frame(image, options)
    
    result = cv2.cvtColor(result, cv2.COLOR_RGB2BGRA)  # 转换回RGBA
    _, compressed = cv2.imencode('.webp', result, [cv2.IMWRITE_WEBP_QUALITY, int(100 * quality)])

    resultData = {
        'frameId': data['frameId'],
        'imageData': compressed.tobytes()
    }
    emit('sendFrame', resultData)

def process_video_file():
    cap = cv2.VideoCapture(BASE_DIR + "back/static/test.mp4", cv2.CAP_ANY)
    total_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    output = cv2.VideoWriter(BASE_DIR + 'back/static/result.mp4', fourcc, fps, (width, height))
    begin = time.time()
    count = 0
    while cap.isOpened():

        success, img = cap.read()
        if not success: break

        result = handle_frame(img, [False, False, False])
        output.write(result)
        count += 1

        current = time.time()
        if current - begin > 1.0:   # 每1秒更新一次进度
            begin = current
            socketio.emit('updateProgress', {'progress': count / total_count})
            socketio.sleep(0)   # 让socket立即发送

    cap.release()
    output.release()

if __name__ == '__main__':
    # app.run(debug=False)
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
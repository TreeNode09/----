from flask import Flask, Response, request
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
    video.save(BASE_DIR + "static/test.mp4")
    
    # cap = cv2.VideoCapture(BASE_DIR + "static/test.mp4", cv2.CAP_ANY)
    
    # size = (960,384)    #图片的尺寸，一定要和要用的图片size一致
    # fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    # videowrite = cv2.VideoWriter(BASE_DIR + "static/result.mp4", fourcc, 30, size)#20是帧数，size是图片尺寸

    # index = 0
    # while cap.isOpened():

    #     success, img = cap.read()
    #     if not success: break

    #     output = handle_frame(img)
    #     img = cv2.resize(img, (480, 384))
    #     show_img = np.hstack([img, output])
    #     # videowrite.write(show_img)

    #     ret, buffer = cv2.imencode('.jpg', show_img)
    #     frame = buffer.tobytes()

    #     index += 1

    # cap.release()
    # cv2.destroyAllWindows()
    # videowrite.release()

    return "ok"

@app.route('/video-feed')
def feed_video():

    return Response(generate_frames(30), mimetype='multipart/x-mixed-replace; boundary=frame')

def generate_frames(fps: int = 30):
    
    cap = cv2.VideoCapture(BASE_DIR + "back/static/test.mp4", cv2.CAP_ANY)

    while cap.isOpened():

        start = time.time()

        success, img = cap.read()
        if not success: break

        # output = handle_frame(img)
        img = cv2.resize(img, (480, 384))
        # show_img = np.hstack([img, output])

        ret, buffer = cv2.imencode('.jpg', img)
        frame = buffer.tobytes()

        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n'
        )

        delay = 1 / fps - (time.time() - start) #处理下一帧之前需要等待的时间
        if delay < 0: print("慢了%.4fs!" % (time.time() - start)) #太慢啦
        else: time.sleep(delay)

    cap.release()

def process(image: cv2.Mat):
    height, width = image.shape[:2]
    result = cv2.rectangle(image, (width//10, height//10), (width*9//10, height*9//10), (0, 255, 0), 2)
    return result

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
    image_buffer = np.frombuffer(image_blob, dtype=np.uint8)
    print(data['frameId'])

    image = cv2.imdecode(image_buffer, -1)   # 转到openCV的图片格式
    image = cv2.resize(image, (width, height), interpolation=cv2.INTER_LINEAR)
    image = cv2.cvtColor(image, cv2.COLOR_RGBA2BGR)
    
    result = handle_frame(image)
    
    result = cv2.cvtColor(result, cv2.COLOR_RGB2BGRA)  # 转换回RGBA
    height, width = result.shape[:2]
    _, compressed = cv2.imencode('.webp', result, [cv2.IMWRITE_WEBP_QUALITY, 30])

    resultData = {
        'frameId': data['frameId'],
        'imageData': {
            'data': compressed.tobytes(),
            'width': width,
            'height': height
        }
    }
    emit('sendFrame', resultData)

if __name__ == '__main__':
    # app.run(debug=False)
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
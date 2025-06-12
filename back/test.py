import cv2
import os

video_path = r"C:\专业实训三\ImgDetect\back\static\test.mp4"
cap = cv2.VideoCapture(video_path)
print("视频是否打开成功：", cap.isOpened())
print(os.path.exists(video_path))               
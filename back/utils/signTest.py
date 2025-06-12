from ultralytics import YOLO

model = YOLO('C:/专业实训三/ImgDetect/back/models/best.pt')

results = model.predict('C:/专业实训三/image.png')

for result in results:
    result.plot()
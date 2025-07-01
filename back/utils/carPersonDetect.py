from ultralytics import YOLO
from utils.laneUtils.config import BASE_DIR
import cv2
from utils.tracker import *

model = YOLO(BASE_DIR + 'back/models/car_person.pt')
tracker = Tracker()
f = 1000
car_real_length = 1.5

def process(img, fps):
    results = model.predict(img)
    for result in results:
        cp_boxes = result.boxes.xyxy  # 边界框坐标
        cp_classes = result.boxes.cls  # 类别索引     
        cp_names = [model.names[int(cls)] for cls in cp_classes]
        speeds, distances = [], [10000]
        for box, name in zip(cp_boxes, cp_names):
            if name == "car":
                x1, y1, x2, y2 = map(float, box)    #车矩形框的左上角和右下角
                pre_id_heights = tracker.id_heights.copy()
                id = tracker.update([x1, y1, x2, y2])
                if(id != 0):
                    height = tracker.id_heights[id]
                    distance = f * car_real_length / height
                    distances.append(distance)

                    pre_height = pre_id_heights[id]
                    pre_distance = f * car_real_length / pre_height

                    delta_distance = distance - pre_distance
                    delta_time = 1/fps
                    speeds.append(int(delta_distance/delta_time*3.6))
                else:
                    speeds.append(-1)
            else:
                speeds.append(-1)

        return cp_boxes, cp_names, speeds, min(distances)
        
        # # # 如果有类别名称，可以通过类别索引获取
        # # class_names = [model.names[int(cls)] for cls in classes]
        
        # # # 打印检测结果
        # # for box, score, class_name in zip(boxes, scores, class_names):
        # #     print(f"Class: {class_name}, Score: {score:.2f}, Box: {box}")
            
        # # 可视化检测结果
        # annotated_img = result.plot()
        
        # # 显示图像
        # cv2.imshow('Detected Image', annotated_img)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()

if __name__ == "__main__":
    img = cv2.imread('ImgDetect/back/static/image.png',1)
    # print(img.shape)
    boxes,names = process(img)
    # print("boxes:\n", boxes)
    # print("names:\n", names)
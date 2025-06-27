from ultralytics import YOLO
#from utils.laneUtils import config
import cv2

model = YOLO('图像识别/' + 'back/models/sign.pt')

model_names = {
    0: 'limit-5kph', 1: 'limit-15kph', 2: 'limit-30kph',  3: 'limit-40kph', 4: 'limit-50kph',
    5: 'limit-60kph', 6: 'limit-70kph', 7: 'limit-80kph', 18: 'limit-40kph-dated', 19: 'limit-50kph-dated',

    8: 'not-left-and-straight', 9: 'not-right-and-straight', 10: 'not-straight',
    11: 'not-left', 12: 'not-left-right', 13: 'not-right', 14: 'not-overtake',
    15: 'not-turn-around', 16: 'not-car', 17: 'not-horn',
    52: 'not-stop', 53: 'not-stop-all', 54: 'not-parking', 55: 'not-entry', 56: 'not-give-way', 57: 'not-checkpoint',

    20: 'go-straight-and-right', 21: 'go-straight', 22: 'go-left', 23: 'go-left-and-right',
    24: 'go-right', 25: 'go-keep-left', 26: 'go-keep-right', 27: 'go-roundabout',
    28: 'go-car-lane', 29: 'go-horn', 30: 'go-bicycle-lane', 31: 'go-turn-around',

    32: 'warn-bypass', 33: 'warn-traffic-light', 34: 'warn-warning', 35: 'warn-pad-xing',
    36: 'warn-bicycle', 37: 'warn-school', 38: 'warn-sharp-bend-right', 39: 'warn-sharp-bend-left',
    40: 'warn-slope-down', 41: 'warn-slope-up', 42: 'warn-slow', 43: 'warn-t-xing-right', 44: 'warn-t-xing-left',
    45: 'warn-s-curve', 46: 'warn-village', 47: 'warn-train', 48: 'warn-construction',
    49: 'warn-zig-zag', 50: 'warn-railway', 51: 'warn-accident-zone'
}

def process(img):
    results = model.predict(img, conf=0.1)
    for result in results:
        sign_boxes = result.boxes.xyxy  # 边界框坐标
        sign_classes = result.boxes.cls  # 类别索引
        sign_names = [model_names[int(cls)] for cls in sign_classes]

        return sign_boxes, sign_names
        
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
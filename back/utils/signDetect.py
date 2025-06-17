from ultralytics import YOLO
import cv2

model = YOLO('C:/专业实训三/ImgDetect/back/models/sign.pt')

def process(img):
    results = model.predict(img)
    for result in results:
        sign_boxes = result.boxes.xyxy  # 边界框坐标
        sign_classes = result.boxes.cls  # 类别索引      

        return sign_boxes, sign_classes                            
        
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
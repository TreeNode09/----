from . import roadSegmentation
from . import carPersonDetect
from . import signDetect
import cv2
import numpy as np

def append_mask_to_image(image, mask):
    """
    将分割掩码应用到图像上，并用蓝色高亮分割区域
    :param image: 原图 (H, W, 3)
    :param mask: 单通道二值掩码 (H, W)，值为0或255
    :return: 应用掩码后的图像
    """
    # 确保mask为uint8类型且为0/255
    if mask.max() == 1:
        mask = (mask * 255).astype('uint8')
    elif mask.dtype != np.uint8:
        mask = mask.astype('uint8')

    # 创建绿色图层
    green_layer = np.zeros_like(image)
    green_layer[:, :, 0] = 255

    # 掩码三通道化
    mask_3c = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
    mask_bool = mask_3c > 0

    # 原图与绿色图层按掩码混合
    output = image.copy()
    output[mask_bool] = cv2.addWeighted(image, 0.5, green_layer, 0.5, 0)[mask_bool]

    return output

def process_mask(mask):
    if mask.max() == 1:
        mask = (mask * 255).astype('uint8')
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    # 先闭运算填充小洞
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    # 再开运算去除小噪点
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(mask, contours, -1, 255, thickness=cv2.FILLED)
    return mask

def draw_boxes(img, boxes, names, color=(0, 255, 0), thickness=2):
    """
    在图片上绘制识别框和类别标签
    :param img: 原图
    :param boxes: [[x1, y1, x2, y2], ...]
    :param classes: [class_name1, class_name2, ...]
    """
    for box, name in zip(boxes, names):
        x1, y1, x2, y2 = map(int, box)
        cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)
        cv2.putText(img, str(name), (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    return img

def analyze_data(cp_boxes, cp_classes, sign_boxes, sign_classes):
    return {'cpCount': len(cp_classes), 'signCount': len(sign_classes)}

def handle_frame(img: cv2.Mat, options: list[bool]):
    original_size = img.shape[:2]  # (height, width)
    result = img.copy()
    cp_boxes, cp_classes, sign_boxes, sign_classes = [], [], [], []

    if options[0] == True:
        mask = roadSegmentation.process(img.copy())
        mask = cv2.resize(mask, (original_size[1], original_size[0]))
        mask = process_mask(mask)  # <--- 加上这行
        result = append_mask_to_image(result, mask)

    if options[1] == True:
        cp_boxes, cp_classes = carPersonDetect.process(img)
        cp_names = [carPersonDetect.model.names[int(cls)] for cls in cp_classes]
        result = draw_boxes(result, cp_boxes, cp_names, color=(0,255,0))

    if options[2] == True:
        sign_boxes, sign_classes = signDetect.process(img)
        sign_names = [signDetect.model.names[int(cls)] for cls in sign_classes]
        result = draw_boxes(result, sign_boxes, sign_names, color=(255,0,0))

    analyzed = analyze_data(cp_boxes, cp_classes, sign_boxes, sign_classes)

    return result, analyzed

if __name__ == "__main__":
    img = cv2.imread("ImgDetect\\back\\static\\image.png")
    if img is None:
        print("Image not found")
    else:
        handle_frame(img)

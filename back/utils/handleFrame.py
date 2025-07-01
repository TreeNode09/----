from . import roadSegmentation
from . import carPersonDetect
from . import signDetect
from utils.laneUtils import roadSegmentation2
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

def hex_to_bgr(hex):
    hex = hex.lstrip('#')
    red = int(hex[0:2], 16)
    green = int(hex[2:4], 16)
    blue = int(hex[4:6], 16)
    return (blue, green, red)

def draw_boxes(img: cv2.Mat, boxes: list, names: list[str], infos: list):
    for i in range(len(boxes)):
        color = (0, 0, 255)
        text = ""

        index = names[i].find('-')
        if index == -1:
            if names[i] == 'car':
                if infos[i] != -1 and abs(infos[i]) < 100: text = str(infos[i]) + 'km/h'
                color = hex_to_bgr('#54A7FF')
            elif names[i] == 'person':
                color = hex_to_bgr('#A6D3FF')
        else:
            text = names[i][index + 1:]
            if index == 2: color = hex_to_bgr('#25D5D5')    # go-
            elif index == 3: color = hex_to_bgr('#F56C6C')  # not-
            elif index == 7: color = hex_to_bgr('#E6A23C')  # warning-
            elif index == 5: color = hex_to_bgr('#C45656')  # limit-
            else: return img

        x1, y1, x2, y2 = map(int, boxes[i])
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)

        (text_width, text_height), text_bottom = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
        if text != "": cv2.rectangle(img, (x1, y1 - text_height - text_bottom), (x1 + text_width, y1), color, -1)
        cv2.putText(img, text, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    return img

def draw_circle(img, coords):
    for lane in coords:
        for coord in lane:
            cv2.circle(img, coord, 5, (0,255,0), -1)
    return img

def analyze_data(cp_names: list, sign_names: list, min_distance: float):
    return {
        'carCount': cp_names.count('car'),
        'personCount': cp_names.count('person'),
        'signCount': len(sign_names),
        'minDistance': min_distance
    }

def handle_frame(img: cv2.Mat, options: list[bool], fps: float):
    result = img.copy()
    cp_names, sign_names, min_distance = [], [], 10000

    if options[0] == True:
        # mask = roadSegmentation.process(img.copy())
        # mask = cv2.resize(mask, (original_size[1], original_size[0]))
        # mask = process_mask(mask)  # <--- 加上这行
        # result = append_mask_to_image(result, mask)
        coords  = roadSegmentation2.process(img)
        result = draw_circle(result, coords)

    if options[1] == True:
        cp_boxes, cp_names, speeds, min_distance = carPersonDetect.process(img, fps)
        result = draw_boxes(result, cp_boxes, cp_names, speeds)

    if options[2] == True:
        sign_boxes, sign_names = signDetect.process(img)
        result = draw_boxes(result, sign_boxes, sign_names, [])

    analyzed = analyze_data(cp_names, sign_names, min_distance)

    return result, analyzed

if __name__ == "__main__":
    img = cv2.imread("ImgDetect\\back\\static\\image.png")
    if img is None:
        print("Image not found")
    else:
        handle_frame(img)

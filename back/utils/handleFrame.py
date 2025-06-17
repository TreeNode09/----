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


def draw_boxes(img, boxes, classes, color=(0, 255, 0), thickness=2):
    """
    在图片上绘制识别框和类别标签
    :param img: 原图
    :param boxes: [[x1, y1, x2, y2], ...]
    :param classes: [class_name1, class_name2, ...]
    """
    class_names = [carPersonDetect.model.names[int(cls)] for cls in classes]
    for box, cls in zip(boxes, class_names):
        x1, y1, x2, y2 = map(int, box)
        cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)
        cv2.putText(img, str(cls), (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    return img

def handle_frame(img):
    original_size = img.shape[:2]  # (height, width)
    cp_boxes, cp_classes = carPersonDetect.process(img)
    # print("cp:", cp_boxes, cp_classes)
    sign_boxes, sign_classes = signDetect.process(img)
    # print("sign:", sign_boxes, sign_classes)
    mask = roadSegmentation.process(img.copy())
    mask = cv2.resize(mask, (original_size[1], original_size[0]))
    mask = process_mask(mask)  # <--- 加上这行
    img_with_mask = append_mask_to_image(img, mask)
    # 绘制识别框
    img_with_maskAndboxes = draw_boxes(img_with_mask, cp_boxes, cp_classes, color=(0,255,0))
    img_with_maskAndboxes = draw_boxes(img_with_maskAndboxes, sign_boxes, sign_classes, color=(255,0,0))
    cv2.imshow("Result", img_with_maskAndboxes)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    return img_with_maskAndboxes

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

img = cv2.imread("ImgDetect\\back\\static\\image.png")
if img is None:
    print("Image not found")
else:
    handle_frame(img)

import os
os.environ['CUDA_VISIBLE_DEVICES'] = '0'

import numpy as np
import cv2
import matplotlib.pyplot as plt
import albumentations as albu
import torch
import segmentation_models_pytorch as smp
# from torch.utils.data import Dataset as BaseDataset
import imageio


### Dataloader

def process_image(image, augmentation=None, preprocessing=None):
    # read data
    image = image.copy()
    image = cv2.resize(image, (480, 384))   # 改变图片分辨率


    # 图像增强应用
    if augmentation:
        sample = augmentation(image=image)
        image = sample['image']

    # 图像预处理应用
    if preprocessing:
        sample = preprocessing(image=image)
        image = sample['image']

    return image

# ---------------------------------------------------------------

def get_validation_augmentation():
    """调整图像使得图片的分辨率长宽能被32整除"""
    test_transform = [
        albu.PadIfNeeded(384, 480)
    ]
    return albu.Compose(test_transform)


def to_tensor(x, **kwargs):
    return x.transpose(2, 0, 1).astype('float32')


def get_preprocessing(preprocessing_fn):
    """进行图像预处理操作
    Args:
        preprocessing_fn (callbale): 数据规范化的函数
            (针对每种预训练的神经网络)
            
            
    Return:
        transform: albumentations.Compose
    """

    _transform = [
        albu.Lambda(image=preprocessing_fn),
        albu.Lambda(image=to_tensor),
    ]
    return albu.Compose(_transform)


# 图像分割结果的可视化展示
def visualize(image_vis, predicted_mask, raw_img=None):
    predicted_mask = (predicted_mask * 255).astype(np.uint8)
    inverted = cv2.bitwise_not(predicted_mask)
    back_out = cv2.bitwise_and(image_vis, image_vis, mask=inverted)
    array = np.array([0,1,0], dtype=np.uint8)
    predicted_mask = cv2.cvtColor(predicted_mask, cv2.COLOR_GRAY2BGR)
    green_out = predicted_mask * array
    output = cv2.add(back_out, green_out)

    # 拼接原视频帧和分割结果帧
    if raw_img is not None:
        # 保证原图和分割图大小一致
        raw_img_resized = cv2.resize(raw_img, (image_vis.shape[1], image_vis.shape[0]))
        show_img = np.hstack([raw_img_resized, output])
    else:
        show_img = output

    cv2.imshow('Original | Segmentation', show_img)
    cv2.waitKey(1)

# ---------------------------------------------------------------
if __name__ == '__main__':

    ENCODER = 'se_resnext50_32x4d'
    ENCODER_WEIGHTS = 'imagenet'
    CLASSES = ['road']
    ACTIVATION = 'sigmoid' # could be None for logits or 'softmax2d' for multiclass segmentation
    DEVICE = 'cuda'

    # 按照权重预训练的相同方法准备数据
    preprocessing_fn = smp.encoders.get_preprocessing_fn(ENCODER, ENCODER_WEIGHTS)

    # 重新构建模型并加载参数
    model = smp.UnetPlusPlus(
        encoder_name=ENCODER,
        encoder_weights=None,
        classes=len(CLASSES),
        activation=ACTIVATION,
    )
    model.load_state_dict(torch.load('./best_model.pth', map_location=DEVICE))
    model = model.to(DEVICE)
    model.eval()

    VIDEO_DIR = './data/video/test.mp4'
    cap = cv2.VideoCapture(VIDEO_DIR)

    # 固定窗口大小
    WINDOW_WIDTH, WINDOW_HEIGHT = 720, 480

    # 在循环外创建增强和预处理对象
    val_aug = get_validation_augmentation()
    preproc = get_preprocessing(preprocessing_fn)

    while True:
        success, img = cap.read()
        if not success:
            break

        # 等比例缩放到窗口内并居中
        h, w = img.shape[:2]
        scale = min(WINDOW_WIDTH / w, WINDOW_HEIGHT / h)
        new_w, new_h = int(w * scale), int(h * scale)
        resized_img = cv2.resize(img, (new_w, new_h))
        image_vis = np.zeros((WINDOW_HEIGHT, WINDOW_WIDTH, 3), dtype=np.uint8)
        top = (WINDOW_HEIGHT - new_h) // 2
        left = (WINDOW_WIDTH - new_w) // 2
        image_vis[top:top+new_h, left:left+new_w] = resized_img

        # 只做一次增强和预处理
        predict_img = process_image(img, augmentation=val_aug, preprocessing=preproc)
        x_tensor = torch.from_numpy(predict_img).to(DEVICE).unsqueeze(0)
        with torch.no_grad():
            pr_mask = model(x_tensor)
            pr_mask = (pr_mask.squeeze().cpu().numpy().round())

        # mask等比例缩放并居中
        pr_mask = cv2.resize(pr_mask, (new_w, new_h))
        mask_canvas = np.zeros((WINDOW_HEIGHT, WINDOW_WIDTH), dtype=np.uint8)
        mask_canvas[top:top+new_h, left:left+new_w] = (pr_mask * 255).astype(np.uint8)

        # 同时显示原视频帧和分割结果
        visualize(
            image_vis,
            mask_canvas / 255.0,
            raw_img=img
        )

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
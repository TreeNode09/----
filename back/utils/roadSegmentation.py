import os
os.environ['CUDA_VISIBLE_DEVICES'] = '0'

import numpy as np
import cv2
import matplotlib.pyplot as plt
import albumentations as albu
import torch
import segmentation_models_pytorch as smp
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

#得到处理后的图像
def getOutput(image_vis, predicted_mask):
    predicted_mask = (predicted_mask * 255).astype(np.uint8)
    inverted = cv2.bitwise_not(predicted_mask)
    back_out = cv2.bitwise_and(image_vis, image_vis, mask=inverted)
    array = np.array([0,1,0], dtype=np.uint8)
    predicted_mask = cv2.cvtColor(predicted_mask, cv2.COLOR_GRAY2BGR)
    green_out = predicted_mask * array
    output = cv2.add(back_out, green_out)
    return output

# ---------------------------------------------------------------

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
model.load_state_dict(torch.load('C:/专业实训三/ImgDetect/back/models/best_model.pth', map_location=DEVICE))
model = model.to(DEVICE)
model.eval()

# 在循环外创建增强和预处理对象
val_aug = get_validation_augmentation()
preproc = get_preprocessing(preprocessing_fn)

def process(img):
    # 只做一次增强和预处理
    predict_img = process_image(img, augmentation=val_aug, preprocessing=preproc)
    x_tensor = torch.from_numpy(predict_img).to(DEVICE).unsqueeze(0)
    with torch.no_grad():
        pr_mask = model(x_tensor)
        pr_mask = (pr_mask.squeeze().cpu().numpy().round())

    # 同时显示原视频帧和分割结果
    return  getOutput(
        pr_mask / 255.0,
        raw_img=img
    )
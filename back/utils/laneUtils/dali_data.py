# data/dali_data.py
import torch
import numpy as np
import random
import cv2
import json
import os
import math
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from . import my_interp

class LaneDataset(Dataset):
    def __init__(self, data_root, list_path, mode='train', 
                 dataset_name=None, train_size=(800, 288), 
                 top_crop=0.6):
        assert mode in ['train', 'test']
        self.mode = mode
        self.data_root = data_root
        self.train_h, self.train_w = train_size
        self.top_crop = top_crop
        
        # 加载数据列表
        if isinstance(list_path, (list, tuple)):
            self.list = []
            for p in list_path:
                with open(os.path.join(data_root, p)) as f:
                    self.list.extend([line.strip() for line in f])
        else:
            with open(os.path.join(data_root, list_path)) as f:
                self.list = [line.strip() for line in f]

        # 加载标注缓存
        if mode == 'train':
            cache_map = {
                'CULane': 'culane_anno_cache.json',
                'Tusimple': 'tusimple_anno_cache.json',
                'CurveLanes': os.path.join('train', 'curvelanes_anno_cache.json')
            }
            cache_path = os.path.join(data_root, cache_map[dataset_name])
            with open(cache_path) as f:
                self.cached_points = json.load(f)

    def __len__(self):
        return len(self.list)

    def __getitem__(self, idx):
        line = self.list[idx]
        img_rel, seg_rel = line.split()[:2]
        
        # 加载数据
        img = cv2.cvtColor(cv2.imread(os.path.join(self.data_root, img_rel.lstrip('/'))), 
                          cv2.COLOR_BGR2RGB)
        seg = cv2.imread(os.path.join(self.data_root, seg_rel.lstrip('/')), 
                        cv2.IMREAD_GRAYSCALE)
        points = np.array(self.cached_points[img_rel], dtype=np.float32)
        
        # 数据增强
        img, seg, points = self.joint_augment(img, seg, points)
        
        return {
            'image': self.normalize(img),
            'seg': torch.from_numpy(seg.astype(np.float32)).unsqueeze(0),
            'points': torch.from_numpy(points)
        }

    def joint_augment(self, img, seg, points):
        """执行联合空间变换"""
        h, w = img.shape[:2]
        
        # 生成随机变换参数
        scale = random.uniform(0.8, 1.2)
        angle = math.radians(random.uniform(-6, 6))
        dx = random.uniform(-200, 200)
        dy = random.uniform(-100, 100)
        
        # 构建仿射矩阵
        M = cv2.getRotationMatrix2D((w/2, h/2), math.degrees(angle), scale)
        M[:, 2] += [dx, dy]
        
        # 应用变换
        img = cv2.warpAffine(img, M, (w,h), flags=cv2.INTER_LINEAR, borderValue=0)
        seg = cv2.warpAffine(seg, M, (w,h), flags=cv2.INTER_NEAREST, borderValue=0)
        
        # 变换坐标点
        homg_points = np.pad(points, [(0,0),(0,1)], constant_values=1)
        points = (M @ homg_points.T).T
        
        # 尺寸调整和裁剪
        img = self.resize_crop(img)
        seg = self.resize_crop(seg)
        
        return img, seg, points

    def resize_crop(self, img):
        new_h = int(img.shape[0] / self.top_crop)
        resized = cv2.resize(img, (self.train_w, new_h))
        return resized[-self.train_h:]  # 底部裁剪

    def normalize(self, img):
        img = img.astype(np.float32) / 255.
        return transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )(torch.from_numpy(img).permute(2,0,1))

class TrainCollect:
    def __init__(self, cfg):
        self.dataset = LaneDataset(
            cfg.data_root,
            self.get_list_path(cfg),
            mode='train',
            dataset_name=cfg.dataset,
            train_size=(cfg.train_width, cfg.train_height),
            top_crop=cfg.crop_ratio
        )
        
        self.loader = DataLoader(
            self.dataset,
            batch_size=cfg.batch_size,
            shuffle=not cfg.distributed,
            sampler=self.get_sampler(cfg),
            num_workers=4,
            pin_memory=True,
            drop_last=True
        )
        
        # 初始化插值参数
        self.row_anchor = torch.tensor(cfg.row_anchor, dtype=torch.float32)
        self.col_anchor = torch.tensor(cfg.col_anchor, dtype=torch.float32)
        self.original_size = self.get_original_size(cfg.dataset)
        self.num_cells = (cfg.num_row, cfg.num_col)

    def get_list_path(self, cfg):
        path_map = {
            'CULane': 'list/train_gt.txt',
            'Tusimple': 'train_gt.txt',
            'CurveLanes': os.path.join('train', 'train_gt.txt')
        }
        return path_map[cfg.dataset]

    def get_sampler(self, cfg):
        if cfg.distributed:
            from torch.utils.data.distributed import DistributedSampler
            return DistributedSampler(self.dataset)
        return None

    def get_original_size(self, dataset):
        size_map = {
            'CULane': (1640, 590),
            'Tusimple': (1280, 720),
            'CurveLanes': (2560, 1440)
        }
        return torch.tensor(size_map[dataset], dtype=torch.float32)

    def __iter__(self):
        for batch in self.loader:
            # 坐标转换
            points = batch['points'].cuda()
            
            # 行方向插值
            row_loc = self.original_size[1] * self.row_anchor.to(points.device)
            points_row = my_interp.run(points, row_loc, dim=1)
            
            # 列方向插值
            col_loc = self.original_size[0] * self.col_anchor.to(points.device)
            points_col = my_interp.run(points, col_loc, dim=2)
            
            # 生成标签（传入当前batch）
            batch.update(self.process_labels(batch, points_row, points_col))  # ✅ 添加batch参数
            yield batch

    def process_labels(self, batch, row, col):  # ✅ 添加batch参数
        """标签生成逻辑"""
        # 行标签
        labels_row = (row / self.original_size[0] * (self.num_cells[0] - 1)).long()
        labels_row[row < 0] = -1
        labels_row[row > self.original_size[0]] = -1
        
        # 列标签
        labels_col = (col / self.original_size[1] * (self.num_cells[1] - 1)).long()
        labels_col[col < 0] = -1
        labels_col[col > self.original_size[1]] = -1
        
        return {
            'images': batch['image'].cuda(non_blocking=True),
            'seg_images': batch['seg'].cuda(non_blocking=True),
            'labels_row': labels_row,
            'labels_col': labels_col,
            'labels_row_float': row / self.original_size[0],
            'labels_col_float': col / self.original_size[1]
        }

    def __len__(self):
        return len(self.loader)

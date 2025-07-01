from ultralytics import YOLO
#from utils.laneUtils import config
import cv2

model = YOLO('图像识别/' + 'back/models/sign.pt')


# classes = ['ph5', 'p26', 'pl40', 'pl60', 'pn', 'i5', 'p11', 'pne', 'pcl', 'pl50', 'pcr', 'w55', 'pl5', 'ph4.5', 
#             'pl80', 'pg', 'w28', 'w30', 'pl30', 'p19', 'i4l', 'i2r', 'pw3.2', 'pm20', 'pbp', 'p5', 'pl120', 'w24', 
#             'p13', 'w57', 'ip', 'p10', 'il100', 'il60', 'il90', 'pb', 'pl110', 'w59', 'il80', 'pl100', 'ph4', 'pmb', 
#             'p14', 'pl15', 'i4', 'p16', 'p3', 'pl70', 'pdd', 'pr70', 'w13', 'w32', 'i2', 'pr40', 'pm30', 'w63', 
#             'p12', 'p17', 'p18', 'im', 'pl20', 'p6', 'pw3.5', 'p27', 'pcd', 'i14', 'p2', 'p1', 'i12', 'wc', 'i10', 
#             'p23', 'w58', 'p25', 'ph3', 'pl90', 'pbm', 'w5', 'pl10', 'pss', 'pm55', 'phclr', 'i13', 'i1', 'ph2.2', 
#             'w47', 'pr60', 'w38', 'il50', 'w16', 'w22', 'p20', 'pn-2', 'iz', 'p9', 'p1n', 'ph4.3', 'ps', 'pm8', 'w3', 
#             'w21', 'p29', 'w18', 'pa10', 'pa14', 'pa13', 'il70', 'ph2', 'pr100', 'pr80', 'pm5', 'w45', 'pmr', 'w12', 
#             'ph2.9', 'pr50', 'il110', 'w42', 'p8', 'pt', 'pm35', 'pa12', 'w41', 'p28', 'ph3.5', 'pw4', 'pm2.5', 'w37', 
#             'ph5.3', 'ph5.5', 'ph2.8', 'i15', 'w10', 'pmblr', 'p21', 'ph4.2', 'pm15', 'pr30', 'pctl', 'w66', 'w46', 
#             'ph1.8', 'pm50', 'w20', 'w15', 'pl25', 'pm40', 'pa18', 'pa6', 'pw4.5', 'p15', 'ph2.5', 'p4', 'w35', 'pm10', 
#             'pr20', 'i3', 'ph3.2', 'pw3', 'ph2.4', 'ph4.8', 'pw4.2', 'phcs', 'ph2.1', 'w34', 'pc', 'pr45', 'pm2', 'pl35', 
#             'pcs', 'pw2.5', 'i11', 'w60', 'pr10', 'pa8', 'p24', 'w8', 'w14', 'pm13', 'pnlc', 'pclr', 'w56', 'w43', 'ph3.8']

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
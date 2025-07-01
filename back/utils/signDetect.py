from ultralytics import YOLO
from utils.laneUtils.config import BASE_DIR
import cv2

model = YOLO(BASE_DIR + 'back/models/sign.pt')


# classes = ['ph5', 'p26', 'pl40', 'pl60', 'pn', 'i5', 'p11', 'pne', 'pcl', 'pl50', 'pcr', 'w55', 'pl5', 'ph4.5', 
#             'pl80', 'pg', 'w28', 'w30', 'pl30', 'p19', 'i4l', 'i2r', 'pw3.2', 'pm20', 'pbp', 'p5', 'pl120', 'w24', 
#             'p13', 'w57', 'ip', 'p10', 'il100', 'il60', 'il90', 'pb', 'pl110', 'w59', 'il80', 'pl100', 'ph4', 'pmb', 
#             'p14', 'pl15', 'i4', 'p16', 'p3', 'pl70', 'pdd', 'pr70', 'w13', 'w32', 'i2', 'pr40', 'pm30', 'w63', 
#             'p12', 'p17', 'p18', 'im', 'pl20', 'p6', 'pw3.5', 'p27', 'pcd', 'i14', 'p2', 'p1', 'i12', 'wc', 'i10', 
#             'p23', 'w58', 'p25', 'ph3', 'pl90', 'pbm', 'w5', 'pl10', 'pss', 'pm55', 'phclr', 'i13', 'i1', 'ph2.2', 
#             'w47', 'pr60', 'w38', 'il50', 'w16', 'w22', 'p20', 'pn-2', 'iz', 'p9', 
#              'p1n', 'ph4.3', 'ps', 'pm8', 'w3', 

#             'w21', 'p29', 'w18', 
#              'pa10', 'pa14', 'pa13',
#              'il70', 'ph2', 'pr100',   
#               'pr80', 'pm5', 'w45', 'pmr', 'w12',
#  
#             'ph2.9', 'pr50', 'il110', 'w42', 'p8',
#             'pt', 'pm35', 'pa12', 'w41',
#               'p28', 'ph3.5', 'pw4', 'pm2.5', 'w37', 
#             'ph5.3', 'ph5.5', 'ph2.8', 'i15', 'w10', 'pmblr', 'p21', 'ph4.2', 'pm15', 'pr30', 'pctl', 'w66', 'w46', 
#             'ph1.8', 'pm50', 'w20', 'w15', 'pl25', 'pm40', 'pa18', 'pa6', 'pw4.5', 'p15', 'ph2.5', 'p4', 'w35', 'pm10', ##154
#             'pr20', 'i3', 'ph3.2', 'pw3', 'ph2.4', 'ph4.8', 'pw4.2', 'phcs', 'ph2.1' ##163
# , 'w34', 'pc', 'pr45', 'pm2', 'pl35', 
#             'pcs',##169 
# 'pw2.5', 'i11', 'w60', 'pr10', 'pa8', 'p24', 'w8', 'w14', 'pm13', 'pnlc', 'pclr', 'w56', 'w43', 'ph3.8']
# }

model_names = {
    0: 'limit-5height', 2: 'limit-40kph', 3: 'limit-60kph', 9: 'limit-50kph', 12: 'limit-5kph', 13: 'limit-4.5height', 14: 'limit-80kph', 18:'limit-30kph',
    22:'limit-3.2width', 23: 'limit-10t-mass', 27: 'limit-120kph', 36: 'limit-110kph', 39: 'limit-100kph', 40: 'limit-4height', 43: 'limit-15kph',
    47: 'limit-70kph',  54: 'limit-30t-mass', 60: 'limit-20kph', 62: 'limit-3.5width', 74:'lmit-3height', 75: 'limit-90kph', 78: 'limit-10kph', 
    80: 'limit-55tmass', 84: 'limit-2.2height', 96: 'limit-4.3height', 98: 'limit-8t-mass', 103: 'limit-10t-axle', 104: 'limit-14t-axle', 105: 'limit-13t-axle',
    107: 'limit-2height', 110: 'limit-5t-mass', 114: 'limit-2.9height', 120: 'limit-35t-mass', 121: 'limit-12t-axle', 124: 'limit-3.5height', 
    125: 'limit-4width',  126: 'limit-2.5t-mass', 128: 'limit-5.3height',  129: 'limit-5.5height',  130: 'limit-2.8height',
    134:'not-gostright-turn-ringht',135:'limit-4.2height',136:'limit-15t',141:'limit-1.8height', 142:'limit-50t',145:'limit-25kph',146:'limit-40t',147:'limit-18t-axle',
    148:'limit-6t-axle',149:'limit-4.5width',151:'limit-2.5height',154:'limit-10t-mass', 157:'limit-3.2height', 158:'limit-3width',159:'limit-2.4height',160:'limit-4.8height',
    161:'limit-4.2width',163:'limit-2.1height',168:'limit-2t',169:'limit-135kph',170:'limit-2.5width',174:'limit-8t-axle',178:'limit-13t-mass',183: 'limit-3.8height',

    1: 'not-truck', 4: 'not-parking' , 6: 'not-horn', 7: 'not-entry', 8: 'not-car-left', 10: 'not-car-right', 15: 'not-fast-yield', 19: 'not-right',
    24: 'not-bicycle-person', 25: 'not-turn-around', 28: 'not-tractor-truck', 31: 'not-motor', 35: 'not-bicycle', 41: 'not-massive-bus',  42: 'not-straight', 
    45: 'not-human-powered-bicycle', 46: 'not-bus', 56: 'not-motorbicycle', 57: 'not-humanpowered-rickshaw', 58: 'not-tractor', 61: 'not-bicycle',
    63: 'not-car-with-danger-thing', 66:'not-animal-drawn-cart', 67: 'not-overtake', 71: 'not-turn-left', 73: 'not-car', 76: 'not-motorbicycle-bicycle',
    81: 'not-truck-turn-lr', 91: 'not-right-left', 92: 'not-parking-white', 94: 'not-person-walk', 101: 'not-tractor', 118: 'not-trailer',
    119: 'not-parking-2', 123: 'not-straight-left', 133: 'not-massive-bus-lr', 138: 'not-car-truck-left', 150: 'not-handcart', 152:'not-tricycle', 162: 'not-truck-straight', 169: 'not-car-straight', 
    175: 'not-turn-right', 179: 'not-nlc', 180: 'not-car-lr', 

    5: 'go-by-right', 20: 'go-car-left', 21: 'go-bicycle-right', 30: 'go-sidewalk', 32: 'go-above-100kph',  33: 'go-above-60kph', 34: 'go-above-90kph', 38: 'go-above-80kph', 
    44: 'go-car', 52: 'go-bicycle', 59: 'go-motorbicycle', 65: 'go-straight-or-right', 68: 'go-left', 70: 'go-right', 82: 'go-straight', 
    83: 'go-with-parent', 88: 'go-above-50kph', 93: 'go-turn-around',  106: 'go-above-70kph', 112: 'go-motorbicycle-right',
    116: 'go-above-110kph', 131: 'go-straight-right', 156: 'go-round', 171: 'go-right-left', 

    11: 'warning-children', 16: 'warning-uneven', 17: 'warning-slow', 26: 'warning-zig-zag', 29: 'warning-sidewalk-person', 37: 'waring-right-lane',
    48: 'warning-customs', 49: 'warning-unblock-70kph', 50: 'warning-cross', 51: "waring-construction", 53: 'warning-unblock-40kph', 55: 'warning-careful',
    64: 'warning-check', 69: 'warning-camera', 72: 'warning-left-lane', 77: 'warning-dike-right', 79: 'warning-slow-down',
    85: 'warning-right-narrow', 86: 'warning-unblock-60kph', 87: 'warning-openlight-tunnel', 89: 'warning-right-lane', 90: 'warning-right-ding',
    95: 'warning-unblock-overtake', 97: 'warning-stop-yield', 99: 'warning-village', 100: 'warning-left-ding', 102: 'warning-left-narrow',
    108: 'warning-unblock-100kph', 109: 'warning-unblock-80kph', 111: 'warning-trafficlight', 113: 'warning-wet-road', 115: 'warning-unblock-50kph', 117: 'warning-sharpe-right-turn',
    122: 'warning-slope-down', 127: 'warning-tunnel', 132: 'warning-reverse-detour', 137:'warning-free-30kph',139:'warning-Walk-around-left-and-right',140:'warning-railway',143: 'warning-T-road',144: 'warning-left-import',153: 'warning-Two-lane',
    155:'warning-free-20kph', 165:'warning-accident',166:'warning-examine',167:'warning-free-45', 172:'warning-wind',173:'warning-free-10k/h',176:'warning-road-narrows',177:'warning-Insert-lane',181:'warning-cycle-track',182:'warning-sharp-turn-left',
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
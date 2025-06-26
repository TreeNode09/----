import math
import time

def timed_method(interval):
    def decorator(method):
        def wrapper(self, *args, **kwargs):
            now = time.time()
            if not hasattr(self, '_last_call'):
                self._last_call = 0
            if now - self._last_call > interval:
                self._last_call = now
                return method(self, *args, **kwargs)
        return wrapper
    return decorator

class Tracker:
    def __init__(self):
        # 存储目标的中心位置
        self.center_points = {}
        self.id_heights = {}
        # ID计数
        # 每当检测到一个新的目标id时, 计数将增加1
        self.id_count = 1

    @timed_method(3)
    def __empty__(self):
       self.center_points = {}
       self.id_heights = {}

    def update(self, rect):
    
        x1, y1, x2, y2 = rect
        cx = (x1 + x2 ) // 2
        cy = (y1 + y2 ) // 2

        # 看看这个目标是否已经被检测到过
        for id, pt in self.center_points.items():
            dist = math.hypot(cx - pt[0], cy - pt[1])

            if dist < 35:
                self.center_points[id] = (cx, cy)
                self.id_heights[id] = y2-y1
                return id
            
        #说明未被检测，分配id
        self.center_points[self.id_count] = (cx, cy)
        self.id_heights[self.id_count] = y2-y1
        self.id_count += 1

        return 0
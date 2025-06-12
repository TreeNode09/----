from . import roadSegmentation

def handle_frame(img):
    img = roadSegmentation.process(img)
    return img
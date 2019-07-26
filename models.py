import cv2
import numpy as np

class Camera:
    def __init__(self, cam_num):
        self.cam_num = cam_num
        self.cap = None
        self.last_frame = np.zeros((1, 1))

    def initialize(self):
        self.cap = cv2.VideoCapture(self.cam_num)        

    def getFrame(self):
        ret, self.last_frame = self.cap.read()
        return self.last_frame

    def acquireMovie(self, num_frames=0):
        movie = []
        # Make continuous acquiring movie possible, it will run forever if you set the number of frames to 0, or None
        while num_frames == 0:
            movie.append(self.getFrame())
        else:
            for i in range(num_frames):
                movie.append(self.getFrame())
        return movie

    def setBrightness(self, value):
        self.cap.set(cv2.CAP_PROP_BRIGHTNESS, value)

    def getBrightness(self):
        return self.cap.get(cv2.CAP_PROP_BRIGHTNESS)

    def closeCamera(self):
        self.cap.release()

    def __str__(self):
        return 'OpenCV Camera {}'.format(self.cam_num)

if __name__ == '__main__':
    cam = Camera(0)
    cam.initialize()
    print(cam)
    frame = cam.getFrame()
    print(frame)
    cam.setBrightness(1)
    print(cam.getBrightness())
    cam.setBrightness(0.5)
    print(cam.getBrightness())
    cam.closeCamera()
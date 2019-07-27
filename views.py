import numpy as np
from scipy import optimize
from skimage.color import rgb2gray

from PyQt5.QtCore import Qt, QThread, QTimer
from PyQt5.QtWidgets import QMainWindow, QWidget, QPushButton, QVBoxLayout, QApplication, QSlider, QLabel, QLineEdit
from PyQt5.QtGui import QIntValidator

import pyqtgraph as pg
from pyqtgraph import ImageView, GraphicsLayoutWidget

class StartWindow(QMainWindow):
    def __init__(self, camera = None):
        super().__init__()
        self.camera = camera
        self.pixel_size = 0

        self.central_widget = QWidget()
        # Adding click buttons for acquire frame & movie
        self.button_frame = QPushButton('Acquire Frame', self.central_widget)
        self.button_movie = QPushButton('Start Movie', self.central_widget)
        self.button_stop_movie = QPushButton('Stop Movie', self.central_widget)
        self.button_fit = QPushButton('Start Fitting', self.central_widget)
        # Displaying an Image on the GUI
        self.image_view = ImageWindow()
        # Adding a Scrollbar for the Brightness
        self.bightness_slider = QSlider(Qt.Horizontal)
        self.bightness_slider.setRange(0, 10)
        # Adding a QLineEdit widget in order to let the user define the number
        self.frame_line = QLineEdit()
        # Adding validator, set the insert range from 0 to 9999
        self.Intvalidator = QIntValidator()
        self.Intvalidator.setRange(0,9999)
        self.frame_line.setValidator(self.Intvalidator)
        # Adding label for QLineEdit()
        self.frame_label = QLabel('Set Aquiring Frames Number')
        self.horizontal_label = QLabel(self)
        self.vertical_label = QLabel(self)
        self.horizontal_label.setText('Horizontal FWHM:')
        self.vertical_label.setText('Vertical FWHM:')
        self.px_label = QLabel('Pixel size (µm):')
        self.px_line = QLineEdit()
        
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.addWidget(self.button_frame)
        self.layout.addWidget(self.button_movie)
        self.layout.addWidget(self.button_stop_movie)
        self.layout.addWidget(self.frame_label)
        self.layout.addWidget(self.frame_line)
        self.layout.addWidget(self.button_fit)
        self.layout.addWidget(self.px_label)
        self.layout.addWidget(self.px_line) 
        self.layout.addWidget(self.image_view)
        self.layout.addWidget(self.bightness_slider)
        self.layout.addWidget(self.horizontal_label)
        self.layout.addWidget(self.vertical_label)
        self.setCentralWidget(self.central_widget)

        self.button_frame.clicked.connect(self.updateImage)
        self.button_movie.clicked.connect(self.startMovie)
        self.button_stop_movie.clicked.connect(self.stopAcquire)
        self.button_fit.clicked.connect(self.image_view.startFitting)
        self.bightness_slider.valueChanged.connect(self.updateBrightness)
        self.frame_line.editingFinished.connect(self.setAcquireNum)
        self.px_line.editingFinished.connect(self.setPixelSize)

        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.updateMovie)
        self.update_timer.timeout.connect(self.updateText)

    def updateImage(self):
        frame = self.camera.getFrame()
        self.image_view.showImage(frame)

    def updateMovie(self):
        self.image_view.showImage(self.camera.last_frame)

    def updateBrightness(self, value):
        value /= 10
        self.camera.setBrightness(value)

    def startMovie(self):
        self.movie_thread = MovieThread(self.camera)
        # acquire the movie
        self.movie_thread.start()
        # show the movie
        self.update_timer.start(30)

    def stopAcquire(self):
        self.movie_thread = MovieThread(self.camera)
        # stop acquire the movie
        self.movie_thread.exit()
        # stop show the movie
        self.update_timer.stop()

    def setAcquireNum(self):
        self.movie_thread = MovieThread(self.camera)
        self.movie_thread.num_frames = int(self.frame_line.text())
        self.movie_thread.start()
        self.update_timer.start(30)

    def setPixelSize(self):
        text = self.px_line.text()
        if text == None:
            self.pixel_size = 0
        else:
            self.pixel_size = float(text)*10**(-6)
        self.updateText()

    def updateText(self):
        coef_hor_show = self.image_view.coef_hor
        err_hor_show = self.image_view.err_hor
        coef_ver_show = self.image_view.coef_ver
        err_ver_show = self.image_view.err_ver
        self.horizontal_label.setText('Horizontal FWHM:{:.2e} +/- {:.2e}'.format(coef_hor_show[1]*self.pixel_size*2.35482, err_hor_show[1]*self.pixel_size*2.35482))
        self.vertical_label.setText('Vertical FWHM:{:.2e} +/- {:.2e}'.format(coef_ver_show[1]*self.pixel_size*2.35482, err_ver_show[1]*self.pixel_size*2.35482))

class MovieThread(QThread):
    def __init__(self, camera):
        super().__init__()
        self.camera = camera
        self.num_frames = 0

    def run(self):
        self.camera.acquireMovie(self.num_frames)

class ImageWindow(GraphicsLayoutWidget):
    def __init__(self):
        super().__init__()
        self.is_fitting_started = False
        self.coef_hor = np.zeros(3)
        self.err_hor = self.coef_ver = self.err_ver = self.coef_hor
        # generate a random image
        self.data = np.random.normal(size=(800,800))

        # set the window size
        self.resize(1080, 1080)
        # lock the aspect ratio so pixels are always square and disable the mouse event
        self.vb = self.addViewBox(lockAspect=True, enableMouse=False)

        # item for displaying image data
        self.img = pg.ImageItem()
        self.vb.addItem(self.img)

        # add a plot for displaying width data of image
        self.p2 = self.addPlot()
        self.p2.setMaximumWidth(100)
        self.p2.setYLink(self.vb)

        # add a plot for displaying width data of image
        self.nextRow()
        self.p3 = self.addPlot(colspan=1)
        self.p3.setMaximumHeight(100)
        self.p3.setXLink(self.vb)
        self.p3.invertY()
        self.p3.showAxis('top')
        self.p3.hideAxis('bottom')

        # Show image data
        #self.coef_hor, self.err_hor, self.coef_ver, self.err_ver = self.showImage(self.data)
        
        self.show()

    def showImage(self, data):
        # pyqtgraph have some problems in showing an image, the image was rotated in a ImageItem
        self.data = rgb2gray(data).T[::-1, ::-1]

        self.hight, self.width = self.data.shape

        self.img.setImage(self.data)
        self.vb.autoRange()

        self.x2 = np.arange(self.width)
        self.y2 = self.data.sum(axis=0)

        self.p2.clear()
        self.p2.plot(self.y2, self.x2)

        self.x3 = np.arange(self.hight)
        self.y3 = self.data.sum(axis=1)
    
        self.p3.clear()
        self.p3.plot(self.x3, self.y3)
        
        if self.is_fitting_started:
            # fitting the horizontal axis
            popt_hor, pcov_hor = optimize.curve_fit(self.GaussianCurve, self.x2, self.y2, bounds=([0, 0, self.data.min()], [self.width, np.inf, self.data.max()]))
            self.p2.plot(self.GaussianCurve(self.x2, popt_hor[0], popt_hor[1], popt_hor[2]), self.x2, pen='r')
            self.coef_hor = popt_hor
            self.err_hor = np.sqrt(np.diag(pcov_hor))
            #print(self.coef_hor, self.err_hor)

            # fitting the vertical axis
            popt_ver, pcov_ver = optimize.curve_fit(self.GaussianCurve, self.x3, self.y3, bounds=([0, 0, self.data.min()], [self.hight, np.inf, self.data.max()]))
            self.p3.plot(self.x3, self.GaussianCurve(self.x3, popt_ver[0], popt_ver[1], popt_ver[2]), pen='r')
            self.coef_ver = popt_ver
            self.err_ver = np.sqrt(np.diag(pcov_ver))
            #print(self.coef_ver, self.err_ver)

    def startFitting(self):
        self.is_fitting_started = True

    # define a Gaussian curve
    def GaussianCurve(self, x, mu, sigma, c):
        return np.sqrt(2*np.pi*sigma**2)*np.exp(-(x-mu)**2/(2*sigma**2))+c

if __name__ == '__main__':
    app = QApplication([])
    window = StartWindow()
    window.show()
    app.exit(app.exec_())
import numpy as np
from PyQt5.QtCore import Qt, QThread, QTimer
from PyQt5.QtWidgets import QMainWindow, QWidget, QPushButton, QVBoxLayout, QApplication, QSlider, QLabel, QLineEdit
from PyQt5.QtGui import QIntValidator
from pyqtgraph import ImageView

class StartWindow(QMainWindow):
    def __init__(self, camera = None):
        super().__init__()
        self.camera = camera

        self.central_widget = QWidget()
        # Adding click buttons for acquire frame & movie
        self.button_frame = QPushButton('Acquire Frame', self.central_widget)
        self.button_movie = QPushButton('Start Movie', self.central_widget)
        self.button_stop_movie = QPushButton('Stop Movie', self.central_widget)
        # Displaying an Image on the GUI
        self.image_view = ImageView()
        # Adding a Scrollbar for the Brightness
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 10)
        # Adding a QLineEdit widget in order to let the user define the number
        self.line = QLineEdit()
        # Adding validator, set the insert range from 0 to 9999
        self.Intvalidator = QIntValidator()
        self.Intvalidator.setRange(0,9999)
        self.line.setValidator(self.Intvalidator)
        # Adding label for QLineEdit()
        self.label = QLabel('Set Aquiring Frames Number')
        
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.addWidget(self.button_frame)
        self.layout.addWidget(self.button_movie)
        self.layout.addWidget(self.button_stop_movie)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.line)
        self.layout.addWidget(self.image_view)
        self.layout.addWidget(self.slider)
        self.setCentralWidget(self.central_widget)

        self.button_frame.clicked.connect(self.updateImage)
        self.button_movie.clicked.connect(self.startMovie)
        self.button_stop_movie.clicked.connect(self.stopAcquire)
        self.slider.valueChanged.connect(self.updateBrightness)
        self.line.editingFinished.connect(self.setAcquireNum)

        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.updateMovie)

    def updateImage(self):
        frame = self.camera.getFrame()
        self.image_view.setImage(frame.T)

    def updateMovie(self):
        self.image_view.setImage(self.camera.last_frame.T)

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
        self.movie_thread.num_frames = int(self.line.text())
        self.movie_thread.start()
        self.update_timer.start(30)

class MovieThread(QThread):
    def __init__(self, camera):
        super().__init__()
        self.camera = camera
        self.num_frames = 0

    def run(self):
        self.camera.acquireMovie(self.num_frames)

if __name__ == '__main__':
    app = QApplication([])
    window = StartWindow()
    window.show()
    app.exit(app.exec_())
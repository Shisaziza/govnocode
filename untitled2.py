import sys
import numpy as np
import cv2
import imutils
from PyQt5.QtWidgets import QApplication, QWidget, QSlider, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QGridLayout
from PyQt5.QtCore import Qt, QTimer

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.color_ranges = {
            'red': (np.array([0, 100, 100]), np.array([10, 255, 255])),
            'green': (np.array([50, 100, 100]), np.array([70, 255, 255])),
            'blue': (np.array([100, 100, 100]), np.array([130, 255, 255])),
            'yellow': (np.array([20, 100, 100]), np.array([40, 255, 255]))
        }
        self.color_sliders = {}
        for color, (lower, upper) in self.color_ranges.items():
            self.color_sliders[color] = {
                'H_min': QSlider(Qt.Horizontal),
                'S_min': QSlider(Qt.Horizontal),
                'V_min': QSlider(Qt.Horizontal),
                'H_max': QSlider(Qt.Horizontal),
                'S_max': QSlider(Qt.Horizontal),
                'V_max': QSlider(Qt.Horizontal)
            }
            self.color_sliders[color]['H_min'].setMinimum(0)
            self.color_sliders[color]['H_min'].setMaximum(255)
            self.color_sliders[color]['H_min'].setValue(lower.item(0))
            self.color_sliders[color]['S_min'].setMinimum(0)
            self.color_sliders[color]['S_min'].setMaximum(255)
            self.color_sliders[color]['S_min'].setValue(lower.item(1))
            self.color_sliders[color]['V_min'].setMinimum(0)
            self.color_sliders[color]['V_min'].setMaximum(255)
            self.color_sliders[color]['V_min'].setValue(lower.item(2))
            self.color_sliders[color]['H_max'].setMinimum(0)
            self.color_sliders[color]['H_max'].setMaximum(255)
            self.color_sliders[color]['H_max'].setValue(upper.item(0))
            self.color_sliders[color]['S_max'].setMinimum(0)
            self.color_sliders[color]['S_max'].setMaximum(255)
            self.color_sliders[color]['S_max'].setValue(upper.item(1))
            self.color_sliders[color]['V_max'].setMinimum(0)
            self.color_sliders[color]['V_max'].setMaximum(255)
            self.color_sliders[color]['V_max'].setValue(upper.item(2))
        self.line_pos_slider = QSlider(Qt.Horizontal)
        self.line_pos_slider.setMinimum(0)
        self.line_pos_slider.setMaximum(100)
        self.line_pos_slider.setValue(50)
        self.line_pos_slider.valueChanged.connect(self.on_line_pos_changed)
        self.line_pos_label = QLabel('Line position: 0.5')
        self.line_pos_layout = QHBoxLayout()
        self.line_pos_layout.addWidget(self.line_pos_slider)
        self.line_pos_layout.addWidget(self.line_pos_label)
        self.start_button = QPushButton('Start')
        self.start_button.clicked.connect(self.start)
        self.stop_button = QPushButton('Stop')
        self.stop_button.clicked.connect(self.stop)
        self.reset_button = QPushButton('Reset')
        self.reset_button.clicked.connect(self.reset)
        self.car_counters_layout = QGridLayout()
        self.car_counters_layout.addWidget(QLabel('Color'), 0, 0)
        self.car_counters_layout.addWidget(QLabel('Count'), 0, 1)
        self.car_counters = {color: 0 for color in self.color_ranges}
        row = 1
        for color in self.color_ranges:
            self.car_counters_layout.addWidget(QLabel(color), row, 0)
            self.car_counters_layout.addWidget(QLabel(str(self.car_counters[color])), row, 1)
            row += 1
        layout = QVBoxLayout()
        for color, slider in self.color_sliders.items():
            color_layout = QVBoxLayout()
            color_layout.addWidget(QLabel(color))
            color_layout.addWidget(QLabel('H'))
            color_layout.addWidget(slider['H_min'])
            color_layout.addWidget(slider['H_max'])
            color_layout.addWidget(QLabel('S'))
            color_layout.addWidget(slider['S_min'])
            color_layout.addWidget(slider['S_max'])
            color_layout.addWidget(QLabel('V'))
            color_layout.addWidget(slider['V_min'])
            color_layout.addWidget(slider['V_max'])
            layout.addLayout(color_layout)
        layout.addLayout(self.line_pos_layout)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.reset_button)
        layout.addLayout(self.car_counters_layout)
        self.setLayout(layout)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.line_pos = 0.5
        self.color_contours = {color: [] for color in self.color_ranges}

    def on_line_pos_changed(self, value):
        self.line_pos = value / 100
        self.line_pos_label.setText(f'Line position: {self.line_pos}')

    def update_frame(self):
        color_ranges = {}
        for color, slider in self.color_sliders.items():
            color_ranges[color] = (
                np.array([slider['H_min'].value(), slider['S_min'].value(), slider['V_min'].value()]),
                np.array([slider['H_max'].value(), slider['S_max'].value(), slider['V_max'].value()])
            )

        ret, frame = self.cap.read()
        if not ret:
            return
        for color in color_ranges:
            mask = cv2.inRange(frame, *color_ranges[color])
            if detect_crossing(mask, self.line_pos):
                print(f'{color} car crossed the line')
                self.car_counters[color] += 1
                self.car_counters_layout.itemAtPosition(list(self.color_ranges.keys()).index(color) + 1, 1).widget().setText(str(self.car_counters[color]))
                cv2.putText(frame, f'{color} car crossed the line', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
            self.color_contours[color] = []
            contours = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            contours = imutils.grab_contours(contours)
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                center = (int(x + w/2), int(y + h/2))
                if center[1] > self.line_pos * frame.shape[0]:
                    self.color_contours[color].append(contour)
            cv2.imshow(f'{color} mask', mask)
        frame_contours = []
        for color, contours in self.color_contours.items():
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.drawContours(frame, [contour], -1, (0, 255, 0), 2)
                cv2.circle(frame, (int(x + w/2), int(y + h/2)), 5, (0, 0, 255), -1)
                cv2.putText(frame, f'{color} car', (int(x + w/2) + 10, int(y + h/2)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                frame_contours.append(contour)
        cv2.line(frame, (0, int(self.line_pos * frame.shape[0])), (frame.shape[1], int(self.line_pos * frame.shape[0])), (0, 0, 255), 2)
        cv2.imshow('frame', frame)

    def start(self):
        self.cap = cv2.VideoCapture(0)
        self.timer.start(30)

    def stop(self):
        self.timer.stop()
        self.cap.release()
        cv2.destroyAllWindows()

    def reset(self):
        self.car_counters = {color: 0 for color in self.color_ranges}
        for row in range(1, len(self.color_ranges) + 1):
            self.car_counters_layout.itemAtPosition(row, 1).widget().setText('0')

def detect_crossing(mask, line_pos):
    contours = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = imutils.grab_contours(contours)
    for contour in contours:
        (x, y, w, h) = cv2.boundingRect(contour)
        center = (int(x + w/2), int(y + h/2))
        if center[1] > line_pos * mask.shape[0]:
            return True
    return False

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
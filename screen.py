import sys
import os
import cv2
import numpy as np
import time
import chess
import chess.svg
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QHBoxLayout, QGraphicsView, QGraphicsScene, QMessageBox
from PyQt5.QtGui import QPixmap, QPainter, QPen, QImage
from PyQt5.QtCore import Qt, QRect, QTimer, pyqtSignal
from PyQt5.QtSvg import QGraphicsSvgItem, QSvgRenderer
import win32gui
import win32ui
import win32con
import win32api
from stockfish import Stockfish

class ScreenCapture(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Screen Capture Tool')
        self.setGeometry(100, 100, 1200, 600)
        self.start_point = None
        self.end_point = None
        self.is_drawing = False
        self.rect = QRect()
        self.screenshot_timer = QTimer()
        self.screenshot_timer.timeout.connect(self.capture_screen)
        self.capture_enabled = False
        self.initUI()

    def initUI(self):
        self.play_button = QPushButton('Play', self)
        self.stop_button = QPushButton('Stop', self)
        self.stop_button.setEnabled(False)
        self.label = QLabel('Select region and press Play', self)
        self.mouse_coords_label = QLabel('Mouse Coordinates: (0, 0)', self)
        self.mouse_down_label = QLabel('Mouse Down Coordinates (Win32): (0, 0)', self)
        self.mouse_up_label = QLabel('Mouse Up Coordinates (Win32): (0, 0)', self)
        self.selected_area_label = QLabel('Selected Area: (0, 0, 0, 0)', self)
        self.entire_area_label = QLabel(f'Entire Area: (0, 0, {QApplication.desktop().width()}, {QApplication.desktop().height()})', self)

        self.play_button.clicked.connect(self.start_capture)
        self.stop_button.clicked.connect(self.stop_capture)

        self.chess_board = ChessBoard()
        self.screenshot_label = QLabel()
        self.screenshot_label.setFixedSize(400, 400)
        self.screenshot_label.setStyleSheet("border: 1px solid black;")

        self.reset_board_button = QPushButton('Reset Board from Image', self)
        self.reset_board_button.clicked.connect(self.reset_board_from_image)

        self.toggle_computer_button = QPushButton('Toggle Computer Color', self)
        self.toggle_computer_button.clicked.connect(self.toggle_computer_color)
        self.computer_color_label = QLabel('Computer is playing as White', self)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.play_button)
        button_layout.addWidget(self.stop_button)

        layout = QVBoxLayout()
        layout.addLayout(button_layout)
        layout.addWidget(self.label)
        layout.addWidget(self.mouse_coords_label)
        layout.addWidget(self.mouse_down_label)
        layout.addWidget(self.mouse_up_label)
        layout.addWidget(self.selected_area_label)
        layout.addWidget(self.entire_area_label)
        layout.addWidget(self.reset_board_button)
        layout.addWidget(self.toggle_computer_button)
        layout.addWidget(self.computer_color_label)

        board_layout = QHBoxLayout()
        board_layout.addWidget(self.chess_board)
        board_layout.addWidget(self.screenshot_label)
        
        layout.addLayout(board_layout)
        self.setLayout(layout)

    def start_capture(self):
        self.overlay = Overlay(self)
        self.overlay.show()
        self.play_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.capture_enabled = True
        self.label.setText('Capturing... Press Stop to end.')

    def stop_capture(self):
        self.play_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.capture_enabled = False
        self.screenshot_timer.stop()
        self.label.setText('Capture stopped. Select region and press Play.')

    def capture_screen(self):
        if self.capture_enabled and not self.rect.isNull():
            x1 = int(self.rect.left())
            y1 = int(self.rect.top())
            width = int(self.rect.width())
            height = int(self.rect.height())

            hwin = win32gui.GetDesktopWindow()
            hwindc = win32gui.GetWindowDC(hwin)
            srcdc = win32ui.CreateDCFromHandle(hwindc)
            memdc = srcdc.CreateCompatibleDC()
            bmp = win32ui.CreateBitmap()
            bmp.CreateCompatibleBitmap(srcdc, width, height)
            memdc.SelectObject(bmp)
            memdc.BitBlt((0, 0), (width, height), srcdc, (x1, y1), win32con.SRCCOPY)

            bmp_info = bmp.GetInfo()
            bmp_str = bmp.GetBitmapBits(True)

            img = np.frombuffer(bmp_str, dtype='uint8')
            img.shape = (bmp_info['bmHeight'], bmp_info['bmWidth'], 4)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

            win32gui.DeleteObject(bmp.GetHandle())
            memdc.DeleteDC()
            srcdc.DeleteDC()
            win32gui.ReleaseDC(hwin, hwindc)

            timestamp = int(time.time())
            screenshot_path = f'screenshot_{timestamp}.png'
            cv2.imwrite(screenshot_path, img)

            self.update_screenshot_label(screenshot_path)
    
    def update_screenshot_label(self, path):
        pixmap = QPixmap(path)
        self.screenshot_label.setPixmap(pixmap.scaled(self.screenshot_label.size(), Qt.KeepAspectRatio))

    def set_capture_region(self, rect):
        self.rect = rect
        self.update_area_labels()
        if self.capture_enabled:
            self.screenshot_timer.start(1000)

    def update_area_labels(self):
        x1 = int(self.rect.left())
        y1 = int(self.rect.top())
        width = int(self.rect.width())
        height = int(self.rect.height())

        self.selected_area_label.setText(f'Selected Area: ({x1}, {y1}, {width}, {height})')
        self.entire_area_label.setText(f'Entire Area: (0, 0, {QApplication.desktop().width()}, {QApplication.desktop().height()})')

    def update_mouse_coords(self, pos):
        self.mouse_coords_label.setText(f'Mouse Coordinates: ({pos.x()}, {pos.y()})')

    def update_mouse_down_coords(self):
        pos = win32api.GetCursorPos()
        self.mouse_down_label.setText(f'Mouse Down Coordinates (Win32): ({pos[0]}, {pos[1]})')

    def update_mouse_up_coords(self):
        pos = win32api.GetCursorPos()
        self.mouse_up_label.setText(f'Mouse Up Coordinates (Win32): ({pos[0]}, {pos[1]})')

    def reset_board_from_image(self):
        # Assume the screenshot has been saved and use it to update the board
        latest_screenshot = max([f for f in os.listdir('.') if f.startswith('screenshot_')], key=os.path.getctime)
        img = cv2.imread(latest_screenshot)
        board_fen = self.read_board_from_image(img)
        if board_fen:
            self.chess_board.board.set_fen(board_fen)
            self.chess_board.update_board()

    def read_board_from_image(self, img):
        # Use image processing to recognize the chess board and convert it to FEN
        # This is a placeholder for actual chess board recognition logic
        # You need to implement the actual board recognition here
        # For now, let's assume it returns a valid FEN string for the initial position
        return chess.Board().fen()

    def toggle_computer_color(self):
        self.chess_board.computer_is_white = not self.chess_board.computer_is_white
        if self.chess_board.computer_is_white:
            self.computer_color_label.setText('Computer is playing as White')
        else:
            self.computer_color_label.setText('Computer is playing as Black')
        if self.chess_board.board.turn == (self.chess_board.computer_is_white):
            self.chess_board.make_ai_move()

class Overlay(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.start_point = None
        self.end_point = None
        self.is_drawing = False
        self.rect = QRect()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Overlay')
        self.setGeometry(0, 0, QApplication.desktop().width(), QApplication.desktop().height())
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setWindowOpacity(0.3)

    def paintEvent(self, event):
        if self.is_drawing and self.start_point and self.end_point:
            painter = QPainter(self)
            pen = QPen(Qt.red, 2, Qt.SolidLine)
            painter.setPen(pen)
            self.rect = QRect(self.start_point, self.end_point)
            painter.drawRect(self.rect)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_point = event.pos()
            self.is_drawing = True
            self.parent.update_mouse_down_coords()

    def mouseMoveEvent(self, event):
        if self.is_drawing:
            self.end_point = event.pos()
            self.update()
            self.parent.update_mouse_coords(event.pos())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.end_point = event.pos()
            self.is_drawing = False
            self.parent.update_mouse_up_coords()
            self.parent.set_capture_region(self.rect)
            self.close()

class ChessBoard(QGraphicsView):
    move_made = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.board = chess.Board()
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setFixedSize(400, 400)
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.update_board()
        self.selected_piece = None
        self.source_square = None
        self.setMouseTracking(True)
        self.stockfish = Stockfish(path="./stockfish/stockfish-windows-x86-64-avx2.exe")  # Update with the actual path to Stockfish executable
        self.stockfish.set_depth(15)
        self.computer_is_white = True

    def update_board(self):
        svg = chess.svg.board(self.board).encode("UTF-8")
        svg_renderer = QSvgRenderer(svg)
        svg_item = QGraphicsSvgItem()
        svg_item.setSharedRenderer(svg_renderer)
        self.scene.clear()
        self.scene.addItem(svg_item)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = self.mapToScene(event.pos())
            square = self.get_square(pos)
            if self.board.piece_at(square):
                self.selected_piece = self.board.piece_at(square)
                self.source_square = square

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.selected_piece:
            pos = self.mapToScene(event.pos())
            target_square = self.get_square(pos)
            move = chess.Move(self.source_square, target_square)
            if move in self.board.legal_moves:
                self.board.push(move)
                self.update_board()
                self.make_ai_move()
            self.selected_piece = None
            self.source_square = None

    def get_square(self, pos):
        x, y = pos.x(), pos.y()
        square_size = self.width() / 8
        col = int(x / square_size)
        row = 7 - int(y / square_size)
        return chess.square(col, row)

    def make_ai_move(self):
        if self.board.turn == self.computer_is_white:
            self.stockfish.set_fen_position(self.board.fen())
            best_move = self.stockfish.get_best_move()
            self.board.push(chess.Move.from_uci(best_move))
            self.update_board()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    screen_capture_tool = ScreenCapture()
    screen_capture_tool.show()
    sys.exit(app.exec_())

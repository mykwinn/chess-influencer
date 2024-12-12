import pyautogui
import threading
import time


class MouseTracker:
    def __init__(self, ui):
        self.ui = ui
        self.position = (0, 0)
        self.track_mouse()

    def track_mouse(self):
        def update():
            while True:
                x, y = pyautogui.position()
                self.position = (x, y)
                self.ui.mouse_coords_label.config(text=f"Mouse Coordinates: ({x}, {y})")
                time.sleep(0.1)  # Update every 100ms

        thread = threading.Thread(target=update, daemon=True)
        thread.start()

    def get_position(self):
        return self.position

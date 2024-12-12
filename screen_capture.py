import cv2
import numpy as np
import time
import mss
from PIL import Image


class ScreenCapture:
    def __init__(self):
        self.sct = mss.mss()  # MSS instance for capturing
        self.monitors = self.sct.monitors  # List of all monitors

    def capture_screen(self, rect):
        """Capture the selected screen area."""
        if rect:
            x1, y1, width, height = rect  # Use the selected region for capture
            monitor = self.get_monitor_from_position(x1, y1)  # Capture the correct monitor

            # Adjust x1 and y1 relative to the selected monitor
            capture_area = {
                "top": y1 - monitor["top"],
                "left": x1 - monitor["left"],
                "width": width,
                "height": height
            }

            # Capture the screenshot
            screenshot = self.sct.grab(capture_area)

            # Convert the screenshot to a format OpenCV can work with
            img = np.array(screenshot)

            # Convert from BGRA to BGR for OpenCV
            img = img[..., :3]

            # Save the image
            timestamp = int(time.time())
            screenshot_path = f'screenshot_{timestamp}.png'
            cv2.imwrite(screenshot_path, img)
            return screenshot_path

    def get_monitor_from_position(self, x, y):
        """Find the monitor that contains the coordinates (x, y)."""

import tkinter as tk
from PIL import ImageTk, Image
from screen_capture import ScreenCapture
from utils import MouseTracker
from mouse_events import MouseEventsMixin


class ScreenCaptureUI(tk.Tk, MouseEventsMixin):
    def __init__(self):
        super().__init__()
        self.title('Screen Capture Tool')
        self.geometry('1200x600')
        self.start_point = None
        self.end_point = None
        self.is_drawing = False
        self.rect = None
        self.screenshot_enabled = False
        self.sc = ScreenCapture()  # Instance of screen capture logic

        self.active_monitor = "None"  # To track which monitor the user is capturing
        self.initUI()
        self.mouse_tracker = MouseTracker(self)  # Start tracking mouse

    def initUI(self):
        self.play_button = tk.Button(self, text="Play", command=self.start_capture)
        self.capture_button = tk.Button(self, text="Capture", command=self.start_capture_mode)
        self.stop_button = tk.Button(self, text="Stop", command=self.stop_capture, state=tk.DISABLED)
        self.label = tk.Label(self, text="Select region and press Play")
        self.mouse_coords_label = tk.Label(self, text="Mouse Coordinates: (0, 0)")
        self.mouse_down_label = tk.Label(self, text="Mouse Down Coordinates: (0, 0)")
        self.mouse_up_label = tk.Label(self, text="Mouse Up Coordinates: (0, 0)")
        self.screen_label = tk.Label(self, text="Screen: None")
        self.selected_area_label = tk.Label(self, text="Selected Area: (0, 0, 0, 0)")

        self.play_button.pack()
        self.capture_button.pack()
        self.stop_button.pack()
        self.label.pack()
        self.mouse_coords_label.pack()
        self.mouse_down_label.pack()
        self.mouse_up_label.pack()
        self.screen_label.pack()  # Screen label shows active monitor
        self.selected_area_label.pack()

        self.screenshot_label = tk.Label(self)
        self.screenshot_label.pack()

        # Add a canvas for drawing the rectangle
        self.canvas = tk.Canvas(self, width=1200, height=600, bg="white")
        self.canvas.pack(fill="both", expand=True)

        # Bind mouse events for rectangle drawing
        self.canvas.bind("<Button-1>", self.mouse_down)
        self.canvas.bind("<B1-Motion>", self.mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.mouse_up)

    def start_capture(self):
        self.play_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.screenshot_enabled = True
        self.label.config(text="Capturing... Press Stop to end.")
        self.capture_loop()

    def stop_capture(self):
        self.play_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.screenshot_enabled = False
        self.label.config(text="Capture stopped. Select region and press Play.")

    def capture_loop(self):
        if self.screenshot_enabled:
            screenshot_path = self.sc.capture_screen(self.rect)
            if screenshot_path:
                self.update_screenshot_label(screenshot_path)
            self.after(1000, self.capture_loop)  # Capture every 1 second

    def update_screenshot_label(self, path):
        img = Image.open(path)
        img = img.resize((400, 400))
        tk_img = ImageTk.PhotoImage(img)
        self.screenshot_label.config(image=tk_img)
        self.screenshot_label.image = tk_img  # Keep a reference to avoid garbage collection

    def start_capture_mode(self):
        # Dim all screens except the capture area and block other interactions
        self.label.config(text="Screen capture mode enabled. Select the area.")
        self.dim_screens()

    def dim_screens(self):
        # Create an overlay that dims all windows except the selected capture area
        self.capture_overlay = tk.Toplevel(self)
        self.capture_overlay.attributes('-alpha', 0.5)  # Set transparency
        self.capture_overlay.attributes('-fullscreen', True)
        self.capture_overlay.configure(bg='gray')
        self.capture_overlay.grab_set()  # Make it unclickable outside the capture window

        # Bind mouse events on the overlay for drawing capture area
        self.capture_overlay.bind("<Button-1>", self.mouse_down)
        self.capture_overlay.bind("<B1-Motion>", self.mouse_drag)
        self.capture_overlay.bind("<ButtonRelease-1>", self.mouse_up)

        # Update the label to show which screen is active
        x, y = self.mouse_tracker.get_position()
        self.active_monitor = self.sc.get_monitor_from_position(x, y)["id"]
        self.screen_label.config(text=f"Screen: {self.active_monitor}")


if __name__ == "__main__":
    app = ScreenCaptureUI()
    app.mainloop()

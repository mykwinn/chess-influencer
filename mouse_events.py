class MouseEventsMixin:
    def mouse_down(self, event):
        # Capture the start point for the rectangle
        x, y = self.mouse_tracker.get_position()
        self.start_point = (x, y)
        self.mouse_down_label.config(text=f"Mouse Down Coordinates: ({x}, {y})")
        self.is_drawing = True

    def mouse_drag(self, event):
        if self.is_drawing:
            # Update the rectangle as the mouse is dragged
            x, y = self.mouse_tracker.get_position()
            self.end_point = (x, y)
            self.draw_rectangle()

    def mouse_up(self, event):
        # Capture the end point for the rectangle
        x, y = self.mouse_tracker.get_position()
        self.end_point = (x, y)
        self.mouse_up_label.config(text=f"Mouse Up Coordinates: ({x}, {y})")
        self.is_drawing = False
        self.update_selected_area()

        # Close the overlay once the area is selected
        self.capture_overlay.destroy()

    def draw_rectangle(self):
        # Clear previous rectangle before drawing a new one
        self.canvas.delete("selection_rect")
        # Draw the rectangle on the canvas dynamically
        self.canvas.create_rectangle(
            self.start_point[0], self.start_point[1], self.end_point[0], self.end_point[1],
            outline='red', width=2, tags="selection_rect"
        )

    def update_selected_area(self):
        # Calculate the selected area and update the label
        if self.start_point and self.end_point:
            x1, y1

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
import zipfile
import os
from PIL import Image, ImageTk
import io
import numpy as np
import csv

class MinecraftPackViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("RecolorTool")
        self.root.state('zoomed')
        
        self.zip_file = None
        self.png_files = []
        self.file_vars = {}
        self.selected_color = "#00FFFF"
        self.exclude_wood = tk.BooleanVar(value=True)
        self.allowed_files = self.load_allowed_files()
        
        self.setup_ui()
    
    def load_allowed_files(self):
        csv_path = os.path.join(os.path.dirname(__file__), "items.csv")
        allowed_files = []
        
        try:
            with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    if row and not row[0].startswith('//'):
                        allowed_files.append(row[0].strip())
        except FileNotFoundError:
            messagebox.showerror("Error", f"CSV file not found: {csv_path}")
            # Fallback to hardcoded list
            allowed_files = [
                "diamond_sword", "diamond_hoe", "diamond_axe", "diamond_helmet",
                "diamond_chestplate", "diamond_leggings", "diamond_boots",
                "diamond_pickaxe", "diamond_shovel", "fishing_rod_cast",
                "fishing_rod_uncast", "ender_pearl", "diamond_ore", "diamond",
                "diamond_block", "diamond_layer_1", "diamond_layer_2",
                "enchanted_hit", "critical_hit", "angry", "heart", "flame",
                "lava", "fishing_hook", "icons", "widgets", "particles"
            ]
        except Exception as e:
            messagebox.showerror("Error", f"Error reading CSV file: {str(e)}")
            allowed_files = []
        
        return allowed_files
    
    def setup_ui(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Button(top_frame, text="Open ZIP File", command=self.open_zip_file).pack(side="left")
        self.file_label = ttk.Label(top_frame, text="No file selected")
        self.file_label.pack(side="left", padx=(10, 0))
        
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill="both", expand=True)
        
        left_frame = ttk.Frame(content_frame)
        left_frame.pack(side="left", fill="both", expand=True)
        
        file_controls = ttk.Frame(left_frame)
        file_controls.pack(fill="x", pady=(0, 5))
        
        ttk.Label(file_controls, text="PNG Files:").pack(side="left")
        ttk.Button(file_controls, text="All", command=self.select_all).pack(side="right", padx=(5, 0))
        ttk.Button(file_controls, text="None", command=self.select_none).pack(side="right")
        
        checkbox_canvas = tk.Canvas(left_frame)
        checkbox_scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=checkbox_canvas.yview)
        self.checkbox_frame = ttk.Frame(checkbox_canvas)
        
        self.checkbox_frame.bind(
            "<Configure>",
            lambda e: checkbox_canvas.configure(scrollregion=checkbox_canvas.bbox("all"))
        )
        
        checkbox_canvas.create_window((0, 0), window=self.checkbox_frame, anchor="nw")
        checkbox_canvas.configure(yscrollcommand=checkbox_scrollbar.set)
        
        checkbox_canvas.pack(side="left", fill="both", expand=True)
        checkbox_scrollbar.pack(side="right", fill="y")
        
        middle_frame = ttk.Frame(content_frame)
        middle_frame.pack(side="left", fill="y", padx=(10, 0))
        
        color_frame = ttk.LabelFrame(middle_frame, text="Select Color", padding=10)
        color_frame.pack(fill="x", pady=(0, 10))
        
        self.color_display = tk.Label(color_frame, width=10, height=2, bg=self.selected_color, relief="solid")
        self.color_display.pack(pady=(0, 5))
        
        ttk.Button(color_frame, text="Choose Color", command=self.choose_color).pack()
        
        self.color_label = ttk.Label(color_frame, text=f"RGB: {self.hex_to_rgb(self.selected_color)}")
        self.color_label.pack(pady=(5, 0))
        
        wood_checkbox = ttk.Checkbutton(
            color_frame, 
            text="Exclude Wood/Brown", 
            variable=self.exclude_wood
        )
        wood_checkbox.pack(pady=(10, 0))
        
        process_frame = ttk.LabelFrame(middle_frame, text="Processing", padding=10)
        process_frame.pack(fill="x")
        
        ttk.Button(process_frame, text="Preview", command=self.preview_recolor).pack(fill="x", pady=(0, 5))
        ttk.Button(process_frame, text="Save as New ZIP", command=self.save_recolored_zip).pack(fill="x")
        
        self.progress = ttk.Progressbar(process_frame, mode='determinate', maximum=100, value=0)
        self.progress.pack(fill="x", pady=(5, 0))
        
        self.loading_label = ttk.Label(process_frame, text="", foreground="blue")
        self.loading_label.pack(pady=(2, 0))

        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        ttk.Label(right_frame, text="Image Preview:").pack(anchor="w")
        
        image_frame = ttk.Frame(right_frame)
        image_frame.pack(fill="both", expand=True, pady=(5, 0))
        
        self.canvas = tk.Canvas(image_frame, bg="white")
        v_scrollbar = ttk.Scrollbar(image_frame, orient="vertical", command=self.canvas.yview)
        h_scrollbar = ttk.Scrollbar(image_frame, orient="horizontal", command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")
        
        self.info_label = ttk.Label(right_frame, text="")
        self.info_label.pack(pady=(5, 0))
    
    def open_zip_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Minecraft Pack",
            filetypes=[("ZIP files", "*.zip"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                self.zip_file = zipfile.ZipFile(file_path, 'r')
                self.file_label.config(text=f"File: {os.path.basename(file_path)}")
                self.load_png_files()
            except Exception as e:
                messagebox.showerror("Error", f"Error opening ZIP file: {str(e)}")
    
    def rgb_to_hsv(self, r, g, b):
        r, g, b = r/255.0, g/255.0, b/255.0
        max_val = max(r, g, b)
        min_val = min(r, g, b)
        diff = max_val - min_val
        
        # Hue
        if diff == 0:
            h = 0
        elif max_val == r:
            h = (60 * ((g - b) / diff) + 360) % 360
        elif max_val == g:
            h = (60 * ((b - r) / diff) + 120) % 360
        else:
            h = (60 * ((r - g) / diff) + 240) % 360
        
        # Saturation
        if max_val == 0:
            s = 0
        else:
            s = diff / max_val
        
        v = max_val
        
        return h, s, v
    
    def hsv_to_rgb(self, h, s, v):
        c = v * s
        x = c * (1 - abs((h / 60) % 2 - 1))
        m = v - c
        
        if 0 <= h < 60:
            r, g, b = c, x, 0
        elif 60 <= h < 120:
            r, g, b = x, c, 0
        elif 120 <= h < 180:
            r, g, b = 0, c, x
        elif 180 <= h < 240:
            r, g, b = 0, x, c
        elif 240 <= h < 300:
            r, g, b = x, 0, c
        else:
            r, g, b = c, 0, x
        
        r = int((r + m) * 255)
        g = int((g + m) * 255)
        b = int((b + m) * 255)
        
        return r, g, b

    def is_brown_color(self, r, g, b):
        h, s, v = self.rgb_to_hsv(r, g, b)
        is_brown_hue = (10 <= h <= 40) and s > 0.2 and v > 0.2
        
        is_brown_rgb = (
            # Dark brown range
            (r >= 40 and r <= 120 and g >= 20 and g <= 80 and b >= 10 and b <= 50) or
            # Medium brown range
            (r >= 80 and r <= 160 and g >= 50 and g <= 120 and b >= 20 and b <= 80) or
            # Light brown range
            (r >= 120 and r <= 200 and g >= 80 and g <= 150 and b >= 40 and b <= 100)
        )
        
        return is_brown_hue or is_brown_rgb

    def recolor_image(self, image, target_color):
        # Force convert to RGBA to preserve transparency
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        img_array = np.array(image)
        
        target_rgb = self.hex_to_rgb(target_color)
        target_h, target_s, target_v = self.rgb_to_hsv(*target_rgb)
        
        height, width = img_array.shape[:2]
        for y in range(height):
            for x in range(width):
                r, g, b, a = img_array[y, x]

                # Skip fully transparent pixels
                if a < 10:
                    continue
                
                if r < 10 and g < 10 and b < 10:
                    continue
                
                if self.exclude_wood.get() and self.is_brown_color(r, g, b):
                    continue
                
                h, s, v = self.rgb_to_hsv(r, g, b)
                
                should_recolor = False
                
                if s > 0.05 and v > 0.1:
                    should_recolor = True
                elif v > 0.15 and v < 0.95:
                    if not (r > 200 and g > 200 and b > 200 and s < 0.1):
                        should_recolor = True
                
                if should_recolor:
                    if v > 0.8:
                        if s < 0.2:
                            continue
                        new_s = min(target_s * 0.6, 1.0)
                        new_v = min(v * 1.05, 1.0)
                    elif v > 0.5:
                        new_s = target_s * 0.9
                        new_v = v
                    elif v > 0.25:
                        new_s = min(target_s * 1.2, 1.0)
                        new_v = max(v * 1.15, 0.3)
                    else:
                        new_s = target_s * 0.8
                        new_v = max(v * 1.3, 0.2)
                    
                    new_s = max(new_s, 0.15)
                    
                    new_r, new_g, new_b = self.hsv_to_rgb(target_h, new_s, new_v)
                    
                    img_array[y, x] = [new_r, new_g, new_b, a]
        
        return Image.fromarray(img_array, 'RGBA')
    
    def is_diamond_like_color(self, r, g, b):
        diamond_ranges = [
            # Light cyan/aqua
            (150 <= r <= 220 and 220 <= g <= 255 and 220 <= b <= 255),
            # Medium cyan
            (100 <= r <= 180 and 180 <= g <= 240 and 200 <= b <= 255),
            # Darker cyan/blue
            (50 <= r <= 150 and 150 <= g <= 200 and 180 <= b <= 230),
            # Very light blue/white-blue
            (200 <= r <= 255 and 230 <= g <= 255 and 240 <= b <= 255),
            # Gray-blue (for armor shadows/highlights)
            (80 <= r <= 160 and 120 <= g <= 180 and 140 <= b <= 200)
        ]
        
        return any(diamond_ranges)

    def show_loading(self, message, progress=0):
        self.loading_label.config(text=message)
        self.progress['value'] = progress
        self.root.update()
    
    def hide_loading(self):
        self.loading_label.config(text="")
        self.progress['value'] = 0
        self.root.update()

    def auto_display_images(self):
        selected_files = [path for path, var in self.file_vars.items() if var.get()]
        
        if not selected_files:
            self.canvas.delete("all")
            self.info_label.config(text="No files selected")
            return
        
        try:
            self.canvas.delete("all")
            if hasattr(self, 'preview_images'):
                self.preview_images = []
            
            num_files = len(selected_files)
            cols = min(3, num_files) 
            rows = (num_files + cols - 1) // cols

            img_size = 180
            padding = 30
            
            total_width = cols * (img_size + padding) + padding
            total_height = rows * (img_size + padding * 2) + padding + 50 
            
            self.canvas.configure(scrollregion=(0, 0, total_width, total_height))
            
            self.preview_images = []
            
            for i, file_path in enumerate(selected_files):
                row = i // cols
                col = i % cols
                
                x = col * (img_size + padding) + padding + img_size // 2
                y = row * (img_size + padding * 2) + padding + img_size // 2
                
                image_data = self.zip_file.read(file_path)
                original_image = Image.open(io.BytesIO(image_data))
                
                scale = min(img_size / original_image.width, img_size / original_image.height)
                new_width = int(original_image.width * scale)
                new_height = int(original_image.height * scale)
                
                if scale > 1:  # Upscale
                    display_image = original_image.resize((new_width, new_height), Image.Resampling.NEAREST)
                else:  # Downscale
                    display_image = original_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                photo = ImageTk.PhotoImage(display_image)
                
                img_id = self.canvas.create_image(x, y, anchor="center", image=photo)
                
                filename = os.path.basename(file_path).replace('.png', '')
                text_y = y + img_size // 2 + 20
                self.canvas.create_text(x, text_y, text=filename, anchor="center", font=("Arial", 10, "bold"))
                
                self.preview_images.append(photo)
            
            self.info_label.config(
                text=f"{len(selected_files)} files displayed"
            )
            
        except Exception as e:
            messagebox.showerror("Error", f"Error displaying images: {str(e)}")
    
    def preview_recolor(self):
        selected_files = [path for path, var in self.file_vars.items() if var.get()]
        
        if not selected_files:
            messagebox.showwarning("Warning", "No files selected!")
            return
        
        self.show_loading("Loading preview...", 0)
        
        try:
            # Clear canvas
            self.canvas.delete("all")
            if hasattr(self, 'preview_images'):
                self.preview_images = []
            
            # Calculate grid dimensions
            num_files = len(selected_files)
            cols = min(3, num_files)
            rows = (num_files + cols - 1) // cols
            
            img_size = 180
            padding = 30
            
            total_width = cols * (img_size + padding) + padding
            total_height = rows * (img_size + padding * 2) + padding + 50
            
            self.canvas.configure(scrollregion=(0, 0, total_width, total_height))
            
            self.preview_images = []
            
            for i, file_path in enumerate(selected_files):
                progress = int((i / len(selected_files)) * 100)
                self.show_loading(f"Processing {i+1}/{len(selected_files)}...", progress)
                
                row = i // cols
                col = i % cols
                
                x = col * (img_size + padding) + padding + img_size // 2
                y = row * (img_size + padding * 2) + padding + img_size // 2
                
                # Load and recolor image - force RGBA
                image_data = self.zip_file.read(file_path)
                original_image = Image.open(io.BytesIO(image_data)).convert('RGBA')
                recolored_image = self.recolor_image(original_image, self.selected_color)
                
                # Resize image for display
                scale = min(img_size / recolored_image.width, img_size / recolored_image.height)
                new_width = int(recolored_image.width * scale)
                new_height = int(recolored_image.height * scale)
                
                if scale > 1:  # Upscale
                    display_image = recolored_image.resize((new_width, new_height), Image.Resampling.NEAREST)
                else:  # Downscale
                    display_image = recolored_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                photo = ImageTk.PhotoImage(display_image)
                
                img_id = self.canvas.create_image(x, y, anchor="center", image=photo)
                
                filename = os.path.basename(file_path).replace('.png', '')
                text_y = y + img_size // 2 + 20
                self.canvas.create_text(x, text_y, text=filename, anchor="center", font=("Arial", 10, "bold"))
                
                self.preview_images.append(photo)
            
            self.show_loading("Completed!", 100)
            self.root.after(1000, self.hide_loading)
            
            self.info_label.config(
                text=f"Preview: {len(selected_files)} files recolored and displayed"
            )
            
        except Exception as e:
            self.hide_loading()
            messagebox.showerror("Error", f"Error in preview: {str(e)}")
    
    def save_recolored_zip(self):
        if not self.zip_file:
            messagebox.showwarning("Warning", "No ZIP file opened!")
            return
        
        selected_files = [path for path, var in self.file_vars.items() if var.get()]
        
        if not selected_files:
            messagebox.showwarning("Warning", "No files selected for processing!")
            return
        
        save_path = filedialog.asksaveasfilename(
            title="Save New ZIP File",
            defaultextension=".zip",
            filetypes=[("ZIP files", "*.zip"), ("All files", "*.*")]
        )
        
        if not save_path:
            return
        
        try:
            with zipfile.ZipFile(save_path, 'w', zipfile.ZIP_DEFLATED) as new_zip:
                for file_info in self.zip_file.filelist:
                    if file_info.filename in selected_files:
                        image_data = self.zip_file.read(file_info.filename)
                        # Force RGBA mode when loading
                        original_image = Image.open(io.BytesIO(image_data)).convert('RGBA')
                        recolored_image = self.recolor_image(original_image, self.selected_color)
                        
                        img_bytes = io.BytesIO()
                        # Save as RGBA PNG
                        recolored_image.save(img_bytes, format='PNG', optimize=False)
                        new_zip.writestr(file_info.filename, img_bytes.getvalue())
                    else:
                        data = self.zip_file.read(file_info.filename)
                        new_zip.writestr(file_info.filename, data)
            
            messagebox.showinfo(
                "Success", 
                f"Resource Pack saved successfully!\n"
                f"Modified files: {len(selected_files)}\n"
                f"Saved to: {save_path}"
            )
            
        except Exception as e:
            messagebox.showerror("Error", f"Error saving: {str(e)}")
    
    def display_image(self, file_path):
        try:
            if hasattr(self, 'preview_images'):
                self.preview_images = []
            
            image_data = self.zip_file.read(file_path)
            image = Image.open(io.BytesIO(image_data))
            
            max_size = (600, 600)
            image.thumbnail(max_size, Image.Resampling.NEAREST)
            
            photo = ImageTk.PhotoImage(image)
            
            self.canvas.delete("all")
            
            self.canvas_image = self.canvas.create_image(
                self.canvas.winfo_width() // 2,
                self.canvas.winfo_height() // 2,
                anchor="center",
                image=photo
            )
            
            self.canvas.image = photo
            
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            
            original_size = Image.open(io.BytesIO(image_data)).size
            self.info_label.config(
                text=f"Size: {original_size[0]}x{original_size[1]} px | File: {os.path.basename(file_path)}"
            )
            
        except Exception as e:
            messagebox.showerror("Error", f"Error loading image: {str(e)}")
            self.info_label.config(text="Error loading image")
    
    def load_png_files(self):
        if not self.zip_file:
            return
        
        self.png_files = []
        self.file_vars = {}
        
        for widget in self.checkbox_frame.winfo_children():
            widget.destroy()
        
        for file_info in self.zip_file.filelist:
            if file_info.filename.lower().endswith('.png'):
                display_name = os.path.basename(file_info.filename)
                display_name = display_name[:-4] if display_name.endswith('.png') else display_name
                
                if display_name in self.allowed_files:
                    self.png_files.append(file_info.filename)
                    
                    var = tk.BooleanVar(value=True) 
                    self.file_vars[file_info.filename] = var
                    
                    checkbox = ttk.Checkbutton(
                        self.checkbox_frame,
                        text=display_name,
                        variable=var,
                        command=lambda path=file_info.filename: self.on_checkbox_change(path)
                    )
                    checkbox.pack(anchor="w", pady=1)
        
        if not self.png_files:
            messagebox.showinfo("Info", "None of the searched PNG files found in ZIP file.")
        else:
            self.info_label.config(text=f"{len(self.png_files)} of {len(self.allowed_files)} PNG files found")
            self.root.after(100, self.auto_display_images)
    
    def select_all(self):
        for var in self.file_vars.values():
            var.set(True)
        self.auto_display_images()
    
    def select_none(self):
        for var in self.file_vars.values():
            var.set(False)
        self.auto_display_images()
    
    def on_checkbox_change(self, file_path):
        self.auto_display_images()
    
    def choose_color(self):
        color = colorchooser.askcolor(title="Choose Color", color=self.selected_color)
        if color[1]:
            self.selected_color = color[1]
            self.color_display.config(bg=self.selected_color)
            self.color_label.config(text=f"RGB: {self.hex_to_rgb(self.selected_color)}")
    
    def hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def main():
    root = tk.Tk()
    app = MinecraftPackViewer(root)
    root.mainloop()

if __name__ == "__main__":
    main()
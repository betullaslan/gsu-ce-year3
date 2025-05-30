import os
import time
import threading
import struct
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk, ImageOps
import numpy as np

# ===================== UTILITY FUNCTIONS ==================

# Converts a list of binary values (0/1) into bytes (8 bits per byte).
def packbits_py(bitlist):
    out = bytearray()
    n = len(bitlist)
    for i in range(0, n, 8):
        byte = 0
        for j in range(8):
            if i + j < n:
                byte |= (bitlist[i + j] & 1) << (7 - j) 
        out.append(byte)
    return out

# Expands a bytearray into a list of bits (0/1), optionally limited by total_bits.
def unpackbits_py(bytearr, total_bits=None):
    out = []
    for byte in bytearr:
        for i in range(7, -1, -1):
            out.append((byte >> i) & 1)
    if total_bits is not None:
        out = out[:total_bits]
    return out

# Formats a byte count into a human-readable string (KB or MB).
def fmt_size(n_bytes):
    kb = n_bytes / 1024
    if kb < 1024:
        return f"{kb:,.2f} KB"
    else:
        mb = kb / 1024
        return f"{mb:,.2f} MB"


# ===================== MAIN APPLICATION CLASS AND FUNCTIONALITY =====================

class ImageCompressorApp(tk.Tk):
   # Initializes the main application window and sets up the initial GUI layout.
    def __init__(self):
        super().__init__()
        self.title("BetuIMG Studio")
        window_width = 800
        window_height = 600
        self.update_idletasks()  

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2) - 20

        self.geometry(f"{window_width}x{window_height}+{x}+{y}")

        self.light_bg = "#c2e0f7"
        self.dark_bg = "#2e2e2e"
        self.configure(bg=self.light_bg)

        self.image = None
        self.compressed_data = None
        self.decompressed_image = None
        self.compressed_size = 0
        self.edit_applied = False
        self.compressed_saved = False

        self.init_ui()
        self.create_static_buttons()
        
    # Builds the GUI: styles, title, top menu, file buttons, status labels, and progress bar.
    def init_ui(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TButton',font=('Segoe UI', 10, 'bold'), padding=6, background='#003366', foreground='white')
        style.configure('Help.TButton', font=('Segoe UI', 10, 'bold'), padding=6, background='#003366', foreground='white', borderwidth=1)
        style.configure("blue.Horizontal.TProgressbar", troughcolor="#d0d7e2", background="#003366", thickness=1)
        style.configure('Edit.TMenubutton', font=('Segoe UI', 10, 'bold'), padding=6, background='#003366', foreground='white', borderwidth=1)
        style.map('TButton', background=[('active', '#005599')], relief=[('pressed', 'sunken')], foreground=[('active', 'white')])
        style.map('Edit.TMenubutton',background=[('active', '#005599')], foreground=[('active', 'white')], relief=[('pressed', 'sunken')])
        style.map('Help.TButton', background=[('active', '#005599')], foreground=[('active', 'white')])
        
        self.topbar = tk.Frame(self, bg=self.light_bg)
        self.topbar.pack(fill="x", pady=5)

        self.help_button = ttk.Button(self.topbar, text="Help", width=5, style='Help.TButton', command=self.show_help)
        self.help_button.pack(side="right", padx=8)

        self.title_label = tk.Label(self, text="BetuIMG Studio", font=("Segoe UI", 18, "bold"), bg=self.light_bg, fg="#003366")
        self.title_label.pack(pady=5)

        self.file_label = tk.Label(self, text="No file selected", font=("Segoe UI", 10, "bold", 'italic'), bg=self.light_bg, fg="#B22222")
        self.file_label.pack(pady=6)

        self.top_frame = tk.Frame(self, bg=self.light_bg)
        self.top_frame.pack(pady=10)

        ttk.Button(self.top_frame, text="Load Image", command=self.select_image).pack(side="left", padx=6)
        edit_button = ttk.Menubutton(self.top_frame, text="Edit Image", style="Edit.TMenubutton")
        edit_menu = tk.Menu(edit_button, tearoff=0)
        edit_menu.add_command(label="Convert to Grayscale", command=self.convert_image_to_grayscale)
        edit_menu.add_command(label="Invert Colors", command=self.invert_image)
        edit_menu.add_command(label="Apply Sepia Effect", command=self.apply_sepia)
        edit_button["menu"] = edit_menu
        edit_button.pack(side="left", padx=6)
        ttk.Button(self.top_frame, text="Compress (Lossless)", command=self.compress_image_lossless).pack(side="left", padx=6)
        ttk.Button(self.top_frame, text="Compress (Lossy)", command=self.compress_image_lossy).pack(side="left", padx=6)
        ttk.Button(self.top_frame, text="Save as .myimg", command=self.save_file).pack(side="left", padx=6)

        self.bottom_frame = tk.Frame(self, bg=self.light_bg)
        self.bottom_frame.pack(pady=2)

        ttk.Button(self.bottom_frame, text="Load .myimg", command=self.load_file, width=17).pack(side="left", padx=10)
        ttk.Button(self.bottom_frame, text="Decompress", command=self.decompress_image, width=17).pack(side="left", padx=10)
        ttk.Button(self.bottom_frame, text="Save as PNG", command=self.save_decompressed_image, width=17).pack(side="left", padx=10)

        self.status = tk.Label(self, text="", font=("Segoe UI", 10, 'italic', "bold"), bg=self.light_bg, fg="#333")
        self.status.pack(pady=(10, 0))

        self.metrics = tk.Label(self, text="", font=("Segoe UI", 10), bg=self.light_bg, fg="#444", justify="left", anchor="w")
        self.metrics.pack(pady=0)

        self.preview = tk.Label(self, bg=self.light_bg, relief="flat", borderwidth=0, highlightthickness=0)
        self.preview.pack(pady=0)

        self.progress_label = tk.Label(self, text="", font=("Segoe UI", 9), bg=self.light_bg, fg="#003366")
        self.progress = ttk.Progressbar(self, orient="horizontal", length=360, mode="determinate", style="blue.Horizontal.TProgressbar")

    # Creates persistent elements: theme toggle (light/dark) and Reset/Exit buttons.
    def create_static_buttons(self):
        self.toggle_frame = tk.Frame(self, bd=2, relief="ridge", bg="#d0d7e2")
        self.toggle_frame.place(x=10, y=10)
        self.light_btn = tk.Label(self.toggle_frame, text=" Light ", bg="#ffffff", fg="#003366", font=('Segoe UI', 10, 'bold'))
        self.light_btn.grid(row=0, column=0)
        self.dark_btn = tk.Label(self.toggle_frame, text=" Dark ", bg="#d0d7e2", fg="#003366", font=('Segoe UI', 10))
        self.dark_btn.grid(row=0, column=1)
        self.light_btn.bind("<Button-1>", self.set_light_mode)
        self.dark_btn.bind("<Button-1>", self.set_dark_mode)
        self.bottom_static = tk.Frame(self, bg=self.light_bg)
        self.bottom_static.pack(side=tk.BOTTOM, pady=8)
        ttk.Button(self.bottom_static, text="Reset", command=self.confirm_reset).pack(side=tk.LEFT, padx=20)
        ttk.Button(self.bottom_static, text="Exit", command=self.confirm_exit).pack(side=tk.LEFT, padx=20)


    # ===================== FILE SELECTION AND SAVE OPERATIONS =====================

    # Opens a file dialog for the user to select a new image file.
    # Resets previous states and displays the selected image in the preview area.
    def select_image(self):
        filetypes = [('Image Files', '*.png *.jpg *.jpeg *.bmp *.webp *.gif *.tif *.tiff *.ico *.jp2 *.pbm *.pgm *.ppm')]
        path = filedialog.askopenfilename(filetypes=filetypes)
        if not path:
            return
        self.image = Image.open(path)
        self.image_path = path
        self.compressed_data = None
        self.decompressed_image = None
        self.file_label.config(text=f"{os.path.basename(path)} (Original Image)")
        self.status.config(text=f"Image loaded: {os.path.basename(path)}")
        self.metrics.config(text="")
        self.update_preview(self.image)
        self.edit_applied = False
        self.compressed_saved = False

    # Loads a previously saved .myimg compressed file.
    # Resets current image/decompressed states and updates file status.
    def load_file(self):
        path = filedialog.askopenfilename(filetypes=[('My Image Format', '*.myimg')])
        if path:
            self.metrics.config(text="") 
            with open(path, "rb") as f:
                self.compressed_data = f.read()
            self.compressed_size = len(self.compressed_data)
            self.image = None
            self.decompressed_image = None
            self.file_label.config(text=f"{os.path.basename(path)} (Compressed Image)")
            self.preview.config(image="")
            self.preview.image = None
            self.status.config(text=f"Compressed file loaded: {os.path.basename(path)}")
            self.last_myimg_filename = os.path.basename(path)
            self.edit_applied = False
            self.compressed_saved = False
            self.image_path = None 
    
    # Saves the current compressed data to a file with the .myimg extension.
    # Warns the user if no compression has been performed yet.
    def save_file(self):
        if self.compressed_data and self.image is not None and self.decompressed_image is None:
            self.metrics.config(text="") 
            path = filedialog.asksaveasfilename(defaultextension=".myimg")
            if path:
                with open(path, "wb") as f:
                    f.write(self.compressed_data)
                self.compressed_size = os.path.getsize(path)
                self.status.config(text=f"Compressed file saved: {os.path.basename(path)}")
                self.preview.config(image="")
                self.preview.image = None
                self.file_label.config(text="")
                self.metrics.config(text="")
                self.edit_applied = False
                self.compressed_saved = True
        else:
            messagebox.showwarning("No Compressed Data", "There is no compressed image to save.\nPlease compress an image first.")

    # Saves the decompressed image as a standard PNG file.
    # Warns the user if decompression hasn't been performed yet.
    def save_decompressed_image(self):
        if self.decompressed_image:
            self.metrics.config(text="") 
            path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
            if path:
                self.decompressed_image.save(path)
                self.status.config(text=f"Image saved as PNG: {os.path.basename(path)}")
                self.preview.config(image="")
                self.preview.image = None
                self.file_label.config(text="")
                self.edit_applied = False
        else:
            messagebox.showwarning("No Decompressed Image", "There is no decompressed image to save.\nPlease decompress an image first.")
    

    # ===================== IMAGE PREVIEW AND PROGRESS HANDLING =====================

    # Displays a thumbnail preview of the given image in the GUI.
    def update_preview(self, img):
        preview_size = (330, 330)
        if img.mode != "RGB":
            img_copy = img.convert("RGB")
        else:
            img_copy = img.copy()
        img_copy.thumbnail(preview_size)
        img_tk = ImageTk.PhotoImage(img_copy)
        self.preview.configure(image=img_tk)
        self.preview.image = img_tk

    # Prepares and displays the progress bar and percentage label before a time-consuming task.
    def show_progress(self):
        if not self.progress_label.winfo_ismapped():
            self.progress_label.pack(before=self.preview, pady=(0, 0))
        if not self.progress.winfo_ismapped():
            self.progress.pack(before=self.preview, pady=(0, 10))
        self.progress_label.config(text="0%")
        self.progress["value"] = 0

    # Hides the progress bar and percentage label after the task is finished.
    def hide_progress(self):
        self.progress_label.pack_forget()
        self.progress.pack_forget()

    # Gradually updates the progress bar by calling update_progress() until completion, then executes callback.
    def simulate_progress(self, callback):
        self.show_progress()
        self.progress["value"] = 0
        self.update_progress(callback, step=4)

    # Increments the progress bar gradually by the given step size, recursively updates until complete.
    def update_progress(self, callback, step):
        if self.progress["value"] < 100:
            self.progress["value"] += step
            percent = int(self.progress["value"])
            self.progress_label.config(text=f"{percent}%")
            self.progress.update_idletasks()
            self.after(12, lambda: self.update_progress(callback, step))
        else:
            self.progress["value"] = 100
            self.progress_label.config(text="100%")
            self.after(200, self.hide_progress)
            callback()

    # Safely updates progress bar and label from background threads.
    def update_progressbar_safe(self, value):
        self.after(0, lambda: (self.progress.config(value=value), self.progress_label.config(text=f"{value}%")))


    # ===================== LOSSLESS COMPRESSION & DECOMPRESSION =====================

    # Starts the lossless compression process in a background thread using LZW.
    def compress_image_lossless(self):
        if self.image and self.compressed_data is None and self.decompressed_image is None:
            self.status.config(text="Compressing (Lossless)...")
            self.show_progress()
            self.compressed_saved = False 
            threading.Thread(target=self.compress_image_lossless_thread, daemon=True).start()
        elif self.image is None:
            messagebox.showwarning("No Image", "Please load an image before attempting compression.")
        elif self.compressed_data is not None:
            if getattr(self, "compressed_saved", False):
                messagebox.showinfo(
                    "Already Compressed and Saved", "This image has already been compressed and saved.\n"
                    "To compress a new image, please load a new file.")
            else:
                messagebox.showinfo("Already Compressed","This image has already been compressed.\n"
                    "To compress another image, please load a new file.")
        elif self.decompressed_image is not None:
            messagebox.showinfo("Invalid Operation", "You cannot compress an already decompressed image.\nPlease load a new original image.")
        else:
            messagebox.showwarning("No Image", "Please load an image before attempting compression.")

    # Applies LZW-based lossless compression to the image and stores the result.
    def compress_image_lossless_thread(self):
        try:
            pal_img = self.image.convert("P", palette=Image.Palette.ADAPTIVE, colors=256)
            arr = np.array(pal_img)
            pixel_bytes = arr.tobytes()
            total_steps = len(pixel_bytes)
            dict_size = 256
            max_dict_size = 4096
            dictionary = {bytes([i]): i for i in range(dict_size)}
            w = b""
            output = []
            step_counter = 0

            for c in pixel_bytes:
                wc = w + bytes([c])
                if wc in dictionary:
                    w = wc
                else:
                    output.append(dictionary[w])
                    if dict_size < max_dict_size:
                        dictionary[wc] = dict_size
                        dict_size += 1
                    w = bytes([c])
                step_counter += 1
                if step_counter % 5000 == 0 or step_counter == total_steps:
                    progress = int((step_counter / total_steps) * 100)
                    self.update_progressbar_safe(progress)
            if w:
                output.append(dictionary[w])

            out_bytes = bytearray()
            for code in output:
                out_bytes += code.to_bytes(2, 'big')
            palette_bytes = bytes(pal_img.getpalette()[:256*3])
            palette_bytes = palette_bytes + bytes(768 - len(palette_bytes))
            w_img, h_img = arr.shape[1], arr.shape[0]
            header = struct.pack(">BHH", 0, w_img, h_img)
            self.compressed_data = header + palette_bytes + out_bytes

            self.after(0, self.on_compress_lossless_done)
        except Exception as e:
            self.after(0, lambda: self.status.config(text=f"Compression failed: {e}"))
    
    # Finalizes lossless compression: updates UI and shows statistics.
    def on_compress_lossless_done(self):
        self.compressed_size = len(self.compressed_data)
        self.status.config(text="Image compressed (lossless)")
        self.progress["value"] = 100
        self.progress_label.config(text="100%")
        self.hide_progress()
        self.preview.config(image="")
        self.preview.image = None
        self.file_label.config(text="")
        self.show_compression_stats()

    # Runs lossless decompression and updates the interface upon completion.
    def decompress_lossless_thread(self):
        try:
            img = self.decompress_lossless_progress(self.compressed_data)
            self.decompressed_image = img
            self.after(0, self.on_decompress_done)
        except Exception as e:
            self.after(0, lambda: self.status.config(text=f"Decompression failed: {e}"))

    # Reconstructs the original image from LZW-compressed data and palette information.
    def decompress_lossless_progress(self, data):
        if len(data) < 5+768:
            raise ValueError("Invalid compressed file format")
        header, content = data[:5], data[5:]
        mode, w, h = struct.unpack(">BHH", header)
        palette = list(content[:768])
        compressed = content[768:]
        dict_size = 256
        dictionary = {i: bytes([i]) for i in range(dict_size)}
        codes = [int.from_bytes(compressed[i:i+2], 'big') for i in range(0, len(compressed), 2)]
        result = bytearray()
        w_seq = dictionary[codes[0]]
        result += w_seq
        steps = len(codes)
        for idx, k in enumerate(codes[1:], start=1):
            if k in dictionary:
                entry = dictionary[k]
            elif k == dict_size:
                entry = w_seq + w_seq[:1]
            else:
                raise ValueError("Invalid LZW code: %d" % k)
            result += entry
            dictionary[dict_size] = w_seq + entry[:1]
            dict_size += 1
            w_seq = entry
            if idx % 5000 == 0 or idx == steps - 1:
                self.update_progressbar_safe(int((idx / steps) * 100))
                time.sleep(0.001)
        arr = np.frombuffer(result, dtype='uint8').reshape((h, w))
        pal_img = Image.fromarray(arr, mode='P')
        pal_img.putpalette(palette)
        return pal_img.convert('RGB')


    # ===================== LOSSY COMPRESSION & DECOMPRESSION =====================

    # Starts the lossy compression process using block-wise color approximation.
    def compress_image_lossy(self):
        if self.image and self.compressed_data is None and self.decompressed_image is None:
            self.status.config(text="Compressing (Lossy)...")
            self.show_progress()
            threading.Thread(target=self.compress_image_lossy_thread, daemon=True).start()
            self.compressed_saved = False
        elif self.image is None:
            messagebox.showwarning("No Image", "Please load an image before attempting compression.")
        elif self.compressed_data is not None:
            if getattr(self, "compressed_saved", False):
                messagebox.showinfo(
                    "Already Compressed and Saved", "This image has already been compressed and saved.\n"
                    "To compress a new image, please load a new file.")
            else:
                messagebox.showinfo(
                    "Already Compressed", "This image has already been compressed.\n"
                    "To compress another image, please load a new file.")
        elif self.decompressed_image is not None:
            messagebox.showinfo("Invalid Operation","You cannot compress an already decompressed image.\nPlease load a new original image.")
        else:
            messagebox.showwarning("No Image","Please load an image before attempting compression.")

    # Performs lossy image compression using block-wise average color masking and bit packing.
    def compress_image_lossy_thread(self):
        try:
            arr = np.array(self.image.convert("RGB"))
            h, w, _ = arr.shape
            block_size = 16
            blocks_y = (h + block_size - 1) // block_size
            blocks_x = (w + block_size - 1) // block_size
            blocks = []

            total_blocks = blocks_y * blocks_x
            block_index = 0

            for by in range(blocks_y):
                for bx in range(blocks_x):
                    y0, y1 = by * block_size, min((by + 1) * block_size, h)
                    x0, x1 = bx * block_size, min((bx + 1) * block_size, w)
                    block = arr[y0:y1, x0:x1].reshape(-1, 3)

                    gray = (0.2989 * block[:, 0] + 0.587 * block[:, 1] + 0.114 * block[:, 2])
                    mean = gray.mean()
                    mask = (gray >= mean).astype(np.uint8)

                    los, his = [], []
                    for ch in range(3):
                        ch_vals = block[:, ch]
                        hi = ch_vals[mask == 1].mean() if np.any(mask == 1) else ch_vals.mean()
                        lo = ch_vals[mask == 0].mean() if np.any(mask == 0) else ch_vals.mean()
                        los.append(int(lo))
                        his.append(int(hi))

                    mask_bytes = packbits_py(mask)
                    blocks.append(struct.pack(">BBBBBB", *los, *his) + mask_bytes)

                    block_index += 1
                    if block_index % 100 == 0 or block_index == total_blocks:
                        progress = int((block_index / total_blocks) * 100)
                        self.update_progressbar_safe(progress)
                        time.sleep(0.001)

            header = struct.pack(">BHHB", 4, w, h, block_size)
            self.compressed_data = header + b''.join(blocks)

            self.after(0, self.on_compress_lossy_done)
        except Exception as e:
            self.after(0, lambda: self.status.config(text=f"Compression failed: {e}"))

    # Finalizes lossy compression: updates UI and displays stats.
    def on_compress_lossy_done(self):
        self.compressed_size = len(self.compressed_data)
        self.status.config(text="Image compressed (lossy)")
        self.progress["value"] = 100
        self.progress_label.config(text="100%")
        self.hide_progress()
        self.preview.config(image="")
        self.preview.image = None
        self.file_label.config(text="")
        self.show_compression_stats()

    # Runs lossy decompression in a background thread and updates the result on completion.
    def decompress_lossy_thread(self):
        try:
            img = self.decompress_lossy_progress(self.compressed_data)
            self.decompressed_image = img
            self.after(0, self.on_decompress_done)
        except Exception as e:
            self.after(0, lambda: self.status.config(text=f"Decompression failed: {e}"))

    # Reconstructs the image from lossy compressed data using block-wise decoding.
    def decompress_lossy_progress(self, data):
        mode, w, h, block_size = struct.unpack(">BHHB", data[:6])
        arr = np.zeros((h, w, 3), dtype=np.uint8)
        blocks_y = (h + block_size - 1) // block_size
        blocks_x = (w + block_size - 1) // block_size
        idx = 6
        total_blocks = blocks_y * blocks_x
        block_index = 0

        for by in range(blocks_y):
            for bx in range(blocks_x):
                y0, y1 = by * block_size, min((by + 1) * block_size, h)
                x0, x1 = bx * block_size, min((bx + 1) * block_size, w)
                block_pixels = (y1 - y0) * (x1 - x0)

                los = list(data[idx:idx + 3])
                his = list(data[idx + 3:idx + 6])

                mask_bytes_len = (block_pixels + 7) // 8
                mask_bytes = data[idx + 6:idx + 6 + mask_bytes_len]
                mask = unpackbits_py(mask_bytes, block_pixels)

                block = np.zeros((block_pixels, 3), dtype=np.uint8)
                for ch in range(3):
                    block[:, ch] = np.where(np.array(mask) == 1, his[ch], los[ch])

                arr[y0:y1, x0:x1] = block.reshape((y1 - y0, x1 - x0, 3))
                idx += 6 + mask_bytes_len

                block_index += 1
                if block_index % 100 == 0 or block_index == total_blocks:
                    progress = int((block_index / total_blocks) * 100)
                    self.update_progressbar_safe(progress)
                    time.sleep(0.001)

        return Image.fromarray(arr, "RGB")


    # ===================== DECOMPRESSION ENTRY AND UI UPDATE =====================

    # Starts the appropriate decompression process (lossless or lossy) in a background thread.
    def decompress_image(self):
        if self.compressed_data and self.image is None and self.decompressed_image is None:
            self.metrics.config(text="") 
            mode = self.compressed_data[0]
            self.status.config(text="Decompressing...")
            self.show_progress()
            if mode == 0:
                threading.Thread(target=self.decompress_lossless_thread, daemon=True).start()
            else:
                threading.Thread(target=self.decompress_lossy_thread, daemon=True).start()
        elif self.decompressed_image is not None:
            messagebox.showinfo("Already Decompressed", "This file has already been decompressed.\nPlease load a new .myimg file if needed.")
        elif self.image:
            messagebox.showinfo("Wrong File Type", "This is not a .myimg compressed file.\nPlease load a .myimg file before attempting decompression.")
        else:
            messagebox.showwarning("No Compressed Data", "No compressed image available to decompress.\nPlease load a .myimg file first.")

    # Finalizes decompression by updating the preview, status, and UI labels.
    def on_decompress_done(self):
        self.status.config(text="Image decompressed")
        self.progress["value"] = 100
        self.progress_label.config(text="100%")
        self.hide_progress()
        self.update_preview(self.decompressed_image)
        if hasattr(self, 'last_myimg_filename'):
            self.file_label.config(text=f"{self.last_myimg_filename} (Decompressed Image)")
        else:
            self.file_label.config(text="(Decompressed Image)")


    # ===================== IMAGE EDITING FUNCTIONS =====================

    # Converts the loaded image to grayscale.
    def convert_image_to_grayscale(self):
        self.metrics.config(text="") 
        if self.edit_applied:
            messagebox.showwarning("Edit Blocked", "You have already applied an effect.\nPlease reset or reload the image to apply another.")
            return
        if self.image and self.compressed_data is None:
            self.image = self.image.convert("L").convert("RGB")
            self.update_preview(self.image)
            self.status.config(text="Grayscale effect applied.")
            self.edit_applied = True
        elif self.compressed_data:
            messagebox.showwarning("Compressed File Loaded", "Cannot apply effects to a compressed image.\nPlease load a regular image file.")
        else:
            messagebox.showwarning("No Image Loaded", "Please load an image before applying effects.")

    # Inverts the colors of the loaded image (RGB → inverse RGB).
    def invert_image(self):
        self.metrics.config(text="") 
        if self.edit_applied:
            messagebox.showwarning("Edit Blocked", "An effect has already been applied.\nPlease reset or reload the image to apply another.")
            return
        if self.image and self.compressed_data is None:
            self.image = ImageOps.invert(self.image.convert("RGB"))
            self.update_preview(self.image)
            self.status.config(text="Invert effect applied.")
            self.edit_applied = True
        elif self.compressed_data:
            messagebox.showwarning("Compressed File Loaded", "Cannot apply effects to a compressed image.\nPlease load a regular image file.")
        else:
            messagebox.showwarning("No Image Loaded", "Please load an image before applying effects.")

    # Applies a sepia tone effect to the loaded image for a warm, vintage look.
    def apply_sepia(self):
        self.metrics.config(text="") 
        if self.edit_applied:
            messagebox.showwarning("Edit Blocked", "An effect has already been applied.\nPlease reset or reload the image to apply another.")
            return
        if self.image and self.compressed_data is None:
            img = self.image.convert("RGB")
            arr = np.array(img)

            tr = (arr[:, :, 0] * 0.393 + arr[:, :, 1] * 0.769 + arr[:, :, 2] * 0.189)
            tg = (arr[:, :, 0] * 0.349 + arr[:, :, 1] * 0.686 + arr[:, :, 2] * 0.168)
            tb = (arr[:, :, 0] * 0.272 + arr[:, :, 1] * 0.534 + arr[:, :, 2] * 0.131)

            arr[:, :, 0] = np.clip(tr, 0, 255)
            arr[:, :, 1] = np.clip(tg, 0, 255)
            arr[:, :, 2] = np.clip(tb, 0, 255)

            self.image = Image.fromarray(arr.astype(np.uint8))
            self.update_preview(self.image)
            self.status.config(text="Sepia effect applied.")
            self.edit_applied = True
        elif self.compressed_data:
            messagebox.showwarning("Compressed File Loaded", "Cannot apply effects to a compressed image.\nPlease load a regular image file.")
        else:
            messagebox.showwarning("No Image Loaded", "Please load an image before applying effects.")

    
    # ===================== THEME SWITCHING =====================

    # Switches the application UI to light theme colors.
    def set_light_mode(self, event=None):
        self.configure(bg=self.light_bg)
        self.topbar.configure(bg=self.light_bg)
        self.title_label.configure(bg=self.light_bg, fg="#003366")
        self.file_label.configure(bg=self.light_bg)
        self.top_frame.configure(bg=self.light_bg)
        self.bottom_frame.configure(bg=self.light_bg)
        self.status.configure(bg=self.light_bg, fg="#333")
        self.metrics.configure(bg=self.light_bg, fg="#444")
        self.preview.configure(bg=self.light_bg)
        self.progress_label.configure(bg=self.light_bg, fg="#003366")
        self.bottom_static.configure(bg=self.light_bg)
        self.toggle_frame.configure(bg="#d0d7e2")
        self.light_btn.configure(bg="#ffffff", fg="#003366", font=('Segoe UI', 10, 'bold'))
        self.dark_btn.configure(bg="#d0d7e2", fg="#003366", font=('Segoe UI', 10))

    def set_dark_mode(self, event=None):
        self.configure(bg=self.dark_bg)
        self.topbar.configure(bg=self.dark_bg)
        self.title_label.configure(bg=self.dark_bg, fg="#eaf6ff")
        self.file_label.configure(bg=self.dark_bg, fg="#ff5555") 
        self.top_frame.configure(bg=self.dark_bg)
        self.bottom_frame.configure(bg=self.dark_bg)
        self.status.configure(bg=self.dark_bg, fg="white")
        self.metrics.configure(bg=self.dark_bg, fg="white")
        self.preview.configure(bg=self.dark_bg)
        self.progress_label.configure(bg=self.dark_bg, fg="#ddd")
        self.bottom_static.configure(bg=self.dark_bg)
        self.toggle_frame.configure(bg="#263243")
        self.light_btn.configure(bg="#444", fg="#ccc", font=('Segoe UI', 10))
        self.dark_btn.configure(bg="#ffffff", fg="#003366", font=('Segoe UI', 10, 'bold'))

    
    # ===================== HELP AND INFO =====================

    # Displays instructions for using the image compression application.
    def show_help(self):
        messagebox.showinfo("Help",
        "How to Use:\n\n"
        "▪ Load Image: Select an image file to compress.\n"
        "▪ Edit Image: Apply effects like Grayscale, Invert, or Sepia to an original image.\n"
        "▪ Compress (Lossless): Apply LZW'84-based compression.\n"
        "▪ Compress (Lossy): Apply block-wise color approximation.\n"
        "▪ Save as .myimg: Save compressed data to a .myimg file.\n"
        "▪ Load .myimg: Load a previously saved .myimg file.\n"
        "▪ Decompress: Reconstruct the original image from .myimg.\n"
        "▪ Save as PNG: Export the decompressed image.\n"
        "▪ Reset: Clear loaded and compressed data.\n"
        "▪ Theme Toggle: Switch between light and dark themes.\n"
        "▪ Exit: Close the application."
        )

    # ===================== APPLICATION STATE MANAGEMENT =====================
    
    # Prompts the user before exiting to prevent accidental data loss.
    def confirm_exit(self):
        if messagebox.askokcancel("Exit", "Are you sure you want to exit?\nAny unsaved data will be lost."):
            self.destroy()

    # Prompts the user before resetting to prevent accidental data loss.
    def confirm_reset(self):
        if messagebox.askokcancel("Reset", "Are you sure you want to reset?\nAny unsaved data will be lost."):
            self.reset()
    
    # Clears all loaded data and resets the interface to its initial state.
    def reset(self):
        self.image = None
        self.compressed_data = None
        self.decompressed_image = None
        self.image_path = None
        self.compressed_size = 0
        self.preview.config(image="")
        self.preview.image = None
        self.status.config(text="Reset completed.")
        self.metrics.config(text="")
        self.file_label.config(text="No file selected")
        self.edit_applied = False
        self.compressed_saved = False
        self.progress["value"] = 0
        self.progress_label.config(text="")

    # ===================== COMPRESSION STATISTICS DISPLAY =====================
    
    # Displays compression stats: file size, raw RGB size, and reduction rates.
    def show_compression_stats(self):
        if self.image and self.compressed_data:
            w, h = self.image.size
            raw_size = w * h * 3
            compressed_size = self.compressed_size

            if self.image_path and os.path.exists(self.image_path):
                original_file_size = os.path.getsize(self.image_path)
                ratio_file = (1 - (compressed_size / original_file_size)) * 100
                line1 = (
                     "[Original File Comparison]\n"
                    f"{'Original File Size':<24}: {fmt_size(original_file_size):>10}\n"
                    f"{'Compressed Size':<20}: {fmt_size(compressed_size):>10}\n"
                    f"{'Size Reduction':<23}: {ratio_file:>9.2f}%"
                                )
            else:
                line1 = ""

            ratio_raw = (1 - (compressed_size / raw_size)) * 100
            line2 = (
                 "[Raw RGB Data Comparison]\n"
                f"{'Raw RGB Size':<24}: {fmt_size(raw_size):>10}\n"
                f"{'Compressed Size':<21}: {fmt_size(compressed_size):>10}\n"
                f"{'Size Reduction':<24}: {ratio_raw:>9.2f}%"
            )

            stats = f"{line1}\n\n{line2}" if line1 else line2
            self.metrics.config(text=stats)

    
# ================== ENTRY POINT ==================

if __name__ == "__main__":
    app = ImageCompressorApp()
    app.mainloop()

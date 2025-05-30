# Image Compression Tool

This project presents a desktop application developed in Python for compressing and decompressing digital images using both **lossless** and **lossy** algorithms. The tool provides an educational platform to observe how different compression strategies influence file size, image fidelity, and performance.

The application features an intuitive GUI built with Tkinter, allowing users to load an image, apply visual effects, compress it with their choice of algorithm, and export or inspect the result. Compressed data is saved in a custom binary format with the `.myimg` extension, designed specifically for this project.

The tool supports two compression methods:

- **Lossless Compression (LZW'84)**:  
  Implements a 12-bit version of the Lempel-Ziv-Welch (LZW) algorithm. The image is first quantized to an 8-bit palette before compression. This mode preserves all image data and is reversible with no quality loss.

- **Lossy Compression (Block-based)**:  
  Images are divided into fixed-size blocks (16×16 pixels). For each block, grayscale brightness is used to split pixels into two groups, and each group is encoded with a representative RGB color. A bitmask is used to distinguish group membership. This reduces the amount of color information stored at the cost of some visual detail.

The application is ideal for coursework, demonstrations, and lightweight image optimization tasks.

## Project Info

- **Project Name:** Image Compression Tool
- **Language:** Python 
- **Author:** Betul Aslan

---

## Academic Info

- **Course:** Information Theory  
- **Institution:** Galatasaray University  
- **Department:** Computer Engineering  
- **Academic Year:** 2024–2025 Spring  
- **Assignment:** Term Project  

---

## Features

- **Graphical Interface** built with Tkinter
- **Load image files** of multiple formats: PNG, JPG, BMP, etc.
- **Basic image editing**: Grayscale, Invert, Sepia
- **Compression Modes:**
  - **Lossless**: Uses LZW (Lempel-Ziv-Welch, 12-bit) compression on 8-bit palettized images.
  - **Lossy**: Uses block-wise (16×16) compression with binary masks and dual-tone color encoding.
- **Save and load `.myimg` format**: Custom binary format for compressed images.
- **Decompression**: Reconstruct the original or approximated image for visual comparison.
- **Export as PNG** after decompression
- **Compression metrics**: Shows reduction percentage compared to raw RGB and original file
- **Light/Dark theme toggle** for user preference
- **Threaded operations**: All compression and decompression tasks run in the background without freezing the UI.
- **Progress bar with percentage updates** for long operations

---

## Technologies Used

- **Python 3**
- **Tkinter** (GUI)
- **Pillow (PIL)** – for image I/O and processing
- **NumPy** – for matrix and block operations
- **Struct** – for binary file packing/unpacking

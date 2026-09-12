"""Interactive Forensic Bit-Plane Slicer."""

import numpy as np
import customtkinter as ctk
from PIL import Image

class BitPlaneSlicerWindow(ctk.CTkToplevel):
    def __init__(self, master, image_path):
        super().__init__(master)
        
        filename = image_path.split('/')[-1] if '/' in image_path else image_path.split('\\')[-1]
        self.title(f"Forensic Bit-Plane Inspector: {filename}")
        self.geometry("920x650")
        self.minsize(800, 500)
        self.configure(fg_color="#161618")
        
        # Ensures this window stays on top and grabs focus
        self.grab_set()

        # Load and process image into a NumPy array
        self.img = Image.open(image_path).convert("RGB")
        self.img_arr = np.array(self.img)
        self.display_size = (650, 550)

        # UI State variables
        self.current_channel = ctk.StringVar(value="Red")
        self.current_bit = ctk.IntVar(value=0)  # Default to Bit 0 (LSB)

        self._build_ui()
        self._update_preview()

    def _build_ui(self):
        # Left Panel: Controls
        ctrl_frame = ctk.CTkFrame(self, width=220, fg_color="#212124", corner_radius=10, border_width=1, border_color="#2d2d30")
        ctrl_frame.pack(side="left", fill="y", padx=16, pady=16)
        ctrl_frame.pack_propagate(False)

        # Right Panel: Preview Area
        preview_frame = ctk.CTkFrame(self, fg_color="#19191b", corner_radius=10, border_width=1, border_color="#2d2d30")
        preview_frame.pack(side="right", fill="both", expand=True, padx=(0, 16), pady=16)

        # --- Channel Selector ---
        ctk.CTkLabel(ctrl_frame, text="Color Channel", font=ctk.CTkFont(size=14, weight="bold"), text_color="#f5f5f7").pack(anchor="w", padx=16, pady=(20, 10))
        
        self.seg_channel = ctk.CTkSegmentedButton(
            ctrl_frame, 
            values=["Red", "Green", "Blue"],
            variable=self.current_channel,
            command=self._on_change,
            selected_color="#0a84ff",
            selected_hover_color="#0071e3"
        )
        self.seg_channel.pack(fill="x", padx=16)

        # --- Bit Plane Selector ---
        ctk.CTkLabel(ctrl_frame, text="Bit Plane Layer", font=ctk.CTkFont(size=14, weight="bold"), text_color="#f5f5f7").pack(anchor="w", padx=16, pady=(30, 10))
        
        for b in range(7, -1, -1):
            if b == 7:
                label_text = f"Bit 7 (MSB - Visual)"
            elif b == 0:
                label_text = f"Bit 0 (LSB - Stego)"
            else:
                label_text = f"Bit {b}"
                
            rb = ctk.CTkRadioButton(
                ctrl_frame, 
                text=label_text,
                variable=self.current_bit,
                value=b,
                command=self._on_change,
                fg_color="#0a84ff",
                text_color="#86868b",
                font=ctk.CTkFont(size=13)
            )
            rb.pack(anchor="w", padx=20, pady=7)

        # --- Educational Context ---
        info_text = (
            "Bit 7 holds the main structural image data.\n\n"
            "Bit 0 is normally pure static noise. If a sequential steganography tool is used, obvious blocks of solid data appear here."
        )
        ctk.CTkLabel(ctrl_frame, text=info_text, text_color="#86868b", font=ctk.CTkFont(size=11), wraplength=180, justify="left").pack(side="bottom", padx=16, pady=20)

        # --- Image Output ---
        self.lbl_preview = ctk.CTkLabel(preview_frame, text="")
        self.lbl_preview.pack(fill="both", expand=True, padx=10, pady=10)

    def _on_change(self, *args):
        self._update_preview()

    def _update_preview(self):
        # Map channel text to array index
        ch_idx = {"Red": 0, "Green": 1, "Blue": 2}[self.current_channel.get()]
        bit = self.current_bit.get()

        # 1. Isolate the specific channel matrix (H x W)
        channel_data = self.img_arr[:, :, ch_idx]
        
        # 2. Bitwise right-shift to drop lower bits, then AND with 1 to isolate the target bit.
        # Multiply by 255 to map 0 to pure black and 1 to pure white.
        bit_plane = ((channel_data >> bit) & 1) * 255
        bit_plane = bit_plane.astype(np.uint8)

        # 3. Convert back to PIL Image (Mode 'L' for Grayscale)
        out_img = Image.fromarray(bit_plane, mode="L")
        
        # NEAREST resampling is critical here to prevent blurring the exact pixel bits
        out_img.thumbnail(self.display_size, Image.Resampling.NEAREST)
        
        ctk_img = ctk.CTkImage(light_image=out_img, dark_image=out_img, size=out_img.size)
        self.lbl_preview.configure(image=ctk_img)
        
        # Keep a reference to prevent Python's garbage collector from destroying the image
        self.lbl_preview.image = ctk_img
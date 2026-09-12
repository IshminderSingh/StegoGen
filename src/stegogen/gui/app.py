"""Desktop Graphical User Interface for StegoGen using Tkinter."""

from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk

from stegogen.core.encoder import encode_text, encode_file
from stegogen.core.decoder import decode_text, decode_file, extract_payload_from_array
from stegogen.core.capacity import assess_capacity
from stegogen.utils.image_utils import load_image_as_rgb


class StegoGenApp(tk.Tk):
    """Main application window for StegoGen."""

    def __init__(self) -> None:
        super().__init__()
        self.title("StegoGen -- Secure Image Steganography Generator")
        self.geometry("780x680")
        self.minsize(700, 600)

        # Style configuration
        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        # Tabbed Layout
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=12)

        self.encode_frame = ttk.Frame(self.notebook, padding=12)
        self.decode_frame = ttk.Frame(self.notebook, padding=12)

        self.notebook.add(self.encode_frame, text="   Encode (Hide Data)   ")
        self.notebook.add(self.decode_frame, text="   Decode (Extract Data)   ")

        self._build_encode_tab()
        self._build_decode_tab()

    # -------------------------------------------------------------
    # ENCODE TAB
    # -------------------------------------------------------------
    def _build_encode_tab(self) -> None:
        # Cover image row
        img_box = ttk.LabelFrame(self.encode_frame, text=" 1. Select Cover Image ", padding=8)
        img_box.pack(fill="x", pady=4)

        self.cover_path_var = tk.StringVar()
        ttk.Entry(img_box, textvariable=self.cover_path_var, width=55).pack(side="left", padx=4, fill="x", expand=True)
        ttk.Button(img_box, text="Browse Image", command=self._browse_cover_image).pack(side="left", padx=4)

        # Preview & Capacity summary
        preview_box = ttk.Frame(self.encode_frame)
        preview_box.pack(fill="x", pady=6)

        self.preview_label = ttk.Label(preview_box, text="[No Image Loaded]", anchor="center", relief="solid")
        self.preview_label.config(width=24)
        self.preview_label.pack(side="left", padx=6, pady=4)

        self.capacity_text_var = tk.StringVar(value="Select an image to see capacity metrics.")
        ttk.Label(preview_box, textvariable=self.capacity_text_var, justify="left").pack(side="left", padx=12, fill="both", expand=True)

        # Secret payload row (Text or File toggle)
        payload_box = ttk.LabelFrame(self.encode_frame, text=" 2. Secret Data ", padding=8)
        payload_box.pack(fill="both", expand=True, pady=4)

        self.payload_type_var = tk.StringVar(value="text")
        radio_row = ttk.Frame(payload_box)
        radio_row.pack(fill="x", pady=2)
        ttk.Radiobutton(radio_row, text="Secret Text Message", variable=self.payload_type_var, value="text", command=self._toggle_payload_view).pack(side="left", padx=6)
        ttk.Radiobutton(radio_row, text="Binary File", variable=self.payload_type_var, value="file", command=self._toggle_payload_view).pack(side="left", padx=6)

        # Text input area
        self.text_frame = ttk.Frame(payload_box)
        self.text_frame.pack(fill="both", expand=True, pady=4)
        ttk.Label(self.text_frame, text="Enter Secret Message:").pack(anchor="w")
        self.secret_text_box = tk.Text(self.text_frame, height=5, wrap="word")
        self.secret_text_box.pack(fill="both", expand=True, pady=2)

        # File input area
        self.file_frame = ttk.Frame(payload_box)
        self.secret_file_var = tk.StringVar()
        ttk.Label(self.file_frame, text="Select Secret File:").pack(anchor="w")
        file_row = ttk.Frame(self.file_frame)
        file_row.pack(fill="x", pady=2)
        ttk.Entry(file_row, textvariable=self.secret_file_var).pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(file_row, text="Browse File", command=self._browse_secret_file).pack(side="left", padx=4)

        # Security box
        sec_box = ttk.LabelFrame(self.encode_frame, text=" 3. Security (Optional Password) ", padding=8)
        sec_box.pack(fill="x", pady=4)

        ttk.Label(sec_box, text="Password:").pack(side="left", padx=4)
        self.encode_pass_var = tk.StringVar()
        ttk.Entry(sec_box, textvariable=self.encode_pass_var, show="*", width=30).pack(side="left", padx=4)
        ttk.Label(sec_box, text="(Leave blank for unencrypted LSB embedding)", font=("Segoe UI", 8, "italic")).pack(side="left", padx=8)

        # Action Buttons
        btn_row = ttk.Frame(self.encode_frame)
        btn_row.pack(fill="x", pady=8)
        ttk.Button(btn_row, text="Encode & Save Stego Image", command=self._on_encode).pack(side="left", padx=4)
        ttk.Button(btn_row, text="Reset Fields", command=self._reset_encode_fields).pack(side="right", padx=4)

    def _toggle_payload_view(self) -> None:
        if self.payload_type_var.get() == "text":
            self.file_frame.pack_forget()
            self.text_frame.pack(fill="both", expand=True, pady=4)
        else:
            self.text_frame.pack_forget()
            self.file_frame.pack(fill="both", expand=True, pady=4)

    def _browse_cover_image(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Select Cover Image",
            filetypes=[("Supported Images", "*.png;*.jpg;*.jpeg;*.bmp"), ("PNG Images", "*.png"), ("All Files", "*.*")],
        )
        if not file_path:
            return

        self.cover_path_var.set(file_path)
        try:
            pil_img = load_image_as_rgb(file_path)
            # Update preview thumbnail
            thumb = pil_img.copy()
            thumb.thumbnail((120, 120))
            self.preview_image_tk = ImageTk.PhotoImage(thumb)
            self.preview_label.config(image=self.preview_image_tk, text="")

            # Compute capacity report
            rep = assess_capacity(pil_img, "")
            self.capacity_text_var.set(
                f"Dimensions: {rep.width} x {rep.height} px\n"
                f"Total Available Carrier Capacity: {rep.total_carrier_bytes / 1024:.2f} KB\n"
                f"Max Usable Data Capacity: {rep.max_usable_bytes / 1024:.2f} KB"
            )
        except Exception as exc:
            messagebox.showerror("Image Error", f"Unable to read image: {exc}")

    def _browse_secret_file(self) -> None:
        file_path = filedialog.askopenfilename(title="Select Secret File to Hide")
        if file_path:
            self.secret_file_var.set(file_path)

    def _on_encode(self) -> None:
        cover_path = self.cover_path_var.get().strip()
        if not cover_path or not Path(cover_path).is_file():
            messagebox.showerror("Error", "Please select a valid cover image.")
            return

        output_path = filedialog.asksaveasfilename(
            title="Save Stego Image As",
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png")],
        )
        if not output_path:
            return

        password = self.encode_pass_var.get() or None

        try:
            if self.payload_type_var.get() == "text":
                msg = self.secret_text_box.get("1.0", "end-1c")
                if not msg:
                    messagebox.showwarning("Warning", "Secret text message is empty.")
                    return
                encode_text(cover_path, msg, output_path, password=password)
            else:
                sec_file = self.secret_file_var.get().strip()
                if not sec_file or not Path(sec_file).is_file():
                    messagebox.showerror("Error", "Please select a valid file to hide.")
                    return
                encode_file(cover_path, sec_file, output_path, password=password)

            messagebox.showinfo("Success", f"Data successfully embedded!\nStego image saved to:\n{output_path}")
        except Exception as exc:
            messagebox.showerror("Encoding Failed", str(exc))

    def _reset_encode_fields(self) -> None:
        self.cover_path_var.set("")
        self.secret_file_var.set("")
        self.encode_pass_var.set("")
        self.secret_text_box.delete("1.0", "end")
        self.preview_label.config(image="", text="[No Image Loaded]")
        self.capacity_text_var.set("Select an image to see capacity metrics.")

    # -------------------------------------------------------------
    # DECODE TAB
    # -------------------------------------------------------------
    def _build_decode_tab(self) -> None:
        img_box = ttk.LabelFrame(self.decode_frame, text=" 1. Select Stego Image ", padding=8)
        img_box.pack(fill="x", pady=4)

        self.stego_path_var = tk.StringVar()
        ttk.Entry(img_box, textvariable=self.stego_path_var, width=55).pack(side="left", padx=4, fill="x", expand=True)
        ttk.Button(img_box, text="Browse Stego PNG", command=self._browse_stego_image).pack(side="left", padx=4)

        # Password
        sec_box = ttk.LabelFrame(self.decode_frame, text=" 2. Decryption Password (if required) ", padding=8)
        sec_box.pack(fill="x", pady=4)
        self.decode_pass_var = tk.StringVar()
        ttk.Entry(sec_box, textvariable=self.decode_pass_var, show="*", width=30).pack(side="left", padx=4)

        # Extract button
        btn_box = ttk.Frame(self.decode_frame)
        btn_box.pack(fill="x", pady=8)
        ttk.Button(btn_box, text="Extract Hidden Data", command=self._on_decode).pack(side="left", padx=4)

        # Results area
        res_box = ttk.LabelFrame(self.decode_frame, text=" 3. Recovered Output ", padding=8)
        res_box.pack(fill="both", expand=True, pady=4)

        self.decode_status_var = tk.StringVar(value="Ready to extract data.")
        ttk.Label(res_box, textvariable=self.decode_status_var, font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=2)

        self.recovered_text_box = tk.Text(res_box, height=10, wrap="word")
        self.recovered_text_box.pack(fill="both", expand=True, pady=4)

    def _browse_stego_image(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Select Stego Image",
            filetypes=[("PNG Images", "*.png"), ("All Files", "*.*")],
        )
        if file_path:
            self.stego_path_var.set(file_path)

    def _on_decode(self) -> None:
        stego_path = self.stego_path_var.get().strip()
        if not stego_path or not Path(stego_path).is_file():
            messagebox.showerror("Error", "Please select a valid stego image.")
            return

        password = self.decode_pass_var.get() or None

        try:
            img = load_image_as_rgb(stego_path)
            import numpy as np
            pixel_array = np.array(img, dtype=np.uint8)
            payload = extract_payload_from_array(pixel_array)

            if payload.is_file:
                # Prompt user for destination directory
                save_dir = filedialog.askdirectory(title="Select Destination Folder to Save Recovered File")
                if not save_dir:
                    return
                restored_path = decode_file(stego_path, save_dir, password=password)
                self.decode_status_var.set(f"File extracted successfully: {restored_path.name}")
                self.recovered_text_box.delete("1.0", "end")
                self.recovered_text_box.insert("1.0", f"File safely restored to:\n{restored_path.resolve()}\nSize: {restored_path.stat().st_size} bytes")
                messagebox.showinfo("Success", f"File recovered:\n{restored_path.name}")
            else:
                recovered_msg = decode_text(stego_path, password=password)
                self.decode_status_var.set("Text message recovered successfully:")
                self.recovered_text_box.delete("1.0", "end")
                self.recovered_text_box.insert("1.0", recovered_msg)
                messagebox.showinfo("Success", "Hidden message extracted successfully!")

        except Exception as exc:
            self.decode_status_var.set("Extraction failed.")
            messagebox.showerror("Decoding Failed", str(exc))


def launch_gui() -> None:
    """Entry point for the GUI application."""
    app = StegoGenApp()
    app.mainloop()

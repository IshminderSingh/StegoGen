import os
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image

from stegogen.core.encoder import encode_text
from stegogen.core.decoder import decode_text
from stegogen.core.capacity import assess_capacity
from stegogen.utils.analysis import compare_images

ctk.set_appearance_mode("Dark")

# Minimalist Apple Dark Theme
CANVAS_BG = "#161618"          # Smooth graphite
CARD_BG = "#212124"            # Clean elevated card
WELL_BG = "#19191b"            # Subtle input well
ACCENT_BLUE = "#0a84ff"        # Apple System Blue
ACCENT_HOVER = "#0071e3"
TEXT_TITLE = "#f5f5f7"
TEXT_SUB = "#86868b"
BORDER_COLOR = "#2d2d30"


class StegoGenSimpleApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("StegoGen")
        self.geometry("820x620")
        self.minsize(760, 560)
        self.configure(fg_color=CANVAS_BG)

        self.cover_path = None
        self.stego_path = None

        # Top Bar: Segmented Switcher
        self._build_top_switcher()

        # Content Area
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=32, pady=(10, 24))

        self.views = {
            "hide": self._view_hide(),
            "read": self._view_read(),
            "check": self._view_check()
        }

        self._show_tab("hide")

    # -------------------------------------------------------------
    # TOP PILL SWITCHER
    # -------------------------------------------------------------
    def _build_top_switcher(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=32, pady=(24, 12))

        ctk.CTkLabel(
            header,
            text="StegoGen",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=TEXT_TITLE
        ).pack(side="left")

        # Apple-style segmented control
        self.seg_tab = ctk.CTkSegmentedButton(
            header,
            values=["Hide Message", "Read Message", "Check Quality"],
            command=self._on_segment_click,
            corner_radius=8,
            selected_color=ACCENT_BLUE,
            selected_hover_color=ACCENT_HOVER,
            unselected_color="#26262a",
            unselected_hover_color="#303035",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=32
        )
        self.seg_tab.set("Hide Message")
        self.seg_tab.pack(side="right")

    def _on_segment_click(self, value):
        mapping = {
            "Hide Message": "hide",
            "Read Message": "read",
            "Check Quality": "check"
        }
        self._show_tab(mapping[value])

    def _show_tab(self, key):
        for name, frame in self.views.items():
            if name == key:
                frame.pack(fill="both", expand=True)
            else:
                frame.pack_forget()

    # -------------------------------------------------------------
    # TAB 1: HIDE MESSAGE (SIMPLE)
    # -------------------------------------------------------------
    def _view_hide(self):
        card = ctk.CTkFrame(self.container, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        card.grid_columnconfigure((0, 1), weight=1)

        # Left Column: Image Pick
        left = ctk.CTkFrame(card, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=24, pady=24)

        ctk.CTkLabel(left, text="1. Choose a Photo", font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_TITLE).pack(anchor="w")
        ctk.CTkLabel(left, text="Must be a .png file", font=ctk.CTkFont(size=11), text_color=TEXT_SUB).pack(anchor="w", pady=(0, 10))

        self.lbl_cover_preview = ctk.CTkLabel(
            left,
            text="No photo selected",
            fg_color=WELL_BG,
            corner_radius=10,
            text_color=TEXT_SUB,
            height=180
        )
        self.lbl_cover_preview.pack(fill="both", expand=True, pady=(0, 12))

        ctk.CTkButton(
            left,
            text="Browse Photo...",
            height=34,
            corner_radius=8,
            fg_color="#323238",
            hover_color="#3e3e44",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._choose_cover
        ).pack(fill="x")

        # Right Column: Secret Text & Password
        right = ctk.CTkFrame(card, fg_color="transparent")
        right.pack(side="right", fill="both", expand=True, padx=24, pady=24)

        ctk.CTkLabel(right, text="2. Type Secret Message", font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_TITLE).pack(anchor="w")
        ctk.CTkLabel(right, text="What would you like to conceal?", font=ctk.CTkFont(size=11), text_color=TEXT_SUB).pack(anchor="w", pady=(0, 10))

        self.txt_secret = ctk.CTkTextbox(right, fg_color=WELL_BG, corner_radius=10, border_width=1, border_color=BORDER_COLOR, height=130)
        self.txt_secret.pack(fill="both", expand=True, pady=(0, 12))

        ctk.CTkLabel(right, text="Password (Optional)", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_TITLE).pack(anchor="w")
        self.ent_hide_pass = ctk.CTkEntry(
            right,
            show="•",
            placeholder_text="Add password for extra protection",
            fg_color=WELL_BG,
            border_color=BORDER_COLOR,
            corner_radius=8,
            height=34
        )
        self.ent_hide_pass.pack(fill="x", pady=(4, 16))

        ctk.CTkButton(
            right,
            text="Save Protected Photo",
            height=38,
            corner_radius=8,
            fg_color=ACCENT_BLUE,
            hover_color=ACCENT_HOVER,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._do_hide
        ).pack(fill="x")

        return card

    # -------------------------------------------------------------
    # TAB 2: READ MESSAGE (SIMPLE)
    # -------------------------------------------------------------
    def _view_read(self):
        card = ctk.CTkFrame(self.container, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        card.pack(fill="both", expand=True)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=32, pady=24)

        ctk.CTkLabel(inner, text="Read a Hidden Message", font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT_TITLE).pack(anchor="w")
        ctk.CTkLabel(inner, text="Select the protected image and reveal what's inside", font=ctk.CTkFont(size=12), text_color=TEXT_SUB).pack(anchor="w", pady=(0, 16))

        # Top bar to choose file
        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack(fill="x", pady=(0, 12))

        ctk.CTkButton(
            row,
            text="Choose Image...",
            height=34,
            corner_radius=8,
            fg_color="#323238",
            hover_color="#3e3e44",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._choose_stego
        ).pack(side="left", padx=(0, 12))

        self.lbl_read_file = ctk.CTkLabel(row, text="No image selected", text_color=TEXT_SUB)
        self.lbl_read_file.pack(side="left")

        # Password + Read button
        pass_row = ctk.CTkFrame(inner, fg_color="transparent")
        pass_row.pack(fill="x", pady=(0, 14))

        self.ent_read_pass = ctk.CTkEntry(
            pass_row,
            show="•",
            placeholder_text="Enter password (if one was set)...",
            fg_color=WELL_BG,
            border_color=BORDER_COLOR,
            corner_radius=8,
            height=36
        )
        self.ent_read_pass.pack(side="left", fill="x", expand=True, padx=(0, 12))

        ctk.CTkButton(
            pass_row,
            text="Reveal Message",
            height=36,
            corner_radius=8,
            fg_color=ACCENT_BLUE,
            hover_color=ACCENT_HOVER,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._do_read
        ).pack(side="right")

        ctk.CTkLabel(inner, text="Decoded Message:", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_SUB).pack(anchor="w", pady=(6, 4))

        self.txt_revealed = ctk.CTkTextbox(inner, fg_color=WELL_BG, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
        self.txt_revealed.pack(fill="both", expand=True)

        return card

    # -------------------------------------------------------------
    # TAB 3: QUALITY CHECK (FRIENDLY)
    # -------------------------------------------------------------
    def _view_check(self):
        card = ctk.CTkFrame(self.container, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        card.pack(fill="both", expand=True)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=32, pady=24)

        ctk.CTkLabel(inner, text="Image Quality Verification", font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT_TITLE).pack(anchor="w")
        ctk.CTkLabel(inner, text="Confirm that the secret data did not alter the image quality", font=ctk.CTkFont(size=12), text_color=TEXT_SUB).pack(anchor="w", pady=(0, 20))

        # Big Visual Status Tile
        self.status_box = ctk.CTkFrame(inner, fg_color=WELL_BG, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        self.status_box.pack(fill="x", pady=(0, 20), ipady=16)

        self.lbl_verdict = ctk.CTkLabel(
            self.status_box,
            text="Ready to Compare",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=TEXT_TITLE
        )
        self.lbl_verdict.pack(pady=(12, 4))

        self.lbl_verdict_sub = ctk.CTkLabel(
            self.status_box,
            text="Make sure you have loaded an original photo and created a secret photo first.",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_SUB
        )
        self.lbl_verdict_sub.pack(pady=(0, 12))

        ctk.CTkButton(
            inner,
            text="Run Quality Test",
            height=38,
            corner_radius=8,
            fg_color=ACCENT_BLUE,
            hover_color=ACCENT_HOVER,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._do_check
        ).pack(fill="x")

        return card

    # -------------------------------------------------------------
    # SIMPLE EVENT HANDLERS
    # -------------------------------------------------------------
    def _choose_cover(self):
        path = filedialog.askopenfilename(filetypes=[("PNG Images", "*.png")])
        if path:
            self.cover_path = path
            try:
                img = Image.open(path)
                img.thumbnail((260, 160))
                thumb = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
                self.lbl_cover_preview.configure(image=thumb, text="")
            except Exception:
                self.lbl_cover_preview.configure(text=os.path.basename(path))

    def _choose_stego(self):
        path = filedialog.askopenfilename(filetypes=[("PNG Images", "*.png")])
        if path:
            self.stego_path = path
            self.lbl_read_file.configure(text=os.path.basename(path), text_color=TEXT_TITLE)

    def _do_hide(self):
        if not self.cover_path:
            messagebox.showinfo("Select Photo", "Please pick a PNG photo first.")
            return

        msg = self.txt_secret.get("1.0", "end-1c").strip()
        if not msg:
            messagebox.showinfo("Enter Message", "Please type a message to hide.")
            return

        out_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Images", "*.png")])
        if not out_path:
            return

        pwd = self.ent_hide_pass.get().strip() or None
        try:
            encode_text(self.cover_path, msg, out_path, password=pwd)
            self.stego_path = out_path  # Pre-load for quality test
            messagebox.showinfo("Success", "Your secret photo has been created and saved!")
        except Exception as e:
            messagebox.showerror("Notice", str(e))

    def _do_read(self):
        if not self.stego_path:
            messagebox.showinfo("Select Photo", "Please choose the image you want to read.")
            return

        pwd = self.ent_read_pass.get().strip() or None
        try:
            text = decode_text(self.stego_path, password=pwd)
            self.txt_revealed.delete("1.0", "end")
            self.txt_revealed.insert("1.0", text)
        except Exception:
            messagebox.showerror("Unable to Read", "Could not find a valid message. Either the password is incorrect or this image contains no secret data.")

    def _do_check(self):
        if not self.cover_path or not self.stego_path:
            messagebox.showinfo("Files Needed", "Please hide a message into an image first so we have both before and after images to compare.")
            return
        
        report = compare_images(self.cover_path, self.stego_path)
        
        # User-friendly verdict
        if report.psnr > 40:
            self.lbl_verdict.configure(text="✓ Perfect Visual Quality", text_color="#30d158")
            self.lbl_verdict_sub.configure(text=f"The secret message is 100% invisible to the human eye ({report.psnr:.1f} dB score).")
        else:
            self.lbl_verdict.configure(text="Quality Warning", text_color="#ff9f0a")
            self.lbl_verdict_sub.configure(text="Minor changes were detected between the images.")


def launch_gui():
    app = StegoGenSimpleApp()
    app.mainloop()


if __name__ == "__main__":
    launch_gui()
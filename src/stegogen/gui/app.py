"""Modern Apple-style dark UI for StegoGen with interactive analytics graphs."""

import os
import numpy as np
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from stegogen.core.encoder import encode_text
from stegogen.core.decoder import decode_text
from stegogen.core.capacity import assess_capacity
from stegogen.utils.analysis import compare_images, generate_diff_heatmap, analyze_pairs_of_values

ctk.set_appearance_mode("Dark")

CANVAS_BG = "#161618"
CARD_BG = "#212124"
WELL_BG = "#19191b"
ACCENT_BLUE = "#0a84ff"
ACCENT_HOVER = "#0071e3"
TEXT_TITLE = "#f5f5f7"
TEXT_SUB = "#86868b"
BORDER_COLOR = "#2d2d30"

IMAGE_FILETYPES = [
    ("Supported Images (*.png;*.jpg;*.jpeg)", "*.png;*.jpg;*.jpeg"),
    ("PNG Images (*.png)", "*.png"),
    ("JPEG Images (*.jpg;*.jpeg)", "*.jpg;*.jpeg"),
    ("All Files (*.*)", "*.*")
]


class StegoGenSimpleApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("StegoGen Analytics Studio")
        self.geometry("1060x750")
        self.minsize(920, 650)
        self.configure(fg_color=CANVAS_BG)

        # Hook clean exit handler to silence Tkinter "after" script errors
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        self.cover_path = None
        self.stego_path = None
        self.chart_canvas = None

        self._build_top_switcher()

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=24, pady=(8, 16))

        self.views = {
            "hide": self._view_hide(),
            "read": self._view_read(),
            "check": self._view_check()
        }

        self._show_tab("hide")

    def _on_closing(self):
        """Cleanly releases Matplotlib figures and terminates event loops."""
        try:
            plt.close("all")
        except Exception:
            pass
        self.quit()
        self.destroy()

    def _build_top_switcher(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(16, 6))

        ctk.CTkLabel(
            header,
            text="StegoGen",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color=TEXT_TITLE
        ).pack(side="left")

        self.seg_tab = ctk.CTkSegmentedButton(
            header,
            values=["Hide Message", "Read Message", "Quality & Analytics"],
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
            "Quality & Analytics": "check"
        }
        self._show_tab(mapping[value])

    def _show_tab(self, key):
        for name, frame in self.views.items():
            if name == key:
                frame.pack(fill="both", expand=True)
            else:
                frame.pack_forget()

    # -------------------------------------------------------------
    # TAB 1: HIDE MESSAGE
    # -------------------------------------------------------------
    def _view_hide(self):
        card = ctk.CTkFrame(self.container, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=BORDER_COLOR)

        left = ctk.CTkFrame(card, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(left, text="1. Choose Cover Carrier", font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_TITLE).pack(anchor="w")
        ctk.CTkLabel(left, text="Supports .png, .jpg, .jpeg (exports to lossless .png)", font=ctk.CTkFont(size=11), text_color=TEXT_SUB).pack(anchor="w", pady=(0, 8))

        self.lbl_cover_preview = ctk.CTkLabel(
            left,
            text="No carrier photo selected",
            fg_color=WELL_BG,
            corner_radius=10,
            text_color=TEXT_SUB,
            height=200
        )
        self.lbl_cover_preview.pack(fill="both", expand=True, pady=(0, 10))

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

        right = ctk.CTkFrame(card, fg_color="transparent")
        right.pack(side="right", fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(right, text="2. Secret Message", font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_TITLE).pack(anchor="w")

        self.txt_secret = ctk.CTkTextbox(right, fg_color=WELL_BG, corner_radius=10, border_width=1, border_color=BORDER_COLOR, height=140)
        self.txt_secret.pack(fill="both", expand=True, pady=(6, 6))
        self.txt_secret.bind("<KeyRelease>", self._update_capacity_meter)

        self.capacity_bar = ctk.CTkProgressBar(right, orientation="horizontal", height=7, corner_radius=4, progress_color=ACCENT_BLUE)
        self.capacity_bar.set(0.0)
        self.capacity_bar.pack(fill="x", pady=(2, 2))

        self.lbl_capacity_status = ctk.CTkLabel(right, text="Capacity: Select an image", font=ctk.CTkFont(size=11), text_color=TEXT_SUB)
        self.lbl_capacity_status.pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(right, text="Password Protection (AES-256-GCM)", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_TITLE).pack(anchor="w")
        self.ent_hide_pass = ctk.CTkEntry(
            right,
            show="•",
            placeholder_text="Optional encryption passphrase...",
            fg_color=WELL_BG,
            border_color=BORDER_COLOR,
            corner_radius=8,
            height=34
        )
        self.ent_hide_pass.pack(fill="x", pady=(4, 14))
        self.ent_hide_pass.bind("<KeyRelease>", self._update_capacity_meter)

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
    # TAB 2: READ MESSAGE
    # -------------------------------------------------------------
    def _view_read(self):
        card = ctk.CTkFrame(self.container, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=28, pady=20)

        ctk.CTkLabel(inner, text="Extract Concealed Payload", font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT_TITLE).pack(anchor="w")
        ctk.CTkLabel(inner, text="Select a stego image to authenticate and reveal hidden plaintext", font=ctk.CTkFont(size=12), text_color=TEXT_SUB).pack(anchor="w", pady=(0, 14))

        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack(fill="x", pady=(0, 10))

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

        pass_row = ctk.CTkFrame(inner, fg_color="transparent")
        pass_row.pack(fill="x", pady=(0, 12))

        self.ent_read_pass = ctk.CTkEntry(
            pass_row,
            show="•",
            placeholder_text="Enter password (if protected)...",
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

        hdr_row = ctk.CTkFrame(inner, fg_color="transparent")
        hdr_row.pack(fill="x", pady=(4, 4))
        ctk.CTkLabel(hdr_row, text="Decoded Payload:", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_SUB).pack(side="left")

        ctk.CTkButton(
            hdr_row,
            text="Copy to Clipboard",
            width=130,
            height=26,
            corner_radius=6,
            fg_color="#323238",
            hover_color="#3e3e44",
            font=ctk.CTkFont(size=11),
            command=self._copy_message
        ).pack(side="right")

        self.txt_revealed = ctk.CTkTextbox(inner, fg_color=WELL_BG, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
        self.txt_revealed.pack(fill="both", expand=True)

        return card

    # -------------------------------------------------------------
    # TAB 3: QUALITY & ANALYTICS DASHBOARD
    # -------------------------------------------------------------
    def _view_check(self):
        card = ctk.CTkFrame(self.container, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=14)

        # Top Control Row
        top_ctrl = ctk.CTkFrame(inner, fg_color="transparent")
        top_ctrl.pack(fill="x", pady=(0, 10))

        ctk.CTkButton(top_ctrl, text="Original Photo...", width=115, height=30, corner_radius=8, fg_color="#323238", hover_color="#3e3e44", command=self._pick_qual_cover).pack(side="left", padx=(0, 6))
        self.lbl_qual_cover = ctk.CTkLabel(top_ctrl, text="No original", text_color=TEXT_SUB, width=120, anchor="w")
        self.lbl_qual_cover.pack(side="left", padx=(0, 8))

        ctk.CTkButton(top_ctrl, text="Protected Stego...", width=115, height=30, corner_radius=8, fg_color="#323238", hover_color="#3e3e44", command=self._pick_qual_stego).pack(side="left", padx=(0, 6))
        self.lbl_qual_stego = ctk.CTkLabel(top_ctrl, text="No protected photo", text_color=TEXT_SUB, width=120, anchor="w")
        self.lbl_qual_stego.pack(side="left", padx=(0, 8))

        ctk.CTkButton(top_ctrl, text="Run Analytics", width=110, height=30, corner_radius=8, fg_color=ACCENT_BLUE, hover_color=ACCENT_HOVER, font=ctk.CTkFont(weight="bold"), command=self._do_check).pack(side="right")
        ctk.CTkButton(top_ctrl, text="Residue Heatmap", width=120, height=30, corner_radius=8, fg_color="#323238", hover_color="#3e3e44", command=self._show_heatmap).pack(side="right", padx=(0, 6))
        ctk.CTkButton(top_ctrl, text="What do these mean?", width=140, height=30, corner_radius=8, fg_color="#323238", hover_color="#3e3e44", font=ctk.CTkFont(size=12), command=self._show_explanation_dialog).pack(side="right", padx=(0, 6))

        # Split Dashboard
        dash = ctk.CTkFrame(inner, fg_color="transparent")
        dash.pack(fill="both", expand=True)

        # Left Gauges Column
        left_panel = ctk.CTkFrame(dash, fg_color=WELL_BG, corner_radius=10, border_width=1, border_color=BORDER_COLOR, width=290)
        left_panel.pack(side="left", fill="both", padx=(0, 10), pady=2)
        left_panel.pack_propagate(False)

        ctk.CTkLabel(left_panel, text="Signal & Fidelity Gauges", font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT_TITLE).pack(anchor="w", padx=14, pady=(12, 8))

        # PSNR Level Bar
        self.lbl_gauge_psnr = ctk.CTkLabel(left_panel, text="PSNR: -- dB (Threshold ≥ 40 dB)", font=ctk.CTkFont(size=11), text_color=TEXT_SUB)
        self.lbl_gauge_psnr.pack(anchor="w", padx=14, pady=(4, 2))
        self.bar_psnr = ctk.CTkProgressBar(left_panel, height=8, corner_radius=4, progress_color="#30d158")
        self.bar_psnr.set(0.0)
        self.bar_psnr.pack(fill="x", padx=14, pady=(0, 8))

        # SSIM Level Bar
        self.lbl_gauge_ssim = ctk.CTkLabel(left_panel, text="SSIM: -- (Target ≈ 1.0)", font=ctk.CTkFont(size=11), text_color=TEXT_SUB)
        self.lbl_gauge_ssim.pack(anchor="w", padx=14, pady=(4, 2))
        self.bar_ssim = ctk.CTkProgressBar(left_panel, height=8, corner_radius=4, progress_color=ACCENT_BLUE)
        self.bar_ssim.set(0.0)
        self.bar_ssim.pack(fill="x", padx=14, pady=(0, 8))

        # Statistical Suspicion Bar
        self.lbl_gauge_pov = ctk.CTkLabel(left_panel, text="Statistical Suspicion: -- (Target < 20%)", font=ctk.CTkFont(size=11), text_color=TEXT_SUB)
        self.lbl_gauge_pov.pack(anchor="w", padx=14, pady=(4, 2))
        self.bar_pov = ctk.CTkProgressBar(left_panel, height=8, corner_radius=4, progress_color="#ffd60a")
        self.bar_pov.set(0.0)
        self.bar_pov.pack(fill="x", padx=14, pady=(0, 12))

        # Status Verdict Badge
        self.badge_box = ctk.CTkFrame(left_panel, fg_color="#212124", corner_radius=8, border_width=1, border_color=BORDER_COLOR)
        self.badge_box.pack(fill="x", padx=14, pady=(4, 10), ipady=6)

        self.lbl_verdict = ctk.CTkLabel(self.badge_box, text="Awaiting Analysis", font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_TITLE)
        self.lbl_verdict.pack(pady=(4, 2))
        self.lbl_verdict_sub = ctk.CTkLabel(self.badge_box, text="Pick original and stego carriers to inspect.", font=ctk.CTkFont(size=10), text_color=TEXT_SUB)
        self.lbl_verdict_sub.pack(pady=(0, 4))

        # Right Visualization Frame
        self.chart_container = ctk.CTkFrame(dash, fg_color=WELL_BG, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
        self.chart_container.pack(side="right", fill="both", expand=True, pady=2)

        self._init_empty_charts()

        return card

    # -------------------------------------------------------------
    # EMBEDDED MATPLOTLIB VISUALIZATIONS
    # -------------------------------------------------------------
    def _init_empty_charts(self):
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.2, 3.4), facecolor="#19191b")

        for ax in (ax1, ax2):
            ax.set_facecolor("#19191b")
            ax.tick_params(colors="#86868b", labelsize=8)
            for spine in ax.spines.values():
                spine.set_color("#2d2d30")

        ax1.set_title("Channel MSE Distortion", color="#f5f5f7", fontsize=10, pad=8)
        ax1.set_xticks([0, 1, 2])
        ax1.set_xticklabels(["Red", "Green", "Blue"])

        ax2.set_title("Luminance Distribution Overlay", color="#f5f5f7", fontsize=10, pad=8)
        ax2.set_xlabel("Pixel Value (0-255)", color="#86868b", fontsize=8)

        fig.tight_layout(pad=2.0)

        self.chart_canvas = FigureCanvasTkAgg(fig, master=self.chart_container)
        self.chart_canvas.draw()
        self.chart_canvas.get_tk_widget().pack(fill="both", expand=True, padx=6, pady=6)

    def _render_charts(self, report, stats):
        for widget in self.chart_container.winfo_children():
            widget.destroy()

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.2, 3.4), facecolor="#19191b")

        for ax in (ax1, ax2):
            ax.set_facecolor("#19191b")
            ax.tick_params(colors="#86868b", labelsize=8)
            for spine in ax.spines.values():
                spine.set_color("#2d2d30")

        # 1. Bar Chart: MSE per RGB channel
        channels = ["Red", "Green", "Blue"]
        colors = ["#ff453a", "#30d158", "#0a84ff"]
        ax1.bar(channels, report.mse_rgb, color=colors, width=0.45)
        ax1.set_title("Channel MSE Distortion", color="#f5f5f7", fontsize=10, pad=8)
        ax1.set_ylabel("MSE", color="#86868b", fontsize=8)

        # 2. Line Chart: Luminance Distribution Overlay
        bins = np.linspace(0, 255, len(report.cover_hist))
        ax2.plot(bins, report.cover_hist, label="Original", color="#86868b", linewidth=1.5, linestyle="--")
        ax2.plot(bins, report.stego_hist, label="Stego", color=ACCENT_BLUE, linewidth=1.5)
        ax2.set_title("Luminance Distribution Overlay", color="#f5f5f7", fontsize=10, pad=8)
        ax2.set_xlabel("Pixel Luminance (0-255)", color="#86868b", fontsize=8)
        legend = ax2.legend(facecolor="#212124", edgecolor="#2d2d30", fontsize=8)
        for text in legend.get_texts():
            text.set_color("#f5f5f7")

        fig.tight_layout(pad=2.0)

        self.chart_canvas = FigureCanvasTkAgg(fig, master=self.chart_container)
        self.chart_canvas.draw()
        self.chart_canvas.get_tk_widget().pack(fill="both", expand=True, padx=6, pady=6)

    # -------------------------------------------------------------
    # NON-TECHNICAL EXPLANATION DIALOG
    # -------------------------------------------------------------
    def _show_explanation_dialog(self):
        """Displays a plain-English guide explaining the metrics and graphs."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Understanding Your Image Quality & Graphs")
        dialog.geometry("580x470")
        dialog.minsize(500, 380)
        dialog.configure(fg_color=CANVAS_BG)
        dialog.grab_set()

        container = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            container,
            text="How to Read the Results",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=TEXT_TITLE
        ).pack(anchor="w", pady=(0, 10))

        items = [
            (
                "PSNR (Signal Clarity)",
                "Measures visual purity. Higher is better. A score above 40 dB means your eye cannot spot any visual difference between the two pictures."
            ),
            (
                "SSIM (Visual Similarity)",
                "Scores how identical the structures look on a scale from 0.0 to 1.0. A score near 1.000 means lines, edges, textures, and lighting remained intact."
            ),
            (
                "Statistical Suspicion",
                "Evaluates whether an automated detector would guess that data is hidden inside. Below 20% is clean and safe; higher values indicate unusual patterns."
            ),
            (
                "Left Chart: Channel Distortion (MSE)",
                "Shows how much each individual color (Red, Green, Blue) was altered. Tiny bars mean virtually zero disturbance to that color channel."
            ),
            (
                "Right Chart: Brightness Overlay",
                "Compares the brightness profile of the original photo (gray dashed) with the stego photo (blue solid). Perfect overlap proves the hidden data caused no color or lighting shift."
            ),
            (
                "Residue Heatmap",
                "An amplified difference map magnified 150 times to reveal altered bits. Black areas mean the pixels were left untouched."
            )
        ]

        for title, desc in items:
            card = ctk.CTkFrame(container, fg_color=CARD_BG, corner_radius=8, border_width=1, border_color=BORDER_COLOR)
            card.pack(fill="x", pady=(0, 8))

            ctk.CTkLabel(
                card,
                text=title,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=ACCENT_BLUE
            ).pack(anchor="w", padx=12, pady=(8, 2))

            ctk.CTkLabel(
                card,
                text=desc,
                font=ctk.CTkFont(size=11),
                text_color=TEXT_SUB,
                wraplength=500,
                justify="left"
            ).pack(anchor="w", padx=12, pady=(0, 8))

        ctk.CTkButton(
            container,
            text="Got It",
            height=32,
            corner_radius=8,
            fg_color=ACCENT_BLUE,
            hover_color=ACCENT_HOVER,
            command=dialog.destroy
        ).pack(fill="x", pady=(10, 0))

    # -------------------------------------------------------------
    # EVENT HANDLERS
    # -------------------------------------------------------------
    def _choose_cover(self):
        path = filedialog.askopenfilename(title="Select Cover Photo (PNG or JPG)", filetypes=IMAGE_FILETYPES)
        if path:
            self.cover_path = path
            if hasattr(self, "lbl_qual_cover"):
                self.lbl_qual_cover.configure(text=os.path.basename(path), text_color=TEXT_TITLE)
            try:
                img = Image.open(path)
                img.thumbnail((260, 160))
                thumb = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
                self.lbl_cover_preview.configure(image=thumb, text="")
            except Exception:
                self.lbl_cover_preview.configure(text=os.path.basename(path))
            self._update_capacity_meter()

    def _choose_stego(self):
        path = filedialog.askopenfilename(title="Select Protected Image (PNG)", filetypes=[("PNG Images (*.png)", "*.png"), ("All Files (*.*)", "*.*")])
        if path:
            self.stego_path = path
            self.lbl_read_file.configure(text=os.path.basename(path), text_color=TEXT_TITLE)
            if hasattr(self, "lbl_qual_stego"):
                self.lbl_qual_stego.configure(text=os.path.basename(path), text_color=TEXT_TITLE)

    def _pick_qual_cover(self):
        path = filedialog.askopenfilename(title="Select Original Photo", filetypes=IMAGE_FILETYPES)
        if path:
            self.cover_path = path
            self.lbl_qual_cover.configure(text=os.path.basename(path), text_color=TEXT_TITLE)

    def _pick_qual_stego(self):
        path = filedialog.askopenfilename(title="Select Protected Stego Photo", filetypes=[("PNG Images (*.png)", "*.png"), ("All Files (*.*)", "*.*")])
        if path:
            self.stego_path = path
            self.lbl_qual_stego.configure(text=os.path.basename(path), text_color=TEXT_TITLE)

    def _update_capacity_meter(self, event=None):
        if not self.cover_path:
            return
        msg = self.txt_secret.get("1.0", "end-1c")
        try:
            report = assess_capacity(
                self.cover_path,
                msg,
                is_encrypted=bool(self.ent_hide_pass.get().strip()),
                is_file=False
            )
            pct = report.usage_percentage / 100.0
            self.capacity_bar.set(min(1.0, pct))
            rem_kb = report.remaining_bytes / 1024.0

            if report.fits:
                self.capacity_bar.configure(progress_color=ACCENT_BLUE)
                self.lbl_capacity_status.configure(
                    text=f"Used: {report.usage_percentage:.2f}% | Available: {rem_kb:.1f} KB",
                    text_color=TEXT_SUB
                )
            else:
                self.capacity_bar.configure(progress_color="#ff453a")
                self.lbl_capacity_status.configure(
                    text=f"Capacity Exceeded! Overshoot: {abs(rem_kb):.1f} KB",
                    text_color="#ff453a"
                )
        except Exception:
            pass

    def _copy_message(self):
        text = self.txt_revealed.get("1.0", "end-1c").strip()
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            messagebox.showinfo("Copied", "Decoded message copied to clipboard.")

    def _do_hide(self):
        if not self.cover_path:
            messagebox.showinfo("Select Photo", "Please choose a photo (PNG or JPG) first.")
            return

        msg = self.txt_secret.get("1.0", "end-1c").strip()
        if not msg:
            messagebox.showinfo("Enter Message", "Please type a secret message to hide.")
            return

        out_path = filedialog.asksaveasfilename(
            title="Save Protected Photo",
            defaultextension=".png",
            filetypes=[("PNG Image (Lossless)", "*.png")]
        )
        if not out_path:
            return

        pwd = self.ent_hide_pass.get().strip() or None
        try:
            encode_text(self.cover_path, msg, out_path, password=pwd)
            self.stego_path = out_path
            if hasattr(self, "lbl_qual_stego"):
                self.lbl_qual_stego.configure(text=os.path.basename(out_path), text_color=TEXT_TITLE)
            messagebox.showinfo("Success", "Protected PNG image created successfully!")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _do_read(self):
        if not self.stego_path:
            messagebox.showinfo("Select Photo", "Please pick an image to read.")
            return

        pwd = self.ent_read_pass.get().strip() or None
        try:
            text = decode_text(self.stego_path, password=pwd)
            self.txt_revealed.delete("1.0", "end")
            self.txt_revealed.insert("1.0", text)
        except Exception:
            messagebox.showerror("Notice", "Could not extract message. Check your password or ensure this image contains stego data.")

    def _do_check(self):
        if not self.cover_path:
            path = filedialog.askopenfilename(title="Select Original Image", filetypes=IMAGE_FILETYPES)
            if path:
                self.cover_path = path
                self.lbl_qual_cover.configure(text=os.path.basename(path), text_color=TEXT_TITLE)
            else:
                return

        if not self.stego_path:
            path = filedialog.askopenfilename(title="Select Protected Stego Image", filetypes=[("PNG Images (*.png)", "*.png")])
            if path:
                self.stego_path = path
                self.lbl_qual_stego.configure(text=os.path.basename(path), text_color=TEXT_TITLE)
            else:
                return

        try:
            report = compare_images(self.cover_path, self.stego_path)
            stats = analyze_pairs_of_values(self.stego_path)

            # Update Gauges
            psnr = report.psnr_db
            psnr_norm = 1.0 if (psnr == float("inf") or report.is_identical) else min(1.0, max(0.0, psnr / 60.0))
            self.bar_psnr.set(psnr_norm)
            psnr_display = "∞ dB" if (psnr == float("inf") or report.is_identical) else f"{psnr:.2f} dB"
            self.lbl_gauge_psnr.configure(text=f"PSNR: {psnr_display} (Benchmark ≥ 40 dB)")

            ssim = report.ssim
            self.bar_ssim.set(min(1.0, max(0.0, ssim)))
            self.lbl_gauge_ssim.configure(text=f"SSIM: {ssim:.5f} (Target ≈ 1.0)")

            suspicion = stats["suspicion_pct"]
            self.bar_pov.set(min(1.0, max(0.0, suspicion / 100.0)))
            self.bar_pov.configure(progress_color="#30d158" if suspicion < 30.0 else "#ff453a")
            self.lbl_gauge_pov.configure(text=f"Statistical Suspicion: {suspicion:.1f}%")

            # Update Status Badge
            if report.is_identical or psnr == float("inf") or psnr >= 40.0:
                self.lbl_verdict.configure(text="✓ Imperceptible Fidelity", text_color="#30d158")
                self.lbl_verdict_sub.configure(text="LSB perturbation within noise thresholds.")
            else:
                self.lbl_verdict.configure(text="⚠ Noticeable Variance", text_color="#ff9f0a")
                self.lbl_verdict_sub.configure(text="Deviation exceeds optimal threshold.")

            # Render Matplotlib Subplots
            self._render_charts(report, stats)

        except Exception as e:
            self.lbl_verdict.configure(text="Test Failed", text_color="#ff453a")
            self.lbl_verdict_sub.configure(text=str(e))

    def _show_heatmap(self):
        if not self.cover_path or not self.stego_path:
            messagebox.showinfo("Select Images", "Please select both original and protected photos first.")
            return

        try:
            diff_img = generate_diff_heatmap(self.cover_path, self.stego_path, amplification=150)

            top = ctk.CTkToplevel(self)
            top.title("LSB Residue Heatmap (150x Amplified)")
            top.geometry("620x500")

            diff_img.thumbnail((580, 440))
            ctk_img = ctk.CTkImage(light_image=diff_img, dark_image=diff_img, size=diff_img.size)

            lbl = ctk.CTkLabel(top, image=ctk_img, text="")
            lbl.pack(fill="both", expand=True, padx=20, pady=20)
        except Exception as e:
            messagebox.showerror("Heatmap Error", str(e))


def launch_gui():
    app = StegoGenSimpleApp()
    app.mainloop()


if __name__ == "__main__":
    launch_gui()
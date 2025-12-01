#!/usr/bin/env python3
"""
PyPSA Alternative - Comprehensive Utilities GUI
Interactive interface to run all utility tools.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import sys
import os
from pathlib import Path
from datetime import datetime


class RedirectText:
    """Redirect stdout/stderr to GUI text widget."""

    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, string):
        self.text_widget.insert(tk.END, string)
        self.text_widget.see(tk.END)

    def flush(self):
        pass


class UtilsGUI:
    """Comprehensive GUI for all PyPSA utilities."""

    def __init__(self, root):
        self.root = root
        self.root.title("PyPSA Utilities - All Tools")
        self.root.geometry("1200x800")  # Increased width for left sidebar

        # Store original stdout/stderr
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr

        # Store tabs for custom tab system
        self.tabs = {}
        self.current_tab = None

        # Create widgets
        self.create_widgets()

    def create_scrollable_frame(self, parent):
        """Create a scrollable frame for tab content."""
        # Create canvas and scrollbar
        canvas = tk.Canvas(parent, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack scrollbar and canvas
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # Enable mousewheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        def _bind_to_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)

        def _unbind_from_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")

        canvas.bind('<Enter>', _bind_to_mousewheel)
        canvas.bind('<Leave>', _unbind_from_mousewheel)

        return scrollable_frame

    def add_tab(self, name, icon, frame):
        """Add a tab with a sidebar button."""
        # Create button in sidebar
        btn = tk.Button(
            self.sidebar_frame,
            text=f"{icon} {name}",
            command=lambda: self.show_tab(name),
            relief=tk.FLAT,
            anchor=tk.W,
            padx=15,
            pady=8,
            font=("Helvetica", 10),
            bg="#f0f0f0",
            activebackground="#e0e0e0",
            cursor="hand2",
            width=20
        )
        btn.pack(fill=tk.X, padx=5, pady=2)

        # Store tab info
        self.tabs[name] = {
            'frame': frame,
            'button': btn
        }

    def show_tab(self, name):
        """Show the selected tab and hide others."""
        # Hide current tab
        if self.current_tab and self.current_tab in self.tabs:
            self.tabs[self.current_tab]['frame'].pack_forget()
            self.tabs[self.current_tab]['button'].config(
                relief=tk.FLAT,
                bg="#f0f0f0",
                font=("Helvetica", 10)
            )

        # Show new tab
        if name in self.tabs:
            self.tabs[name]['frame'].pack(fill=tk.BOTH, expand=True)
            self.tabs[name]['button'].config(
                relief=tk.SUNKEN,
                bg="#d0d0d0",
                font=("Helvetica", 10, "bold")
            )
            self.current_tab = name

    def create_widgets(self):
        """Create all GUI widgets."""

        # Title
        title_frame = ttk.Frame(self.root, padding="10")
        title_frame.pack(fill=tk.X)

        title_label = ttk.Label(
            title_frame,
            text="PyPSA Utilities - All Tools",
            font=("Helvetica", 16, "bold")
        )
        title_label.pack()

        subtitle_label = ttk.Label(
            title_frame,
            text="Run any utility tool with a click - 13 tools available",
            font=("Helvetica", 10)
        )
        subtitle_label.pack()

        # Create main container with sidebar and content
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Left sidebar for tab buttons
        sidebar = ttk.Frame(main_container, relief=tk.RAISED, borderwidth=1)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))

        # Sidebar title
        sidebar_title = ttk.Label(sidebar, text="Tools", font=("Helvetica", 12, "bold"))
        sidebar_title.pack(pady=10, padx=10)

        ttk.Separator(sidebar, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=5, pady=5)

        # Scrollable sidebar content
        sidebar_canvas = tk.Canvas(sidebar, width=180, highlightthickness=0)
        sidebar_scrollbar = ttk.Scrollbar(sidebar, orient="vertical", command=sidebar_canvas.yview)
        self.sidebar_frame = ttk.Frame(sidebar_canvas)

        self.sidebar_frame.bind(
            "<Configure>",
            lambda e: sidebar_canvas.configure(scrollregion=sidebar_canvas.bbox("all"))
        )

        sidebar_canvas.create_window((0, 0), window=self.sidebar_frame, anchor="nw")
        sidebar_canvas.configure(yscrollcommand=sidebar_scrollbar.set)

        sidebar_scrollbar.pack(side="right", fill="y")
        sidebar_canvas.pack(side="left", fill="both", expand=True)

        # Right side: content area
        self.content_frame = ttk.Frame(main_container)
        self.content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Create tabs (this will add buttons to sidebar and create hidden frames)
        self.create_geocoding_tab()
        self.create_reverse_geocode_tab()
        self.create_download_tab()
        self.create_csv_to_excel_tab()
        self.create_encoding_converter_tab()
        self.create_add_cc_groups_tab()
        self.create_merge_cc_groups_tab()
        self.create_expand_mainland_tab()
        self.create_unique_names_tab()
        self.create_province_mapper_tab()
        self.create_fill_missing_tab()
        self.create_resample_rules_tab()
        self.create_diagnostic_tab()
        self.create_aggregate_facilities_tab()

        # Show first tab by default
        if self.tabs:
            first_tab = list(self.tabs.keys())[0]
            self.show_tab(first_tab)

        # Output console at bottom
        self.create_output_console()

        # Status bar
        self.status_var = tk.StringVar(value="Ready - Select a tool and click Run")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def create_geocoding_tab(self):
        """Geocoding utility tab."""
        tab = ttk.Frame(self.content_frame)
        main_frame = self.create_scrollable_frame(tab)
        self.add_tab("Geocoding", "📍", tab)

        ttk.Label(main_frame, text="Add geographic coordinates (x, y) to CSV files",
                 font=("Helvetica", 10, "italic")).pack(pady=5, padx=10)

        # Input settings
        frame = ttk.LabelFrame(main_frame, text="Input Settings", padding="10")
        frame.pack(fill=tk.X, pady=5, padx=10)

        ttk.Label(frame, text="CSV Folder:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.geo_folder_var = tk.StringVar(value="data/2024")
        ttk.Entry(frame, textvariable=self.geo_folder_var, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(frame, text="Browse...", command=lambda: self.browse_folder(self.geo_folder_var)).grid(row=0, column=2)

        ttk.Label(frame, text="Address Column:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.geo_address_var = tk.StringVar(value="address")
        ttk.Entry(frame, textvariable=self.geo_address_var, width=50).grid(row=1, column=1, padx=5)

        # Options
        opt_frame = ttk.LabelFrame(main_frame, text="Options", padding="10")
        opt_frame.pack(fill=tk.X, pady=5, padx=10)

        self.geo_overwrite_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(opt_frame, text="Overwrite existing", variable=self.geo_overwrite_var).pack(anchor=tk.W)

        ttk.Label(opt_frame, text="Jitter:").pack(anchor=tk.W)
        self.geo_jitter_var = tk.StringVar(value="none")
        ttk.Radiobutton(opt_frame, text="None", variable=self.geo_jitter_var, value="none").pack(anchor=tk.W)
        ttk.Radiobutton(opt_frame, text="Auto (prompt if needed)", variable=self.geo_jitter_var, value="auto").pack(anchor=tk.W)
        ttk.Radiobutton(opt_frame, text="1 km", variable=self.geo_jitter_var, value="1").pack(anchor=tk.W)
        ttk.Radiobutton(opt_frame, text="5 km", variable=self.geo_jitter_var, value="5").pack(anchor=tk.W)

        ttk.Button(main_frame, text="▶ Run Geocoding", command=self.run_geocoding).pack(pady=10)

    def create_reverse_geocode_tab(self):
        """Reverse geocoding utility tab."""
        tab = ttk.Frame(self.content_frame)
        main_frame = self.create_scrollable_frame(tab)
        self.add_tab("Reverse Geocode", "🔍", tab)

        ttk.Label(main_frame, text="Get region names from coordinates (country, province, city, etc.)",
                 font=("Helvetica", 10, "italic")).pack(pady=5)

        # File settings
        frame = ttk.LabelFrame(main_frame, text="Files", padding="10")
        frame.pack(fill=tk.X, pady=5, padx=10)

        ttk.Label(frame, text="Input File:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.revgeo_input_var = tk.StringVar(value="")
        ttk.Entry(frame, textvariable=self.revgeo_input_var, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(frame, text="Browse", command=lambda: self.browse_file(self.revgeo_input_var, [("CSV", "*.csv")])).grid(row=0, column=2)

        ttk.Label(frame, text="Output File:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.revgeo_output_var = tk.StringVar(value="")
        ttk.Entry(frame, textvariable=self.revgeo_output_var, width=50).grid(row=1, column=1, padx=5)
        ttk.Button(frame, text="Browse", command=lambda: self.browse_save_file(self.revgeo_output_var, [("CSV", "*.csv")])).grid(row=1, column=2)

        # Column settings
        col_frame = ttk.LabelFrame(main_frame, text="Coordinate Columns", padding="10")
        col_frame.pack(fill=tk.X, pady=5, padx=10)

        ttk.Label(col_frame, text="Longitude Column:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.revgeo_x_var = tk.StringVar(value="x")
        ttk.Entry(col_frame, textvariable=self.revgeo_x_var, width=20).grid(row=0, column=1, padx=5, sticky=tk.W)

        ttk.Label(col_frame, text="Latitude Column:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.revgeo_y_var = tk.StringVar(value="y")
        ttk.Entry(col_frame, textvariable=self.revgeo_y_var, width=20).grid(row=1, column=1, padx=5, sticky=tk.W)

        # Options
        opt_frame = ttk.LabelFrame(main_frame, text="Options", padding="10")
        opt_frame.pack(fill=tk.X, pady=5, padx=10)

        self.revgeo_overwrite_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(opt_frame, text="Overwrite existing region info", variable=self.revgeo_overwrite_var).pack(anchor=tk.W)

        ttk.Label(opt_frame, text="Language:").pack(anchor=tk.W, pady=(10, 0))
        self.revgeo_language_var = tk.StringVar(value="en")
        lang_frame = ttk.Frame(opt_frame)
        lang_frame.pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(lang_frame, text="English", variable=self.revgeo_language_var, value="en").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(lang_frame, text="한국어 (Korean)", variable=self.revgeo_language_var, value="ko").pack(side=tk.LEFT, padx=5)

        # Timeout setting
        timeout_frame = ttk.Frame(opt_frame)
        timeout_frame.pack(anchor=tk.W, pady=(10, 0))
        ttk.Label(timeout_frame, text="API Timeout (seconds):").pack(side=tk.LEFT)
        self.revgeo_timeout_var = tk.StringVar(value="1")
        timeout_entry = ttk.Entry(timeout_frame, textvariable=self.revgeo_timeout_var, width=5)
        timeout_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(timeout_frame, text="(increase if getting timeouts)", font=("Helvetica", 8), foreground="gray").pack(side=tk.LEFT)

        # Dry run option
        self.revgeo_dryrun_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(opt_frame, text="Dry run (test with first 10 rows only)", variable=self.revgeo_dryrun_var).pack(anchor=tk.W, pady=(5, 0))

        # Info about output
        info_frame = ttk.LabelFrame(main_frame, text="Output Columns Added", padding="10")
        info_frame.pack(fill=tk.X, pady=5, padx=10)

        info_text = """region_1: Province/State (e.g., Gangwon State, 강원도, Seoul, 서울특별시)
region_2: County/City/District (e.g., Taebaek-si, 평창군, Gangnam-gu, 양천구)"""
        ttk.Label(info_frame, text=info_text, font=("Courier", 9), foreground="gray", justify=tk.LEFT).pack(anchor=tk.W)

        ttk.Button(main_frame, text="▶ Run Reverse Geocoding", command=self.run_reverse_geocode).pack(pady=10)

    def create_download_tab(self):
        """Network download utility tab."""
        tab = ttk.Frame(self.content_frame)
        main_frame = self.create_scrollable_frame(tab)
        self.add_tab("Network Download", "🌍", tab)

        ttk.Label(main_frame, text="Download power network data from OpenStreetMap",
                 font=("Helvetica", 10, "italic")).pack(pady=5)

        # Country
        frame = ttk.LabelFrame(main_frame, text="Country Settings", padding="10")
        frame.pack(fill=tk.X, pady=5, padx=10)

        ttk.Label(frame, text="Country Code:").grid(row=0, column=0, sticky=tk.W)
        self.dl_country_var = tk.StringVar(value="KR")
        ttk.Entry(frame, textvariable=self.dl_country_var, width=10).grid(row=0, column=1, padx=5)

        # Quick buttons
        quick_frame = ttk.Frame(frame)
        quick_frame.grid(row=1, column=0, columnspan=3, pady=5)
        for name, code in [("KR", "KR"), ("DE", "DE"), ("US", "US"), ("GB", "GB"), ("FR", "FR")]:
            ttk.Button(quick_frame, text=name, width=5,
                      command=lambda c=code: self.dl_country_var.set(c)).pack(side=tk.LEFT, padx=2)

        # Options
        opt_frame = ttk.LabelFrame(main_frame, text="Options", padding="10")
        opt_frame.pack(fill=tk.X, pady=5, padx=10)

        ttk.Label(opt_frame, text="Min Voltage (kV):").grid(row=0, column=0, sticky=tk.W)
        self.dl_voltage_var = tk.StringVar(value="220")
        ttk.Combobox(opt_frame, textvariable=self.dl_voltage_var, values=["110", "220", "380"], width=10).grid(row=0, column=1, padx=5)

        ttk.Label(opt_frame, text="Output Dir:").grid(row=1, column=0, sticky=tk.W)
        self.dl_output_var = tk.StringVar(value="./networks")
        ttk.Entry(opt_frame, textvariable=self.dl_output_var, width=40).grid(row=1, column=1, padx=5)

        ttk.Button(main_frame, text="▶ Download Network", command=self.run_download).pack(pady=10)

    def create_csv_to_excel_tab(self):
        """CSV to Excel converter tab."""
        tab = ttk.Frame(self.content_frame)
        main_frame = self.create_scrollable_frame(tab)
        self.add_tab("CSV→Excel", "📊", tab)

        ttk.Label(main_frame, text="Convert CSV files to Excel format",
                 font=("Helvetica", 10, "italic")).pack(pady=5)

        frame = ttk.LabelFrame(main_frame, text="Files", padding="10")
        frame.pack(fill=tk.X, pady=5, padx=10)

        ttk.Label(frame, text="Input CSV / Folder:").grid(row=0, column=0, sticky=tk.W)
        self.csv_input_var = tk.StringVar(value="")
        ttk.Entry(frame, textvariable=self.csv_input_var, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(frame, text="File", command=lambda: self.browse_file(self.csv_input_var, [("CSV", "*.csv")])).grid(row=0, column=2)
        ttk.Button(frame, text="Folder", command=lambda: self.browse_folder(self.csv_input_var)).grid(row=0, column=3)

        ttk.Label(frame, text="Output (optional):").grid(row=1, column=0, sticky=tk.W)
        self.csv_output_var = tk.StringVar(value="")
        ttk.Entry(frame, textvariable=self.csv_output_var, width=50).grid(row=1, column=1, padx=5)
        ttk.Label(frame, text="(Leave empty for auto)").grid(row=1, column=2, columnspan=2, sticky=tk.W)

        ttk.Button(main_frame, text="▶ Convert to Excel", command=self.run_csv_to_excel).pack(pady=10)

    def create_encoding_converter_tab(self):
        """Encoding converter tab."""
        tab = ttk.Frame(self.content_frame)
        main_frame = self.create_scrollable_frame(tab)
        self.add_tab("Encoding", "🔤", tab)

        ttk.Label(main_frame, text="Convert file encoding from EUC-KR/CP949 to UTF-8",
                 font=("Helvetica", 10, "italic")).pack(pady=5)

        frame = ttk.LabelFrame(main_frame, text="Files", padding="10")
        frame.pack(fill=tk.X, pady=5, padx=10)

        ttk.Label(frame, text="Input File / Folder:").grid(row=0, column=0, sticky=tk.W)
        self.enc_input_var = tk.StringVar(value="")
        ttk.Entry(frame, textvariable=self.enc_input_var, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(frame, text="File", command=lambda: self.browse_file(self.enc_input_var)).grid(row=0, column=2)
        ttk.Button(frame, text="Folder", command=lambda: self.browse_folder(self.enc_input_var)).grid(row=0, column=3)

        opt_frame = ttk.LabelFrame(main_frame, text="Options", padding="10")
        opt_frame.pack(fill=tk.X, pady=5, padx=10)

        self.enc_backup_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(opt_frame, text="Create backup (.bak)", variable=self.enc_backup_var).pack(anchor=tk.W)

        ttk.Button(main_frame, text="▶ Convert Encoding", command=self.run_encoding_converter).pack(pady=10)

    def create_add_cc_groups_tab(self):
        """Add CC groups tab."""
        tab = ttk.Frame(self.content_frame)
        main_frame = self.create_scrollable_frame(tab)
        self.add_tab("Add CC Groups", "⚡", tab)

        ttk.Label(main_frame, text="Add combined cycle (CC) group names to generators.csv",
                 font=("Helvetica", 10, "italic")).pack(pady=5)

        frame = ttk.LabelFrame(main_frame, text="Files", padding="10")
        frame.pack(fill=tk.X, pady=5, padx=10)

        ttk.Label(frame, text="Input File:").grid(row=0, column=0, sticky=tk.W)
        self.addcc_input_var = tk.StringVar(value="data/2024/generators.csv")
        ttk.Entry(frame, textvariable=self.addcc_input_var, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(frame, text="Browse", command=lambda: self.browse_file(self.addcc_input_var, [("CSV", "*.csv")])).grid(row=0, column=2)

        opt_frame = ttk.LabelFrame(main_frame, text="Options", padding="10")
        opt_frame.pack(fill=tk.X, pady=5, padx=10)

        self.addcc_backup_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(opt_frame, text="Create backup", variable=self.addcc_backup_var).pack(anchor=tk.W)

        ttk.Button(main_frame, text="▶ Add CC Groups", command=self.run_add_cc_groups).pack(pady=10)

    def create_merge_cc_groups_tab(self):
        """Merge CC groups tab."""
        tab = ttk.Frame(self.content_frame)
        main_frame = self.create_scrollable_frame(tab)
        self.add_tab("Merge CC", "🔗", tab)

        ttk.Label(main_frame, text="Merge CC generators by group (combine GT + ST into single unit)",
                 font=("Helvetica", 10, "italic")).pack(pady=5)

        frame = ttk.LabelFrame(main_frame, text="Files", padding="10")
        frame.pack(fill=tk.X, pady=5, padx=10)

        ttk.Label(frame, text="Input File:").grid(row=0, column=0, sticky=tk.W)
        self.mergecc_input_var = tk.StringVar(value="data/2024/generators.csv")
        ttk.Entry(frame, textvariable=self.mergecc_input_var, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(frame, text="Browse", command=lambda: self.browse_file(self.mergecc_input_var, [("CSV", "*.csv")])).grid(row=0, column=2)

        ttk.Label(frame, text="Output File:").grid(row=1, column=0, sticky=tk.W)
        self.mergecc_output_var = tk.StringVar(value="data/2024/generators_merged.csv")
        ttk.Entry(frame, textvariable=self.mergecc_output_var, width=50).grid(row=1, column=1, padx=5)

        ttk.Button(main_frame, text="▶ Merge CC Groups", command=self.run_merge_cc_groups).pack(pady=10)

    def create_expand_mainland_tab(self):
        """Expand mainland data tab."""
        tab = ttk.Frame(self.content_frame)
        main_frame = self.create_scrollable_frame(tab)
        self.add_tab("Expand Mainland", "🗺️", tab)

        ttk.Label(main_frame, text="Expand mainland (육지) data to individual provinces",
                 font=("Helvetica", 10, "italic")).pack(pady=5)

        frame = ttk.LabelFrame(main_frame, text="Files", padding="10")
        frame.pack(fill=tk.X, pady=5, padx=10)

        ttk.Label(frame, text="Input File:").grid(row=0, column=0, sticky=tk.W)
        self.expand_input_var = tk.StringVar(value="")
        ttk.Entry(frame, textvariable=self.expand_input_var, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(frame, text="Browse", command=lambda: self.browse_file(self.expand_input_var, [("CSV", "*.csv")])).grid(row=0, column=2)

        ttk.Label(frame, text="Output File:").grid(row=1, column=0, sticky=tk.W)
        self.expand_output_var = tk.StringVar(value="")
        ttk.Entry(frame, textvariable=self.expand_output_var, width=50).grid(row=1, column=1, padx=5)

        ttk.Button(main_frame, text="▶ Expand Mainland Data", command=self.run_expand_mainland).pack(pady=10)

    def create_unique_names_tab(self):
        """Make names unique tab."""
        tab = ttk.Frame(self.content_frame)
        main_frame = self.create_scrollable_frame(tab)
        self.add_tab("Unique Names", "🏷️", tab)

        ttk.Label(main_frame, text="Make 'name' column unique by adding _1, _2 suffixes",
                 font=("Helvetica", 10, "italic")).pack(pady=5)

        frame = ttk.LabelFrame(main_frame, text="Files", padding="10")
        frame.pack(fill=tk.X, pady=5, padx=10)

        ttk.Label(frame, text="Input File:").grid(row=0, column=0, sticky=tk.W)
        self.unique_input_var = tk.StringVar(value="")
        ttk.Entry(frame, textvariable=self.unique_input_var, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(frame, text="Browse", command=lambda: self.browse_file(self.unique_input_var, [("CSV", "*.csv")])).grid(row=0, column=2)

        opt_frame = ttk.LabelFrame(main_frame, text="Options", padding="10")
        opt_frame.pack(fill=tk.X, pady=5, padx=10)

        self.unique_backup_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(opt_frame, text="Create backup", variable=self.unique_backup_var).pack(anchor=tk.W)

        self.unique_dryrun_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(opt_frame, text="Dry run (preview only)", variable=self.unique_dryrun_var).pack(anchor=tk.W)

        ttk.Button(main_frame, text="▶ Make Names Unique", command=self.run_unique_names).pack(pady=10)

    def create_output_console(self):
        """Create output console."""
        console_frame = ttk.LabelFrame(self.root, text="Output Console", padding="5")
        console_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Console with dark theme
        self.console = scrolledtext.ScrolledText(console_frame, height=10,
                                                 wrap=tk.WORD, font=("Courier", 9),
                                                 bg="#1e1e1e", fg="#d4d4d4")
        self.console.pack(fill=tk.BOTH, expand=True)

        # Buttons
        btn_frame = ttk.Frame(console_frame)
        btn_frame.pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="Clear Console", command=self.clear_output).pack(side=tk.LEFT, padx=2)

        # Welcome
        self.log("="*60)
        self.log("PyPSA Utilities - All Tools")
        self.log("="*60)
        self.log(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log("Select a tool from the tabs above and click Run\n")

    def log(self, message):
        """Log message."""
        self.console.insert(tk.END, f"{message}\n")
        self.console.see(tk.END)

    def clear_output(self):
        """Clear console."""
        self.console.delete(1.0, tk.END)
        self.log(f"Console cleared at {datetime.now().strftime('%H:%M:%S')}\n")

    def browse_folder(self, var):
        """Browse for folder."""
        folder = filedialog.askdirectory()
        if folder:
            var.set(folder)

    def browse_file(self, var, filetypes=None):
        """Browse for file."""
        if filetypes is None:
            filetypes = [("All files", "*.*")]
        file = filedialog.askopenfilename(filetypes=filetypes)
        if file:
            var.set(file)

    def browse_save_file(self, var, filetypes=None):
        """Browse for save file."""
        if filetypes is None:
            filetypes = [("All files", "*.*")]
        file = filedialog.asksaveasfilename(filetypes=filetypes, defaultextension=".csv")
        if file:
            var.set(file)

    def run_in_thread(self, func):
        """Run function in background thread."""
        thread = threading.Thread(target=func, daemon=True)
        thread.start()

    def run_geocoding(self):
        """Run geocoding."""
        folder = self.geo_folder_var.get()
        if not folder or not Path(folder).exists():
            messagebox.showerror("Error", f"Folder not found: {folder}")
            return

        self.status_var.set("Running geocoding...")
        self.log("\n" + "="*60)
        self.log("GEOCODING")
        self.log("="*60)

        def task():
            try:
                from geocode_addresses import AddressGeocoder
                sys.stdout = RedirectText(self.console)
                sys.stderr = RedirectText(self.console)

                jitter = self.geo_jitter_var.get()
                if jitter == "none":
                    jitter = None
                elif jitter not in ["auto"]:
                    jitter = float(jitter)

                # Use cache in parent directory
                cache_path = Path(__file__).parent.parent / "cache" / "geocode_cache.json"
                geocoder = AddressGeocoder(cache_file=str(cache_path))
                geocoder.process_folder(
                    folder_path=folder,
                    address_column=self.geo_address_var.get(),
                    overwrite=self.geo_overwrite_var.get(),
                    jitter=jitter
                )
                self.log("\n✓ Geocoding completed!")
                self.status_var.set("Geocoding completed")
            except Exception as e:
                self.log(f"\n✗ Error: {e}")
                self.status_var.set("Geocoding failed")
            finally:
                sys.stdout = self.original_stdout
                sys.stderr = self.original_stderr

        self.run_in_thread(task)

    def run_download(self):
        """Run network download."""
        country = self.dl_country_var.get().strip().upper()
        if not country or len(country) != 2:
            messagebox.showerror("Error", "Enter valid 2-letter country code")
            return

        self.status_var.set("Downloading network...")
        self.log("\n" + "="*60)
        self.log("NETWORK DOWNLOAD")
        self.log("="*60)

        def task():
            try:
                from libs.pypsa_earth_backend import create_pypsa_network_with_earth, cleanup_temp_files
                sys.stdout = RedirectText(self.console)
                sys.stderr = RedirectText(self.console)

                network_path = create_pypsa_network_with_earth(
                    country_code=country,
                    voltage_min=int(self.dl_voltage_var.get()),
                    output_dir=self.dl_output_var.get()
                )
                self.log(f"\n✓ Network saved to: {network_path}")
                cleanup_temp_files()
                self.status_var.set("Download completed")
            except Exception as e:
                self.log(f"\n✗ Error: {e}")
                self.status_var.set("Download failed")
            finally:
                sys.stdout = self.original_stdout
                sys.stderr = self.original_stderr

        self.run_in_thread(task)

    def run_csv_to_excel(self):
        """Run CSV to Excel."""
        input_path = self.csv_input_var.get()
        if not input_path:
            messagebox.showerror("Error", "Select input file or folder")
            return

        self.status_var.set("Converting to Excel...")
        self.log("\n" + "="*60)
        self.log("CSV TO EXCEL")
        self.log("="*60)

        def task():
            try:
                from csv_to_excel import csv_to_excel, convert_directory
                sys.stdout = RedirectText(self.console)
                sys.stderr = RedirectText(self.console)

                input_p = Path(input_path)
                output_path = self.csv_output_var.get() if self.csv_output_var.get() else None

                if input_p.is_file():
                    csv_to_excel(input_path, output_path)
                else:
                    convert_directory(input_path, output_path)

                self.log("\n✓ Conversion completed!")
                self.status_var.set("Conversion completed")
            except Exception as e:
                self.log(f"\n✗ Error: {e}")
                self.status_var.set("Conversion failed")
            finally:
                sys.stdout = self.original_stdout
                sys.stderr = self.original_stderr

        self.run_in_thread(task)

    def run_encoding_converter(self):
        """Run encoding converter."""
        input_path = self.enc_input_var.get()
        if not input_path:
            messagebox.showerror("Error", "Select input file or folder")
            return

        self.status_var.set("Converting encoding...")
        self.log("\n" + "="*60)
        self.log("ENCODING CONVERTER")
        self.log("="*60)

        def task():
            try:
                from encodingconverter import convert_euckr_to_utf8, convert_folder
                sys.stdout = RedirectText(self.console)
                sys.stderr = RedirectText(self.console)

                input_p = Path(input_path)
                backup = self.enc_backup_var.get()

                if input_p.is_file():
                    convert_euckr_to_utf8(input_path, backup)
                else:
                    convert_folder(input_path, backup)

                self.log("\n✓ Encoding conversion completed!")
                self.status_var.set("Encoding conversion completed")
            except Exception as e:
                self.log(f"\n✗ Error: {e}")
                self.status_var.set("Encoding conversion failed")
            finally:
                sys.stdout = self.original_stdout
                sys.stderr = self.original_stderr

        self.run_in_thread(task)

    def run_add_cc_groups(self):
        """Run add CC groups."""
        input_file = self.addcc_input_var.get()
        if not input_file or not Path(input_file).exists():
            messagebox.showerror("Error", f"File not found: {input_file}")
            return

        self.status_var.set("Adding CC groups...")
        self.log("\n" + "="*60)
        self.log("ADD CC GROUPS")
        self.log("="*60)

        def task():
            try:
                from add_cc_groups import read_csv_safely, add_cc_groups
                sys.stdout = RedirectText(self.console)
                sys.stderr = RedirectText(self.console)

                # Read CSV
                df, encoding = read_csv_safely(Path(input_file), None, False)

                # Backup if requested
                if self.addcc_backup_var.get():
                    import shutil
                    shutil.copy(input_file, f"{input_file}.bak")
                    self.log(f"Created backup: {input_file}.bak")

                # Add CC groups
                df = add_cc_groups(df)

                # Save
                df.to_csv(input_file, index=False, encoding='utf-8-sig')
                self.log(f"Saved: {input_file}")

                self.log("\n✓ CC groups added!")
                self.status_var.set("CC groups added")
            except Exception as e:
                self.log(f"\n✗ Error: {e}")
                self.status_var.set("Add CC groups failed")
            finally:
                sys.stdout = self.original_stdout
                sys.stderr = self.original_stderr

        self.run_in_thread(task)

    def run_merge_cc_groups(self):
        """Run merge CC groups."""
        input_file = self.mergecc_input_var.get()
        output_file = self.mergecc_output_var.get()
        if not input_file or not Path(input_file).exists():
            messagebox.showerror("Error", f"File not found: {input_file}")
            return

        self.status_var.set("Merging CC groups...")
        self.log("\n" + "="*60)
        self.log("MERGE CC GROUPS")
        self.log("="*60)

        def task():
            try:
                from merge_cc_groups import read_csv_safely, merge_cc_by_group
                sys.stdout = RedirectText(self.console)
                sys.stderr = RedirectText(self.console)

                # Read CSV
                df, encoding = read_csv_safely(Path(input_file), None, False)

                # Merge CC groups
                df = merge_cc_by_group(df)

                # Save
                df.to_csv(output_file, index=False, encoding='utf-8-sig')
                self.log(f"Saved: {output_file}")

                self.log("\n✓ CC groups merged!")
                self.status_var.set("CC groups merged")
            except Exception as e:
                self.log(f"\n✗ Error: {e}")
                self.status_var.set("Merge CC groups failed")
            finally:
                sys.stdout = self.original_stdout
                sys.stderr = self.original_stderr

        self.run_in_thread(task)

    def run_expand_mainland(self):
        """Run expand mainland."""
        input_file = self.expand_input_var.get()
        output_file = self.expand_output_var.get()
        if not input_file or not Path(input_file).exists():
            messagebox.showerror("Error", f"File not found: {input_file}")
            return
        if not output_file:
            messagebox.showerror("Error", "Specify output file")
            return

        self.status_var.set("Expanding mainland data...")
        self.log("\n" + "="*60)
        self.log("EXPAND MAINLAND DATA")
        self.log("="*60)

        def task():
            try:
                from expand_mainland_data import read_csv_safely, expand_mainland_to_provinces
                sys.stdout = RedirectText(self.console)
                sys.stderr = RedirectText(self.console)

                # Read CSV
                df, encoding = read_csv_safely(Path(input_file), None, False)

                # Expand mainland
                df = expand_mainland_to_provinces(df)

                # Save
                df.to_csv(output_file, index=False, encoding='utf-8-sig')
                self.log(f"Saved: {output_file}")

                self.log("\n✓ Mainland data expanded!")
                self.status_var.set("Mainland expansion completed")
            except Exception as e:
                self.log(f"\n✗ Error: {e}")
                self.status_var.set("Mainland expansion failed")
            finally:
                sys.stdout = self.original_stdout
                sys.stderr = self.original_stderr

        self.run_in_thread(task)

    def run_unique_names(self):
        """Run unique names."""
        input_file = self.unique_input_var.get()
        if not input_file or not Path(input_file).exists():
            messagebox.showerror("Error", f"File not found: {input_file}")
            return

        self.status_var.set("Making names unique...")
        self.log("\n" + "="*60)
        self.log("MAKE NAMES UNIQUE")
        self.log("="*60)

        def task():
            try:
                from uniquename import make_csv_names_unique
                sys.stdout = RedirectText(self.console)
                sys.stderr = RedirectText(self.console)

                make_csv_names_unique(
                    input_file,
                    dry_run=self.unique_dryrun_var.get(),
                    backup=self.unique_backup_var.get()
                )

                self.log("\n✓ Names made unique!")
                self.status_var.set("Names made unique")
            except Exception as e:
                self.log(f"\n✗ Error: {e}")
                self.status_var.set("Make names unique failed")
            finally:
                sys.stdout = self.original_stdout
                sys.stderr = self.original_stderr

        self.run_in_thread(task)

    def create_province_mapper_tab(self):
        """Province name mapper tab."""
        tab = ttk.Frame(self.content_frame)
        main_frame = self.create_scrollable_frame(tab)
        self.add_tab("Province Mapper", "🗺️", tab)

        ttk.Label(main_frame, text="Map province names to standardized official names",
                 font=("Helvetica", 10, "italic")).pack(pady=5)

        # Mapping file
        mapping_frame = ttk.LabelFrame(main_frame, text="Mapping File", padding="10")
        mapping_frame.pack(fill=tk.X, pady=5, padx=10)

        ttk.Label(mapping_frame, text="Province Mapping CSV:").grid(row=0, column=0, sticky=tk.W)
        self.province_mapping_var = tk.StringVar(value="data/others/province_mapping.csv")
        ttk.Entry(mapping_frame, textvariable=self.province_mapping_var, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(mapping_frame, text="Browse", command=lambda: self.browse_file(self.province_mapping_var, [("CSV", "*.csv")])).grid(row=0, column=2)

        # Input files
        input_frame = ttk.LabelFrame(main_frame, text="Input Files", padding="10")
        input_frame.pack(fill=tk.X, pady=5, padx=10)

        ttk.Label(input_frame, text="Input File / Folder:").grid(row=0, column=0, sticky=tk.W)
        self.province_input_var = tk.StringVar(value="")
        ttk.Entry(input_frame, textvariable=self.province_input_var, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(input_frame, text="File", command=lambda: self.browse_file(self.province_input_var, [("CSV", "*.csv")])).grid(row=0, column=2)
        ttk.Button(input_frame, text="Folder", command=lambda: self.browse_folder(self.province_input_var)).grid(row=0, column=3)

        # Options
        opt_frame = ttk.LabelFrame(main_frame, text="Options", padding="10")
        opt_frame.pack(fill=tk.X, pady=5, padx=10)

        ttk.Label(opt_frame, text="Column Name:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.province_column_var = tk.StringVar(value="province")
        ttk.Entry(opt_frame, textvariable=self.province_column_var, width=20).grid(row=0, column=1, padx=5, sticky=tk.W)

        ttk.Label(opt_frame, text="Mapping Direction:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.province_direction_var = tk.StringVar(value="to_short")
        direction_frame = ttk.Frame(opt_frame)
        direction_frame.grid(row=1, column=1, sticky=tk.W, pady=2)
        ttk.Radiobutton(direction_frame, text="To Short (강원특별자치도 → 강원)",
                       variable=self.province_direction_var, value="to_short").pack(anchor=tk.W)
        ttk.Radiobutton(direction_frame, text="To Official (강원 → 강원특별자치도)",
                       variable=self.province_direction_var, value="to_official").pack(anchor=tk.W)

        self.province_backup_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(opt_frame, text="Create backup (.bak)", variable=self.province_backup_var).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=2)

        self.province_recursive_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(opt_frame, text="Process folders recursively", variable=self.province_recursive_var).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=2)

        # Info
        info_frame = ttk.LabelFrame(main_frame, text="Info", padding="10")
        info_frame.pack(fill=tk.X, pady=5, padx=10)

        info_text = """This tool maps province names to their official standardized names.
Example: Maps both "강원특별자치도" and other variants to "강원" (short form).
Any unmapped province names will be reported for manual addition to mapping file."""
        ttk.Label(info_frame, text=info_text, font=("Helvetica", 9), foreground="gray", justify=tk.LEFT, wraplength=800).pack(anchor=tk.W)

        ttk.Button(main_frame, text="▶ Map Province Names", command=self.run_province_mapper).pack(pady=10)

    def run_province_mapper(self):
        """Run province name mapper."""
        mapping_file = self.province_mapping_var.get()
        input_path = self.province_input_var.get()

        if not mapping_file or not Path(mapping_file).exists():
            messagebox.showerror("Error", f"Mapping file not found: {mapping_file}")
            return
        if not input_path or not Path(input_path).exists():
            messagebox.showerror("Error", f"Input path not found: {input_path}")
            return

        self.status_var.set("Mapping province names...")
        self.log("\n" + "="*60)
        self.log("PROVINCE NAME MAPPER")
        self.log("="*60)

        def task():
            try:
                from province_mapper import load_province_mapping, process_file, process_directory
                sys.stdout = RedirectText(self.console)
                sys.stderr = RedirectText(self.console)

                # Load mapping
                direction = self.province_direction_var.get()
                mapping, _ = load_province_mapping(Path(mapping_file), direction, None, False)

                input_p = Path(input_path)
                column = self.province_column_var.get()
                backup = self.province_backup_var.get()

                if input_p.is_file():
                    # Single file
                    changes, unmapped = process_file(
                        input_p, mapping, column, None,
                        backup, "utf-8-sig", None, False, direction
                    )
                    self.log(f"\nTotal changes: {changes}")
                    if unmapped:
                        self.log(f"Unmapped names: {len(unmapped)}")
                else:
                    # Directory
                    recursive = self.province_recursive_var.get()
                    files_processed, total_changes, all_unmapped = process_directory(
                        input_p, mapping, column, recursive,
                        backup, "utf-8-sig", None, False, direction
                    )
                    self.log(f"\nFiles processed: {files_processed}")
                    self.log(f"Total changes: {total_changes}")
                    if all_unmapped:
                        self.log(f"Unmapped names: {len(all_unmapped)}")

                self.log("\n✓ Province name mapping completed!")
                self.status_var.set("Province mapping completed")
            except Exception as e:
                self.log(f"\n✗ Error: {e}")
                import traceback
                self.log(traceback.format_exc())
                self.status_var.set("Province mapping failed")
            finally:
                sys.stdout = self.original_stdout
                sys.stderr = self.original_stderr

        self.run_in_thread(task)

    def run_reverse_geocode(self):
        """Run reverse geocoding."""
        input_file = self.revgeo_input_var.get()
        output_file = self.revgeo_output_var.get()

        if not input_file or not Path(input_file).exists():
            messagebox.showerror("Error", f"Input file not found: {input_file}")
            return
        if not output_file:
            messagebox.showerror("Error", "Please specify output file")
            return

        self.status_var.set("Running reverse geocoding...")
        self.log("\n" + "="*60)
        self.log("REVERSE GEOCODING")
        self.log("="*60)

        def task():
            try:
                from reverse_geocode import ReverseGeocoder
                sys.stdout = RedirectText(self.console)
                sys.stderr = RedirectText(self.console)

                # Use cache in parent directory
                cache_path = Path(__file__).parent.parent / "cache" / "reverse_geocode_cache.json"
                language = self.revgeo_language_var.get()

                # Get timeout value
                try:
                    timeout = int(self.revgeo_timeout_var.get())
                except ValueError:
                    timeout = 1

                # Load province mapping
                province_mapping = None
                mapping_path = Path(__file__).parent.parent / "data" / "others" / "province_mapping.csv"
                if mapping_path.exists():
                    try:
                        self.log(f"Loading province mapping from: {mapping_path.name}")
                        import csv
                        mapping_dict = {}
                        with open(mapping_path, 'r', encoding='utf-8-sig') as f:
                            reader = csv.DictReader(f)
                            for row in reader:
                                short = row['short'].strip()
                                official = row['official'].strip()
                                # Map both official -> short and short -> short
                                mapping_dict[official] = short
                                mapping_dict[short] = short
                        province_mapping = mapping_dict
                        self.log(f"  Loaded {len(mapping_dict)} province mapping entries")
                    except Exception as e:
                        self.log(f"  Warning: Could not load province mapping: {e}")

                geocoder = ReverseGeocoder(cache_file=str(cache_path), language=language, timeout=timeout, province_mapping=province_mapping)
                geocoder.process_csv(
                    input_file=input_file,
                    output_file=output_file,
                    x_column=self.revgeo_x_var.get(),
                    y_column=self.revgeo_y_var.get(),
                    overwrite=self.revgeo_overwrite_var.get(),
                    dry_run=self.revgeo_dryrun_var.get()
                )

                self.log("\n✓ Reverse geocoding completed!")
                self.status_var.set("Reverse geocoding completed")
            except Exception as e:
                self.log(f"\n✗ Error: {e}")
                import traceback
                self.log(traceback.format_exc())
                self.status_var.set("Reverse geocoding failed")
            finally:
                sys.stdout = self.original_stdout
                sys.stderr = self.original_stderr

        self.run_in_thread(task)

    def create_fill_missing_tab(self):
        """Fill missing values utility tab."""
        tab = ttk.Frame(self.content_frame)
        main_frame = self.create_scrollable_frame(tab)
        self.add_tab("Fill Missing", "📊", tab)

        ttk.Label(main_frame, text="Fill missing values in CSV columns using intelligent imputation",
                 font=("Helvetica", 10, "italic")).pack(pady=5)

        # Files
        file_frame = ttk.LabelFrame(main_frame, text="Files", padding="10")
        file_frame.pack(fill=tk.X, pady=5, padx=10)

        ttk.Label(file_frame, text="Input File:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.fillmiss_input_var = tk.StringVar(value="data/Singlenode2024/generators.csv")
        ttk.Entry(file_frame, textvariable=self.fillmiss_input_var, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(file_frame, text="Browse", command=lambda: self.browse_file(self.fillmiss_input_var, [("CSV", "*.csv")])).grid(row=0, column=2)

        ttk.Label(file_frame, text="Output File:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.fillmiss_output_var = tk.StringVar(value="")
        ttk.Entry(file_frame, textvariable=self.fillmiss_output_var, width=50).grid(row=1, column=1, padx=5)
        ttk.Label(file_frame, text="(Leave empty to overwrite input)", font=("Helvetica", 8), foreground="gray").grid(row=1, column=2, sticky=tk.W)

        # Column settings
        col_frame = ttk.LabelFrame(main_frame, text="Column Settings", padding="10")
        col_frame.pack(fill=tk.X, pady=5, padx=10)

        ttk.Label(col_frame, text="Target Column (to fill):").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.fillmiss_target_var = tk.StringVar(value="capital_cost")
        ttk.Entry(col_frame, textvariable=self.fillmiss_target_var, width=30).grid(row=0, column=1, padx=5, sticky=tk.W)

        ttk.Label(col_frame, text="Grouping Columns:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.fillmiss_groups_var = tk.StringVar(value="build_year,type,carrier")
        ttk.Entry(col_frame, textvariable=self.fillmiss_groups_var, width=30).grid(row=1, column=1, padx=5, sticky=tk.W)
        ttk.Label(col_frame, text="(comma-separated)", font=("Helvetica", 8), foreground="gray").grid(row=1, column=2, sticky=tk.W)

        # Method
        method_frame = ttk.LabelFrame(main_frame, text="Imputation Method", padding="10")
        method_frame.pack(fill=tk.X, pady=5, padx=10)

        self.fillmiss_method_var = tk.StringVar(value="regression")

        methods = [
            ("regression", "Regression (predicts based on grouping variables)"),
            ("group_mean", "Group Mean (simple, fast, robust)"),
            ("group_median", "Group Median (robust to outliers)"),
            ("recent_mean", "Recent Mean (mean of values from nearby years)"),
            ("recent_median", "Recent Median (median of values from nearby years)"),
            ("forward_fill", "Forward Fill (propagate last known value)"),
            ("backward_fill", "Backward Fill (propagate next known value)")
        ]

        for i, (value, label) in enumerate(methods):
            ttk.Radiobutton(method_frame, text=label, variable=self.fillmiss_method_var, value=value).grid(
                row=i, column=0, sticky=tk.W, pady=1, padx=10
            )

        # Time window options (for recent_mean/recent_median)
        time_window_frame = ttk.Frame(method_frame)
        time_window_frame.grid(row=len(methods), column=0, sticky=tk.W, pady=5, padx=30)

        ttk.Label(time_window_frame, text="Time Window (years):").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.fillmiss_time_window_var = tk.StringVar(value="10")
        ttk.Entry(time_window_frame, textvariable=self.fillmiss_time_window_var, width=10).grid(row=0, column=1, sticky=tk.W)
        ttk.Label(time_window_frame, text="(e.g., 10 = use 1977-5 to 1977+5 for year 1977)", font=("Helvetica", 8),
                 foreground="gray").grid(row=0, column=2, sticky=tk.W, padx=(5, 0))

        ttk.Label(time_window_frame, text="Year Column:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.fillmiss_year_column_var = tk.StringVar(value="build_year")
        ttk.Entry(time_window_frame, textvariable=self.fillmiss_year_column_var, width=20).grid(row=1, column=1, sticky=tk.W, pady=(5, 0))
        ttk.Label(time_window_frame, text="(auto-detect if empty)", font=("Helvetica", 8),
                 foreground="gray").grid(row=1, column=2, sticky=tk.W, padx=(5, 0), pady=(5, 0))

        ttk.Label(time_window_frame, text="Exclude Outliers:").grid(row=2, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.fillmiss_exclude_outliers_var = tk.StringVar(value="0")
        ttk.Entry(time_window_frame, textvariable=self.fillmiss_exclude_outliers_var, width=10).grid(row=2, column=1, sticky=tk.W, pady=(5, 0))
        ttk.Label(time_window_frame, text="(e.g., 1 = exclude 1 min and 1 max)", font=("Helvetica", 8),
                 foreground="gray").grid(row=2, column=2, sticky=tk.W, padx=(5, 0), pady=(5, 0))

        # Options
        opt_frame = ttk.LabelFrame(main_frame, text="Options", padding="10")
        opt_frame.pack(fill=tk.X, pady=5, padx=10)

        self.fillmiss_nonneg_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(opt_frame, text="Non-negative constraint (ensure no negative values)",
                       variable=self.fillmiss_nonneg_var).pack(anchor=tk.W, pady=2)

        self.fillmiss_backup_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(opt_frame, text="Create backup file",
                       variable=self.fillmiss_backup_var).pack(anchor=tk.W, pady=2)

        # Info
        info_frame = ttk.LabelFrame(main_frame, text="How It Works", padding="10")
        info_frame.pack(fill=tk.X, pady=5, padx=10)

        info_text = """Example: Fill missing capital_cost using (build_year, type, carrier)
• Regression: Predicts values based on patterns in the data
• Group Mean/Median: Uses average of similar groups
• Recent Mean/Median: Uses values from nearby years (e.g., 10 years = year-5 to year+5)
• Non-negative: Ensures physical constraints (e.g., costs can't be negative)
• Outlier exclusion: Remove extreme values before calculating mean/median"""
        ttk.Label(info_frame, text=info_text, font=("Courier", 9), foreground="gray",
                 justify=tk.LEFT, wraplength=800).pack(anchor=tk.W)

        ttk.Button(main_frame, text="▶ Fill Missing Values", command=self.run_fill_missing).pack(pady=10)

    def run_fill_missing(self):
        """Run fill missing values."""
        input_file = self.fillmiss_input_var.get()
        output_file = self.fillmiss_output_var.get()
        target_col = self.fillmiss_target_var.get()
        groups_str = self.fillmiss_groups_var.get()

        if not input_file or not Path(input_file).exists():
            messagebox.showerror("Error", f"Input file not found: {input_file}")
            return

        if not target_col:
            messagebox.showerror("Error", "Please specify target column")
            return

        if not groups_str:
            messagebox.showerror("Error", "Please specify grouping columns")
            return

        # Parse grouping columns
        grouping_cols = [c.strip() for c in groups_str.split(',')]

        if not output_file:
            output_file = None

        self.status_var.set("Filling missing values...")
        self.log("\n" + "="*60)
        self.log("FILL MISSING VALUES")
        self.log("="*60)

        def task():
            try:
                from fill_missing_values import MissingValueFiller
                sys.stdout = RedirectText(self.console)
                sys.stderr = RedirectText(self.console)

                # Get time window and year column parameters
                time_window = None
                year_column = None
                exclude_outliers = 0
                method = self.fillmiss_method_var.get()

                if method in ['recent_mean', 'recent_median']:
                    try:
                        time_window_str = self.fillmiss_time_window_var.get().strip()
                        if time_window_str:
                            time_window = int(time_window_str)
                    except ValueError:
                        self.log("⚠ Invalid time window value, using default (10 years)")
                        time_window = 10

                    year_column_str = self.fillmiss_year_column_var.get().strip()
                    if year_column_str:
                        year_column = year_column_str
                    # If empty, it will be auto-detected

                    try:
                        exclude_outliers_str = self.fillmiss_exclude_outliers_var.get().strip()
                        if exclude_outliers_str:
                            exclude_outliers = int(exclude_outliers_str)
                            if exclude_outliers < 0:
                                exclude_outliers = 0
                    except ValueError:
                        self.log("⚠ Invalid exclude outliers value, using default (0)")
                        exclude_outliers = 0

                filler = MissingValueFiller(verbose=True)
                stats = filler.process_file(
                    input_file=input_file,
                    output_file=output_file,
                    target_column=target_col,
                    grouping_columns=grouping_cols,
                    method=method,
                    non_negative=self.fillmiss_nonneg_var.get(),
                    predictor_columns=None,
                    backup=self.fillmiss_backup_var.get(),
                    time_window=time_window,
                    year_column=year_column,
                    exclude_outliers=exclude_outliers
                )

                self.log(f"\n✓ Fill missing values completed!")
                self.log(f"  Filled: {stats['filled_count']} values")
                self.log(f"  Remaining missing: {stats['remaining_missing']}")
                self.status_var.set("Fill missing values completed")
            except Exception as e:
                self.log(f"\n✗ Error: {e}")
                import traceback
                self.log(traceback.format_exc())
                self.status_var.set("Fill missing values failed")
            finally:
                sys.stdout = self.original_stdout
                sys.stderr = self.original_stderr

        self.run_in_thread(task)

    def create_resample_rules_tab(self):
        """Create Resample Rules Template Generator tab."""
        tab = ttk.Frame(self.content_frame)
        main_frame = self.create_scrollable_frame(tab)
        self.add_tab("Resample Rules", "⏱️", tab)

        ttk.Label(main_frame, text="Generate template for temporal resampling rules",
                 font=("Helvetica", 10, "italic")).pack(pady=5, padx=10)

        # Info frame
        info_frame = ttk.LabelFrame(main_frame, text="About", padding="10")
        info_frame.pack(fill=tk.X, pady=5, padx=10)

        info_text = """This tool generates a template 'resample_rules' sheet for config_group.xlsx.

The resample_rules sheet controls how PyPSA network data is resampled when changing
temporal resolution (e.g., from 1-hour to 4-hour snapshots).

Rules include:
  • mean: Average values over period (for time-series like solar availability)
  • sum: Sum values over period (for energy flows like hydro inflow)
  • max/min: Take maximum/minimum (for conservative estimates)
  • scale: Multiply by weights (for per-snapshot rates like ramp limits)
  • fixed: Set to specific value
  • skip: Do not modify

Carrier-Specific Rules:
  • Leave 'carrier' column empty for default (applies to all carriers)
  • Specify carrier name (e.g., 'solar', 'nuclear') to override for that carrier only
  • Example: Default uses 'mean', but solar/wind use 'max' for conservative estimates

The generated template includes all critical attributes and carrier-specific examples."""

        ttk.Label(info_frame, text=info_text, justify=tk.LEFT, wraplength=700).pack(anchor=tk.W)

        # Output settings
        output_frame = ttk.LabelFrame(main_frame, text="Output Settings", padding="10")
        output_frame.pack(fill=tk.X, pady=5, padx=10)

        ttk.Label(output_frame, text="Output File:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.resample_output_var = tk.StringVar(value="resample_rules_template.xlsx")
        ttk.Entry(output_frame, textvariable=self.resample_output_var, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(output_frame, text="Browse...",
                  command=lambda: self.browse_save_file(self.resample_output_var,
                  [("Excel files", "*.xlsx"), ("All files", "*.*")])).grid(row=0, column=2)

        # Actions
        action_frame = ttk.Frame(main_frame, padding="10")
        action_frame.pack(fill=tk.X, pady=10, padx=10)

        ttk.Button(action_frame, text="📄 Generate Template",
                  command=self.run_resample_rules_generator,
                  style="Accent.TButton").pack(side=tk.LEFT, padx=5)

        ttk.Button(action_frame, text="📖 View Documentation",
                  command=self.view_resample_docs).pack(side=tk.LEFT, padx=5)

        # Quick reference
        ref_frame = ttk.LabelFrame(main_frame, text="Quick Reference", padding="10")
        ref_frame.pack(fill=tk.BOTH, expand=True, pady=5, padx=10)

        ref_text = scrolledtext.ScrolledText(ref_frame, height=15, width=90, wrap=tk.WORD)
        ref_text.pack(fill=tk.BOTH, expand=True)

        reference = """CRITICAL ATTRIBUTES THAT NEED SCALING:

1. Ramp Limits (must multiply by weights):
   - generators.ramp_limit_up/down
   - storage_units.ramp_limit_up/down
   - links.ramp_limit_up/down
   → PyPSA applies these per snapshot, not per hour!

2. Standing Losses (must multiply by weights):
   - storage_units.standing_loss
   - stores.standing_loss
   → Specified as loss per hour, must scale to per snapshot

TIME-SERIES RESAMPLING:
   - generators_t.p_max_pu: Use 'mean' (or 'max' for conservative)
   - loads_t.p_set: Use 'mean'
   - storage_units_t.inflow: Use 'sum' (total energy)

After generating the template:
1. Open resample_rules_template.xlsx
2. Copy the 'resample_rules' sheet
3. Paste into your config_group.xlsx
4. Customize rules as needed (change mean→max, add skip rules, etc.)
5. Run your model with weights>1 in modelling_setting sheet"""

        ref_text.insert(tk.END, reference)
        ref_text.config(state=tk.DISABLED)

    def run_resample_rules_generator(self):
        """Run the resample rules template generator."""
        def task():
            try:
                sys.stdout = RedirectText(self.output_text)
                sys.stderr = RedirectText(self.output_text)

                output_file = self.resample_output_var.get()

                if not output_file:
                    self.log("✗ Please specify output file")
                    return

                self.log("=" * 80)
                self.log("GENERATING RESAMPLE RULES TEMPLATE")
                self.log("=" * 80)
                self.status_var.set("Generating template...")

                # Import and run the generator
                import pandas as pd

                # Create comprehensive resample rules
                resample_rules = pd.DataFrame([
                    # Time-series components - DEFAULT rules
                    {'component': 'generators_t', 'attribute': 'p_max_pu', 'carrier': None, 'rule': 'mean', 'value': None, 'notes': 'Default: Average renewable availability'},
                    # Carrier-specific examples
                    {'component': 'generators_t', 'attribute': 'p_max_pu', 'carrier': 'solar', 'rule': 'max', 'value': None, 'notes': 'EXAMPLE: Solar uses max (conservative)'},
                    {'component': 'generators_t', 'attribute': 'p_max_pu', 'carrier': 'wind', 'rule': 'max', 'value': None, 'notes': 'EXAMPLE: Wind uses max (conservative)'},

                    # Other time-series
                    {'component': 'generators_t', 'attribute': 'p_min_pu', 'carrier': None, 'rule': 'mean', 'value': None, 'notes': 'Average minimum output'},
                    {'component': 'generators_t', 'attribute': 'p_set', 'carrier': None, 'rule': 'mean', 'value': None, 'notes': 'Average power setpoint'},
                    {'component': 'generators_t', 'attribute': 'marginal_cost', 'carrier': None, 'rule': 'mean', 'value': None, 'notes': 'Average marginal cost'},
                    {'component': 'generators_t', 'attribute': 'fuel_cost', 'carrier': None, 'rule': 'mean', 'value': None, 'notes': 'Average fuel cost'},
                    {'component': 'loads_t', 'attribute': 'p_set', 'carrier': None, 'rule': 'mean', 'value': None, 'notes': 'Average load demand'},
                    {'component': 'storage_units_t', 'attribute': 'inflow', 'carrier': None, 'rule': 'sum', 'value': None, 'notes': 'Total inflow over period'},
                    {'component': 'storage_units_t', 'attribute': 'p_max_pu', 'carrier': None, 'rule': 'mean', 'value': None, 'notes': 'Average maximum power'},
                    {'component': 'links_t', 'attribute': 'p_max_pu', 'carrier': None, 'rule': 'mean', 'value': None, 'notes': 'Average link capacity'},
                    {'component': 'links_t', 'attribute': 'efficiency', 'carrier': None, 'rule': 'mean', 'value': None, 'notes': 'Average efficiency'},

                    # Static attributes - scaling
                    {'component': 'generators', 'attribute': 'ramp_limit_up', 'carrier': None, 'rule': 'scale', 'value': None, 'notes': 'CRITICAL: Scale by weights'},
                    {'component': 'generators', 'attribute': 'ramp_limit_down', 'carrier': None, 'rule': 'scale', 'value': None, 'notes': 'CRITICAL: Scale by weights'},
                    {'component': 'generators', 'attribute': 'ramp_limit_start_up', 'carrier': None, 'rule': 'scale', 'value': None, 'notes': 'Scale by weights'},
                    {'component': 'generators', 'attribute': 'ramp_limit_shut_down', 'carrier': None, 'rule': 'scale', 'value': None, 'notes': 'Scale by weights'},
                    {'component': 'storage_units', 'attribute': 'ramp_limit_up', 'carrier': None, 'rule': 'scale', 'value': None, 'notes': 'Scale by weights'},
                    {'component': 'storage_units', 'attribute': 'ramp_limit_down', 'carrier': None, 'rule': 'scale', 'value': None, 'notes': 'Scale by weights'},
                    {'component': 'storage_units', 'attribute': 'standing_loss', 'carrier': None, 'rule': 'scale', 'value': None, 'notes': 'CRITICAL: Per hour → per snapshot'},
                    {'component': 'stores', 'attribute': 'standing_loss', 'carrier': None, 'rule': 'scale', 'value': None, 'notes': 'CRITICAL: Per hour → per snapshot'},
                    {'component': 'links', 'attribute': 'ramp_limit_up', 'carrier': None, 'rule': 'scale', 'value': None, 'notes': 'Scale by weights'},
                    {'component': 'links', 'attribute': 'ramp_limit_down', 'carrier': None, 'rule': 'scale', 'value': None, 'notes': 'Scale by weights'},
                ])

                # Save to Excel
                resample_rules.to_excel(output_file, index=False, sheet_name='resample_rules')

                self.log(f"\n✓ Template generated successfully!")
                self.log(f"  Output: {output_file}")
                self.log(f"  Rows: {len(resample_rules)}")
                self.log("\nNext steps:")
                self.log("  1. Open the generated file in Excel")
                self.log("  2. Copy the 'resample_rules' sheet")
                self.log("  3. Paste into your config_group.xlsx")
                self.log("  4. Customize rules as needed")
                self.log("  5. See RESAMPLE_RULES_GUIDE.md for detailed documentation")

                self.status_var.set(f"Template generated: {output_file}")
                messagebox.showinfo("Success", f"Template generated successfully!\n\nSaved to: {output_file}")

            except Exception as e:
                self.log(f"\n✗ Error: {e}")
                import traceback
                self.log(traceback.format_exc())
                self.status_var.set("Template generation failed")
                messagebox.showerror("Error", f"Failed to generate template:\n{e}")
            finally:
                sys.stdout = self.original_stdout
                sys.stderr = self.original_stderr

        self.run_in_thread(task)

    def view_resample_docs(self):
        """Open the resample rules documentation."""
        doc_path = Path(__file__).parent.parent / "RESAMPLE_RULES_GUIDE.md"
        if doc_path.exists():
            import webbrowser
            webbrowser.open(str(doc_path))
        else:
            messagebox.showwarning("Documentation Not Found",
                                 f"Documentation file not found:\n{doc_path}\n\n" +
                                 "Please check the project root directory.")

    def create_diagnostic_tab(self):
        """Create Network Diagnostics tab."""
        tab = ttk.Frame(self.content_frame)
        main_frame = self.create_scrollable_frame(tab)
        self.add_tab("Diagnostics", "🔍", tab)

        ttk.Label(main_frame, text="Diagnose network before/after resampling to identify infeasibility causes",
                 font=("Helvetica", 10, "italic")).pack(pady=5, padx=10)

        # Info frame
        info_frame = ttk.LabelFrame(main_frame, text="About", padding="10")
        info_frame.pack(fill=tk.X, pady=5, padx=10)

        info_text = """This tool helps diagnose why resampling causes infeasibility.

It analyzes:
  • Snapshot frequency and total hours
  • Generator capacity by carrier
  • Renewable availability (p_max_pu) statistics
  • Energy constraints (e_sum_max, e_sum_min)
  • Load statistics (total energy, average, peak)
  • Ramp limits
  • Potential load-generation mismatches

Use this to compare the network before and after resampling to identify what causes infeasibility."""

        ttk.Label(info_frame, text=info_text, justify=tk.LEFT, wraplength=700).pack(anchor=tk.W)

        # Network file input
        input_frame = ttk.LabelFrame(main_frame, text="Network to Diagnose", padding="10")
        input_frame.pack(fill=tk.X, pady=5, padx=10)

        ttk.Label(input_frame, text="Network File (*.nc):").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.diag_network_var = tk.StringVar(value="")
        ttk.Entry(input_frame, textvariable=self.diag_network_var, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(input_frame, text="Browse...",
                  command=lambda: self.browse_file(self.diag_network_var,
                  [("NetCDF files", "*.nc"), ("All files", "*.*")])).grid(row=0, column=2)

        ttk.Label(input_frame, text="Label:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.diag_label_var = tk.StringVar(value="Network Diagnosis")
        ttk.Entry(input_frame, textvariable=self.diag_label_var, width=50).grid(row=1, column=1, columnspan=2, padx=5, sticky=tk.W)

        # Actions
        action_frame = ttk.Frame(main_frame, padding="10")
        action_frame.pack(fill=tk.X, pady=10, padx=10)

        ttk.Button(action_frame, text="🔍 Diagnose Network",
                  command=self.run_network_diagnostics,
                  style="Accent.TButton").pack(side=tk.LEFT, padx=5)

        ttk.Button(action_frame, text="📋 Copy to Clipboard",
                  command=self.copy_output_to_clipboard).pack(side=tk.LEFT, padx=5)

        # Usage instructions
        usage_frame = ttk.LabelFrame(main_frame, text="How to Use", padding="10")
        usage_frame.pack(fill=tk.BOTH, expand=True, pady=5, padx=10)

        usage_text = scrolledtext.ScrolledText(usage_frame, height=20, width=90, wrap=tk.WORD)
        usage_text.pack(fill=tk.BOTH, expand=True)

        usage = """WORKFLOW TO DIAGNOSE INFEASIBILITY:

1. Save your network BEFORE resampling:
   In main_group.py, add this line before resample_network():

   network.export_to_netcdf("network_before_resample.nc")

2. Save your network AFTER resampling:
   Add this line after resample_network():

   network.export_to_netcdf("network_after_resample.nc")

3. Run diagnostics on both:
   • Load network_before_resample.nc, label it "Before Resampling"
   • Click "Diagnose Network"
   • Load network_after_resample.nc, label it "After Resampling"
   • Click "Diagnose Network"

4. Compare the outputs to find differences:
   • Generator p_max_pu: Did averaging reduce renewable capacity too much?
   • Energy constraints: Are e_sum_max/e_sum_min too restrictive?
   • Load-generation mismatches: Any snapshots where gen < load?
   • Ramp limits: Too restrictive after scaling?

COMMON ISSUES:

• p_max_pu averaging: Using 'mean' reduces renewable peaks
  → Solution: Use 'max' rule for renewables in resample_rules

• Energy constraints: e_sum_max/e_sum_min calculated before resampling
  → Solution: Set them to 'default' rule in resample_rules

• Load-generation mismatch: Peak load > available generation
  → Solution: Check that loads are being resampled correctly

• Ramp limits: Scaled too aggressively
  → Solution: Check ramp_limit scaling rules"""

        usage_text.insert(tk.END, usage)
        usage_text.config(state=tk.DISABLED)

    def run_network_diagnostics(self):
        """Run network diagnostics."""
        def task():
            try:
                sys.stdout = RedirectText(self.console)
                sys.stderr = RedirectText(self.console)

                network_file = self.diag_network_var.get()
                label = self.diag_label_var.get()

                if not network_file:
                    self.log("✗ Please specify a network file")
                    return

                if not Path(network_file).exists():
                    self.log(f"✗ File not found: {network_file}")
                    return

                self.status_var.set(f"Diagnosing network: {label}...")

                # Import PyPSA and diagnostic module
                import pypsa
                from diagnose_resampling import diagnose_network

                # Load network
                self.log(f"Loading network from: {network_file}")
                network = pypsa.Network(network_file)

                # Run diagnostics
                diagnose_network(network, label)

                self.status_var.set(f"Diagnostics complete: {label}")

            except Exception as e:
                self.log(f"\n✗ Error: {e}")
                import traceback
                self.log(traceback.format_exc())
                self.status_var.set("Diagnostics failed")
                messagebox.showerror("Error", f"Failed to run diagnostics:\n{e}")
            finally:
                sys.stdout = self.original_stdout
                sys.stderr = self.original_stderr

        self.run_in_thread(task)

    def copy_output_to_clipboard(self):
        """Copy output console text to clipboard."""
        try:
            output_text = self.console.get("1.0", tk.END)
            self.root.clipboard_clear()
            self.root.clipboard_append(output_text)
            self.status_var.set("Output copied to clipboard")
            messagebox.showinfo("Success", "Output copied to clipboard!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy to clipboard:\n{e}")

    def create_aggregate_facilities_tab(self):
        """Create Aggregate Facilities tab."""
        tab = ttk.Frame(self.content_frame)
        main_frame = self.create_scrollable_frame(tab)
        self.add_tab("Aggregate Data", "📊", tab)

        ttk.Label(main_frame, text="Aggregate generation facility data by any columns",
                 font=("Helvetica", 10, "italic")).pack(pady=5, padx=10)

        # File selection
        file_frame = ttk.LabelFrame(main_frame, text="Files", padding="10")
        file_frame.pack(fill=tk.X, pady=5, padx=10)

        ttk.Label(file_frame, text="Input File:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.agg_input_var = tk.StringVar(value="data/raw/generation_by_facility.xlsx")
        ttk.Entry(file_frame, textvariable=self.agg_input_var, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(file_frame, text="Browse",
                  command=lambda: self.browse_file(self.agg_input_var,
                  [("Excel/CSV", "*.xlsx *.xls *.csv"), ("All files", "*.*")])).grid(row=0, column=2)

        ttk.Label(file_frame, text="Output File:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.agg_output_var = tk.StringVar(value="")
        ttk.Entry(file_frame, textvariable=self.agg_output_var, width=50).grid(row=1, column=1, padx=5)
        ttk.Button(file_frame, text="Browse",
                  command=lambda: self.browse_save_file(self.agg_output_var,
                  [("CSV files", "*.csv"), ("Excel files", "*.xlsx"), ("All files", "*.*")])).grid(row=1, column=2)

        # Load and inspect button
        load_frame = ttk.Frame(main_frame, padding="5")
        load_frame.pack(fill=tk.X, pady=5, padx=10)
        ttk.Button(load_frame, text="📂 Load File and Inspect Columns",
                  command=self.load_aggregate_file).pack()

        # Filters section
        filter_frame = ttk.LabelFrame(main_frame, text="Filters (Optional)", padding="10")
        filter_frame.pack(fill=tk.X, pady=5, padx=10)

        # Container for filter rows
        self.agg_filter_container = ttk.Frame(filter_frame)
        self.agg_filter_container.pack(fill=tk.X, pady=5)
        self.agg_filters = []  # Store filter widget references

        ttk.Button(filter_frame, text="+ Add Filter",
                  command=self.add_aggregate_filter).pack(pady=5)

        # Group by section
        groupby_frame = ttk.LabelFrame(main_frame, text="Group By (Aggregation Columns)", padding="10")
        groupby_frame.pack(fill=tk.X, pady=5, padx=10)

        ttk.Label(groupby_frame, text="Select columns to group by (checked columns will be used for aggregation):",
                 font=("Helvetica", 9, "italic")).pack(anchor=tk.W, pady=2)

        # Scrollable checkboxes for group by
        groupby_canvas = tk.Canvas(groupby_frame, height=120, bg="white")
        groupby_scrollbar = ttk.Scrollbar(groupby_frame, orient="vertical", command=groupby_canvas.yview)
        self.agg_groupby_frame = ttk.Frame(groupby_canvas)

        self.agg_groupby_frame.bind(
            "<Configure>",
            lambda e: groupby_canvas.configure(scrollregion=groupby_canvas.bbox("all"))
        )

        groupby_canvas.create_window((0, 0), window=self.agg_groupby_frame, anchor="nw")
        groupby_canvas.configure(yscrollcommand=groupby_scrollbar.set)

        groupby_canvas.pack(side="left", fill="both", expand=True)
        groupby_scrollbar.pack(side="right", fill="y")

        self.agg_groupby_vars = {}  # Dictionary to store checkbutton variables

        # Name order section
        name_order_frame = ttk.LabelFrame(main_frame, text="Name Column Order (Optional)", padding="10")
        name_order_frame.pack(fill=tk.X, pady=5, padx=10)

        ttk.Label(name_order_frame, text="Specify order of columns in generated name (e.g., 'carrier_province' vs 'province_carrier'):",
                 font=("Helvetica", 9, "italic")).pack(anchor=tk.W, pady=2)

        ttk.Label(name_order_frame, text="Enter column names in order, comma-separated (leave empty to use group-by order):",
                 font=("Helvetica", 9)).pack(anchor=tk.W, pady=2)

        self.agg_name_order_var = tk.StringVar(value="")
        ttk.Entry(name_order_frame, textvariable=self.agg_name_order_var, width=50).pack(anchor=tk.W, pady=2, padx=5)

        ttk.Label(name_order_frame, text="Example: 'carrier,province' will create names like 'solar_경남', 'wind_강원'",
                 font=("Helvetica", 8), foreground="gray").pack(anchor=tk.W, pady=2)

        # Aggregation column
        agg_col_frame = ttk.LabelFrame(main_frame, text="Aggregation Settings", padding="10")
        agg_col_frame.pack(fill=tk.X, pady=5, padx=10)

        ttk.Label(agg_col_frame, text="Column to Aggregate (sum):").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.agg_column_var = tk.StringVar(value="p_nom")
        self.agg_column_combo = ttk.Combobox(agg_col_frame, textvariable=self.agg_column_var,
                                              state="readonly", width=20)
        self.agg_column_combo.grid(row=0, column=1, padx=5, sticky=tk.W)

        # Info section
        info_frame = ttk.LabelFrame(main_frame, text="How It Works", padding="10")
        info_frame.pack(fill=tk.X, pady=5, padx=10)

        info_text = """1. Load File: Click "Load File and Inspect Columns" to see available columns
2. Add Filters: Filter data by specific values (e.g., market=중앙, carrier=wind,solar)
3. Group By: Select columns to aggregate by (e.g., province, carrier)
4. Aggregate Column: Choose column to sum (default: p_nom)
5. Run: Data will be grouped and summed, with names created from group values

Example: Group by [province, carrier] will create names like "경남_solar", "강원_wind"
         Single column groups create names like "경남", "강원" """

        ttk.Label(info_frame, text=info_text, font=("Courier", 9), foreground="gray",
                 justify=tk.LEFT, wraplength=800).pack(anchor=tk.W)

        # Action buttons
        action_frame = ttk.Frame(main_frame, padding="10")
        action_frame.pack(fill=tk.X, pady=10, padx=10)

        ttk.Button(action_frame, text="▶ Run Aggregation",
                  command=self.run_aggregate_facilities,
                  style="Accent.TButton").pack(side=tk.LEFT, padx=5)

    def load_aggregate_file(self):
        """Load the aggregation input file and populate column options."""
        input_file = self.agg_input_var.get()

        if not input_file or not Path(input_file).exists():
            messagebox.showerror("Error", f"File not found: {input_file}")
            return

        self.status_var.set("Loading file...")
        self.log("\n" + "="*60)
        self.log("LOADING AGGREGATION FILE")
        self.log("="*60)

        def task():
            try:
                from aggregate_facilities import read_input_file
                sys.stdout = RedirectText(self.console)
                sys.stderr = RedirectText(self.console)

                # Read file
                df = read_input_file(Path(input_file))
                self.agg_loaded_df = df  # Store for later use

                self.log(f"\n✓ File loaded successfully!")
                self.log(f"  Rows: {len(df)}")
                self.log(f"  Columns: {list(df.columns)}")

                # Update UI with available columns
                self.root.after(0, lambda: self.populate_aggregate_columns(df.columns))

                self.status_var.set("File loaded successfully")
                messagebox.showinfo("Success", f"File loaded!\n{len(df)} rows, {len(df.columns)} columns")

            except Exception as e:
                self.log(f"\n✗ Error: {e}")
                import traceback
                self.log(traceback.format_exc())
                self.status_var.set("Loading failed")
                messagebox.showerror("Error", f"Failed to load file:\n{e}")
            finally:
                sys.stdout = self.original_stdout
                sys.stderr = self.original_stderr

        self.run_in_thread(task)

    def populate_aggregate_columns(self, columns):
        """Populate column options after file is loaded."""
        columns = list(columns)

        # Update aggregation column combobox
        self.agg_column_combo["values"] = columns
        if "p_nom" in columns:
            self.agg_column_var.set("p_nom")
        elif columns:
            self.agg_column_var.set(columns[0])

        # Clear existing groupby checkboxes
        for widget in self.agg_groupby_frame.winfo_children():
            widget.destroy()
        self.agg_groupby_vars.clear()

        # Create checkboxes for group by (default: province and carrier)
        defaults = ["province", "carrier"]
        for i, col in enumerate(columns):
            var = tk.BooleanVar(value=(col in defaults))
            self.agg_groupby_vars[col] = var
            cb = ttk.Checkbutton(self.agg_groupby_frame, text=col, variable=var)
            cb.grid(row=i // 4, column=i % 4, sticky=tk.W, padx=10, pady=2)

        # Update filter column options
        for filter_widget in self.agg_filters:
            if filter_widget and "column_combo" in filter_widget:
                filter_widget["column_combo"]["values"] = columns

    def add_aggregate_filter(self):
        """Add a filter row for aggregation."""
        if not hasattr(self, 'agg_loaded_df') or self.agg_loaded_df is None:
            messagebox.showwarning("Warning", "Please load a file first")
            return

        row_idx = len(self.agg_filters)

        frame = ttk.Frame(self.agg_filter_container)
        frame.pack(fill=tk.X, pady=2)

        ttk.Label(frame, text="Column:").pack(side=tk.LEFT, padx=5)

        col_var = tk.StringVar()
        col_combo = ttk.Combobox(frame, textvariable=col_var,
                                  values=list(self.agg_loaded_df.columns),
                                  state="readonly", width=15)
        col_combo.pack(side=tk.LEFT, padx=5)

        ttk.Label(frame, text="Values (comma-separated):").pack(side=tk.LEFT, padx=5)

        val_var = tk.StringVar()
        val_entry = ttk.Entry(frame, textvariable=val_var, width=30)
        val_entry.pack(side=tk.LEFT, padx=5)

        # Show unique button
        def show_unique():
            col = col_var.get()
            if col and col in self.agg_loaded_df.columns:
                unique_vals = self.agg_loaded_df[col].dropna().unique()
                msg = f"Unique values in '{col}' ({len(unique_vals)} total):\n\n"
                msg += ", ".join(str(v) for v in sorted(unique_vals)[:50])
                if len(unique_vals) > 50:
                    msg += f"\n\n... and {len(unique_vals) - 50} more"
                messagebox.showinfo(f"Unique Values: {col}", msg)

        ttk.Button(frame, text="Show Unique", command=show_unique).pack(side=tk.LEFT, padx=2)

        # Remove button
        def remove():
            frame.destroy()
            self.agg_filters.remove(filter_dict)

        ttk.Button(frame, text="Remove", command=remove).pack(side=tk.LEFT, padx=2)

        filter_dict = {
            "frame": frame,
            "column_var": col_var,
            "value_var": val_var,
            "column_combo": col_combo
        }
        self.agg_filters.append(filter_dict)

    def run_aggregate_facilities(self):
        """Run the aggregation."""
        input_file = self.agg_input_var.get()
        output_file = self.agg_output_var.get()

        if not input_file or not Path(input_file).exists():
            messagebox.showerror("Error", f"Input file not found: {input_file}")
            return

        if not output_file:
            messagebox.showerror("Error", "Please specify an output file")
            return

        # Get selected group by columns
        groupby_cols = [col for col, var in self.agg_groupby_vars.items() if var.get()]
        if not groupby_cols:
            messagebox.showerror("Error", "Please select at least one column to group by")
            return

        agg_col = self.agg_column_var.get()
        if not agg_col:
            messagebox.showerror("Error", "Please select an aggregation column")
            return

        # Get name order if specified
        name_order_str = self.agg_name_order_var.get().strip()
        name_order = None
        if name_order_str:
            name_order = [col.strip() for col in name_order_str.split(",")]
            # Validate name_order columns are in groupby_cols
            invalid = [col for col in name_order if col not in groupby_cols]
            if invalid:
                messagebox.showerror("Error", f"Name order contains columns not in group-by: {invalid}")
                return

        self.status_var.set("Aggregating data...")
        self.log("\n" + "="*60)
        self.log("AGGREGATE FACILITIES")
        self.log("="*60)

        def task():
            try:
                from aggregate_facilities import (
                    read_input_file, apply_filters, aggregate_facilities, save_output_file
                )
                sys.stdout = RedirectText(self.console)
                sys.stderr = RedirectText(self.console)

                # Read file
                df = read_input_file(Path(input_file))
                self.log(f"Loaded {len(df)} rows")

                # Apply filters
                filters = {}
                for f in self.agg_filters:
                    col = f["column_var"].get()
                    vals_str = f["value_var"].get().strip()
                    if col and vals_str:
                        vals = [v.strip() for v in vals_str.split(",")]
                        filters[col] = vals

                if filters:
                    self.log(f"Applying filters: {filters}")
                    df = apply_filters(df, filters)
                    self.log(f"After filtering: {len(df)} rows")

                if df.empty:
                    self.log("✗ No data remains after filtering")
                    self.status_var.set("Aggregation failed: no data")
                    return

                # Aggregate
                self.log(f"Grouping by: {groupby_cols}")
                if name_order:
                    self.log(f"Name order: {name_order}")
                self.log(f"Aggregating: {agg_col} (sum)")

                result = aggregate_facilities(df, groupby_cols, agg_col, name_order)

                # Save
                save_output_file(result, Path(output_file))
                self.log(f"\n✓ Aggregation complete!")
                self.log(f"  Output: {output_file}")
                self.log(f"  Rows: {len(result)}")
                self.log("\nPreview (first 10 rows):")
                self.log(str(result.head(10)))

                self.status_var.set("Aggregation completed")
                messagebox.showinfo("Success", f"Aggregation complete!\n{len(result)} rows saved to:\n{output_file}")

            except Exception as e:
                self.log(f"\n✗ Error: {e}")
                import traceback
                self.log(traceback.format_exc())
                self.status_var.set("Aggregation failed")
                messagebox.showerror("Error", f"Aggregation failed:\n{e}")
            finally:
                sys.stdout = self.original_stdout
                sys.stderr = self.original_stderr

        self.run_in_thread(task)


def main():
    """Main entry point."""
    root = tk.Tk()
    app = UtilsGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

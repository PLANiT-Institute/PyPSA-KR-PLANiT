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
        self.root.geometry("1000x750")

        # Store original stdout/stderr
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr

        # Create widgets
        self.create_widgets()

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
            text="Run any utility tool with a click - 9 tools available",
            font=("Helvetica", 10)
        )
        subtitle_label.pack()

        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Create tabs for all utilities
        self.create_geocoding_tab()
        self.create_reverse_geocode_tab()
        self.create_download_tab()
        self.create_csv_to_excel_tab()
        self.create_encoding_converter_tab()
        self.create_add_cc_groups_tab()
        self.create_merge_cc_groups_tab()
        self.create_expand_mainland_tab()
        self.create_unique_names_tab()

        # Output console at bottom
        self.create_output_console()

        # Status bar
        self.status_var = tk.StringVar(value="Ready - Select a tool and click Run")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def create_geocoding_tab(self):
        """Geocoding utility tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📍 Geocoding")

        main_frame = ttk.Frame(tab, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Add geographic coordinates (x, y) to CSV files",
                 font=("Helvetica", 10, "italic")).pack(pady=5)

        # Input settings
        frame = ttk.LabelFrame(main_frame, text="Input Settings", padding="10")
        frame.pack(fill=tk.X, pady=5)

        ttk.Label(frame, text="CSV Folder:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.geo_folder_var = tk.StringVar(value="data/2024")
        ttk.Entry(frame, textvariable=self.geo_folder_var, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(frame, text="Browse...", command=lambda: self.browse_folder(self.geo_folder_var)).grid(row=0, column=2)

        ttk.Label(frame, text="Address Column:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.geo_address_var = tk.StringVar(value="address")
        ttk.Entry(frame, textvariable=self.geo_address_var, width=50).grid(row=1, column=1, padx=5)

        # Options
        opt_frame = ttk.LabelFrame(main_frame, text="Options", padding="10")
        opt_frame.pack(fill=tk.X, pady=5)

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
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🔍 Reverse Geocode")

        main_frame = ttk.Frame(tab, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Get region names from coordinates (country, province, city, etc.)",
                 font=("Helvetica", 10, "italic")).pack(pady=5)

        # File settings
        frame = ttk.LabelFrame(main_frame, text="Files", padding="10")
        frame.pack(fill=tk.X, pady=5)

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
        col_frame.pack(fill=tk.X, pady=5)

        ttk.Label(col_frame, text="Longitude Column:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.revgeo_x_var = tk.StringVar(value="x")
        ttk.Entry(col_frame, textvariable=self.revgeo_x_var, width=20).grid(row=0, column=1, padx=5, sticky=tk.W)

        ttk.Label(col_frame, text="Latitude Column:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.revgeo_y_var = tk.StringVar(value="y")
        ttk.Entry(col_frame, textvariable=self.revgeo_y_var, width=20).grid(row=1, column=1, padx=5, sticky=tk.W)

        # Options
        opt_frame = ttk.LabelFrame(main_frame, text="Options", padding="10")
        opt_frame.pack(fill=tk.X, pady=5)

        self.revgeo_overwrite_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(opt_frame, text="Overwrite existing region info", variable=self.revgeo_overwrite_var).pack(anchor=tk.W)

        ttk.Label(opt_frame, text="Language:").pack(anchor=tk.W, pady=(10, 0))
        self.revgeo_language_var = tk.StringVar(value="en")
        lang_frame = ttk.Frame(opt_frame)
        lang_frame.pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(lang_frame, text="English", variable=self.revgeo_language_var, value="en").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(lang_frame, text="한국어 (Korean)", variable=self.revgeo_language_var, value="ko").pack(side=tk.LEFT, padx=5)

        # Info about output
        info_frame = ttk.LabelFrame(main_frame, text="Output Columns Added", padding="10")
        info_frame.pack(fill=tk.X, pady=5)

        info_text = """Country, country_code, state, province, region, city, town, village,
county, municipality, suburb, district, postcode"""
        ttk.Label(info_frame, text=info_text, font=("Courier", 9), foreground="gray").pack()

        ttk.Button(main_frame, text="▶ Run Reverse Geocoding", command=self.run_reverse_geocode).pack(pady=10)

    def create_download_tab(self):
        """Network download utility tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🌍 Network Download")

        main_frame = ttk.Frame(tab, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Download power network data from OpenStreetMap",
                 font=("Helvetica", 10, "italic")).pack(pady=5)

        # Country
        frame = ttk.LabelFrame(main_frame, text="Country Settings", padding="10")
        frame.pack(fill=tk.X, pady=5)

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
        opt_frame.pack(fill=tk.X, pady=5)

        ttk.Label(opt_frame, text="Min Voltage (kV):").grid(row=0, column=0, sticky=tk.W)
        self.dl_voltage_var = tk.StringVar(value="220")
        ttk.Combobox(opt_frame, textvariable=self.dl_voltage_var, values=["110", "220", "380"], width=10).grid(row=0, column=1, padx=5)

        ttk.Label(opt_frame, text="Output Dir:").grid(row=1, column=0, sticky=tk.W)
        self.dl_output_var = tk.StringVar(value="./networks")
        ttk.Entry(opt_frame, textvariable=self.dl_output_var, width=40).grid(row=1, column=1, padx=5)

        ttk.Button(main_frame, text="▶ Download Network", command=self.run_download).pack(pady=10)

    def create_csv_to_excel_tab(self):
        """CSV to Excel converter tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📊 CSV→Excel")

        main_frame = ttk.Frame(tab, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Convert CSV files to Excel format",
                 font=("Helvetica", 10, "italic")).pack(pady=5)

        frame = ttk.LabelFrame(main_frame, text="Files", padding="10")
        frame.pack(fill=tk.X, pady=5)

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
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🔤 Encoding")

        main_frame = ttk.Frame(tab, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Convert file encoding from EUC-KR/CP949 to UTF-8",
                 font=("Helvetica", 10, "italic")).pack(pady=5)

        frame = ttk.LabelFrame(main_frame, text="Files", padding="10")
        frame.pack(fill=tk.X, pady=5)

        ttk.Label(frame, text="Input File / Folder:").grid(row=0, column=0, sticky=tk.W)
        self.enc_input_var = tk.StringVar(value="")
        ttk.Entry(frame, textvariable=self.enc_input_var, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(frame, text="File", command=lambda: self.browse_file(self.enc_input_var)).grid(row=0, column=2)
        ttk.Button(frame, text="Folder", command=lambda: self.browse_folder(self.enc_input_var)).grid(row=0, column=3)

        opt_frame = ttk.LabelFrame(main_frame, text="Options", padding="10")
        opt_frame.pack(fill=tk.X, pady=5)

        self.enc_backup_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(opt_frame, text="Create backup (.bak)", variable=self.enc_backup_var).pack(anchor=tk.W)

        ttk.Button(main_frame, text="▶ Convert Encoding", command=self.run_encoding_converter).pack(pady=10)

    def create_add_cc_groups_tab(self):
        """Add CC groups tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="⚡ Add CC Groups")

        main_frame = ttk.Frame(tab, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Add combined cycle (CC) group names to generators.csv",
                 font=("Helvetica", 10, "italic")).pack(pady=5)

        frame = ttk.LabelFrame(main_frame, text="Files", padding="10")
        frame.pack(fill=tk.X, pady=5)

        ttk.Label(frame, text="Input File:").grid(row=0, column=0, sticky=tk.W)
        self.addcc_input_var = tk.StringVar(value="data/2024/generators.csv")
        ttk.Entry(frame, textvariable=self.addcc_input_var, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(frame, text="Browse", command=lambda: self.browse_file(self.addcc_input_var, [("CSV", "*.csv")])).grid(row=0, column=2)

        opt_frame = ttk.LabelFrame(main_frame, text="Options", padding="10")
        opt_frame.pack(fill=tk.X, pady=5)

        self.addcc_backup_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(opt_frame, text="Create backup", variable=self.addcc_backup_var).pack(anchor=tk.W)

        ttk.Button(main_frame, text="▶ Add CC Groups", command=self.run_add_cc_groups).pack(pady=10)

    def create_merge_cc_groups_tab(self):
        """Merge CC groups tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🔗 Merge CC")

        main_frame = ttk.Frame(tab, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Merge CC generators by group (combine GT + ST into single unit)",
                 font=("Helvetica", 10, "italic")).pack(pady=5)

        frame = ttk.LabelFrame(main_frame, text="Files", padding="10")
        frame.pack(fill=tk.X, pady=5)

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
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🗺️ Expand Mainland")

        main_frame = ttk.Frame(tab, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Expand mainland (육지) data to individual provinces",
                 font=("Helvetica", 10, "italic")).pack(pady=5)

        frame = ttk.LabelFrame(main_frame, text="Files", padding="10")
        frame.pack(fill=tk.X, pady=5)

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
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🏷️ Unique Names")

        main_frame = ttk.Frame(tab, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Make 'name' column unique by adding _1, _2 suffixes",
                 font=("Helvetica", 10, "italic")).pack(pady=5)

        frame = ttk.LabelFrame(main_frame, text="Files", padding="10")
        frame.pack(fill=tk.X, pady=5)

        ttk.Label(frame, text="Input File:").grid(row=0, column=0, sticky=tk.W)
        self.unique_input_var = tk.StringVar(value="")
        ttk.Entry(frame, textvariable=self.unique_input_var, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(frame, text="Browse", command=lambda: self.browse_file(self.unique_input_var, [("CSV", "*.csv")])).grid(row=0, column=2)

        opt_frame = ttk.LabelFrame(main_frame, text="Options", padding="10")
        opt_frame.pack(fill=tk.X, pady=5)

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
                geocoder = ReverseGeocoder(cache_file=str(cache_path), language=language)
                geocoder.process_csv(
                    input_file=input_file,
                    output_file=output_file,
                    x_column=self.revgeo_x_var.get(),
                    y_column=self.revgeo_y_var.get(),
                    overwrite=self.revgeo_overwrite_var.get()
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


def main():
    """Main entry point."""
    root = tk.Tk()
    app = UtilsGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

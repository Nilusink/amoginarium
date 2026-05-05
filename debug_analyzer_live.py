"""
debug_analyzer.py

Live dashboard for analyzing the runtimes of the Amoginatorium application.
Features live-reloading, multi-file comparison, performance caching,
interactive native legends, dynamic space reclamation, and side-by-side modes.
"""

import datetime
import glob
import json
import os
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

# --- SETTINGS MANAGEMENT ---
SETTINGS_FILE = "debug_viewer_settings.json"
DEFAULT_SETTINGS = {
    "auto_switch_new": True,
    "max_files": -1,
    "comparison_mode": "Merged",  # "Merged" or "Side-by-Side"
    "theme": "Dark",              # "Dark" or "Light"
    "sash_position": 300          # Saved width of the left column
}


def load_settings() -> dict:
    """Loads application settings from the JSON file or returns defaults."""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                settings = json.load(f)
                return {**DEFAULT_SETTINGS, **settings}
        except (json.JSONDecodeError, OSError):
            pass
    return DEFAULT_SETTINGS.copy()


def save_settings(settings: dict) -> None:
    """Saves the current application settings to the JSON file."""
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=4)
    except OSError:
        pass


# --- CUSTOM GRAPH WIDGET ---
class GraphWidget(ctk.CTkFrame):
    """Encapsulates a Matplotlib figure, toolbar, and interactive legend."""

    def __init__(self, master: tk.Widget, graph_id: str, title_text: str, app, **kwargs):
        super().__init__(master, corner_radius=4, **kwargs)
        self.graph_id = graph_id
        self.app = app
        self.is_minimized = False
        self.is_fullscreen = False

        # 1. Header (Window Title Bar)
        self.header = ctk.CTkFrame(self, height=35, corner_radius=4)
        self.header.pack(fill=tk.X, padx=1, pady=(1, 0))
        self.header.pack_propagate(False)

        self.title_label = ctk.CTkLabel(self.header, text=title_text, font=("Arial", 12, "bold"))
        self.title_label.pack(side=tk.LEFT, padx=10)

        # Toolbar Buttons
        self.btn_full = ctk.CTkButton(self.header, text="⛶", width=30, height=25,
                                      command=self.toggle_fullscreen, fg_color="transparent",
                                      hover_color=("gray75", "gray40"))
        self.btn_full.pack(side=tk.RIGHT, padx=2)

        self.btn_min = ctk.CTkButton(self.header, text="▼", width=30, height=25,
                                     command=self.toggle_minimize, fg_color="transparent",
                                     hover_color=("gray75", "gray40"))
        self.btn_min.pack(side=tk.RIGHT, padx=2)

        # 2. Content Frame (Holds Graph + Toolbar)
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        self.content_frame.pack_propagate(False)

        # Matplotlib Figure
        self.fig = plt.Figure(figsize=(4, 3), dpi=100, layout="constrained")
        self.ax = self.fig.add_subplot(111)
        self.ax_twin = None

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.content_frame)
        self.canvas.get_tk_widget().configure(borderwidth=0, highlightthickness=0)

        self.toolbar = NavigationToolbar2Tk(self.canvas, self.content_frame, pack_toolbar=False)
        self.toolbar.configure(borderwidth=0, highlightthickness=0)

        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.toolbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Native interactive legend
        self.linedict = {}
        self.fig.canvas.mpl_connect('pick_event', self.on_pick)

    def toggle_minimize(self) -> None:
        """Toggles the minimized state of the graph frame."""
        if self.is_fullscreen:
            return
        self.is_minimized = not self.is_minimized
        self.btn_min.configure(text="▶" if self.is_minimized else "▼")
        self.app.apply_layout()

    def toggle_fullscreen(self) -> None:
        """Toggles the fullscreen state of the graph frame."""
        self.is_fullscreen = not self.is_fullscreen
        self.btn_full.configure(text="🗗" if self.is_fullscreen else "⛶")
        self.app.set_fullscreen_widget(self if self.is_fullscreen else None)

    def setup_interactive_legend(self) -> None:
        """Configures the Matplotlib legend to toggle plot lines on click."""
        leg = self.ax.get_legend()
        if not leg and self.ax_twin:
            leg = self.ax_twin.get_legend()

        if not leg:
            return

        orig_handles = {}
        h1, l1 = self.ax.get_legend_handles_labels()
        for h, l in zip(h1, l1):
            orig_handles[l] = h

        if self.ax_twin:
            h2, l2 = self.ax_twin.get_legend_handles_labels()
            for h, l in zip(h2, l2):
                orig_handles[l] = h

        self.linedict = {}

        for leg_obj, text_obj in zip(leg.legend_handles, leg.texts):
            leg_obj.set_picker(True)
            leg_obj.set_pickradius(5)
            text_obj.set_picker(True)

            label = text_obj.get_text()
            orig_obj = orig_handles.get(label)

            if orig_obj:
                self.linedict[leg_obj] = orig_obj
                self.linedict[text_obj] = orig_obj

    def on_pick(self, event) -> None:
        """Handles pick events to toggle line visibility."""
        artist = event.artist
        origline = self.linedict.get(artist)
        if origline is None:
            return

        vis = not origline.get_visible()
        origline.set_visible(vis)

        leg = self.ax.get_legend()
        if not leg and self.ax_twin:
            leg = self.ax_twin.get_legend()

        if leg:
            for l_h, l_t in zip(leg.legend_handles, leg.texts):
                if self.linedict.get(l_h) == origline or self.linedict.get(l_t) == origline:
                    l_h.set_alpha(1.0 if vis else 0.3)
                    l_t.set_alpha(1.0 if vis else 0.3)

        self.canvas.draw_idle()


# --- MAIN APP ---
class DebugAnalyzerApp:
    """Main application class for the Debug Analyzer."""

    def __init__(self, root: ctk.CTk):
        self.root = root
        self.root.title("Amoginatorium Debug Analyzer")
        self.root.geometry("1400x850")

        self.settings = load_settings()

        self.debug_dir = "debug"
        os.makedirs(self.debug_dir, exist_ok=True)

        self.known_files = []
        self.selected_identifiers = []
        self.data_cache = {}
        self.graphs = {}
        self.fullscreen_widget = None
        self._is_saving_settings = False

        self.apply_theme_settings()
        self._setup_ui()
        self.sync_theme_to_widgets()
        self.poll_directory()

    def apply_theme_settings(self) -> None:
        """Applies global theme configurations based on user settings."""
        ctk.set_appearance_mode(self.settings["theme"])
        ctk.set_default_color_theme("blue")

        if self.settings["theme"] == "Dark":
            plt.style.use('dark_background')
            self.pw_bg = "#0a0a0a"
            self.left_bg = "#171717"
            self.listbox_bg = "#171717"
            self.listbox_fg = "#ffffff"
            self.listbox_sel = "#1f538d"
            self.graph_bg = "#1e1e1e"
            self.header_bg = "#2b2b2b"
            self.mpl_bg = "#1e1e1e"
            self.mpl_fg = "#ffffff"
        else:
            plt.style.use('default')
            self.pw_bg = "#d0d0d0"
            self.left_bg = "#f3f3f3"
            self.listbox_bg = "#f3f3f3"
            self.listbox_fg = "#000000"
            self.listbox_sel = "#3a7ebf"
            self.graph_bg = "#ffffff"
            self.header_bg = "#e5e5e5"
            self.mpl_bg = "#ffffff"
            self.mpl_fg = "#000000"

        self.root.configure(bg=self.pw_bg)

        plt.rcParams.update({
            "figure.facecolor": self.mpl_bg,
            "figure.edgecolor": self.mpl_bg,
            "axes.facecolor": self.mpl_bg,
            "axes.edgecolor": self.mpl_fg,
            "axes.labelcolor": self.mpl_fg,
            "text.color": self.mpl_fg,
            "xtick.color": self.mpl_fg,
            "ytick.color": self.mpl_fg,
        })

    def sync_theme_to_widgets(self) -> None:
        """Updates all existing widgets to match the current theme."""
        if hasattr(self, 'paned_window'):
            self.paned_window.configure(bg=self.pw_bg)
            self.left_frame.configure(fg_color=self.left_bg)
            self.listbox.configure(bg=self.listbox_bg, fg=self.listbox_fg, selectbackground=self.listbox_sel)

        if hasattr(self, 'collapsed_sidebar'):
            self.collapsed_sidebar.configure(fg_color=self.left_bg)
            self.btn_expand.configure(text_color=self.mpl_fg)
            self.btn_collapse.configure(text_color=self.mpl_fg)

        for gw in self.graphs.values():
            self._sync_widget_theme(gw)

    def _sync_widget_theme(self, gw: GraphWidget) -> None:
        """Applies theme variables to an individual GraphWidget."""
        gw.configure(fg_color=self.graph_bg)
        gw.header.configure(fg_color=self.header_bg)
        gw.btn_full.configure(text_color=self.mpl_fg)
        gw.btn_min.configure(text_color=self.mpl_fg)
        gw.title_label.configure(text_color=self.mpl_fg)

        gw.fig.patch.set_facecolor(self.mpl_bg)
        gw.ax.set_facecolor(self.mpl_bg)
        gw.ax.tick_params(colors=self.mpl_fg)
        for spine in gw.ax.spines.values():
            spine.set_color(self.mpl_fg)

        if gw.ax_twin:
            gw.ax_twin.set_facecolor(self.mpl_bg)
            gw.ax_twin.tick_params(colors=self.mpl_fg)
            for spine in gw.ax_twin.spines.values():
                spine.set_color(self.mpl_fg)

        # Standardize toolbar styling with neutral colors
        toolbar_bg = "#e5e5e5"
        gw.toolbar.configure(background=toolbar_bg, borderwidth=0, highlightthickness=0)

        for child in gw.toolbar.winfo_children():
            if isinstance(child, tk.Widget):
                child.configure(background=toolbar_bg)
            if isinstance(child, tk.Label):
                child.configure(foreground="black")
            elif isinstance(child, tk.Button):
                child.configure(activebackground="#d5d5d5", borderwidth=0, highlightthickness=0)

    def _setup_ui(self) -> None:
        """Constructs the application layout."""
        self.collapsed_sidebar = ctk.CTkFrame(self.root, width=40, corner_radius=0, fg_color=self.left_bg)
        self.btn_expand = ctk.CTkButton(self.collapsed_sidebar, text="▶", width=30, height=30,
                                        command=self.expand_sidebar, fg_color="transparent")
        self.btn_expand.pack(pady=15, padx=5)

        self.paned_window = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bd=0, sashwidth=6,
                                           bg=self.pw_bg, opaqueresize=False)
        self.paned_window.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.paned_window.bind("<ButtonRelease-1>", self.save_current_settings)

        # 1. Left Panel (Files & Settings)
        self.left_frame = ctk.CTkFrame(self.paned_window, corner_radius=0, fg_color=self.left_bg)

        left_header = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        left_header.pack(fill=tk.X, padx=15, pady=(15, 5))
        ctk.CTkLabel(left_header, text="Debug Runs", font=("Arial", 16, "bold")).pack(side=tk.LEFT)
        self.btn_collapse = ctk.CTkButton(left_header, text="◀", width=30, height=25,
                                          command=self.collapse_sidebar, fg_color="transparent")
        self.btn_collapse.pack(side=tk.RIGHT)

        self.listbox_frame = ctk.CTkFrame(self.left_frame, corner_radius=0, fg_color="transparent")
        self.listbox_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        list_scroll = ctk.CTkScrollbar(self.listbox_frame)
        list_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox = tk.Listbox(
            self.listbox_frame, selectmode=tk.EXTENDED, bd=0, highlightthickness=0,
            font=("Consolas", 10), activestyle="none", exportselection=False
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scroll.configure(command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=list_scroll.set)
        self.listbox.bind("<<ListboxSelect>>", self.on_listbox_select)

        # Settings Area
        settings_frame = ctk.CTkFrame(self.left_frame, corner_radius=8, fg_color=("gray85", "#222222"))
        settings_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=15)

        inner_settings = ctk.CTkFrame(settings_frame, fg_color="transparent")
        inner_settings.pack(fill=tk.X, padx=15, pady=15)

        ctk.CTkLabel(inner_settings, text="Settings", font=("Arial", 14, "bold")).pack(anchor="w", pady=(0, 10))

        self.theme_seg = ctk.CTkSegmentedButton(inner_settings, values=["Dark", "Light"], command=self.on_theme_change)
        self.theme_seg.set(self.settings["theme"])
        self.theme_seg.pack(fill=tk.X, pady=5)

        ctk.CTkLabel(inner_settings, text="Comparison Mode:", font=("Arial", 11)).pack(anchor="w", pady=(5, 0))
        self.comp_mode_seg = ctk.CTkSegmentedButton(inner_settings, values=["Merged", "Side-by-Side"], command=self.on_mode_change)
        self.comp_mode_seg.set(self.settings["comparison_mode"])
        self.comp_mode_seg.pack(fill=tk.X, pady=(0, 5))

        self.auto_switch_var = tk.BooleanVar(value=self.settings["auto_switch_new"])
        ctk.CTkSwitch(inner_settings, text="Auto switch to new", variable=self.auto_switch_var,
                      command=self.save_current_settings).pack(anchor="w", pady=10)

        max_files_frame = ctk.CTkFrame(inner_settings, fg_color="transparent")
        max_files_frame.pack(fill=tk.X, pady=5)
        ctk.CTkLabel(max_files_frame, text="Max files (-1=inf):", font=("Arial", 11)).pack(side=tk.LEFT)
        self.max_files_entry = ctk.CTkEntry(max_files_frame, width=50, height=24)
        self.max_files_entry.insert(0, str(self.settings["max_files"]))
        self.max_files_entry.pack(side=tk.RIGHT)
        self.max_files_entry.bind("<Return>", self.save_current_settings)
        self.max_files_entry.bind("<FocusOut>", self.save_current_settings)

        # 2. Right Panel (Graphs Container)
        self.graphs_container = ctk.CTkFrame(self.paned_window, corner_radius=0, fg_color="transparent")

        if self.settings.get("sidebar_collapsed", False):
            self.collapsed_sidebar.pack(side=tk.LEFT, fill=tk.Y, before=self.paned_window)
            self.paned_window.add(self.graphs_container, minsize=400)
        else:
            self.paned_window.add(self.left_frame, minsize=250)
            self.paned_window.add(self.graphs_container, minsize=400)
            self.root.after(50, lambda: self.paned_window.sash_place(0, self.settings.get("sash_position", 300), 0))

        self.placeholder_frame = ctk.CTkFrame(self.graphs_container, fg_color="transparent")
        ctk.CTkLabel(self.placeholder_frame, text="No runs selected or available.", font=("Arial", 20, "bold"),
                     text_color=("gray60", "gray40")).place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        self.apply_layout()

    # --- UI EVENT HANDLERS ---
    def collapse_sidebar(self) -> None:
        """Hides the left panel and displays a compact collapse sidebar."""
        try:
            sash_coords = self.paned_window.sash_coord(0)
            if sash_coords:
                self.settings["sash_position"] = sash_coords[0]
        except tk.TclError:
            pass

        self.settings["sidebar_collapsed"] = True
        save_settings(self.settings)

        self.paned_window.forget(self.graphs_container)
        self.paned_window.forget(self.left_frame)
        self.collapsed_sidebar.pack(side=tk.LEFT, fill=tk.Y, before=self.paned_window)
        self.paned_window.add(self.graphs_container, minsize=400)

    def expand_sidebar(self) -> None:
        """Restores the full settings panel."""
        self.settings["sidebar_collapsed"] = False
        save_settings(self.settings)

        self.collapsed_sidebar.pack_forget()
        self.paned_window.forget(self.graphs_container)
        self.paned_window.add(self.left_frame, minsize=250)
        self.paned_window.add(self.graphs_container, minsize=400)

        self.root.update_idletasks()
        self.paned_window.sash_place(0, self.settings.get("sash_position", 300), 0)

    def save_current_settings(self, event=None) -> None:
        """Parses UI variables and commits them to the configuration file."""
        if getattr(self, '_is_saving_settings', False):
            return
        self._is_saving_settings = True

        self.root.after(50, self._perform_save, event)

    def _perform_save(self, event) -> None:
        """Internal execution method for delayed save and layout application."""
        try:
            try:
                max_f = int(self.max_files_entry.get())
            except ValueError:
                max_f = -1

            if event and hasattr(event, 'keysym') and event.keysym == "Return":
                self.root.focus_set()

            if 0 <= max_f < len(self.known_files) and max_f != self.settings.get("max_files", -1):
                num_to_delete = len(self.known_files) - max_f
                msg = f"Changing max files to {max_f} will delete the {num_to_delete} oldest run(s).\n\nProceed?"
                if not messagebox.askyesno("Confirm Deletion", msg):
                    self.max_files_entry.delete(0, tk.END)
                    self.max_files_entry.insert(0, str(self.settings.get("max_files", -1)))
                    return

            if not self.settings.get("sidebar_collapsed", False):
                try:
                    sash_coords = self.paned_window.sash_coord(0)
                    if sash_coords:
                        self.settings["sash_position"] = sash_coords[0]
                except tk.TclError:
                    pass

            self.settings.update({
                "auto_switch_new": self.auto_switch_var.get(),
                "max_files": max_f,
                "comparison_mode": self.comp_mode_seg.get(),
                "theme": self.theme_seg.get()
            })
            save_settings(self.settings)
            self.enforce_max_files()
        finally:
            self._is_saving_settings = False

    def on_theme_change(self, value: str) -> None:
        """Handles theme toggle updates."""
        self.settings["theme"] = value
        self.apply_theme_settings()
        self.sync_theme_to_widgets()
        self.update_plot()
        self.save_current_settings()

    def on_mode_change(self, value: str) -> None:
        """Handles comparison mode toggle updates."""
        self.settings["comparison_mode"] = value
        self.apply_layout()
        self.update_plot()
        self.save_current_settings()

    def on_listbox_select(self, event=None) -> None:
        """Handles selection events from the main Listbox."""
        indices = self.listbox.curselection()
        if not indices and self.known_files:
            if self.selected_identifiers:
                self.sync_listbox_selection()
                return
            else:
                self.listbox.selection_set(0)
                indices = (0,)

        self.selected_identifiers = [self.known_files[i][0] for i in indices if i < len(self.known_files)]
        self.sync_listbox_selection()
        self.apply_layout()
        self.update_plot()

    def sync_listbox_selection(self) -> None:
        """Synchronizes the visual selection of the Listbox with internal state."""
        self.listbox.selection_clear(0, tk.END)
        for i, (ident, _, _, _, _) in enumerate(self.known_files):
            if ident in self.selected_identifiers:
                self.listbox.selection_set(i)

    # --- LAYOUT MANAGEMENT ---
    def get_or_create_graph(self, g_id: str, title: str) -> GraphWidget:
        """Retrieves an existing GraphWidget by ID or initializes a new one."""
        if g_id not in self.graphs:
            self.graphs[g_id] = GraphWidget(self.graphs_container, g_id, title, self)
            self._sync_widget_theme(self.graphs[g_id])
        else:
            self.graphs[g_id].title_label.configure(text=title)
        return self.graphs[g_id]

    def set_fullscreen_widget(self, widget: GraphWidget) -> None:
        """Assigns the target graph to consume all container space."""
        self.fullscreen_widget = widget
        self.apply_layout()

    def apply_layout(self) -> None:
        """Calculates and renders grid constraints for active graphs."""
        for gw in self.graphs.values():
            gw.grid_forget()

        for i in range(20):
            self.graphs_container.grid_columnconfigure(i, weight=0, uniform="")

        if not self.selected_identifiers:
            self.placeholder_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
            self.graphs_container.grid_columnconfigure(0, weight=1)
            self.graphs_container.grid_rowconfigure(0, weight=1)
            self.graphs_container.grid_rowconfigure(1, weight=1)
            return
        else:
            self.placeholder_frame.grid_forget()

        if self.fullscreen_widget:
            self.graphs_container.grid_columnconfigure(0, weight=1, uniform="colGroup")
            self.graphs_container.grid_rowconfigure(0, weight=1)
            self.graphs_container.grid_rowconfigure(1, weight=0)
            self.fullscreen_widget.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
            if self.fullscreen_widget.content_frame.winfo_manager() == "":
                self.fullscreen_widget.content_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
            return

        mode = self.settings["comparison_mode"]
        active_widgets = []

        if mode == "Merged" or len(self.selected_identifiers) <= 1:
            g_r = self.get_or_create_graph("merged_r", "Runtime vs Entities")
            g_l = self.get_or_create_graph("merged_l", "Loop Times")
            active_widgets.append((g_r, g_l, 0))
        else:
            for i, ident in enumerate(self.selected_identifiers):
                g_r = self.get_or_create_graph(f"r_{ident}", f"Runtime [ {ident} ]")
                g_l = self.get_or_create_graph(f"l_{ident}", f"Loop Times [ {ident} ]")
                active_widgets.append((g_r, g_l, i))

        row_0_weight = 0
        row_1_weight = 0

        for g_r, g_l, col_idx in active_widgets:
            self.graphs_container.grid_columnconfigure(col_idx, weight=1, uniform="colGroup")

            if g_r.is_minimized:
                g_r.content_frame.pack_forget()
                g_r.grid(row=0, column=col_idx, sticky="new", padx=5, pady=5)
            else:
                if g_r.content_frame.winfo_manager() == "":
                    g_r.content_frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
                g_r.grid(row=0, column=col_idx, sticky="nsew", padx=5, pady=5)
                row_0_weight = 1

            if g_l.is_minimized:
                g_l.content_frame.pack_forget()
                g_l.grid(row=1, column=col_idx, sticky="new", padx=5, pady=5)
            else:
                if g_l.content_frame.winfo_manager() == "":
                    g_l.content_frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
                g_l.grid(row=1, column=col_idx, sticky="nsew", padx=5, pady=5)
                row_1_weight = 1

        self.graphs_container.grid_rowconfigure(0, weight=row_0_weight)
        self.graphs_container.grid_rowconfigure(1, weight=row_1_weight)

    # --- FILE SYSTEM POLLING ---
    def enforce_max_files(self) -> None:
        """Deletes files exceeding the defined max limitation limit."""
        max_f = self.settings.get("max_files", -1)
        if max_f < 0:
            return

        if len(self.known_files) > max_f:
            files_to_remove = self.known_files[max_f:]
            for f in files_to_remove:
                ident, _, _, g_path, l_path = f
                if g_path and os.path.exists(g_path):
                    os.remove(g_path)
                if l_path and os.path.exists(l_path):
                    os.remove(l_path)
                self.data_cache.pop(ident, None)

            self.known_files = self.known_files[:max_f]
            self.selected_identifiers = [i for i in self.selected_identifiers if i in [k[0] for k in self.known_files]]
            self.refresh_file_list_ui()
            self.apply_layout()
            self.update_plot()

    def poll_directory(self) -> None:
        """Scans the directory for file changes and updates structures."""
        grouped_files = {}

        for filepath in glob.glob(os.path.join(self.debug_dir, "*.json")):
            try:
                mtime = os.path.getmtime(filepath)
                filename = os.path.basename(filepath)
                identifier = filename
                is_graphic, is_logic = False, False

                if filename.startswith("graphic_debug_") and filename.endswith(".json"):
                    identifier = filename[len("graphic_debug_"):-5]
                    is_graphic = True
                elif filename.startswith("logic_debug_") and filename.endswith(".json"):
                    identifier = filename[len("logic_debug_"):-5]
                    is_logic = True
                else:
                    continue

                if identifier not in grouped_files:
                    grouped_files[identifier] = {'graphic': None, 'logic': None, 'mtime': 0}

                if is_graphic: grouped_files[identifier]['graphic'] = filepath
                if is_logic: grouped_files[identifier]['logic'] = filepath
                grouped_files[identifier]['mtime'] = max(grouped_files[identifier]['mtime'], mtime)
            except OSError:
                continue

        files_data = []
        for ident, info in grouped_files.items():
            dt = datetime.datetime.fromtimestamp(info['mtime']).strftime('%H:%M:%S %d.%m.')
            display = f"{ident} ({dt})"
            files_data.append((ident, info['mtime'], display, info['graphic'], info['logic']))

        files_data.sort(key=lambda x: x[1], reverse=True)

        list_changed = [f[0] for f in files_data] != [f[0] for f in self.known_files]

        if list_changed:
            new_idents = [f[0] for f in files_data if f[0] not in [k[0] for k in self.known_files]]
            self.known_files = files_data

            max_f = self.settings.get("max_files", -1)
            if max_f >= 0 and len(self.known_files) > max_f:
                self.enforce_max_files()

            if self.settings.get("auto_switch_new", True) and new_idents:
                current_sel_count = max(1, len(self.selected_identifiers))
                combined = new_idents + self.selected_identifiers
                self.selected_identifiers = combined[:current_sel_count]

            self.refresh_file_list_ui()
            self.apply_layout()
            self.update_plot()
        else:
            needs_replot = False
            for ident in self.selected_identifiers:
                current = next((f for f in files_data if f[0] == ident), None)
                cached_mtime = self.data_cache.get(ident, (0, None))[0]
                if current and current[1] != cached_mtime:
                    needs_replot = True
                    for i, kf in enumerate(self.known_files):
                        if kf[0] == ident:
                            self.known_files[i] = current
                            break
            if needs_replot:
                self.update_plot()

        self.root.after(1000, self.poll_directory)

    def refresh_file_list_ui(self) -> None:
        """Fully redraws the Listbox contents."""
        self.listbox.delete(0, tk.END)
        for ident, _, display, _, _ in self.known_files:
            self.listbox.insert(tk.END, display)
        self.sync_listbox_selection()

    def get_data(self, identifier: str, graphic_filepath: str, logic_filepath: str, mtime: float) -> dict:
        """Fetches and caches merged application diagnostic data."""
        if identifier in self.data_cache and self.data_cache[identifier][0] == mtime:
            return self.data_cache[identifier][1]

        combined_data = {}
        try:
            if graphic_filepath and os.path.exists(graphic_filepath):
                with open(graphic_filepath, "r") as f:
                    combined_data.update(json.load(f))
            if logic_filepath and os.path.exists(logic_filepath):
                with open(logic_filepath, "r") as f:
                    combined_data.update(json.load(f))
            self.data_cache[identifier] = (mtime, combined_data)
            return combined_data
        except (json.JSONDecodeError, OSError):
            return self.data_cache.get(identifier, (0, {}))[1]

    # --- PLOTTING LOGIC ---
    def update_plot(self) -> None:
        """Updates and renders the visual graphs."""
        for gw in self.graphs.values():
            gw.ax.clear()
            if gw.ax_twin:
                gw.ax_twin.remove()
                gw.ax_twin = None

        mode = self.settings["comparison_mode"]
        is_multi = len(self.selected_identifiers) > 1 and mode == "Merged"

        color_families = [
            ('#1f77b4', '#004c99', '#aec7e8'), # Blues
            ('#d62728', '#990000', '#ff9896'), # Reds
            ('#2ca02c', '#006600', '#98df8a'), # Greens
            ('#9467bd', '#5a009d', '#c5b0d5'), # Purples
            ('#ff7f0e', '#cc5500', '#ffbb78'), # Oranges
        ]

        for idx, identifier in enumerate(self.selected_identifiers):
            file_info = next((f for f in self.known_files if f[0] == identifier), None)
            if not file_info:
                continue

            ident, mtime, _, graphic_filepath, logic_filepath = file_info
            data = self.get_data(identifier, graphic_filepath, logic_filepath, mtime)
            if not data:
                continue

            if mode == "Merged" or len(self.selected_identifiers) <= 1:
                target_r = self.graphs.get("merged_r")
                target_l = self.graphs.get("merged_l")
            else:
                target_r = self.graphs.get(f"r_{ident}")
                target_l = self.graphs.get(f"l_{ident}")

            if not target_r or not target_l:
                continue

            if target_r.ax_twin is None:
                target_r.ax_twin = target_r.ax.twinx()
                self._sync_widget_theme(target_r)

            if not is_multi:
                c_pygame, c_logic, c_ent = "orange", "blue", "tab:red"
            else:
                c_pygame, c_logic, c_ent = color_families[idx % len(color_families)]

            prefix = f"[{identifier}] " if is_multi else ""

            pygame_xs = [v[0] for v in data.get("pygame", [])]
            pygame_ys = [v[1] * 1000 for v in data.get("pygame", [])]
            logic_xs = [v[0] for v in data.get("logic", [])[2:]]
            logic_ys = [v[1] * 1000 for v in data.get("logic", [])[2:]]
            bullets_xs = [v[0] for v in data.get("bullets", [])]
            n_bullets = [v[1] for v in data.get("bullets", [])]
            bullets_ys = [(v[2] * 1000 if v[2] is not None else None) for v in data.get("bullets", [])]

            av_bullet_xs, av_bullet_ys = [], []
            if n_bullets:
                av_bullets_ys_tmp = [None] * (max(n_bullets) + 1)
                for nb, lt in zip(n_bullets, bullets_ys):
                    if lt is None:
                        continue
                    if av_bullets_ys_tmp[nb] is None:
                        av_bullets_ys_tmp[nb] = []
                    av_bullets_ys_tmp[nb].append(lt)

                av_bullet_ys_full = [None] * (max(n_bullets) + 1)
                av_bullet_xs_full = list(range(len(av_bullet_ys_full)))
                for nb in range(len(av_bullets_ys_tmp)):
                    times = av_bullets_ys_tmp[nb]
                    if not times:
                        av_bullet_xs_full[nb] = None
                        continue
                    av_bullet_ys_full[nb] = sum(times) / len(times)

                av_bullet_xs = [v for v in av_bullet_xs_full if v is not None]
                av_bullet_ys = [v for v in av_bullet_ys_full if v is not None]

            target_r.ax.plot(pygame_xs, pygame_ys, label=f"{prefix}pygame", color=c_pygame)
            target_r.ax.plot(logic_xs, logic_ys, label=f"{prefix}logic", color=c_logic)
            target_r.ax_twin.plot(bullets_xs, n_bullets, color=c_ent, label=f"{prefix}entities",
                                  linestyle='--' if is_multi else '-')

            target_l.ax.scatter(n_bullets, bullets_ys, label=f"{prefix}loops", color=c_logic, alpha=0.5)
            target_l.ax.plot(av_bullet_xs, av_bullet_ys, label=f"{prefix}avg", color=c_ent, linewidth=2)

        for gw in self.graphs.values():
            if not gw.ax.lines and not gw.ax.collections:
                continue

            is_r_graph = gw.graph_id.startswith("merged_r") or gw.graph_id.startswith("r_")

            if is_r_graph:
                gw.ax.set_xlabel("Time (s)")
                gw.ax.set_ylabel("Loop time (ms)")
                gw.ax.grid(True, alpha=0.3)

                lines1, labels1 = gw.ax.get_legend_handles_labels()
                lines2, labels2 = gw.ax_twin.get_legend_handles_labels() if gw.ax_twin else ([], [])

                if gw.ax_twin:
                    gw.ax_twin.set_ylabel('n (entities)', color='tab:red')
                    gw.ax_twin.yaxis.set_label_position("right")
                    gw.ax_twin.yaxis.tick_right()
                    gw.ax_twin.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize='small')
                else:
                    gw.ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize='small')

            else:
                gw.ax.set_xlabel("Entities (n)")
                gw.ax.set_ylabel("Iteration time (ms)")
                gw.ax.grid(True, alpha=0.3)
                gw.ax.legend(loc='upper left', fontsize='small')

            gw.fig.canvas.draw()
            gw.setup_interactive_legend()

            gw.toolbar.update()
            if hasattr(gw.toolbar, '_nav_stack'):
                gw.toolbar._nav_stack.clear()
            gw.toolbar.push_current()


if __name__ == "__main__":
    root = ctk.CTk()
    app = DebugAnalyzerApp(root)
    root.protocol("WM_DELETE_WINDOW", root.quit)
    root.mainloop()

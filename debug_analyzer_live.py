"""
debug_analyzer.py

Live dashboard for analyzing the runtimes of amoginatorium.
Features live-reloading, multi-file comparison, background thread caching,
interactive native legends, dynamic space reclamation, and batch toggles.

Author: Nilusink (Rewritten for Live GUI with CustomTkinter)
"""
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import json
import os
import glob
import typing as tp
import datetime
import threading

os.makedirs("debug", exist_ok=True)

# --- SETTINGS MANAGEMENT ---
SETTINGS_FILE = "debug_viewer_settings.json"
DEFAULT_SETTINGS = {
    "auto_switch_new": True,
    "auto_switch_mode": "Oldest",  # "Oldest", "Newest", or "Add"
    "max_files": -1,
    "comparison_mode": "Merged",  # "Merged" or "Side-by-Side"
    "theme": "Dark",  # "Dark" or "Light"
    "sash_position": 300,
    "sidebar_collapsed": False,
    "batch_rules": {
        "pygame": "-", "logic": "-", "entities": "-",
        "top": "-", "bot": "-"
    }
}


def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                settings = json.load(f)

                # Ensure all nested defaults exist
                for k, v in DEFAULT_SETTINGS.items():
                    if k not in settings:
                        settings[k] = v
                if "batch_rules" not in settings:
                    settings["batch_rules"] = DEFAULT_SETTINGS["batch_rules"].copy()

                return settings
        except (json.JSONDecodeError, OSError):
            pass
    return DEFAULT_SETTINGS.copy()


def save_settings(settings):
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=4)
    except OSError:
        pass


# --- CUSTOM GRAPH WIDGET ---
class GraphWidget(ctk.CTkFrame):
    """
    GraphWidget

    A custom frame containing a Matplotlib figure, toolbar, and interactive controls.
    """
    __slots__ = (
        "graph_id", "app", "is_minimized", "is_fullscreen", "header",
        "title_label", "btn_full", "btn_min", "content_frame",
        "loading_label", "fig", "ax", "ax_twin", "canvas", "toolbar", "linedict"
    )

    def __init__(self, master: tk.Widget, graph_id: str, title_text: str,
                 app: 'DebugAnalyzerApp',
                 **kwargs: tp.Any) -> None:
        """
        Initializes the graph widget.

        :param master: Parent tkinter widget.
        :param graph_id: Unique identifier for the graph.
        :param title_text: Text displayed in the header.
        :param app: Reference to the main application instance.
        """
        super().__init__(master, corner_radius=4, bg_color=app.pw_bg, **kwargs)
        self.graph_id = graph_id
        self.app = app
        self.is_minimized = False
        self.is_fullscreen = False

        # 1. Header (Window Title Bar)
        self.header = ctk.CTkFrame(self, height=35, corner_radius=4)
        self.header.pack(fill="x", padx=1, pady=(1, 0))
        self.header.pack_propagate(False)

        self.title_label = ctk.CTkLabel(self.header, text=title_text,
                                        font=("Arial", 12, "bold"))
        self.title_label.pack(side="left", padx=10)

        self.btn_full = ctk.CTkButton(self.header, text="⛶", width=30, height=25,
                                      command=self.toggle_fullscreen,
                                      fg_color="transparent",
                                      hover_color=("gray75", "gray40"))
        self.btn_full.pack(side=tk.RIGHT, padx=2)

        self.btn_min = ctk.CTkButton(self.header, text="▼", width=30, height=25,
                                     command=self.toggle_minimize,
                                     fg_color="transparent",
                                     hover_color=("gray75", "gray40"))
        self.btn_min.pack(side=tk.RIGHT, padx=2)

        # 2. Content Frame (Native tk.Frame prevents CTk resize jittering)
        self.content_frame = tk.Frame(self, bg=app.graph_bg)
        self.content_frame.pack(fill="both", expand=True, padx=1, pady=1)

        # Loading Overlay
        self.loading_label = ctk.CTkLabel(self, text="Processing Data...",
                                          font=("Arial", 16, "bold"),
                                          fg_color=app.graph_bg)

        # 3. Matplotlib Layout
        self.fig = plt.Figure(figsize=(4, 3), dpi=100, layout="constrained")
        self.ax = self.fig.add_subplot(111)
        self.ax_twin = None

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.content_frame)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.content_frame,
                                            pack_toolbar=False)

        # Kill the white focus border natively present on tk Canvas
        self.canvas.get_tk_widget().configure(highlightthickness=0, bd=0)
        self.fig.patch.set_linewidth(0)

        self.canvas.get_tk_widget().pack(side=tk.TOP, fill="both", expand=True)
        self.toolbar.pack(side="bottom", fill="x")

        self.linedict = {}
        self.fig.canvas.mpl_connect('pick_event', self.on_pick)  # noqa

    def toggle_minimize(self) -> None:
        """
        Toggles the minimized state of the graph to reclaim vertical space.
        """
        if self.is_fullscreen: return

        # Break the rule since the user manually clicked it
        is_top = self.graph_id.startswith("merged_r") or self.graph_id.startswith("r_")
        self.app.override_rule("top" if is_top else "bot")

        self.is_minimized = not self.is_minimized
        self.btn_min.configure(text="▶" if self.is_minimized else "▼")
        self.app.root.after(10, self.app.apply_layout)

    def toggle_fullscreen(self) -> None:
        """
        Toggles the fullscreen state of the specific graph.
        """
        self.is_fullscreen = not self.is_fullscreen
        self.btn_full.configure(text="🗗" if self.is_fullscreen else "⛶")
        self.app.root.after(10, lambda: self.app.set_fullscreen_widget(
            self if self.is_fullscreen else None))

    def setup_interactive_legend(self) -> None:
        """
        Sets up pickers on legend elements to allow toggling line visibility.
        """
        target_ax = self.ax_twin if self.ax_twin and self.ax_twin.get_legend() else self.ax
        leg = target_ax.get_legend()
        if not leg: return

        orig_handles = {}
        h1, l1 = self.ax.get_legend_handles_labels()
        for h, l in zip(h1, l1): orig_handles[l] = h

        if self.ax_twin:
            h2, l2 = self.ax_twin.get_legend_handles_labels()
            for h, l in zip(h2, l2): orig_handles[l] = h

        self.linedict = {}
        for leg_obj, text_obj in zip(leg.legend_handles, leg.texts):
            leg_obj.set_picker(True)  # type: ignore
            leg_obj.set_pickradius(5)  # noqa
            text_obj.set_picker(True)  # type: ignore

            label = text_obj.get_text()
            orig_obj = orig_handles.get(label)
            if orig_obj:
                self.linedict[leg_obj] = orig_obj
                self.linedict[text_obj] = orig_obj

    def on_pick(self, event: tp.Any) -> None:
        """
        Handles legend pick events to toggle visibility of data series.

        :param event: The Matplotlib pick event.
        """
        artist = event.artist
        origline = self.linedict.get(artist)
        if origline is None: return

        vis = not origline.get_visible()
        origline.set_visible(vis)

        # Identify label and override global rule
        lbl_text = ""
        for t_obj, o_obj in self.linedict.items():
            if o_obj == origline and hasattr(t_obj, "get_text"):
                lbl_text = t_obj.get_text().lower()
                break

        for k in ["pygame", "logic", "entities"]:
            if k in lbl_text: self.app.override_rule(k)

        self.sync_legend_alphas()
        self.rescale_y_axes()
        self.canvas.draw_idle()

    def sync_legend_alphas(self) -> None:
        """
        Synchronizes the alpha transparency of legend text with line visibility.
        """
        target_ax = self.ax_twin if self.ax_twin and self.ax_twin.get_legend() else self.ax
        leg = target_ax.get_legend()
        if not leg: return

        for l_h, l_t in zip(leg.legend_handles, leg.texts):
            origline = self.linedict.get(l_h)
            if origline:
                vis = origline.get_visible()
                l_h.set_alpha(1.0 if vis else 0.3)
                l_t.set_alpha(1.0 if vis else 0.3)

    def rescale_y_axes(self) -> None:
        """
        Dynamically rescales the Y-axis based on currently visible lines.
        """
        for axis in [self.ax, self.ax_twin]:
            if not axis: continue

            y_min, y_max = float('inf'), float('-inf')
            has_visible = False

            # Check standard plots
            for line in axis.get_lines():
                if line.get_visible():
                    ydata = line.get_ydata()
                    valid_y = [y for y in ydata if y is not None and y == y]
                    if valid_y:
                        y_min = min(y_min, min(valid_y))  # type: ignore
                        y_max = max(y_max, max(valid_y))  # type: ignore
                        has_visible = True

            # Check scatter collections
            for collection in axis.collections:
                if collection.get_visible():
                    offsets = collection.get_offsets()
                    if len(offsets) > 0:
                        ydata = offsets[:, 1]
                        valid_y = [y for y in ydata if y is not None and y == y]
                        if valid_y:
                            y_min = min(y_min, min(valid_y))  # type: ignore
                            y_max = max(y_max, max(valid_y))  # type: ignore
                            has_visible = True

            if has_visible:
                margin = (y_max - y_min) * 0.05
                if margin == 0: margin = abs(y_max) * 0.05 if y_max != 0 else 0.1
                bottom = y_min - margin
                top = y_max + margin

                # Visual anchor: Keep bottom pinned to 0 if data naturally starts there
                if y_min >= 0 and bottom < 0: bottom = 0
                axis.set_ylim(bottom, top)


# --- MAIN APP ---
class DebugAnalyzerApp:
    """
    DebugAnalyzerApp

    Main application class for the live debug analyzer dashboard.
    """
    __slots__ = (
        "root", "settings", "debug_dir", "known_files", "selected_identifiers",
        "data_cache", "graphs", "rule_segs", "fullscreen_widget", "_is_plotting",
        "_is_saving_settings", "_is_updating_list", "pw_bg", "left_bg",
        "listbox_bg", "listbox_fg", "listbox_sel", "graph_bg", "header_bg",
        "mpl_bg", "mpl_fg", "collapsed_sidebar", "btn_expand", "paned_window",
        "left_frame", "theme_seg", "comp_mode_seg", "auto_switch_var",
        "auto_mode_seg", "max_files_entry", "listbox_frame", "listbox",
        "graphs_container", "placeholder_frame", "btn_collapse"
    )

    def __init__(self, root: ctk.CTk) -> None:
        """
        Initializes the main application.

        :param root: The CustomTkinter root window.
        """
        self.root = root
        self.root.title("Amoginatorium Debug Analyzer")
        self.root.geometry("1500x900")

        self.settings = load_settings()

        self.debug_dir = "debug"
        os.makedirs(self.debug_dir, exist_ok=True)

        # State tracking
        self.known_files = []
        self.selected_identifiers = []
        self.data_cache = {}
        self.graphs = {}
        self.rule_segs = {}
        self.fullscreen_widget = None

        self._is_plotting = False
        self._is_saving_settings = False
        self._is_updating_list = False

        # Theme variables (initialized in apply_theme_settings)
        self.pw_bg = ""
        self.left_bg = ""
        self.listbox_bg = ""
        self.listbox_fg = ""
        self.listbox_sel = ""
        self.graph_bg = ""
        self.header_bg = ""
        self.mpl_bg = ""
        self.mpl_fg = ""

        self.apply_theme_settings()

        # UI components (initialized in _setup_ui)
        self.collapsed_sidebar = None  # type: ignore
        self.btn_expand = None  # type: ignore
        self.paned_window = None  # type: ignore
        self.left_frame = None  # type: ignore
        self.btn_collapse = None  # type: ignore

        self._setup_ui()
        self.sync_theme_to_widgets()

        self.root.after(200, self.restore_sash_position)
        self.poll_directory()

    def apply_theme_settings(self) -> None:
        """
        Applies colors and styles based on the selected theme.
        """
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
            "figure.facecolor": self.mpl_bg, "axes.facecolor": self.mpl_bg,
            "axes.edgecolor": self.mpl_fg, "axes.labelcolor": self.mpl_fg,
            "text.color": self.mpl_fg, "xtick.color": self.mpl_fg,
            "ytick.color": self.mpl_fg,
        })

    def sync_theme_to_widgets(self) -> None:
        """
        Updates existing widget colors to match the current theme.
        """
        if hasattr(self, 'paned_window'):
            self.paned_window.configure(bg=self.pw_bg)
            self.left_frame.configure(fg_color=self.left_bg)
            self.listbox.configure(bg=self.listbox_bg, fg=self.listbox_fg,
                                   selectbackground=self.listbox_sel)

        if hasattr(self, 'collapsed_sidebar'):
            self.collapsed_sidebar.configure(fg_color=self.left_bg)
            self.btn_expand.configure(text_color=self.mpl_fg)
            self.btn_collapse.configure(text_color=self.mpl_fg)

        for gw in self.graphs.values():
            self._sync_widget_theme(gw)

    def _sync_widget_theme(self, gw: GraphWidget) -> None:
        """
        Synchronizes a specific GraphWidget's theme.

        :param gw: The GraphWidget instance to update.
        """
        gw.configure(bg_color=self.pw_bg)
        gw.content_frame.configure(bg=self.graph_bg)
        gw.loading_label.configure(fg_color=self.graph_bg, text_color=self.mpl_fg)
        gw.header.configure(fg_color=self.header_bg)
        gw.btn_full.configure(text_color=self.mpl_fg)
        gw.btn_min.configure(text_color=self.mpl_fg)
        gw.title_label.configure(text_color=self.mpl_fg)

        gw.fig.patch.set_facecolor(self.mpl_bg)
        gw.ax.set_facecolor(self.mpl_bg)
        gw.ax.tick_params(colors=self.mpl_fg)
        for spine in gw.ax.spines.values(): spine.set_color(self.mpl_fg)

        if gw.ax_twin:
            gw.ax_twin.set_facecolor(self.mpl_bg)
            gw.ax_twin.tick_params(colors=self.mpl_fg)
            for spine in gw.ax_twin.spines.values(): spine.set_color(self.mpl_fg)

        # Clean native unicode toolbar styling
        toolbar_bg = self.header_bg if self.settings["theme"] == "Dark" else "#e5e5e5"
        icons = ["⌂", "◀", "▶", "✥", "🔍", "⚙", "💾"]
        try:
            gw.toolbar.config(background=toolbar_bg)
            icon_idx = 0
            for child in gw.toolbar.winfo_children():
                try:
                    child.config(background=toolbar_bg)
                    if isinstance(child, tk.Label):
                        child.config(foreground=self.mpl_fg)
                    elif isinstance(child, tk.Button):
                        child.config(activebackground=self.pw_bg, bd=0,
                                     foreground=self.mpl_fg)
                        if icon_idx < len(icons):
                            child.config(image="", text=icons[icon_idx],
                                         font=("Segoe UI Symbol", 14))
                            icon_idx += 1
                except (Exception,):
                    pass
        except (Exception,):
            pass

    def _setup_ui(self) -> None:
        """
        Constructs the initial UI layout.
        """
        self.collapsed_sidebar = ctk.CTkFrame(self.root, width=40, corner_radius=0,
                                              fg_color=self.left_bg)
        self.btn_expand = ctk.CTkButton(self.collapsed_sidebar, text="▶", width=30,
                                        height=30,
                                        command=self.expand_sidebar,
                                        fg_color="transparent")
        self.btn_expand.pack(pady=15, padx=5)

        self.paned_window = tk.PanedWindow(self.root, bd=0, sashwidth=6, bg=self.pw_bg,
                                           opaqueresize=False)
        self.paned_window.pack(side="left", fill="both", expand=True)
        self.paned_window.bind("<ButtonRelease-1>",
                               lambda e: self.root.after(50, self.save_current_settings))

        # --- LEFT PANEL ---
        self.left_frame = ctk.CTkFrame(self.paned_window, corner_radius=0,
                                       fg_color=self.left_bg)

        left_header = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        left_header.pack(fill="x", padx=15, pady=(15, 5))
        ctk.CTkLabel(left_header, text="Debug Runs", font=("Arial", 16, "bold")).pack(
            side="left")
        self.btn_collapse = ctk.CTkButton(left_header, text="◀", width=30, height=25,
                                          command=self.collapse_sidebar,
                                          fg_color="transparent")
        self.btn_collapse.pack(side=tk.RIGHT)

        # 1. Settings Area (Packed Bottom)
        settings_frame = ctk.CTkFrame(self.left_frame, corner_radius=8,
                                      fg_color=("gray85", "#222222"))
        settings_frame.pack(fill="x", side="bottom", padx=10, pady=(10, 15))

        inner_settings = ctk.CTkFrame(settings_frame, fg_color="transparent")
        inner_settings.pack(fill="x", padx=15, pady=15)

        ctk.CTkLabel(inner_settings, text="Settings", font=("Arial", 14, "bold")).pack(
            anchor="w", pady=(0, 10))

        self.theme_seg = ctk.CTkSegmentedButton(inner_settings,
                                                values=["Dark", "Light"],
                                                command=self.on_theme_change)
        self.theme_seg.set(self.settings["theme"])
        self.theme_seg.pack(fill="x", pady=5)

        ctk.CTkLabel(inner_settings, text="Comparison Mode:", font=("Arial", 11)).pack(
            anchor="w", pady=(5, 0))
        self.comp_mode_seg = ctk.CTkSegmentedButton(inner_settings,
                                                    values=["Merged", "Side-by-Side"],
                                                    command=self.on_mode_change)
        self.comp_mode_seg.set(self.settings["comparison_mode"])
        self.comp_mode_seg.pack(fill="x", pady=(0, 5))

        sw_frame = ctk.CTkFrame(inner_settings, fg_color="transparent")
        sw_frame.pack(fill="x", pady=5)
        self.auto_switch_var = tk.BooleanVar(value=self.settings["auto_switch_new"])
        ctk.CTkSwitch(sw_frame, text="Auto switch to new:",
                      variable=self.auto_switch_var,
                      command=self.save_current_settings).pack(side="left")

        self.auto_mode_seg = ctk.CTkSegmentedButton(inner_settings,
                                                    values=["Oldest", "Newest", "Add"],
                                                    command=self.on_strat_change)
        self.auto_mode_seg.set(self.settings.get("auto_switch_mode", "Oldest"))
        self.auto_mode_seg.pack(fill="x", pady=(0, 5))

        max_files_frame = ctk.CTkFrame(inner_settings, fg_color="transparent")
        max_files_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(max_files_frame, text="Max files (-1=inf):",
                     font=("Arial", 11)).pack(side="left")
        self.max_files_entry = ctk.CTkEntry(max_files_frame, width=50, height=24)
        self.max_files_entry.insert(0, str(self.settings["max_files"]))
        self.max_files_entry.pack(side=tk.RIGHT)
        self.max_files_entry.bind("<Return>", self.save_current_settings)
        self.max_files_entry.bind("<FocusOut>", self.save_current_settings)

        # 2. Batch Rules Area (Packed Bottom above Settings)
        batch_frame = ctk.CTkFrame(self.left_frame, corner_radius=8,
                                   fg_color=("gray85", "#222222"))
        batch_frame.pack(fill="x", side="bottom", padx=10, pady=(5, 10))

        ctk.CTkLabel(batch_frame, text="Batch Rules", font=("Arial", 12, "bold")).pack(
            anchor="w", padx=10, pady=(5, 0))

        def create_rule_row(parent, target, text):
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(fill="x", padx=10, pady=2)
            ctk.CTkLabel(row, text=text, width=60, anchor="w", font=("Arial", 11)).pack(
                side="left")
            seg = ctk.CTkSegmentedButton(row, values=["Hide", "-", "Show"],
                                         command=lambda v,
                                                        t=target: self.on_rule_change(t,
                                                                                      v))
            seg.set(self.settings["batch_rules"].get(target, "-"))
            seg.pack(side=tk.RIGHT, fill="x", expand=True, padx=(5, 0))
            self.rule_segs[target] = seg

        create_rule_row(batch_frame, "pygame", "Pygame")
        create_rule_row(batch_frame, "logic", "Logic")
        create_rule_row(batch_frame, "entities", "Entities")

        btn_row = ctk.CTkFrame(batch_frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=10, pady=(2, 6))
        ctk.CTkButton(btn_row, text="Hide All", height=24, fg_color="#553333",
                      command=lambda: self.toggle_all_rules("Hide")).pack(side="left",
                                                                          expand=True,
                                                                          padx=2)
        ctk.CTkButton(btn_row, text="Show All", height=24, fg_color="#3a7ebf",
                      command=lambda: self.toggle_all_rules("Show")).pack(side=tk.RIGHT,
                                                                          expand=True,
                                                                          padx=2)

        create_rule_row(batch_frame, "top", "Top Graph")
        create_rule_row(batch_frame, "bot", "Bot Graph")

        # 3. Listbox (Packed filling remaining space)
        self.listbox_frame = ctk.CTkFrame(self.left_frame, corner_radius=0,
                                          fg_color="transparent")
        self.listbox_frame.pack(fill="both", expand=True, padx=10, pady=5)

        list_scroll = ctk.CTkScrollbar(self.listbox_frame)
        list_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox = tk.Listbox(
            self.listbox_frame, selectmode=tk.EXTENDED, bd=0, highlightthickness=0,
            font=("Consolas", 10), activestyle="none", exportselection=False
        )
        self.listbox.pack(side="left", fill="both", expand=True)
        list_scroll.configure(command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=list_scroll.set)
        self.listbox.bind("<<ListboxSelect>>", self.on_listbox_select)

        # --- RIGHT PANEL ---
        self.graphs_container = ctk.CTkFrame(self.paned_window, corner_radius=0,
                                             fg_color="transparent")

        if not self.settings.get("sidebar_collapsed", False):
            self.paned_window.add(self.left_frame, minsize=250)
        else:
            self.collapsed_sidebar.pack(side="left", fill=tk.Y,
                                        before=self.paned_window)

        self.paned_window.add(self.graphs_container, minsize=400)

        self.placeholder_frame = ctk.CTkFrame(self.graphs_container,
                                              fg_color="transparent")
        ctk.CTkLabel(self.placeholder_frame, text="No runs selected or available.",
                     font=("Arial", 20, "bold"),
                     text_color=("gray60", "gray40")).place(relx=0.5, rely=0.5,
                                                            anchor=tk.CENTER)

        self.apply_layout()

    def restore_sash_position(self) -> None:
        """
        Restores the paned window sash position from settings.
        """
        if not self.settings.get("sidebar_collapsed", False):
            try:
                self.paned_window.sash_place(0, self.settings.get("sash_position", 300),
                                             0)
            except tk.TclError:
                pass

    def collapse_sidebar(self) -> None:
        """
        Collapses the left sidebar into a thin strip.
        """
        self.settings["sidebar_collapsed"] = True
        try:
            sash_coords = self.paned_window.sash_coord(0)
            if sash_coords: self.settings["sash_position"] = sash_coords[0]
        except tk.TclError:
            pass

        self.paned_window.forget(self.left_frame)
        self.collapsed_sidebar.pack(side="left", fill=tk.Y, before=self.paned_window)
        self.save_settings_no_focus()

    def expand_sidebar(self) -> None:
        """
        Expands the left sidebar from its collapsed state.
        """
        self.settings["sidebar_collapsed"] = False
        self.collapsed_sidebar.pack_forget()
        self.paned_window.forget(self.graphs_container)
        self.paned_window.add(self.left_frame, minsize=250)
        self.paned_window.add(self.graphs_container, minsize=400)
        self.root.after(10, self.restore_sash_position)
        self.save_settings_no_focus()

    def save_settings_no_focus(self) -> None:
        """
        Saves settings to disk without forcing a focus shift.
        """
        save_settings(self.settings)

    def save_current_settings(self, event: tp.Any = None) -> None:
        """
        Collects UI state and saves settings to disk.

        :param event: Optional event from widget binding.
        """
        if getattr(self, '_is_saving_settings', False): return
        self._is_saving_settings = True

        try:
            max_f = int(self.max_files_entry.get())
        except ValueError:
            max_f = -1

        self.root.focus_set()

        if 0 <= max_f < len(self.known_files) and max_f != self.settings.get(
                "max_files", -1):
            num_to_delete = len(self.known_files) - max_f
            if not messagebox.askyesno("Confirm Deletion",
                                       f"Changing max files to {max_f} will delete the {num_to_delete} oldest run(s).\n\nDo you want to proceed?"):
                self.max_files_entry.delete(0, tk.END)
                self.max_files_entry.insert(0, str(self.settings.get("max_files", -1)))
                self._is_saving_settings = False
                return

        try:
            sash_coords = self.paned_window.sash_coord(0)
            sash_pos = sash_coords[0] if sash_coords else 300
        except tk.TclError:
            sash_pos = self.settings.get("sash_position", 300)

        self.settings.update({
            "auto_switch_new": self.auto_switch_var.get(),
            "auto_switch_mode": self.auto_mode_seg.get(),
            "max_files": max_f,
            "comparison_mode": self.comp_mode_seg.get(),
            "theme": self.theme_seg.get(),
            "sash_position": sash_pos
        })
        save_settings(self.settings)
        self.enforce_max_files()

        self._is_saving_settings = False

    def on_theme_change(self, value: str) -> None:
        """
        Callback for theme segmented button.

        :param value: The selected theme name.
        """
        self.settings["theme"] = value
        self.save_settings_no_focus()
        self.apply_theme_settings()
        self.sync_theme_to_widgets()
        self.update_plot()

    def on_mode_change(self, value: str) -> None:
        """
        Callback for comparison mode segmented button.

        :param value: The selected mode.
        """
        self.settings["comparison_mode"] = value
        self.save_settings_no_focus()
        self.apply_layout()
        self.update_plot()

    def on_strat_change(self, value: str) -> None:
        """
        Callback for auto-switch strategy segmented button.

        :param value: The selected strategy.
        """
        self.save_current_settings()

    def on_listbox_select(self, event=None):
        if getattr(self, '_is_updating_list', False): return

        indices = self.listbox.curselection()
        if not indices and self.known_files:
            if self.selected_identifiers:
                self.sync_listbox_selection()
                return
            else:
                self.listbox.selection_set(0)
                indices = (0,)

        self.selected_identifiers = [self.known_files[i][0] for i in indices if
                                     i < len(self.known_files)]
        self.sync_listbox_selection()
        self.apply_layout()
        self.update_plot()

    def sync_listbox_selection(self) -> None:
        """
        Synchronizes the listbox visual selection with the internal state.
        """
        self._is_updating_list = True
        self.listbox.selection_clear(0, tk.END)
        for i, (ident, _, _, _, _) in enumerate(self.known_files):
            if ident in self.selected_identifiers:
                self.listbox.selection_set(i)
        self._is_updating_list = False

    # --- BATCH RULES ---
    def on_rule_change(self, target: str, value: str) -> None:
        """
        Callback for batch rule segmented buttons.

        :param target: The rule target (e.g., 'pygame').
        :param value: The rule state ('Hide', '-', 'Show').
        """
        self.settings["batch_rules"][target] = value
        self.save_settings_no_focus()

        if target in ["top", "bot"]:
            self.apply_layout()
        else:
            self.apply_visibility_rules()

    def toggle_all_rules(self, state: str) -> None:
        """
        Sets all data visibility rules to a specific state.

        :param state: The target state ('Hide' or 'Show').
        """
        for k in ["pygame", "logic", "entities"]:
            self.rule_segs[k].set(state)
            self.settings["batch_rules"][k] = state
        self.save_settings_no_focus()
        self.apply_visibility_rules()

    def override_rule(self, target: str) -> None:
        """
        Resets a specific rule to neutral ('-') when manually overridden by user.

        :param target: The rule target.
        """
        if target in self.rule_segs:
            self.rule_segs[target].set("-")
            self.settings["batch_rules"][target] = "-"
            self.save_settings_no_focus()

    def apply_visibility_rules(self) -> None:
        """
        Applies batch visibility rules to all active graphs.
        """
        for gw in self.graphs.values():
            axes = [gw.ax]
            if gw.ax_twin: axes.append(gw.ax_twin)
            needs_draw = False

            for axis in axes:
                # Catch all artists including invisible ones to re-enable them
                artists = axis.get_lines() + axis.collections
                for artist in artists:
                    label = artist.get_label()
                    if not label or label.startswith('_'): continue

                    lbl_lower = label.lower()
                    for k in ["pygame", "logic", "entities"]:
                        rule = self.settings["batch_rules"].get(k, "-")
                        if k in lbl_lower and rule != "-":
                            should_be_visible = (rule == "Show")
                            if artist.get_visible() != should_be_visible:
                                artist.set_visible(should_be_visible)
                                needs_draw = True
            if needs_draw:
                gw.sync_legend_alphas()
                gw.rescale_y_axes()
                gw.canvas.draw_idle()

    # --- LAYOUT MANAGEMENT ---
    def get_or_create_graph(self, g_id: str, title: str) -> GraphWidget:
        """
        Retrieves an existing graph widget or creates a new one.

        :param g_id: Unique identifier.
        :param title: Title for the graph header.
        :return: The GraphWidget instance.
        """
        if g_id not in self.graphs:
            self.graphs[g_id] = GraphWidget(self.graphs_container, g_id, title, self)
            self._sync_widget_theme(self.graphs[g_id])
        else:
            self.graphs[g_id].title_label.configure(text=title)
        return self.graphs[g_id]

    def set_fullscreen_widget(self, widget: GraphWidget | None) -> None:
        """
        Sets a specific widget to occupy the entire graph container.

        :param widget: The GraphWidget to maximize, or None to restore grid.
        """
        self.fullscreen_widget = widget
        self.apply_layout()

    def apply_layout(self) -> None:
        """
        Recalculates and applies the grid layout for all active graphs.
        """
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
            self.fullscreen_widget.content_frame.pack(fill="both", expand=True, padx=2,
                                                      pady=2)
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

        rule_top = self.settings["batch_rules"].get("top", "-")
        rule_bot = self.settings["batch_rules"].get("bot", "-")

        for g_r, g_l, col_idx in active_widgets:
            self.graphs_container.grid_columnconfigure(col_idx, weight=1,
                                                       uniform="colGroup")

            # Apply global rules
            if rule_top != "-":
                g_r.is_minimized = (rule_top == "Hide")
                g_r.btn_min.configure(text="▶" if g_r.is_minimized else "▼")
            if rule_bot != "-":
                g_l.is_minimized = (rule_bot == "Hide")
                g_l.btn_min.configure(text="▶" if g_l.is_minimized else "▼")

            if g_r.is_minimized:
                g_r.content_frame.pack_forget()
                g_r.grid(row=0, column=col_idx, sticky="new", padx=5, pady=5)
            else:
                g_r.content_frame.pack(fill="both", expand=True, padx=2, pady=2)
                g_r.grid(row=0, column=col_idx, sticky="nsew", padx=5, pady=5)
                row_0_weight = 1

            if g_l.is_minimized:
                g_l.content_frame.pack_forget()
                g_l.grid(row=1, column=col_idx, sticky="new", padx=5, pady=5)
            else:
                g_l.content_frame.pack(fill="both", expand=True, padx=2, pady=2)
                g_l.grid(row=1, column=col_idx, sticky="nsew", padx=5, pady=5)
                row_1_weight = 1

        self.graphs_container.grid_rowconfigure(0, weight=row_0_weight)
        self.graphs_container.grid_rowconfigure(1, weight=row_1_weight)

    # --- FILE SYSTEM POLLING ---
    def enforce_max_files(self) -> None:
        """
        Deletes old debug files if the count exceeds max_files setting.
        """
        max_f = self.settings["max_files"]
        if max_f < 0: return

        if len(self.known_files) > max_f:
            files_to_remove = self.known_files[max_f:]
            for f in files_to_remove:
                ident, _, _, g_path, l_path = f
                if g_path and os.path.exists(g_path): os.remove(g_path)
                if l_path and os.path.exists(l_path): os.remove(l_path)
                self.data_cache.pop(ident, None)

            self.known_files = self.known_files[:max_f]
            self.selected_identifiers = [i for i in self.selected_identifiers if
                                         i in [k[0] for k in self.known_files]]
            self.refresh_file_list_ui()

    def poll_directory(self) -> None:
        """
        Polls the debug directory for new or updated JSON files.
        """
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
                    grouped_files[identifier] = {'graphic': None, 'logic': None,
                                                 'mtime': 0}

                if is_graphic: grouped_files[identifier]['graphic'] = filepath
                if is_logic: grouped_files[identifier]['logic'] = filepath
                grouped_files[identifier]['mtime'] = max(
                    grouped_files[identifier]['mtime'], mtime)
            except OSError:
                continue

        files_data = []
        for ident, info in grouped_files.items():
            dt = datetime.datetime.fromtimestamp(info['mtime']).strftime(
                '%H:%M:%S %d.%m.')
            display = f"{ident} ({dt})"
            files_data.append(
                (ident, info['mtime'], display, info['graphic'], info['logic']))

        files_data.sort(key=lambda x: x[1], reverse=True)

        list_changed = [f[0] for f in files_data] != [f[0] for f in self.known_files]

        if list_changed:
            new_idents = [f[0] for f in files_data if
                          f[0] not in [k[0] for k in self.known_files]]
            self.known_files = files_data
            self.enforce_max_files()

            if self.settings["auto_switch_new"] and new_idents:
                mtime_map = {f[0]: f[1] for f in self.known_files}

                for new_ident in new_idents:
                    if len(self.selected_identifiers) > 0:
                        filtered_sel = [i for i in self.selected_identifiers if
                                        i in mtime_map]
                        current_sel_sorted = sorted(filtered_sel,
                                                    key=lambda x: mtime_map.get(x, 0))

                        mode = self.settings.get("auto_switch_mode", "Oldest")
                        if len(current_sel_sorted) > 0 and mode != "Add":
                            if mode == "Oldest":
                                removed = current_sel_sorted[0]
                            else:
                                removed = current_sel_sorted[-1]
                            filtered_sel.remove(removed)

                        filtered_sel.append(new_ident)
                        self.selected_identifiers = filtered_sel
                    else:
                        self.selected_identifiers = [new_ident]

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
        """
        Refreshes the items in the sidebar listbox.
        """
        self._is_updating_list = True
        self.listbox.delete(0, tk.END)
        for ident, _, display, _, _ in self.known_files:
            self.listbox.insert(tk.END, display)
        self.sync_listbox_selection()
        self._is_updating_list = False

    def get_data(self, identifier: str, graphic_filepath: str | None,
                 logic_filepath: str | None, mtime: float) -> dict[str, tp.Any]:
        """
        Loads and caches data from JSON files.

        :param identifier: Unique run identifier.
        :param graphic_filepath: Path to graphic debug JSON.
        :param logic_filepath: Path to logic debug JSON.
        :param mtime: Modification time for cache validation.
        :return: Dictionary of debug data.
        """
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

    # --- THREADED PLOTTING LOGIC ---
    def update_plot(self) -> None:
        """
        Triggers a background thread to process data and update plots.
        """
        if self._is_plotting: return
        self._is_plotting = True

        for gw in self.graphs.values():
            if gw.winfo_ismapped():
                gw.loading_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        thread = threading.Thread(target=self._process_data_thread)
        thread.daemon = True
        thread.start()

    def _process_data_thread(self) -> None:
        """
        Background thread worker for data processing.
        """
        try:
            mode = self.settings["comparison_mode"]
            is_multi = len(self.selected_identifiers) > 1 and mode == "Merged"

            color_families = [
                ('#1f77b4', '#004c99', '#aec7e8'),  # Blues
                ('#d62728', '#990000', '#ff9896'),  # Reds
                ('#2ca02c', '#006600', '#98df8a'),  # Greens
                ('#9467bd', '#5a009d', '#c5b0d5'),  # Purples
                ('#ff7f0e', '#cc5500', '#ffbb78'),  # Oranges
            ]

            processed_data = []

            for idx, identifier in enumerate(self.selected_identifiers):
                file_info = next((f for f in self.known_files if f[0] == identifier),
                                 None)
                if not file_info: continue

                ident, mtime, _, graphic_filepath, logic_filepath = file_info
                data = self.get_data(identifier, graphic_filepath, logic_filepath,
                                     mtime)
                if not data: continue

                pygame_xs = [v[0] for v in data.get("pygame", [])]
                pygame_ys = [v[1] * 1000 for v in data.get("pygame", [])]
                logic_xs = [v[0] for v in data.get("logic", [])[2:]]
                logic_ys = [v[1] * 1000 for v in data.get("logic", [])[2:]]
                bullets_xs = [v[0] for v in data.get("bullets", [])]
                n_bullets = [v[1] for v in data.get("bullets", [])]
                bullets_ys = [(v[2] * 1000 if v[2] is not None else None) for v in
                              data.get("bullets", [])]

                av_bullet_xs, av_bullet_ys = [], []
                if n_bullets:
                    av_bullets_ys_tmp = [None] * (max(n_bullets) + 1)
                    for nb, lt in zip(n_bullets, bullets_ys):
                        if lt is None: continue
                        if av_bullets_ys_tmp[nb] is None: av_bullets_ys_tmp[nb] = []
                        av_bullets_ys_tmp[nb].append(lt)

                    av_bullet_ys_full = [None] * (max(n_bullets) + 1)
                    av_bullet_xs_full = list(range(len(av_bullet_ys_full)))
                    for nb in range(len(av_bullets_ys_tmp)):
                        times = av_bullets_ys_tmp[nb]
                        if not times:
                            av_bullet_xs_full[nb] = None
                            continue
                        av_bullet_ys_full[nb] = sum(times) / len(times)  # type: ignore

                    av_bullet_xs = [v for v in av_bullet_xs_full if v is not None]
                    av_bullet_ys = [v for v in av_bullet_ys_full if v is not None]

                processed_data.append({
                    "ident": ident, "idx": idx,
                    "pygame_xs": pygame_xs, "pygame_ys": pygame_ys,
                    "logic_xs": logic_xs, "logic_ys": logic_ys,
                    "bullets_xs": bullets_xs, "n_bullets": n_bullets,
                    "bullets_ys": bullets_ys,
                    "av_bullet_xs": av_bullet_xs, "av_bullet_ys": av_bullet_ys
                })

            self.root.after(0, lambda: self._apply_plots(processed_data, mode, is_multi,
                                                         color_families))
        except (Exception,):
            self.root.after(0, self._cleanup_plotting_state)

    def _apply_plots(self, processed_data: list[dict[str, tp.Any]], mode: str,
                     is_multi: bool, color_families: list[tuple[str, ...]]) -> None:
        """
        Main-thread callback to apply processed data to Matplotlib axes.

        :param processed_data: List of data dictionaries from the worker thread.
        :param mode: Current comparison mode.
        :param is_multi: Whether multiple runs are being merged.
        :param color_families: List of color palettes for multi-run plotting.
        """
        for gw in self.graphs.values():
            gw.ax.clear()
            if gw.ax_twin: gw.ax_twin.clear()

        for pd in processed_data:
            idx = pd["idx"]
            ident = pd["ident"]

            if mode == "Merged" or len(self.selected_identifiers) <= 1:
                target_r = self.graphs.get("merged_r")
                target_l = self.graphs.get("merged_l")
            else:
                target_r = self.graphs.get(f"r_{ident}")
                target_l = self.graphs.get(f"l_{ident}")

            if not target_r or not target_l: continue

            if target_r.ax_twin is None:
                target_r.ax_twin = target_r.ax.twinx()
                self._sync_widget_theme(target_r)

            if not is_multi:
                c_pygame, c_logic, c_ent = "orange", "blue", "tab:red"
            else:
                c_pygame, c_logic, c_ent = color_families[idx % len(color_families)]

            prefix = f"[{ident}] " if is_multi else ""

            target_r.ax.plot(pd["pygame_xs"], pd["pygame_ys"], label=f"{prefix}pygame",
                             color=c_pygame)
            target_r.ax.plot(pd["logic_xs"], pd["logic_ys"], label=f"{prefix}logic",
                             color=c_logic)
            target_r.ax_twin.plot(pd["bullets_xs"], pd["n_bullets"], color=c_ent,
                                  label=f"{prefix}entities",
                                  linestyle='--' if is_multi else '-')

            target_l.ax.scatter(pd["n_bullets"], pd["bullets_ys"],
                                label=f"{prefix}loops", color=c_logic, alpha=0.5)
            target_l.ax.plot(pd["av_bullet_xs"], pd["av_bullet_ys"],
                             label=f"{prefix}avg", color=c_ent, linewidth=2)

        # Setup standard layout and legends BEFORE applying rules to ensure correct initial legend generation
        for gw in self.graphs.values():
            if not gw.ax.lines and not gw.ax.collections:
                continue

            is_r_graph = gw.graph_id.startswith("merged_r") or gw.graph_id.startswith(
                "r_")

            if is_r_graph:
                gw.ax.set_xlabel("Time (s)")
                gw.ax.set_ylabel("Loop time (ms)")
                gw.ax.grid(True, alpha=0.3)

                lines1, labels1 = gw.ax.get_legend_handles_labels()
                lines2, labels2 = gw.ax_twin.get_legend_handles_labels() if gw.ax_twin else (
                    [], [])
                if gw.ax_twin:
                    gw.ax_twin.legend(lines1 + lines2, labels1 + labels2,
                                      loc='upper left', fontsize='small')
                else:
                    gw.ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left',
                                 fontsize='small')

                if gw.ax_twin:
                    gw.ax_twin.set_ylabel('n (entities)', color='tab:red')
                    gw.ax_twin.yaxis.set_label_position("right")
                    gw.ax_twin.yaxis.tick_right()
            else:
                gw.ax.set_xlabel("Entities (n)")
                gw.ax.set_ylabel("Iteration time (ms)")
                gw.ax.grid(True, alpha=0.3)
                gw.ax.legend(loc='upper left', fontsize='small')

            gw.setup_interactive_legend()

        # Enforce batch visibility rules generated while parsing
        self.apply_visibility_rules()

        # Final adjustments, single render pass to eliminate flashing
        for gw in self.graphs.values():
            if not gw.ax.lines and not gw.ax.collections:
                continue

            gw.rescale_y_axes()
            gw.sync_legend_alphas()
            gw.fig.canvas.draw()

            gw.toolbar.update()
            if hasattr(gw.toolbar, '_nav_stack'): gw.toolbar._nav_stack.clear()
            gw.toolbar.push_current()

        self._cleanup_plotting_state()

    def _cleanup_plotting_state(self) -> None:
        """
        Resets the plotting flag and hides loading overlays.
        """
        for gw in self.graphs.values():
            gw.loading_label.place_forget()
        self._is_plotting = False


if __name__ == "__main__":
    root = ctk.CTk()
    app = DebugAnalyzerApp(root)
    root.protocol("WM_DELETE_WINDOW", root.quit)
    root.mainloop()

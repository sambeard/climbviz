import tkinter as tk
from tkinter import Menu
from ui.debug_view import DebugView
from ui.interaction_win import open_interaction_window
from ui.analysis_win import open_analysis_window
from ui.playback_win import open_playback_window
from ui.record_win import open_record_window
from ui.mock_win import open_mock_window
from ui.route_win import open_device_grid_window


class ClimbApp(tk.Tk):
    """
    Tkinter root application for ClimbViz. Hosts the debug view and provides
    a menu bar for opening tools like mock sensors, recorder, and interaction tuning.
    """

    def __init__(self, config, mqtt, device_mgr, buffer, interaction_engine, analysis_engine, playback_engine, recorder, state_manager):
        super().__init__()

        self.title("ClimbViz")
        self.geometry("1200x800")
        self.data_path = config.get("data_path", "data/")
        self.config_data = config
        self.mqtt = mqtt
        self.device_mgr = device_mgr
        self.buffer = buffer
        self.interaction_engine = interaction_engine
        self.analysis_engine = analysis_engine
        self.playback_engine = playback_engine
        self.recorder = recorder
        self.state = state_manager

        self._create_menu_bar()
        self._create_main_debug_view()

    def _create_menu_bar(self):
        menubar = Menu(self)

        # File menu
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=filemenu)

        # Tools menu
        toolsmenu = Menu(menubar, tearoff=0)
        toolsmenu.add_command(label="Interaction Config...", command=self._open_interaction)
        toolsmenu.add_command(label="Analysis Config...", command=self._open_analysis)
        toolsmenu.add_command(label="Recording Tools...", command=self._open_recording)
        toolsmenu.add_command(label="Playback Tools...", command=self._open_playback)
        toolsmenu.add_command(label="Mock Sensors...", command=self._open_mocking)
        toolsmenu.add_command(label="Device Grid…",    command=self._open_device_grid)
        menubar.add_cascade(label="Tools", menu=toolsmenu)

        self.config(menu=menubar)

    def _create_main_debug_view(self):
        debug = DebugView(
            self,
            self.config_data,
            self.mqtt,
            self.device_mgr,
            self.buffer,
            self.interaction_engine,
            self.analysis_engine,
            self.state
        )
        debug.pack(fill="both", expand=True)

    def _open_analysis(self):
        open_analysis_window(self, self.state, self.analysis_engine)

    def _open_interaction(self):
        open_interaction_window(self, self.state, self.interaction_engine)

    def _open_device_grid(self):
        open_device_grid_window(self, self.config_data, self.device_mgr)

    def _open_playback(self):
        open_playback_window(self, self.mqtt, self.state, self.playback_engine)

    def _open_recording(self):
        open_record_window(self, self.data_path, self.recorder, self.state)

    def _open_mocking(self):
        open_mock_window(self, self.mqtt, self.state)

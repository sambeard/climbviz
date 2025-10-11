import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# exactly the same state cycle & colours you specified
STATES = ["Off", "Foot", "Hand", "Start", "Finish"]
COLORS = {
    "Off":    "",
    "Foot":   "yellow",
    "Hand":   "blue",
    "Start":  "green",
    "Finish": "purple",
}

class DeviceGridFrame(tk.Frame):
    def __init__(self, master, board_info):
        super().__init__(master)
        self.rows, self.cols = board_info["rows"], board_info["cols"]
        self.sensors =  board_info["sensor_coords"]
        self.route_dir = board_info["route_dir"]
        self.states = {(r,c): "Off"
                       for r in range(self.rows)
                       for c in range(self.cols)}

        # top bar
        bar = tk.Frame(self)
        bar.pack(fill="x", pady=4)
        self.route_var = tk.StringVar(value="Route A")
        ttk.OptionMenu(bar, self.route_var,
                       "Route A", "Route A","Route B","Route C").pack(side="left")
        ttk.Button(bar, text="Save",    command=self.on_save).pack(side="right", padx=4)
        ttk.Button(bar, text="Display", command=self.on_display).pack(side="right", padx=4)
        ttk.Button(bar, text="Clear",   command=self.clear).pack(side="right")

        # canvas of circles
        size = 40
        cvs = tk.Canvas(self,
                        width=self.cols*size, height=self.rows*size,
                        bg="white", highlightthickness=1,
                        highlightbackground="black")
        cvs.pack(pady=6)
        self.cvs = cvs
        cvs.bind("<Button-1>", self._on_canvas_click)

        for r in range(self.rows):
            for c in range(self.cols):
                x0, y0 = c*size+4, r*size+4
                x1, y1 = x0+size-8, y0+size-8
                tag = f"dev_{r}_{c}"
                w = 3 if (r,c) in self.sensors.values() else 1
                cvs.create_oval(x0, y0, x1, y1,
                                fill="", outline="black",
                                width=w, tags=(tag,))
                cvs.tag_bind(tag, "<Button-1>",
                             lambda e, r=r, c=c: self.toggle(r,c))
    def _on_canvas_click(self, event):
        size = 40
        c = event.x // size
        r = event.y // size
        if (r,c) in self.states:
            self.toggle(r, c)

    def toggle(self, r, c):
        cur = self.states[(r,c)]
        nxt = STATES[(STATES.index(cur)+1) % len(STATES)]
        self.states[(r,c)] = nxt
        self.cvs.itemconfigure(f"dev_{r}_{c}", fill=COLORS[nxt])

    def clear(self):
        for (r,c), _ in list(self.states.items()):
            self.states[(r,c)] = "Off"
            self.cvs.itemconfigure(f"dev_{r}_{c}", fill="")

    def on_save(self):
        fn = filedialog.asksaveasfilename(defaultextension=".json",
                                          filetypes=[("JSON","*.json")],
                                          title="Save device config…")
        if not fn: return
        with open(fn, "w") as f:
            json.dump(self.states, f, indent=2)
        messagebox.showinfo("Saved", f"Configuration written to:\n{fn}")

    def on_display(self):
        # hook in your actual display call here:
        print("DISPLAY:", self.route_var.get(), self.states)

def get_board_info(config):
    board = config.get("board", {})
    board["sensor_coords"] = get_sensor_coords(config)
    board["route_dir"] = get_route_dir(config)
    return board

def get_sensor_coords(config):
    coords = {d["id"]:d["config"]["coordinates"]for d in config["devices"]}
    coords = {k:(v["x"], v["y"]) for k,v in coords.items()}
    return coords


def get_route_dir(config):
    """
    Returns the directory where route configurations are stored.
    """
    return config.get("route_dir", "routes/")

def open_device_grid_window(master, config, device_mgr):
    """
    Opens the “Device Grid” tool window.
    """
    win = tk.Toplevel(master)
    win.title("Device Grid")
    win.geometry("1200x800")

    board_info = get_board_info(config)
    tk.Label(win, text="Configure LEDs",
             font=("Arial", 14, "bold")).pack(pady=8)
    frame = DeviceGridFrame(win, board_info)
    frame.pack(fill="both", expand=True, padx=10, pady=10)

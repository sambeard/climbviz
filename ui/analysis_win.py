import tkinter as tk


def open_analysis_window(master, state_manager, analysis_engine):
    """
    Opens a window to display editable parameters for the current analysis.
    Automatically detects which parameters exist for the active analysis.
    """
    win = tk.Toplevel(master)
    win.title("Analysis Parameters")
    win.geometry("300x300")

    analysis = state_manager.get("analysis/active")
    param_path = f"analysis/params/{analysis}"

    tk.Label(win, text=f"analysis: {analysis}", font=("Arial", 12, "bold")).pack(pady=10)

    param_frame = tk.Frame(win)
    param_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

    params = state_manager.get(param_path, {})
    entry_vars = {}

    def update_param(name, vtype):
        try:
            raw = entry_vars[name].get()
            val = float(raw) if vtype == "float" else int(raw)
            state_manager.set(f"{param_path}/{name}", { "value": val, "type": vtype })
            analysis_engine.get_analysis().update_config({name: val})
            analysis_engine.render()
        except ValueError:
            print(f"[Warning] Invalid {vtype} for {name}: {entry_vars[name].get()}")

    if not params:
        tk.Label(param_frame, text="No parameters registered.").pack()
    else:
        for param, meta in params.items():
            val = meta.get("value", "")
            vtype = meta.get("type", "float")

            row = tk.Frame(param_frame)
            row.pack(fill=tk.X, pady=3)

            tk.Label(row, text=param, width=15, anchor="w").pack(side=tk.LEFT)
            var = tk.StringVar(value=str(val))
            entry_vars[param] = var
            entry = tk.Entry(row, textvariable=var)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

            save_btn = tk.Button(row, text="Apply", command=lambda p=param, t=vtype: update_param(p, t))
            save_btn.pack(side=tk.RIGHT)

    # Close
    tk.Button(win, text="Close", command=win.destroy).pack(pady=10)

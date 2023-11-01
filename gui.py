# Imports
import json
import tkinter as tk
from tkinter import ttk, filedialog
from ttkthemes import ThemedTk
from PIL import Image, ImageTk


def load_config(filename="config.json"):
    with open(filename, 'r') as file:
        return json.load(file)


def save_config(config, filename="config.json"):
    with open(filename, 'w') as file:
        json.dump(config, file)


from serial.tools.list_ports import comports


def get_available_com_ports():
    return [port.device for port in comports()]


# todo: add function for reading config file for run modes
# todo: add function for passing config to and executing run modes


class MainWindow:
    def __init__(self, master: ThemedTk):
        self.master = master
        self.master.title("DIC-link v0.0.1")
        self.master.configure()

        # Load image
        try:
            self.logo_image = ImageTk.PhotoImage(Image.open("logo.png"))
            self.logo_image = ImageTk.PhotoImage(Image.open("logo.png"))
            self.logo = ttk.Label(master, image=self.logo_image)
            self.logo.grid(row=0, column=0, rowspan=6, sticky='sw', padx=10, pady=10)
        except Exception as e:
            print(f"Error loading logo: {e}")

        # Config section
        config_frame = ttk.LabelFrame(master, text="Config", padding=(10, 5))
        config_frame.grid(row=1, column=1, padx=10, pady=10, sticky='ew')

        self.new_config_btn = ttk.Button(config_frame, text="New Config", command=self.new_config)
        self.new_config_btn.pack(padx=10, pady=5, fill='x')

        self.configs = ttk.Combobox(config_frame, values=["Config 1", "Config 2"], width=20)
        self.configs.pack(padx=10, pady=10, fill='x')

        self.select_config_btn = ttk.Button(config_frame, text="Select Config", command=self.select_config)
        self.select_config_btn.pack(padx=10, pady=5, fill='x')

        # Run section
        run_frame = ttk.LabelFrame(master, text="Run", padding=(10, 5))
        run_frame.grid(row=2, column=1, padx=10, pady=10, sticky='ew')

        self.run_mode1_btn = ttk.Button(run_frame, text="Run Mode 1", command=self.run_mode1)
        self.run_mode1_btn.pack(padx=10, pady=5, fill='x')

        self.run_mode2_btn = ttk.Button(run_frame, text="Run Mode 2", command=self.run_mode2)
        self.run_mode2_btn.pack(padx=10, pady=5, fill='x')

    def select_config(self):
        # Logic for selecting the configuration goes here
        pass

    def new_config(self):
        # Open the Config Window
        config_window = tk.Toplevel(self.master)
        ConfigWindow(config_window)

    def run_mode1(self):
        # Logic for running mode 1 goes here
        pass

    def run_mode2(self):
        # Logic for running mode 2 goes here
        pass


# todo: make function for get available com ports
# todo: make functin for get available cameras
# todo: split configwindow into sections with headings using LabelFrame
# todo: add function for saving config settings to config file
# todo: add function for loading existing settings from config file


class ConfigWindow:
    def __init__(self, master: tk.Toplevel):
        self.master = master
        self.master.title("Configuration")
        self.master.configure()

        # Define settings in a dictionary
        self.settings = {
            "FPS Settings": {
                "FPS Config": {"type": "entry", "value": ""},
            },
            "Port Settings": {
                "COM Port Config": {"type": "combobox", "value": get_available_com_ports()},
            },
            "IO Settings": {
                "Input Path": {"type": "filedialog", "value": ""},
                "Output Path": {"type": "filedialog", "value": ""},
            },
            "Camera Settings": {
                "CAM Select": {"type": "combobox", "value": ["CAM1", "CAM2"]},
            }
        }

        self.widgets = {}  # To store references to created widgets

        for idx, (section, controls) in enumerate(self.settings.items()):
            frame = ttk.LabelFrame(master, text=section, padding=(10, 5))
            frame.grid(row=idx, column=0, padx=10, pady=10, sticky="ew")
            self.widgets[section] = {}

            for control_idx, (label_text, control) in enumerate(controls.items()):
                ttk.Label(frame, text=label_text).grid(row=control_idx, column=0, padx=10, pady=5, sticky="w")

                if control["type"] == "entry":
                    widget = ttk.Entry(frame)
                    widget.insert(0, control["value"])
                elif control["type"] == "combobox":
                    widget = ttk.Combobox(frame, values=control["value"])
                elif control["type"] == "filedialog":
                    widget = ttk.Entry(frame)
                    widget.insert(0, control["value"])
                    ttk.Button(frame, text="Browse", command=lambda w=widget: self.browse_file(w)).grid(row=control_idx,
                                                                                                        column=2,
                                                                                                        padx=10, pady=5)

                widget.grid(row=control_idx, column=1, padx=10, pady=5, sticky="w")
                self.widgets[section][label_text] = widget

        self.save_config_btn = ttk.Button(master, text="Save Config", command=self.save_config)
        self.save_config_btn.grid(row=len(self.settings), column=0, pady=20)

    def browse_file(self, widget):
        file_path = filedialog.askopenfilename()
        widget.delete(0, tk.END)
        widget.insert(0, file_path)

    def save_config(self):
        config = {}
        for section, controls in self.widgets.items():
            config[section] = {}
            for label_text, widget in controls.items():
                config[section][label_text] = widget.get()

        with open("config.json", "w") as file:
            json.dump(config, file)


if __name__ == "__main__":
    root = ThemedTk(theme="plastik")  # Here, 'arc' is the name of the theme, but there are many others
    app = MainWindow(root)
    root.mainloop()

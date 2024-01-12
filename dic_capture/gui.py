"""This module contains the GUI for the DIC-Capture program. The GUI is used to select settings and run the program.
The main program function is in dic_capture/run.py."""
# =====================================
# Imports
import json
import os
import tkinter as tk
from datetime import datetime
from tkinter import ttk, filedialog, messagebox
from typing import Dict, Union

from PIL import Image
from PIL import ImageTk
from serial.tools.list_ports import comports
from ttkthemes import ThemedTk

from dic_capture.run import run

# =====================================
# Global variables

CONFIG_DIR = "../saved_configs"
DIC_CAPTURE_VERSION = "0.0.3"


# =====================================
# Helper functions for gui. See gui class below.

def run_record_mode(config: Dict):
    """Set the config to record mode and run the program."""
    config["Record Mode"] = True
    run(config)


def run_test_mode(config: Dict):
    """Set the config to test mode and run the program."""
    config["Record Mode"] = False
    run(config)


def list_existing_configs():
    """Return a list of existing config files."""
    return [file for file in os.listdir(CONFIG_DIR) if file.endswith(".json")]


def get_available_com_ports():
    """Get a list of available COM ports."""
    available_com_ports = [str(port.device) for port in comports()]
    if len(available_com_ports) == 0:
        return ["COM1", "COM2"]
    else:
        return ["COM1", "COM2"] + available_com_ports


def get_available_cameras():
    """Get a list of available cameras."""
    # todo: update this to use neoapi to check for available cameras
    return ["Camera auto-detect not yet implemented."]


def browse_file(widget):
    """Open a file dialog and insert the selected file path into the specified widget."""
    file_path = filedialog.askopenfilename()
    widget.delete(0, tk.END)
    widget.insert(0, file_path)


def save_config_file():
    """Save the current settings to the selected file."""
    pass


def save_as_config_file():
    """Save the current settings to a new config file."""
    pass


def update_config(event, select_config_combobox, config_widgets):
    """Update the settings in the Config frame based on the selected config file."""
    if not messagebox.askokcancel("Warning", "Existing settings selections will be overridden. Continue?"):
        return

    # Get the selected file
    selected_file = select_config_combobox.get()

    # Load the configuration from the selected file
    with open(os.path.join(CONFIG_DIR, selected_file), 'r') as file:
        config = json.load(file)

    # Update the settings in the Config frame
    for frame_name, frame_controls in config_widgets.items():
        for control_name, control_options in frame_controls.items():
            # Get the control widget
            control = control_options["widget"]

            # Get the value from the loaded config
            value = config.get(frame_name, {}).get(control_name, "")

            # Update the control widget with the loaded value
            if isinstance(control, ttk.Entry) or isinstance(control, ttk.Combobox):
                control.delete(0, tk.END)
                control.insert(0, value)


# =====================================
# GUI class

packing = dict(padx=4, pady=10, fill='x')


class GUI:
    def __init__(self, master: ThemedTk):
        # Dictionary of settings for creating the widgets in the config frame
        self.config_widgets = {
            "I/O": {
                "Config File": dict(
                    type="savebox", value=list_existing_configs()
                ),
                "Test ID": dict(
                    type="entry", value="Test_ID_" + datetime.now().strftime("%Y%m%d_%H%M%S")
                ),
                "Output Folder": dict(
                    type="filedialog", value=os.getcwd()
                ),
            },
            "Arduino": {
                "Choose COM Port:": dict(
                    type="combobox", value=get_available_com_ports()
                ),
                "Baud Rate": dict(
                    type="entry", value=115200
                ),
                "Max Buffer": dict(
                    type="entry", value=3
                ),
            },
            "Camera 1": {
                "Camera Source": dict(
                    type="combobox", value="P1-6"
                ),
                "Exposure Time (ms)": dict(
                    type="entry", value=1.6
                ),
                'FPS Stages (e.g. "0, 0.1, 0, 0.1")': dict(
                    type="entry", value="0, 0.1"
                ),
            },
            "Camera 2": {
                "Camera Source": dict(
                    type="combobox", value="P1-5"
                ),
                "Exposure Time (ms)": dict(
                    type="entry", value=1.6
                ),
                'FPS Stages (e.g. "0, 0.1, 0, 0.1")': dict(
                    type="entry", value="0, 0.1"
                ),
            },
            "Camera 3": {
                "Camera Source": dict(
                    type="combobox", value=get_available_cameras()
                ),
                "Exposure Time (ms)": dict(
                    type="entry", value=""
                ),
                'FPS Stages (e.g. "0, 0.1, 0, 0.1")': dict(
                    type="entry", value=""
                ),
            },
        }

        # Create the main window
        self.master = master
        self.master.title('DIC-Capture v' + DIC_CAPTURE_VERSION)
        self.master.configure()

        # Create the frames
        self.create_config_frame()
        self.create_run_frame()
        self.load_logo()

        # Variable for storing the current settings
        self.current_settings = dict()

    def create_run_frame(self):
        """Create a frame for running the program."""
        # Create the frame
        frame = ttk.LabelFrame(self.master, text="Run", borderwidth=4)
        frame.grid(row=0, column=0, sticky='ew', padx=10, pady=10)

        # Get all the current settings in the config frame
        self.update_current_settings()

        # Create the run record mode button
        run_record_button = self._create_control(parent=frame, name="Run Record Mode",
                                                 widget_options=dict(type="button", command=lambda: run_record_mode(
                                                     self.current_settings)))
        run_record_button.pack(**packing)

        # Create the run test mode button
        run_test_button = self._create_control(parent=frame, name="Run Test Mode",
                                               widget_options=dict(type="button", command=lambda: run_test_mode(
                                                   self.current_settings)))
        run_test_button.pack(**packing)

    def create_config_frame(self):
        """Create a frame for configuring settings."""
        # Create the outer frame
        frame = ttk.Frame(self.master, relief="sunken", borderwidth=2)
        frame.grid(row=0, rowspan=2, column=1, sticky='nsew', padx=10, pady=10)

        # IO Config Frame
        io_config_frame = ttk.LabelFrame(frame, text="I/O", borderwidth=4)
        io_config_frame.grid(row=0, column=0, columnspan=2, sticky='nsew', padx=10, pady=10)
        self._add_controls(parent=io_config_frame, control_dict=self.config_widgets["I/O"])

        # Arduino Config Frame
        arduino_config_frame = ttk.LabelFrame(frame, text="Arduino", borderwidth=4)
        arduino_config_frame.grid(row=0, column=2, sticky='nsew', padx=10, pady=10)
        self._add_controls(parent=arduino_config_frame, control_dict=self.config_widgets["Arduino"])

        # Camera Config Frames adjacent to each other
        camera_config_frame_1 = ttk.LabelFrame(frame, text="Camera 1", borderwidth=4)
        camera_config_frame_1.grid(row=2, column=0, sticky='nsew', padx=10, pady=10)
        self._add_controls(parent=camera_config_frame_1, control_dict=self.config_widgets["Camera 1"])

        camera_config_frame_2 = ttk.LabelFrame(frame, text="Camera 2", borderwidth=4)
        camera_config_frame_2.grid(row=2, column=1, sticky='nsew', padx=10, pady=10)
        self._add_controls(parent=camera_config_frame_2, control_dict=self.config_widgets["Camera 2"])

        camera_config_frame_3 = ttk.LabelFrame(frame, text="Camera 3", borderwidth=4)
        camera_config_frame_3.grid(row=2, column=2, sticky='nsew', padx=10, pady=10)
        self._add_controls(parent=camera_config_frame_3, control_dict=self.config_widgets["Camera 3"])

    def _add_controls(self, parent: ttk.LabelFrame, control_dict: Dict):
        """Add a control to the parent frame based on the control type and options."""
        for name, option in control_dict.items():
            label = ttk.Label(parent, text=name + ":")
            label.pack({**packing, 'pady': (5, 0)})
            control = self._create_control(parent=parent, name=name, widget_options=option)
            control.pack({**packing, 'pady': 0})
            control_dict[name]["widget"] = control

    def _create_control(self, parent: Union[ttk.LabelFrame, ttk.Frame], name: str, widget_options: Dict):
        """Create a control in the parent frame based on the control type and options."""
        control_type = widget_options["type"]

        if control_type == "button":
            control = ttk.Button(parent, text=name, command=widget_options["command"])

        elif control_type == "entry":
            control = ttk.Entry(parent)
            control.insert(index=0, string=widget_options["value"])

        elif control_type == "combobox":
            control = ttk.Combobox(parent, values=widget_options["value"])

        elif control_type == "filedialog":
            # add a frame with a text entry box and a button
            frame = ttk.Frame(parent)
            frame.pack(padx=0, pady=0, fill='x')
            control = ttk.Entry(frame)
            control.insert(index=0, string=widget_options["value"])
            control.pack(side=tk.LEFT, fill='x', expand=True)  # Make the entry box stretch wider
            button = ttk.Button(frame, text="Browse", command=browse_file)
            button.pack(side=tk.LEFT, padx=4)

        elif control_type == "label":
            control = ttk.Label(parent, text=widget_options["text"])

        elif control_type == "savebox":
            # add a frame with a combobox and two buttons
            frame = ttk.Frame(parent)
            frame.pack(padx=0, pady=0, fill='x')
            control = ttk.Combobox(frame, values=widget_options["value"])
            control.pack(side=tk.LEFT, fill='x', expand=True)
            button = ttk.Button(frame, text="Save", command=save_config_file)
            button.pack(side=tk.LEFT, padx=0)
            button = ttk.Button(frame, text="Save As", command=save_as_config_file)
            button.pack(side=tk.LEFT, padx=4)

            # bind a command to the combobox
            control.bind("<<ComboboxSelected>>", lambda event: update_config(event, control, self.config_widgets))

        else:
            raise Exception(f"Invalid control type: {control_type}")

        return control

    def update_current_settings(self):
        """Get the current settings from the GUI."""
        config = {}

        # Iterate over the frames in the config frame
        for frame_name, frame_controls in self.config_widgets.items():
            frame_config = {}

            # Iterate over the controls in the frame
            for control_name, control_options in frame_controls.items():
                control = control_options["widget"]

                # Get the value from the control widget
                if isinstance(control, ttk.Entry):
                    value = control.get()
                elif isinstance(control, ttk.Combobox):
                    value = control.get()
                else:
                    continue  # Skip non-entry widgets

                frame_config[control_name] = value

            config[frame_name] = frame_config

        self.current_settings = config

    @staticmethod
    def load_config_from_file(config_file_path: str):
        """Load a json config file from the specified path."""
        try:
            with open(config_file_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            messagebox.showerror("Error", f"File not found: {config_file_path}")
        except json.JSONDecodeError:
            messagebox.showerror("Error", f"Invalid JSON file: {config_file_path}")

    def save_config_to_file(self):
        """Read settings from the GUI and save them to a config file."""

        # Open a file dialog to choose where to save the config file
        config_file_path = filedialog.asksaveasfilename(defaultextension=".json")

        # Save the config to the chosen file
        with open(config_file_path, 'w') as file:
            json.dump(config, file, indent=4)

    def load_logo(self):
        """Load the logo image and set the background color to match the logo."""
        try:
            # Load logo image
            image_path = "logo.png"
            self.logo_image = ImageTk.PhotoImage(Image.open(image_path))

            # Create a frame for the logo
            logo_frame = ttk.Frame(self.master)
            logo_frame.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)

            # Add the logo to the frame
            logo = ttk.Label(logo_frame, image=self.logo_image)
            logo.pack()

        except Exception as e:
            print(f"Error loading logo: {e}")


# =====================================
# Main program function

def run_gui():
    """Run the program by opening the GUI."""
    root = ThemedTk(theme="plastik")
    app = GUI(root)
    root.mainloop()


# =====================================
# Helper function for creating a default config file

def make_default_dict():
    """Use current settings from the GUI to create a default config file."""
    # Create the GUI to get the default settings
    root = ThemedTk(theme="plastik")
    app = GUI(root)

    # Initialize an empty dictionary to store the config
    config = {}

    for frame_name, frame_controls in app.config_widgets.items():
        frame_config = {}

        for control_name, control_options in frame_controls.items():
            default_value = control_options.get("value", "")
            frame_config[control_name] = default_value

        config[frame_name] = frame_config  # Add the frame config dicts to the main config dict

    # Write the default config to a json file
    config_json = json.dumps(config, indent=4)
    with open('default_config_file_auto.json', 'w') as file:
        file.write(config_json)


# =====================================
# Run as script

if __name__ == "__main__":
    # run_gui()
    make_default_dict()

# =====================================
# Todos

# todo: add function for loading existing settings from config file
# todo: make save dialog open to saved_configs folder
# todo: update actual settings from gui. eg. comport
# todo: add function for saving config settings to config file
# todo: separate creation of controls and filling with default values
# todo: add max_buffer_arr setting

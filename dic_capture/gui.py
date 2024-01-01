"""This module contains the GUI for the DIC-Capture program.
The GUI is used to select settings and run the program.
The main program function is in dic_capture/run.py."""
# =====================================
# Imports
import json
import os
import tkinter as tk
from datetime import datetime
from tkinter import ttk, filedialog
from typing import Dict, Union

from PIL import Image
from PIL import ImageTk
from serial.tools.list_ports import comports
from ttkthemes import ThemedTk

from dic_capture.run import run

# =====================================
# Global variables

CONFIG_DIR = "../saved_configs"
DIC_CAPTURE_VERSION = "0.0.2"


# =====================================
# Helper functions for gui. See gui class below.

def run_record_mode(config: Dict):
    """Set the config to record mode and run the program."""
    config["record_mode"] = True
    run(config)


def run_test_mode(config: Dict):
    """Set the config to test mode and run the program."""
    config["record_mode"] = False
    run(config)


def list_existing_configs():
    """Return a list of existing config files."""
    return [file for file in os.listdir(CONFIG_DIR) if file.endswith(".json")]


def new_config_file():
    """Create a new config file with default settings, and save it to a specified path."""
    # Load the default settings from the JSON file
    with open('default_config_file.json', 'r') as file:
        default_config = json.load(file)

    # Open a file dialog to choose where to save the new config file
    config_file_path = filedialog.asksaveasfilename(defaultextension=".json")

    # Save the default config to the chosen file
    with open(config_file_path, 'w') as file:
        json.dump(default_config, file, indent=4)


def get_available_com_ports():
    """Get a list of available COM ports."""
    available_com_ports = [port.device for port in comports()]
    if len(available_com_ports) == 0:
        return ["No COM ports available"]
    else:
        return available_com_ports


def get_available_cameras():
    """Get a list of available cameras."""
    # todo: update this to use neoapi to check for available cameras
    return ["Camera auto-detect not yet implemented."]


def browse_file(widget):
    """Open a file dialog and insert the selected file path into the specified widget."""
    # todo: update this to open to default location with informative header and default new name
    file_path = filedialog.askopenfilename()
    widget.delete(0, tk.END)
    widget.insert(0, file_path)


# =====================================
# GUI class
packing = dict(padx=10, pady=5, fill='x')


class GUI:
    def __init__(self, master: ThemedTk):
        self.CONFIG_WIDGETS = {
            "IO Config": {
                # "Input Path": dict(
                #     type="filedialog", value=os.getcwd()
                # ),
                "Output Folder": dict(
                    type="filedialog", value=os.getcwd()
                ),
                "Test ID": dict(
                    type="entry", value="Test_ID_" + datetime.now().strftime("%Y%m%d_%H%M%S")
                ),
            },
            "Arduino Config": {
                "Choose COM Port:": dict(
                    type="combobox", value=get_available_com_ports()
                ),
                "Baud Rate": dict(
                    type="entry", value=""
                ),
                "Max Buffer": dict(
                    type="entry", value=""
                ),
            },
            "Camera 1 Config": {
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
            "Camera 2 Config": {
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
            "Camera 3 Config": {
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
            # "Naming": {
            #     "Test ID": dict(
            #         type="entry", value="Test_ID_" + datetime.now().strftime("%Y%m%d_%H%M%S")
            #     ),
            # },
            # "Other Settings": {
            #     "Other Setting 1": dict(
            #         type="entry", value="default value"
            #     ),
        }

        self.master = master
        self.master.title('DIC-Capture v' + DIC_CAPTURE_VERSION)
        self.master.configure()

        self.create_config_select_frame()
        self.create_run_frame()
        self.create_config_frame()

        self.load_logo()

    def create_config_frame(self):
        """Create a frame for configuring settings."""
        # Create the outer frame
        frame = ttk.Frame(self.master, relief='sunken', borderwidth=2)

        frame.grid(row=0, rowspan=3, column=1, sticky='nsew', padx=10, pady=10)

        # IO Config Frame
        io_config_frame = ttk.LabelFrame(frame, text="IO Config")
        io_config_frame.grid(row=0, column=0, columnspan=2, sticky='nsew', padx=10, pady=10)
        self.add_controls(parent=io_config_frame, control_dict=self.CONFIG_WIDGETS["IO Config"])

        # Arduino Config Frame
        arduino_config_frame = ttk.LabelFrame(frame, text="Arduino Config")
        arduino_config_frame.grid(row=0, column=2, sticky='nsew', padx=10, pady=10)
        self.add_controls(parent=arduino_config_frame, control_dict=self.CONFIG_WIDGETS["Arduino Config"])

        # Camera Config Frames adjacent to each other
        camera_config_frame_1 = ttk.LabelFrame(frame, text="Camera 1 Config")
        camera_config_frame_1.grid(row=2, column=0, sticky='nsew', padx=10, pady=10)
        self.add_controls(parent=camera_config_frame_1, control_dict=self.CONFIG_WIDGETS["Camera 1 Config"])

        camera_config_frame_2 = ttk.LabelFrame(frame, text="Camera 2 Config")
        camera_config_frame_2.grid(row=2, column=1, sticky='nsew', padx=10, pady=10)
        self.add_controls(parent=camera_config_frame_2, control_dict=self.CONFIG_WIDGETS["Camera 2 Config"])

        camera_config_frame_3 = ttk.LabelFrame(frame, text="Camera 3 Config")
        camera_config_frame_3.grid(row=2, column=2, sticky='nsew', padx=10, pady=10)
        self.add_controls(parent=camera_config_frame_3, control_dict=self.CONFIG_WIDGETS["Camera 3 Config"])

        # Naming Frame
        # test_id_frame = ttk.LabelFrame(frame, text="Naming")
        # test_id_frame.grid(row=3, column=0, columnspan=3, sticky='nsew', padx=10, pady=10)
        # self.add_controls(parent=test_id_frame, control_dict=self.CONFIG_WIDGETS["Naming"])

        # Other Settings Frame
        # other_settings_frame = ttk.LabelFrame(frame, text="Other Settings")
        # other_settings_frame.grid(row=4, column=0, columnspan=3, sticky='nsew', padx=10, pady=10)
        # self.add_controls(parent=other_settings_frame, control_dict=self.CONFIG_WIDGETS["Other Settings"])

    def add_controls(self, parent: ttk.LabelFrame, control_dict: Dict):
        """Add a control to the parent frame based on the control type and options."""
        for name, option in control_dict.items():
            label = ttk.Label(parent, text=name + ":")
            label.pack(**packing)
            control = self.create_control(parent=parent, name=name, options=option)
            control.pack(**packing)
            control_dict[name]["widget"] = control

    def create_config_select_frame(self):
        """Create a frame for selecting a config file."""
        # Create the frame
        frame = ttk.LabelFrame(self.master, text="Config File")
        frame.grid(row=0, column=0, sticky='ew', padx=10, pady=10)

        # Create the controls in the frame
        new_config_button = self.create_control(parent=frame, name="New Config File",
                                                options=dict(type="button", command=new_config_file))
        new_config_button.pack(**packing)

        save_config_button = self.create_control(parent=frame, name="Save Config File",
                                                 options=dict(type="button", command=self.save_config_to_file))
        save_config_button.pack(**packing)

        select_config_combobox = self.create_control(parent=frame, name="Select Config File",
                                                     options=dict(type="combobox", value=list_existing_configs()))
        select_config_combobox.pack(**packing)

    def create_run_frame(self):
        """Create a frame for running the program."""
        # Create the frame
        frame = ttk.LabelFrame(self.master, text="Run")
        frame.grid(row=1, column=0, sticky='ew', padx=10, pady=10)

        # Create the controls in the frame
        run_record_button = self.create_control(parent=frame, name="Run Record Mode",
                                                options=dict(type="button", command=run_record_mode))
        run_record_button.pack(**packing)

        run_test_button = self.create_control(parent=frame, name="Run Test Mode",
                                              options=dict(type="button", command=run_test_mode))
        run_test_button.pack(**packing)

    @staticmethod
    def create_control(parent: Union[ttk.LabelFrame, ttk.Frame], name: str, options: Dict):
        """Create a control in the parent frame based on the control type and options."""
        control_type = options["type"]

        if control_type == "button":
            control = ttk.Button(parent, text=name, command=options["command"])

        elif control_type == "entry":
            control = ttk.Entry(parent)
            control.insert(index=0, string=options["value"])

        elif control_type == "combobox":
            control = ttk.Combobox(parent, values=options["value"])

        elif control_type == "filedialog":
            # add a frame with a text entry box and a button
            frame = ttk.Frame(parent)
            frame.pack(padx=0, pady=0, fill='x')
            control = ttk.Entry(frame)
            control.insert(index=0, string=options["value"])
            control.pack(side=tk.LEFT, fill='x', expand=True)  # Make the entry box stretch wider
            button = ttk.Button(frame, text="Browse", command=browse_file)
            button.pack(side=tk.LEFT, padx=10)

        elif control_type == "label":
            control = ttk.Label(parent, text=options["text"])

        elif control_type == "custom":
            control = options["custom_func"](parent)

        else:
            raise Exception(f"Invalid control type: {control_type}")

        return control

    def load_config_from_file(self, config_file_path: str):
        """Load a json config file from the specified path."""
        with open(config_file_path, 'r') as file:
            return json.load(file)

    def save_config_to_file(self):
        """Read settings from the GUI and save them to a config file."""
        # Initialize an empty dictionary to store the config
        config = {}

        # Iterate over the frames in the config frame
        for frame_name, frame_controls in self.CONFIG_WIDGETS.items():
            # Initialize an empty dictionary to store the settings for this frame
            frame_config = {}

            # Iterate over the controls in the frame
            for control_name, control_options in frame_controls.items():
                # Get the control widget
                control = control_options["widget"]

                # Get the value from the control widget
                if isinstance(control, ttk.Entry):
                    value = control.get()
                elif isinstance(control, ttk.Combobox):
                    value = control.get()
                else:
                    continue  # Skip non-entry widgets

                # Add the value to the frame config
                frame_config[control_name] = value

            # Add the frame config to the main config
            config[frame_name] = frame_config

        # Convert the config dictionary to a JSON string
        config_json = json.dumps(config, indent=4)

        # Open a file dialog to choose where to save the config file
        config_file_path = filedialog.asksaveasfilename(defaultextension=".json")

        # Save the config to the chosen file
        with open(config_file_path, 'w') as file:
            file.write(config_json)

    def load_logo(self):
        """Load the logo image and set the background color to match the logo."""
        try:
            # Load logo image
            image_path = "logo.png"
            self.logo_image = ImageTk.PhotoImage(Image.open(image_path))

            # Create a frame for the logo
            logo_frame = ttk.Frame(self.master)
            logo_frame.grid(row=2, column=0, sticky='nsew', padx=10, pady=10)

            # Add the logo to the frame
            logo = ttk.Label(logo_frame, image=self.logo_image)
            logo.pack()

        except Exception as e:
            print(f"Error loading logo: {e}")


def run_gui():
    root = ThemedTk(theme="plastik")
    app = GUI(root)
    root.mainloop()


def make_default_dict():
    root = ThemedTk(theme="plastik")
    app = GUI(root)
    config = {}  # Initialize an empty dictionary to store the config

    for frame_name, frame_controls in app.CONFIG_WIDGETS.items():
        frame_config = {}  # Initialize an empty dictionary to store the settings for this frame

        for control_name, control_options in frame_controls.items():
            default_value = control_options.get("value", "")
            frame_config[control_name] = default_value

        config[frame_name] = frame_config  # Add the frame config to the main config

    config_json = json.dumps(config, indent=4)
    with open('default_config_file_auto.json', 'w') as file:
        file.write(config_json)


if __name__ == "__main__":
    run_gui()
    # make_default_dict()

# todo: update actual settings from gui. eg. comport
# todo: add function for saving config settings to config file
# todo: add function for loading existing settings from config file
# todo: separate creation of controls and filling with default values
# todo: add max_buffer_arr setting

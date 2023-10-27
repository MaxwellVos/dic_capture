import tkinter as tk
from tkinter import filedialog, messagebox
import yaml

class ConfigApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Configuration Settings")

        # Define the labels and entry widgets
        tk.Label(root, text="Frame Rate:").grid(row=0, column=0, sticky=tk.W)
        self.frame_rate = tk.Entry(root)
        self.frame_rate.grid(row=0, column=1)

        tk.Label(root, text="COM Port:").grid(row=1, column=0, sticky=tk.W)
        self.com_port = tk.Entry(root)
        self.com_port.grid(row=1, column=1)

        tk.Label(root, text="Number of Cameras:").grid(row=2, column=0, sticky=tk.W)
        self.num_cameras = tk.Entry(root)
        self.num_cameras.grid(row=2, column=1)

        tk.Label(root, text="Save Directory:").grid(row=3, column=0, sticky=tk.W)
        self.save_directory = tk.Entry(root)
        self.save_directory.grid(row=3, column=1)

        # Save button
        self.save_button = tk.Button(root, text="Save Config", command=self.save_config)
        self.save_button.grid(row=4, column=0, columnspan=2)

        # If not creating a new config, load existing config
        if not messagebox.askyesno("Configuration", "Create new configuration?"):
            self.load_config()

    def load_config(self):
        config_file = filedialog.askopenfilename(filetypes=[("YAML files", "*.yaml")])
        if config_file:
            with open(config_file, 'r') as file:
                config = yaml.safe_load(file)
            # Set the entries to the loaded values
            self.frame_rate.insert(0, config.get('frame_rate', ''))
            self.com_port.insert(0, config.get('com_port', ''))
            self.num_cameras.insert(0, config.get('num_cameras', ''))
            self.save_directory.insert(0, config.get('save_directory', ''))

    def save_config(self):
        config = {
            'frame_rate': self.frame_rate.get(),
            'com_port': self.com_port.get(),
            'num_cameras': self.num_cameras.get(),
            'save_directory': self.save_directory.get()
        }
        # Validate and sanitize inputs here

        save_file = filedialog.asksaveasfilename(defaultextension=".yaml", filetypes=[("YAML files", "*.yaml")])
        if save_file:
            with open(save_file, 'w') as file:
                yaml.dump(config, file)
            messagebox.showinfo("Success", f"Config saved to {save_file}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ConfigApp(root)
    root.mainloop()

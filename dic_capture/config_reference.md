# Config Reference

## Config File

The config file is a JSON file. Here is an example config file:

```json
{
  "record_mode": false,
  "exposure_time_ms": 1.6,
  "max_buffer_arr": 3,
  "test_ID": "",
  "camera_sources": {
    "cam1": "P1-6",
    "cam2": "P1-5"
  },
  "arduino_port": "COM4",
  "baud_rate": 115200,
  "fps_values": [ 0, 0.125, 0.125, 0.125, 0, 0.125 ],
  "save_path": 
}
```

### record_mode

This is a boolean value. If true, the program will record the video. If false, the program will not record the video.

### exposure_time_ms

This is a float value. It is the exposure time of the camera in milliseconds.

### max_buffer_arr

This is an integer value. It is the maximum number of frames that can be stored in the buffer.

### test_ID

This is a string value. It is the ID of the test.

### camera_sources

This is a dictionary. It contains the camera sources. The keys are the camera names and the values are the camera
sources. The camera sources can be found in the [camera sources](#camera-sources) section.

### arduino_port

This is a string value. It is the port of the Arduino.

### baud_rate

This is an integer value. It is the baud rate of the Arduino.

### fps_values

This is a list of float values. It is the fps values of the cameras. 


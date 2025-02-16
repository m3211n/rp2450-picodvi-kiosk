![alt text](https://github.com/m3211n/rp2450-picodvi-kiosk/blob/main/preview/photo_2025-02-16_00-53-03.jpg?raw=true)

# RP2450 + PicoDVI Sock Kiosk Display
Raspberry Pi Pico 2W meets PicoDVI and goes to 27" display!

## Libraries used:
* [Adafruit Requests](https://github.com/adafruit/Adafruit_CircuitPython_Requests)
* [Adafruit NTP](https://github.com/adafruit/Adafruit_CircuitPython_NTP)
* [Adafruit Display Shapes](https://github.com/adafruit/Adafruit_CircuitPython_Display_Shapes)
* [Adafruit Bitmap Font](https://github.com/adafruit/Adafruit_CircuitPython_Bitmap_Font)
* [Adafruit Display Text](https://github.com/adafruit/Adafruit_CircuitPython_Display_Text)
* [Adafruit Connection Manager](https://github.com/adafruit/Adafruit_CircuitPython_Connection_Manager)

## Copyright and License

All libraries used in this project are provided by Adafruit and are subject to their respective licenses.

- **Adafruit Bitmap Font**: Copyright (c) 2017-2023 Adafruit Industries. Licensed under the MIT License.
- **Adafruit Display Shapes**: Copyright (c) 2019-2023 Adafruit Industries. Licensed under the MIT License.
- **Adafruit Display Text**: Copyright (c) 2017-2023 Adafruit Industries. Licensed under the MIT License.
- **Adafruit Requests**: Copyright (c) 2019-2023 Adafruit Industries. Licensed under the MIT License.
- **Adafruit NTP**: Copyright (c) 2019-2023 Adafruit Industries. Licensed under the MIT License.
- **Adafruit Connection Manager**: Copyright (c) 2019-2023 Adafruit Industries. Licensed under the MIT License.

For more information, please refer to the respective library links provided above.

## Dependencies

- `gc`: Garbage collection module
- `time`: Time module
- `displayio`: Display I/O module
- `picodvi`: PicoDVI library
- `board`: Board-specific pin definitions
- `framebufferio`: Framebuffer I/O module
- `wifi`: WiFi module
- `adafruit_requests`: Adafruit Requests library
- `adafruit_connection_manager`: Adafruit Connection Manager library
- `adafruit_ntp`: Adafruit NTP library
- `rtc`: Real-Time Clock module
- `os`: Operating system interfaces
- `dashboard.ui`: Custom UI components (Text, Progress, Widget, palette, STATUS, WEATHER_ICONS)

---
All fonts are manually created using Fony editor (http://hukka.ncn.fi/?fony). Font 'Chicago' is inspired by Apple Macintosh OS, but also contains some extra icons.
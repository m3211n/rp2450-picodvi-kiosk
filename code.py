import gc
import time

import displayio
from picodvi import Framebuffer
import board
from framebufferio import FramebufferDisplay

from wifi import radio
from adafruit_requests import Session
from adafruit_connection_manager import get_radio_socketpool, get_radio_ssl_context
from adafruit_ntp import NTP
from rtc import RTC
from os import getenv

from dashboard.ui import Text, Progress, Widget, palette, STATUS, WEATHER_ICONS

gc.enable()



def check_connection():
    ssid = getenv("CIRCUITPY_WIFI_SSID")
    pwd = getenv("CIRCUITPY_WIFI_PASSWORD")
    radio.enabled = False
    time.sleep(5)
    radio.enabled = True
    if not radio.connected:
        try:
            print(ssid)
            print(pwd)
            radio.connect(ssid, pwd)
        except OSError as e:
            print(e)
            raise e



def get_json(url):
    global session
    try:
        response = session.get(url)
        dict = response.json()
        response.close()
        return dict
    except MemoryError as e:
        raise e



def free_mem():
    """
    Cleans the memory and updates the status bar

    """
    gc.collect()
    free = gc.mem_free()
    total = free + gc.mem_alloc()
    return free, round(free/total*100, 0)



def time_date_formatted():
    """
    Updates the clock on screen with current RTC() time

    """
    global pool

    try:
        ntp = NTP(pool, tz_offset=1)
        RTC().datetime = ntp.datetime
    except Exception as e:
        print(f"NTP Sync failed ({e}). Getting time from API")

        api_time = get_json("https://timeapi.io/api/time/current/zone?timeZone=Europe%2FAmsterdam")
        struct_time = time.struct_time(
            api_time["year"], 
            api_time["month"], 
            api_time["day"], 
            api_time["hour"], 
            api_time["minute"], 
            api_time["seconds"])
        
        RTC().datetime = struct_time

    now = RTC().datetime
    weekday = ["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag", "Lördag", "Söndag"]
    month = ["Jan", "Feb", "Mar", "Apr", "Maj", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    time_str = "{:02}:{:02}".format(now.tm_hour, now.tm_min)
    date_str = "{} \u00d7 {} {:02}".format(weekday[now.tm_wday], month[now.tm_mon-1], now.tm_mday)

    return time_str, date_str



def degrees_to_direction(degrees):
    """
    Converts degrees into geographical direction.
    """
    directions = (
        "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
        "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"
    )

    return directions[round(degrees / 22.5) % 16]



def get_weather_icon_for_code(code: int):
    if code == 0:
        return "9"
    elif code in (1, 2):
        return "8"
    elif code == 3:
        return "7"
    elif code in (51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82):
        return "6"
    elif code in (71, 73, 75, 77, 85, 86):
        return "5"



get_hours = lambda : tuple(int(h) for h in getenv("WEATHER_HOURS").split(","))



def parse_weather_data(data):
    """
    Parses weather data and prints current and hourly weather information.
    """
    # Process current weather data

    data["current_units"] = {}
    data["hourly_units"] = {}
    data["hourly"]["time"] = {}
    gc.collect()
    print("Cleaned.")
    print(gc.mem_free())


    current = [
        get_weather_icon_for_code(data["current"]["weather_code"]),
        data['current']['temperature_2m'],
        data['current']['wind_speed_10m']
    ]

    # Process hourly weather data

    hourly = {}

    for hour in get_hours():
        weather_code = data["hourly"]["weather_code"][hour]
        temp = data["hourly"]["temperature_2m"][hour]
        wind_speed = data["hourly"]["wind_speed_10m"][hour]

        hourly[f"{hour}:00"] = [
            get_weather_icon_for_code(weather_code),
            temp,
            wind_speed,
        ]

    return current, hourly



def parse_sl_data(dict) -> str:
    """
    Fetches SL train data every minute
    """
    result = []
    departures = dict.get("departures", [])

    for departure in departures:
        if departure["state"] in ["ATSTOP", "EXPECTED"] and departure["display"] not in result:
            result.append(departure["display"])
        if len(result) == 3:
            break

    # Clear the dictionary to free memory
    dict.clear()
    gc.collect()

    return ", ".join(result) if result else "Inga avgångar"



class WeatherWidget(Widget):
    def __init__(self, position=(0, 0), small: bool = False):
        scale = 2 if not small else 1
        super().__init__(position=position, padding=0, content=[
            # 0: Symbol
            Text(text="9", scale=scale, anchor_point=(0.5, 0.0), anchored_position=(0, 0), font=WEATHER_ICONS),
            # 1: Temperature
            Text(scale=2*scale, anchor_point=(0.5, 0.0), anchored_position=(0, 24*scale)),
            # 2: Wind speed
            Text(scale=scale, anchor_point=(0.5, 0.0), anchored_position=(0, 60*scale))
            # 3: Wind direction
            # Text(scale=scale, anchor_point=(0.5, 0.0), anchored_position=(0, 80*scale), font=STATUS)
        ])

    def update(self, s):
        symbol, temp, wsp = s
        if RTC().datetime.tm_hour > 19 or RTC().datetime.tm_hour < 5:
            if symbol == "9":
                symbol = "2"
            if symbol == "8":
                symbol = "1"

        self.content[0].text = symbol
        if symbol in ("9", "2", "8", "1"): 
            self.content[0].color_code = 6
        if symbol in ("5", "6"):
            self.content[0].color_code = 3
        self.content[1].color_code = 3 if temp < 0 else 6
        self.content[1].text = f"{temp}\u0008"
        self.content[2].text = f"\u0000 {wsp} \u0006"



class WeatherList(Widget):
    def __init__(self, position=(0, 0)):
        super().__init__(position=position, padding=0, content=[
            Text(font=STATUS, anchor_point=(0.5, 0), anchored_position=(66, 0)),
            WeatherWidget((66, 16), True),
            Text(font=STATUS, anchor_point=(0.5, 0), anchored_position=(182, 0)),
            WeatherWidget((182, 16), True),
            Text(font=STATUS, anchor_point=(0.5, 0), anchored_position=(66, 136)),
            WeatherWidget((66, 150), True),
            Text(font=STATUS, anchor_point=(0.5, 0), anchored_position=(182, 136)),
            WeatherWidget((182, 150), True)
        ])

    def update(self, dict):
        print(get_hours())
        # ordered_dict = {key: dict[key] for key in sorted(dict)}
        for index, h in enumerate(get_hours()):
            key = f"{h}:00"
            self.content[index * 2].text = key
            self.content[index * 2 + 1].update(dict[key])



class RamWidget(Widget):
    def __init__(self, total=0, **kwarg):
        self._progress = 0
        self._free = 0
        self._total = total
        super().__init__(padding=0, content=[
            Text(font=STATUS, anchor_point=(1.0, 0), anchored_position=(-8, -2)),
            Progress(y=2, width=50)
        ], **kwarg)

    @property
    def free(self):
        return self._free

    @free.setter
    def free(self, free):
        self._free = free
        self.content[0].text = f"{round(self._free / 1024, 2)}KB"

    @property
    def progress(self):
        return self._progress

    @progress.setter
    def progress(self, progress):
        self._progress = progress
        self.content[1].value = int(self._progress)

    def set_total(self, value):
        self._total = value



# Initialize display

displayio.release_displays()

fb = Framebuffer(640, 480,
                 clk_dp=board.GP14, clk_dn=board.GP15, red_dp=board.GP12, red_dn=board.GP13, green_dp=board.GP18, green_dn=board.GP19,
                 blue_dp=board.GP16, blue_dn=board.GP17,
                 color_depth=4)

display = FramebufferDisplay(fb)

display.root_group = Widget(content=[
    Text(text="connecting to wifi...", anchor_point=(0.5, 0), anchored_position=(320, 220), font=STATUS)
])

status_wifi = Text(font=STATUS, anchor_point=(0.0, 0.0), anchored_position=(0, -2))
ram_widget = RamWidget(position = (286, 0))
time_now = Text(scale=12, color=palette[3], font=STATUS, anchor_point=(0, 0), anchored_position=(16, -16))
date_today = Text(scale=3, color=palette[3], font=STATUS, anchor_point=(0, 0), anchored_position=(16, 112))
train_departures = Text(color=palette[2], scale=2, anchor_point=(0.0, 0.0), anchored_position=(8, 40))
bus_departures = Text(color=palette[2], scale=2, anchor_point=(0.0, 0.0), anchored_position=(8, 40))
current_weather = WeatherWidget((124, 16))
hourly_weather = WeatherList((0, 200))

# Trying WIFI connection

while True:
    try:
        check_connection()
        pool = get_radio_socketpool(radio)
        ssl_context = get_radio_ssl_context(radio)
        session = Session(pool, ssl_context)
        break
    except Exception as e:
        reset_time = ready_time = time.monotonic() + 15
        radio.enabled = False
        display.root_group = Widget(content=[
            Text(f"WIFI Anslutningen misslykades: {e}", anchor_point=(0.5, 0), anchored_position=(320, 220), font=STATUS, color=palette[4]),
            Text("Nästa försök om 15 sekunder.", anchor_point=(0.5, 0), anchored_position=(320, 240), font=STATUS),
        ])
        delay = 15
        while delay > 0:
            ready_time = time.monotonic()
            display.root_group[0][1].text = f"Nästa försök om {delay} sekunder."
            delay = delay - 1
            time.sleep(1)
        radio.enabled = True
        # raise e



display.root_group = Widget(padding=0, content=[
    Widget(size=(368, 240), content=[
        time_now,
        date_today,
        status_wifi,
        ram_widget
    ]),
    Widget(position=(0, 232), size=(368, 128), title="pendeltåg", content=[
        Text("\u0005 Nynäshamn (via Sundbyberg)", anchor_point=(0.0, 0.0), anchored_position=(8, 16)),
        train_departures
    ]),
    Widget(position=(0, 352), size=(368, 128), title="buss", content=[
        Text("\u0004 Jakobsbergs Station", anchor_point=(0.0, 0.0), anchored_position=(8, 16)),
        bus_departures
    ]),
    # Widget(position=(0, 380), size=(368, 100), title="störningar"),
    Widget(position=(360, 0), size=(280, 480), title="väder", content=[
        current_weather,
        hourly_weather
    ])
])



# def print_widget_tree(widget, indent=0):
#     """
#     Recursively prints the widget tree with indentation.
#     """
#     indent_str = " " * indent
#     print(f"{indent_str}{widget}")

#     if not ("Rect" in str(type(widget)) or "Text" in str(type(widget))):
#         for child in widget:
#             print_widget_tree(child, indent + 2)

# # Example usage:
# print("Widget Tree:")
# print_widget_tree(display.root_group[0])



ram_widget.free, ram_widget.progress = free_mem()
status_wifi.text = f"\u0014 {getenv("CIRCUITPY_WIFI_SSID")} ({radio.ipv4_address})"

# Main loop

next_attempt_60 = next_attempt_900 = current_time = time.monotonic()

while True:

    current_time = time.monotonic()
    if current_time >= next_attempt_60:
        next_attempt_60 = current_time + 60
        time_now.text, date_today.text = time_date_formatted()

        try:
            train_departures.text = "Hämtar avgångar..."
            train_departures.text = parse_sl_data(get_json(getenv("TRAIN_URL")))
        except Exception as e:
            train_departures.text = "Fel uppstod..."
            print(f"Error while getting Train data: {e}")
            raise e
        ram_widget.free, ram_widget.progress = free_mem()

        try:
            bus_departures.text = "Hämtar avrångar..."
            bus_departures.text = parse_sl_data(get_json(getenv("BUS_URL")))
        except Exception as e:
            bus_departures.text = "Fel uppstod..."
            print(f"Error while getting Bus data: {e}")
            raise e
        ram_widget.free, ram_widget.progress = free_mem()

    if current_time >= next_attempt_900:
        next_attempt_900 = current_time + 900
        c, h = parse_weather_data(get_json(getenv("WEATHER_URL")))
        current_weather.update(c)
        hourly_weather.update(h)
        ram_widget.free, ram_widget.progress = free_mem()

    ram_widget.free, ram_widget.progress = free_mem()
    time.sleep(5)

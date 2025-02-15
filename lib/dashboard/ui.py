from displayio import Palette, Group

from adafruit_bitmap_font import bitmap_font
from adafruit_display_text import bitmap_label
from adafruit_display_shapes.rect import Rect

FONT = bitmap_font.load_font("/fonts/chicago.pcf")
STATUS = bitmap_font.load_font("/fonts/status.pcf")
WEATHER_ICONS = bitmap_font.load_font("/fonts/weather.pcf")

palette = Palette(color_count=8)
palette[0] = 0x000000
palette[1] = 0x000080
palette[2] = 0x008000
palette[3] = 0x008080
palette[4] = 0x800000
palette[5] = 0x800080
palette[6] = 0x808000
palette[7] = 0x808080



class Text(bitmap_label.Label):
    def __init__(self, text="...", font=FONT, **kwargs):
        super().__init__(text=text, font=font, **kwargs)
        self.save_text = False
    
    @property
    def color_code(self):
        return palette.index(self.color)

    @color_code.setter
    def color_code(self, code: int):
        self.color = palette[code]

    @property
    def value(self):
        return None
    
    @value.setter
    def value(self, text: str):
        self.text = text



class Progress(Group):
    def __init__(self, x: int = 0, y: int = 0, color: int = 7, width: int = 100):
        super().__init__(x=x, y=y)
        self.width = width
        self._value = 100
        bar_size = self.width - 2
        self.append(Rect(0, 0, self.width, 5, outline=palette[color]))
        self.append(Rect(1, 1, bar_size, 3))
    
    @property
    def value(self):
        return self._value
    
    @value.setter
    def value(self, percent: int):
        bar_size = int(round((self.width - 2) / 100 * percent, 0))
        if percent > 50:
            color_index = 2
        elif percent > 25:
            color_index = 6
        else:
            color_index = 4
        self[1] = Rect(1, 1, bar_size, 3, fill=palette[color_index])



class Widget(Group):
    def __init__(self, size=(0, 0), position=(0, 0), padding:int=8, scale=1, title="", content=[]):
        super().__init__(x=position[0], y=position[1], scale=scale)
        if size[0] > 0 and size[1] > 0:
            if padding > 0:
                self.append(Rect(padding, padding, size[0] - padding*2, size[1] - padding*2, outline=palette[7]))
            if len(title) > 0: 
                self.append(Text(text=f" {title} ", font=STATUS, x=padding+4, y=padding, background_color=0))
        self.content = Group(x=padding*2, y=padding*2)
        self.append(self.content)
        self._init_(content)

    def _init_(self, content):
        for item in content:
            self.content.append(item)
    


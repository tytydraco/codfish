import log


class MiniProgress:
    maximum = 0.0
    progress = 0.0
    char_filled = '▒'
    char_filled_head = '▓'
    visual_width = 50

    def __init__(self, maximum):
        self.maximum = maximum

    def reset(self):
        self.progress = 0.0

    def inc(self):
        self.progress += 1.0

    def dec(self):
        self.progress -= 1.0

    def percent(self):
        if self.maximum <= 0:
            return 0.0

        return 100.0 * (self.progress / self.maximum)

    def visual(self):
        percent = self.percent()
        cur = percent / 100.0
        amount_filled = int(cur * self.visual_width)
        amount_empty = self.visual_width - amount_filled

        filled_chars = (self.char_filled * amount_filled)[:-1] + self.char_filled_head
        empty_chars = ' ' * amount_empty

        log.progress(f'╔{filled_chars}{empty_chars}╗ «{int(percent)}%»')
        if percent == 100:
            print()

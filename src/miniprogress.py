import log


# Tiny helper library that represents an integer progress bar
class MiniProgress:
    reason = ''
    maximum = 0.0
    progress = 0.0
    char_filled = '▒'
    char_filled_head = '▓'
    visual_width = 25

    def __init__(self, maximum, reason=''):
        self.maximum = maximum
        self.reason = reason

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

        log.progress(f'╔\033[1;32;48m{filled_chars}{empty_chars}\033[1;37;0m╗ «{int(percent)}%» {self.reason}')
        if percent == 100:
            print()

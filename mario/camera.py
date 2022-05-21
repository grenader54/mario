from pygame.rect import Rect
from pygame.sprite import Group


class Camera(Rect):
    def __init__(self, player, left, top, width, height, all_sprites: Group):
        Rect.__init__(self, left, top, width, height)
        self.player = player
        self.left = left
        self.top = top
        self.width = width
        self.height = height
        self.level_width = 0
        self.__set_right_border(all_sprites)

    def __set_right_border(self, all_sprites):
        for sprite in all_sprites.sprites():
            if self.level_width < sprite.rect.right:
                self.level_width = sprite.rect.right
        self.level_width -= 3

    def scroll(self):
        if self.player.rect.right > -self.x + self.width / 2 and abs(self.x - self.width) < self.level_width:
            self.x = -self.player.rect.right + self.width / 2

    @property
    def rect(self):
        return Rect(abs(self.left), abs(self.top), self.width, self.height)

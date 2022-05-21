import pygame

from mario.camera import Camera


class OffsetGroup(pygame.sprite.Group):
    def __init__(self):
        pygame.sprite.Group.__init__(self)

    def offset_draw(self, surface: pygame.Surface, camera: Camera):
        for sprite in self.sprites():
            rect = sprite.rect
            surface.blit(sprite.image, pygame.Rect(rect.left + camera.left, rect.top, rect.width, rect.height))

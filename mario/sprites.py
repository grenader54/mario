import math

import pygame

GRAVITY = 5


class BasicMovableSprite(pygame.sprite.Sprite):
    def __init__(self, screen_width):
        pygame.sprite.Sprite.__init__(self)
        self.screen_width = screen_width
        self.left_move_images = []
        self.right_move_images = []
        self.die_image = None
        self.speed_x = 0
        self.speed_y = 0
        self.jump_force = 0
        self.on_ground = True
        self.jump_ban = False
        self.is_left = False
        self.is_right = False
        self.animation_frame = 0
        self.left_border_x = 0
        self.is_die = False

    def update(self, **kwargs):
        pass

    def move(self, **kwargs):
        pass

    def collide(self, speed_x, speed_y, blocks):
        pass

    def animate(self):
        self.animation_frame += 1
        if self.is_die:
            self.image = self.die_image
            self.speed_x = 0
            if self.animation_frame > 30:
                self.kill()
        elif self.speed_x <= 0:
            self.image = self.left_move_images[self.animation_frame // 8 % len(self.left_move_images)]
        else:
            self.image = self.right_move_images[self.animation_frame // 8 % len(self.left_move_images)]


class Player(BasicMovableSprite):
    def __init__(self, x, bottom, screen_width, score, coins):
        BasicMovableSprite.__init__(self, screen_width)
        self.image = pygame.image.load("mario/images/mario1.png")
        self.right_stand_image = self.image
        self.left_stand_image = pygame.transform.flip(self.image, True, False)
        for frame_number in range(2, 7):
            image = pygame.image.load(f"mario/images/mario{frame_number}.png")
            self.right_move_images.append(image)
        for image in self.right_move_images:
            self.left_move_images.append(pygame.transform.flip(image, True, False))
        self.die_image = pygame.image.load(f"mario/images/mario_die.png")
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.bottom = bottom
        self.score = score
        self.coins = coins
        self.die_animation = False
        self.jump_music_play = False

    def update(self, all_sprites, blocks, creatures, **kwargs):
        self.move(all_sprites, blocks)
        if not self.die_animation:
            self.change_direction()
            self.enemy_collide(creatures)
            self.jump()
            self.border()
        self.animate()

    def move(self, all_sprites, blocks):
        if self.speed_x < 0:
            self.rect.x += (self.speed_x - 9) / 10
        else:
            self.rect.x += (self.speed_x + 9) / 10
        self.collide(self.speed_x, 0, blocks)

        if self.speed_y <= 0:
            if self.die_animation:
                self.speed_y += GRAVITY / 2
            else:
                self.speed_y += GRAVITY

        self.rect.top += self.speed_y
        if not self.die_animation:
            self.box_collide(self.speed_y, blocks, all_sprites)
            self.collide(0, self.speed_y, blocks)

    def change_direction(self):
        key_state = pygame.key.get_pressed()
        if key_state[pygame.K_LEFT] or key_state[pygame.K_a]:
            if self.speed_x > -40:
                self.speed_x -= 1
            self.is_left = True
            self.is_right = False
        elif key_state[pygame.K_RIGHT] or key_state[pygame.K_d]:
            if self.speed_x < 40:
                self.speed_x += 1
            self.is_left = False
            self.is_right = True
        elif abs(self.speed_x) <= 3:
            self.speed_x = 0
        else:
            self.speed_x += math.copysign(1.5 * -1, -1 * self.speed_x)

    def jump(self):
        key_state = pygame.key.get_pressed()

        if (key_state[pygame.K_UP] or key_state[pygame.K_w]) and self.jump_force < 5 * 30 and not self.jump_ban:
            self.jump_force += 6
            self.speed_y = -6 - GRAVITY
            self.on_ground = False
            if not self.jump_music_play:
                sound = pygame.mixer.Sound("mario/sounds/jump.mp3")
                sound.play()
                self.jump_music_play = True
        else:
            self.jump_ban = True

        if not (key_state[pygame.K_UP] or key_state[pygame.K_w]) and self.on_ground:
            self.jump_ban = False
            self.jump_music_play = False

    def border(self):
        if self.rect.x < self.left_border_x:
            self.rect.x = self.left_border_x
        if self.rect.right > self.left_border_x + self.screen_width / 2:
            self.left_border_x = self.rect.right - self.screen_width / 2

    def collide(self, speed_x, speed_y, blocks):
        collided_sprites = pygame.sprite.spritecollide(self, blocks, False)
        for sprite in collided_sprites:
            if speed_x > 0:
                self.rect.right = sprite.rect.left
                self.speed_x = 0

            if speed_x < 0:
                self.rect.left = sprite.rect.right
                self.speed_x = 0

            if speed_y > 0:
                self.rect.bottom = sprite.rect.top
                self.on_ground = True
                self.jump_force = 0
                self.speed_y = 0

            if speed_y < 0:
                self.rect.top = sprite.rect.bottom
                self.speed_y = 0
                self.jump_ban = True

        if collided_sprites:
            return True
        return False

    def box_collide(self, speed_y, blocks, all_sprites):
        collided_sprites = pygame.sprite.spritecollide(self, blocks, False)
        for sprite in collided_sprites:
            if speed_y < 0 and isinstance(sprite, Box):
                self.rect.top = sprite.rect.bottom
                self.speed_y = 0
                self.jump_ban = True
                sprite.is_die = True
                coin = Coin(sprite.rect.x, sprite.rect.top)
                all_sprites.add(coin)
                self.score += 200
                coin.is_die = True
                pygame.mixer.Sound("mario/sounds/coin.mp3").play()

    def enemy_collide(self, enemies):
        collided_sprites = pygame.sprite.spritecollide(self, enemies, False)
        for sprite in collided_sprites:
            if self.rect.bottom - 10 < sprite.rect.top and not sprite.is_die:
                sprite.is_die = True
                sprite.animation_frame = 0
                self.speed_y = -GRAVITY * 3
                pygame.mixer.Sound("mario/sounds/kill.mp3").play()
                self.score += 200
                self.coins += 1
            elif not self.die_animation and not sprite.is_die:
                self.die()

    def die(self):
        self.die_animation = True
        self.speed_y = -GRAVITY * 4
        self.animation_frame = 0
        self.speed_x = 0
        pygame.mixer.music.stop()
        pygame.mixer.Sound("mario/sounds/lose.mp3").play()

    def animate(self):
        self.animation_frame += 1
        key_state = pygame.key.get_pressed()

        if self.die_animation:
            self.image = self.die_image
            if self.animation_frame > 200:
                self.is_die = True
        elif self.speed_x == 0 and self.on_ground:
            if self.is_left:
                self.image = self.left_stand_image
            elif self.is_right:
                self.image = self.right_stand_image
        elif not self.on_ground:
            if self.is_left:
                self.image = self.left_move_images[4]
            elif self.is_right:
                self.image = self.right_move_images[4]

        elif (key_state[pygame.K_RIGHT] or key_state[pygame.K_d]) and self.speed_x < 0:
            self.image = self.right_move_images[3]
            self.animation_frame = 0

        elif (key_state[pygame.K_LEFT] or key_state[pygame.K_a]) and self.speed_x > 0:
            self.image = self.left_move_images[3]
            self.animation_frame = 0

        elif self.is_left:
            self.image = self.left_move_images[self.animation_frame // 8 % 3]

        elif self.is_right:
            self.image = self.right_move_images[self.animation_frame // 8 % 3]


class BasicBlock(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.images = []
        self.die_image = None
        self.animation_frame = 0
        self.is_die = False

    def update(self, **kwargs):
        pass

    def animate(self):
        self.animation_frame += 1
        if self.is_die:
            self.image = self.die_image
        else:
            self.image = self.images[self.animation_frame // 12 % len(self.images)]


class Block(BasicBlock):
    def __init__(self, x, bottom):
        BasicBlock.__init__(self)
        self.image = pygame.image.load("mario/images/block.png")
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.bottom = bottom


class Box(BasicBlock):
    def __init__(self, x, bottom):
        BasicBlock.__init__(self)
        self.image = pygame.image.load("mario/images/box4.png")
        for frame_number in range(1, 5):
            image = pygame.image.load(f"mario/images/box{frame_number}.png")
            self.images.append(image)
        self.images.append(pygame.image.load(f"mario/images/box4.png"))
        self.die_image = pygame.image.load(f"mario/images/box5.png")
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.bottom = bottom

    def update(self, **kwargs):
        self.animate()


class Coin(BasicBlock):
    def __init__(self, x, bottom):
        BasicBlock.__init__(self)
        self.image = pygame.image.load("mario/images/coin1.png")
        for frame_number in range(1, 6):
            image = pygame.image.load(f"mario/images/coin{frame_number}.png")
            self.images.append(image)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.bottom = bottom
        self.timer = 0

    def update(self, **kwargs):
        self.animate()

    def animate(self):
        self.timer += 1
        self.image = self.images[self.timer // 4 % len(self.images)]
        if self.timer < 20:
            self.rect.y -= 3
        else:
            self.rect.y += 3
        if self.timer >= 40:
            self.kill()


class Brick(BasicBlock):
    def __init__(self, x, bottom):
        BasicBlock.__init__(self)
        self.image = pygame.image.load("mario/images/brick.png")
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.bottom = bottom


class Floor(BasicBlock):
    def __init__(self, x, bottom):
        BasicBlock.__init__(self)
        self.image = pygame.image.load("mario/images/floor.png")
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.bottom = bottom


class Pipe(BasicBlock):
    def __init__(self, x, bottom, pipe_type):
        BasicBlock.__init__(self)
        if pipe_type == 1:
            self.image = pygame.image.load("mario/images/pipe1.png")
        if pipe_type == 2:
            self.image = pygame.image.load("mario/images/pipe2.png")
        if pipe_type == 3:
            self.image = pygame.image.load("mario/images/pipe3.png")
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.bottom = bottom


class Enemy(BasicMovableSprite):
    def __init__(self, screen_width):
        BasicMovableSprite.__init__(self, screen_width)
        self.is_active = False
        self.speed_y = GRAVITY

    def update(self, blocks, camera, **kwargs):
        self.move(blocks)
        self.animate()

        if not self.is_active and pygame.Rect.colliderect(self.rect, camera.rect):
            self.speed_x = -1
            self.is_active = True

    def move(self, blocks):
        self.rect.y += self.speed_y
        self.collide(0, self.speed_y, blocks)

        self.rect.x += self.speed_x
        if self.collide(self.speed_x, 0, blocks):
            self.inverse_direction()

    def inverse_direction(self):
        self.speed_x *= -1

    def collide(self, speed_x, speed_y, blocks):
        collided_sprites = pygame.sprite.spritecollide(self, blocks, False)
        for sprite in collided_sprites:
            if speed_x > 0:
                self.rect.right = sprite.rect.left

            if speed_x < 0:
                self.rect.left = sprite.rect.right

            if speed_y > 0:
                self.rect.bottom = sprite.rect.top

            if speed_y < 0:
                self.rect.top = sprite.rect.bottom
        if collided_sprites:
            return True
        return False


class Turtle(Enemy):
    def __init__(self, x, bottom, screen_width):
        Enemy.__init__(self, screen_width)
        self.image = pygame.image.load("mario/images/turtle1.png")
        for frame_number in range(1, 3):
            image = pygame.image.load(f"mario/images/turtle{frame_number}.png")
            self.left_move_images.append(image)
        for image in self.left_move_images:
            self.right_move_images.append(pygame.transform.flip(image, True, False))
        self.die_image = pygame.image.load(f"mario/images/turtle3.png")
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.bottom = bottom


class Mushroom(Enemy):
    def __init__(self, x, bottom, screen_width):
        Enemy.__init__(self, screen_width)
        self.image = pygame.image.load("mario/images/mushroom1.png")
        for frame_number in range(1, 3):
            image = pygame.image.load(f"mario/images/mushroom{frame_number}.png")
            self.left_move_images.append(image)
        for image in self.left_move_images:
            self.right_move_images.append(pygame.transform.flip(image, True, False))
        self.die_image = pygame.image.load(f"mario/images/mushroom3.png")
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.bottom = bottom


class Button:
    def __init__(self, screen_width, y, text, font):
        self.text = text
        self.font = font
        self.image = self.font.render(text, True, (255, 255, 255))
        self.rect = self.image.get_rect()
        self.rect.x = screen_width / 2 - self.rect.width / 2
        self.rect.y = y
        self.text_surface = None
        self.text_background = None

    def in_focus(self, mouse):
        if self.rect.left < mouse[0] < self.rect.right:
            if self.rect.top < mouse[1] < self.rect.bottom:
                return True
        else:
            return False

    def draw(self, screen, mouse):
        self.text_surface = self.font.render(self.text, True, (255, 255, 255))
        self.image = pygame.Surface((self.text_surface.get_width() + 6, self.text_surface.get_height() + 6))
        self.text_background = pygame.Surface(self.text_surface.get_size())
        if self.in_focus(mouse):
            self.image.fill((255, 255, 255))
        self.image.blit(self.text_background, (3, 3))
        self.image.blit(self.text_surface, (3, 3))
        screen.blit(self.image, (self.rect.x, self.rect.y))

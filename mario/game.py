import json

import pygame
from pygame.surface import Surface

from mario.camera import Camera
from mario.groups import OffsetGroup
from mario.sprites import Player, Floor, Box, Brick, Pipe, Block, Mushroom, Turtle, Button
from pygame_textinput import TextInputVisualizer


class MarioGame:
    CAMERA_WIDTH = 1008
    WIDTH = 10000
    HEIGHT = 460
    ZERO_POINT = HEIGHT - 32 * 3 / 2
    FPS = 60

    def __init__(self):
        self.records = None
        self.pause = None
        self.textinput = None
        self.player = None
        self.running = True
        self.time = 0
        self.timer = 0
        self.lives = 3
        self.score = 0
        self.coins = 3
        self.screen = None
        self.clock = pygame.time.Clock()
        self.all_sprites = OffsetGroup()
        self.blocks = pygame.sprite.Group()
        self.creatures = pygame.sprite.Group()
        self.font = None
        self.camera = None
        self.images = []
        self.menu = []
        self.ok_button = None
        self.images_surface = Surface((self.WIDTH, self.ZERO_POINT))
        self.font = pygame.font.Font("mario/mario.otf", 35)
        self.game_font = pygame.font.Font("mario/BarcadeBrawlRegular.ttf", 20)
        self.menu_font = pygame.font.Font("mario/mario.otf", 50)
        self.current_screen = "menu"
        self.level_end = 0
        self.game_end = False
        self.world = ""

    def start(self):
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((self.CAMERA_WIDTH, self.HEIGHT))
        pygame.display.set_icon(pygame.image.load("mario/images/mario1.png"))
        pygame.display.set_caption("Super Mario Bros")
        self.ok_button = Button(self.CAMERA_WIDTH, self.HEIGHT - 64, "    ОК    ", self.font)
        self.load_map()
        self.create_menu()
        self.create_textinput()
        self.loop()

    def load_map(self):
        game_map = json.load(open("mario/map.json", "r"), object_hook=sprites_decoder)
        self.level_end = game_map["level_end"]
        self.records = json.load(open("mario/records.json", "r", encoding="utf8"))
        self.time = game_map["time"]
        self.world = game_map["world"]
        self.create_images_surface(game_map)
        self.all_sprites.empty()
        self.player = Player(game_map["player"]["x"], self.ZERO_POINT, self.CAMERA_WIDTH, self.score, self.coins)
        self.blocks.empty()
        self.creatures.empty()
        for floor in game_map["groups"]["floor"]:
            x = floor["x"]
            for floor_offset in range(floor["width"]):
                floor_sprite = Floor(x + 32 * floor_offset, self.HEIGHT + 16)
                self.all_sprites.add(floor_sprite)
                self.blocks.add(floor_sprite)
                floor_sprite = Floor(x + 32 * floor_offset, self.HEIGHT - 16)
                self.all_sprites.add(floor_sprite)
                self.blocks.add(floor_sprite)

        for sprite in game_map["groups"]["blocks"]:
            self.all_sprites.add(sprite)
            self.blocks.add(sprite)
        for sprite in game_map["groups"]["creatures"]:
            self.all_sprites.add(sprite)
            self.creatures.add(sprite)
        self.all_sprites.add(self.player)

        self.camera = Camera(self.player, 0, 0, self.CAMERA_WIDTH, self.HEIGHT, self.all_sprites)

    def create_images_surface(self, game_map):
        random_color = (100, 150, 200)
        self.images_surface.fill(random_color)
        self.images_surface.set_colorkey(random_color)
        for image in game_map["groups"]["images"]:
            if "type" in image:
                loaded_image = pygame.image.load(f"mario/images/{image['name'].lower()}{image['type']}.png")
            else:
                loaded_image = pygame.image.load(f"mario/images/{image['name'].lower()}.png")
            self.images_surface.blit(loaded_image, (image["x"], self.images_surface.get_height() -
                                                    loaded_image.get_height() - image["bottom"]))

    def create_menu(self):
        top = 60
        self.menu.append(Button(self.CAMERA_WIDTH, top, "  Начать игру  ", self.menu_font))
        self.menu.append(Button(self.CAMERA_WIDTH, top + 84, "  Таблица рекордов  ", self.menu_font))
        self.menu.append(Button(self.CAMERA_WIDTH, top + 84 * 2, "  Справка  ", self.menu_font))
        self.menu.append(Button(self.CAMERA_WIDTH, top + 84 * 3, "  Выйти  ", self.menu_font))

    def create_textinput(self):
        self.textinput = TextInputVisualizer(font_object=self.font, cursor_color=(255, 255, 255))
        self.textinput.cursor_width = 4
        self.textinput.cursor_blink_interval = 400
        self.textinput.antialias = False
        self.textinput.font_color = (255, 255, 255)

    def loop(self):
        self.running = True
        while self.running:
            self.clock.tick(self.FPS)
            events = pygame.event.get()
            self.screen.fill((0, 0, 0))
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.KEYUP and self.current_screen == "game":
                    if event.key == pygame.K_r:
                        self.load_map()
                    if event.key == pygame.K_p:
                        self.pause = not self.pause
                    if event.key == pygame.K_ESCAPE:
                        self.current_screen = "menu"
                        pygame.mixer.music.stop()
                        pygame.mixer.stop()
            if self.current_screen == "game":
                self.game_screen()
            elif self.current_screen == "menu":
                self.menu_screen(events)
            elif self.current_screen == "records":
                self.records_screen(events)
            elif self.current_screen == "help":
                self.help_screen(events)
            elif self.current_screen == "new_record":
                self.new_record_screen(events)
            pygame.display.flip()

        pygame.quit()

    def game_screen(self):
        self.score = self.player.score
        self.coins = self.player.coins
        if not self.game_end and self.lives >= 0 and not self.pause:
            self.camera.scroll()
            self.all_sprites.update(blocks=self.blocks, creatures=self.creatures, camera=self.camera,
                                    all_sprites=self.all_sprites)
            self.time -= 2 / self.FPS
        if self.game_end:
            self.time -= 60 / self.FPS
            self.player.score += int(60 / self.FPS * 50)
            self.score = self.player.score
            if self.time <= 0:
                self.current_screen = "new_record"
        if self.player.is_die:
            self.lives -= 1
            self.game_initialize()
            if self.lives < 0:
                pygame.mixer.music.stop()
                pygame.mixer.music.load("mario/sounds/gameover.mp3")
                pygame.mixer.music.play()
        self.screen.fill((92, 148, 252))
        self.screen.blit(self.images_surface, self.camera)
        self.all_sprites.offset_draw(self.screen, self.camera)
        self.draw_interface()
        if self.lives < 0:
            self.timer += 1
            self.screen.fill((0, 0, 0))
            ren = self.game_font.render("GAME OVER", True, (255, 255, 255))
            self.screen.blit(ren, (self.CAMERA_WIDTH / 2 - ren.get_width() / 2, self.HEIGHT / 2 - ren.get_height() / 2))
            if self.timer > 250:
                self.timer = 0
                pygame.mixer.music.stop()
                self.current_screen = "new_record"
        if self.pause:
            ren = self.game_font.render("PAUSE", True, (255, 255, 255))
            self.screen.blit(ren, (self.CAMERA_WIDTH / 2 - ren.get_width() / 2, self.HEIGHT / 2 - ren.get_height() / 2))
        if self.player.rect.y > self.HEIGHT and not self.player.die_animation:
            self.player.die()
        if self.player.rect.x >= self.level_end and not self.game_end:
            self.game_end = True
            self.player.kill()
            pygame.mixer.music.stop()
            pygame.mixer.music.load("mario/sounds/win.mp3")
            pygame.mixer.music.play()

    def draw_interface(self):
        ren = multiline_surface(f"SCORE\n{self.player.score}", self.game_font, pygame.Rect(0, 0, 160, 320),
                                (255, 255, 255), None, 1)
        self.screen.blit(ren, (30, 5))
        ren = multiline_surface(f"TIME\n{int(self.time)}", self.game_font, pygame.Rect(0, 0, 160, 320),
                                (255, 255, 255), None, 1)
        self.screen.blit(ren, (230, 5))
        ren = multiline_surface(f"WORLD\n{self.world}", self.game_font, pygame.Rect(0, 0, self.CAMERA_WIDTH, 320),
                                (255, 255, 255), None, 1)
        self.screen.blit(ren, (0, 5))
        ren = multiline_surface(f"COINS\n{self.player.coins}", self.game_font, pygame.Rect(0, 0, 160, 320),
                                (255, 255, 255), None, 1)
        self.screen.blit(ren, (630, 5))
        ren = multiline_surface(f"LIVES\n{self.lives}", self.game_font, pygame.Rect(0, 0, 160, 320),
                                (255, 255, 255), None, 1)
        self.screen.blit(ren, (830, 5))

    def game_initialize(self):
        self.current_screen = "game"
        self.load_map()
        pygame.mixer.music.load("mario/sounds/fon.mp3")
        pygame.mixer.music.set_volume(0.4)
        pygame.mixer.music.play()
        self.game_end = False

    def menu_screen(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if self.menu[0].in_focus(pygame.mouse.get_pos()):
                    self.lives = 3
                    self.score = 0
                    self.coins = 0
                    self.game_initialize()
                elif self.menu[1].in_focus(pygame.mouse.get_pos()):
                    self.current_screen = "records"
                elif self.menu[2].in_focus(pygame.mouse.get_pos()):
                    self.current_screen = "help"
                elif self.menu[3].in_focus(pygame.mouse.get_pos()):
                    self.running = False

        for button in self.menu:
            button.draw(self.screen, pygame.mouse.get_pos())

    def records_screen(self, events):
        records_string = ""
        for record_number in range(len(self.records)):
            records_string += f"{record_number + 1}) {self.records[record_number]['name']}: {self.records[record_number]['score']}\n"
        ren = multiline_surface(records_string, self.font,
                                pygame.Rect(0, 0, self.CAMERA_WIDTH - 100, self.HEIGHT - 84), (255, 255, 255),
                                (0, 0, 0), 1)
        self.screen.blit(ren, (50, 20))
        self.draw_ok_button(events)

    def help_screen(self, events):
        help = "УПРАВЛЕНИЕ\n\nДВИЖЕНИЕ: СТРЕЛОЧКИ/WASD\nP: ПАУЗА\nESC: ВЫЙТИ В МЕНЮ"
        ren = multiline_surface(help, self.font, pygame.Rect(0, 0, self.CAMERA_WIDTH, self.HEIGHT),
                                (255, 255, 255), (0, 0, 0), 1)
        self.screen.blit(ren, (0, 50))
        self.draw_ok_button(events)

    def draw_ok_button(self, events):
        self.ok_button.draw(self.screen, pygame.mouse.get_pos())
        for event in events:
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if self.ok_button.in_focus(event.pos):
                    self.current_screen = "menu"

    def new_record_screen(self, events):
        if not self.records or self.records[0]["score"] < self.player.score:
            self.textinput.update(events)
            congratulations = "Поздравляем\nУ вас наибольшее количество очков\nПожалуйста, введите ваше имя"
            ren = multiline_surface(congratulations, self.font, pygame.Rect(0, 0, self.CAMERA_WIDTH, self.HEIGHT),
                                    (255, 255, 255), (0, 0, 0), 1)
            self.screen.blit(ren, (0, 40))
            self.screen.blit(self.textinput.surface,
                             (
                             self.CAMERA_WIDTH / 2 - self.textinput.font_object.size(self.textinput.value)[0] / 2, 220))
            self.ok_button.draw(self.screen, pygame.mouse.get_pos())
            for event in events:
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    if self.ok_button.in_focus(event.pos):
                        self.records.insert(0, {"name": self.textinput.value, "score": self.player.score})
                        json.dump(self.records, open("mario/records.json", "w", encoding="utf8"), indent=2,
                                  ensure_ascii=False)
                        self.textinput.value = ""
                        self.current_screen = "menu"
        else:
            self.current_screen = "menu"


def sprites_decoder(dct):
    if "thing" in dct:
        if dct["thing"] == "Box":
            return Box(dct["x"], MarioGame.ZERO_POINT - dct["bottom"])
        elif dct["thing"] == "Brick":
            return Brick(dct["x"], MarioGame.ZERO_POINT - dct["bottom"])
        elif dct["thing"] == "Pipe":
            return Pipe(dct["x"], MarioGame.ZERO_POINT - dct["bottom"], dct["type"])
        elif dct["thing"] == "Block":
            return Block(dct["x"], MarioGame.ZERO_POINT - dct["bottom"])
        elif dct["thing"] == "Mushroom":
            return Mushroom(dct["x"], MarioGame.ZERO_POINT - dct["bottom"], 0)
        elif dct["thing"] == "Turtle":
            return Turtle(dct["x"], MarioGame.ZERO_POINT - dct["bottom"], 0)
    return dct


def multiline_surface(text: str, font: pygame.font.Font, rect: pygame.rect.Rect, font_color: tuple, bg_color: tuple,
                      justification=0):
    final_lines = []
    requested_lines = text.splitlines()
    for requested_line in requested_lines:
        if font.size(requested_line)[0] > rect.width:
            words = requested_line.split(' ')
            for word in words:
                if font.size(word)[0] >= rect.width:
                    raise Exception("The word " + word + " is too long to fit in the rect passed.")
            accumulated_line = ""
            for word in words:
                test_line = accumulated_line + word + " "
                if font.size(test_line)[0] < rect.width:
                    accumulated_line = test_line
                else:
                    final_lines.append(accumulated_line)
                    accumulated_line = word + " "
            final_lines.append(accumulated_line)
        else:
            final_lines.append(requested_line)
    surface = pygame.Surface(rect.size, pygame.SRCALPHA, 32)
    surface = surface.convert_alpha()
    if bg_color is not None:
        surface.fill(bg_color)
    accumulated_height = 0
    for line in final_lines:
        if accumulated_height + font.size(line)[1] >= rect.height:
            raise Exception("Once word-wrapped, the text string was too tall to fit in the rect.")
        temp_surface = font.render(line, True, font_color)
        if justification == 0:
            surface.blit(temp_surface, (0, accumulated_height))
        elif justification == 1:
            surface.blit(temp_surface, ((rect.width - temp_surface.get_width()) / 2, accumulated_height))
        elif justification == 2:
            surface.blit(temp_surface, (rect.width - temp_surface.get_width(), accumulated_height))
        else:
            raise Exception("Invalid justification argument: " + str(justification))
        accumulated_height += font.size(line)[1]
    return surface

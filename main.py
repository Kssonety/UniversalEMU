import pygame
from pygame.locals import *
from tkinter import filedialog
import struct

class GraphicsHandler:
    def __init__(self, rom_content, width, height):
        self.width = width
        self.height = height
        self.frame_size = width * height * 2  # Assuming 2 bytes per pixel (16-bit color)
        self.total_frames = len(rom_content) // self.frame_size
        self.frame_index = 0
        self.frame_delay = 16.67

    def get_pixels(self, frame_data):
        # Default implementation (assumes 16-bit color)
        return [(pixel & 0x1F, (pixel >> 5) & 0x1F, (pixel >> 10) & 0x1F) for pixel in frame_data]

    def snes_to_rgb(self, color):
        r = ((color >> 0) & 0x1F) * 8
        g = ((color >> 5) & 0x1F) * 8
        b = ((color >> 10) & 0x1F) * 8
        return r, g, b


class GrayscaleHandler(GraphicsHandler):
    def get_pixels(self, frame_data):
        # Grayscale implementation
        return [(pixel, pixel, pixel) for pixel in frame_data]

class DefaultHandler(GraphicsHandler):
    def get_palette(self, rom_content, palette_offset, palette_size):
        palette_data = struct.unpack(f"{palette_size}H", rom_content[palette_offset : palette_offset + palette_size * 2])
        return [self.snes_to_rgb(color) for color in palette_data]

    def get_pixels(self, frame_data, palette):
        pixels = []

        for pixel in frame_data:
            color = palette[pixel % len(palette)]
            pixels.append(color)

        return pixels



def load_rom():
    rom_path = filedialog.askopenfilename(filetypes=[("SNES ROMs", "*.smc")])
    if rom_path:
        with open(rom_path, "rb") as file:
            return file.read()
    return None

def display_game(rom_content, graphics_handler):
    pygame.init()

    width, height = graphics_handler.width, graphics_handler.height

    # Pygame window dimensions
    screen_width = 800
    screen_height = 600

    # Create Pygame window
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("SNES ROM Viewer")

    clock = pygame.time.Clock()

    # Extract palette information (adjust the offset and size based on your ROM)
    palette_offset = 0x100000  # Adjust this offset based on the actual palette offset in your ROM
    palette_size = 16  # Adjust this size based on the actual palette size in your ROM
    palette = graphics_handler.get_palette(rom_content, palette_offset, palette_size)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False

        # Interpret raw binary data as an image
        frame_start = graphics_handler.frame_index * graphics_handler.frame_size
        frame_end = (graphics_handler.frame_index + 1) * graphics_handler.frame_size
        frame_data = struct.unpack(f"{graphics_handler.frame_size // 2}H", rom_content[frame_start:frame_end])

        # Convert to RGB tuples using the selected graphics handler and palette
        pixels = graphics_handler.get_pixels(frame_data, palette)

        # Create a Pygame surface from pixels
        pixels_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        for y in range(height):
            for x in range(width):
                color = tuple(min(255, max(0, c)) for c in pixels[y * width + x])
                pixels_surface.set_at((x, y), color)

        # Resize the image to fit the window
        pixels_surface = pygame.transform.scale(pixels_surface, (screen_width, screen_height))

        # Draw the image to the Pygame window
        screen.blit(pixels_surface, (0, 0))
        pygame.display.flip()

        graphics_handler.frame_index = (graphics_handler.frame_index + 1) % graphics_handler.total_frames  # Cycle through frames

        # Control frame rate
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    rom_content = load_rom()

    if rom_content:
        # Choose the graphics handler based on the ROM or game
        graphics_handler = DefaultHandler(rom_content, width=256, height=224)

        display_game(rom_content, graphics_handler)

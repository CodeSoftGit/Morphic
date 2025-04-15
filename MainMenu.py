import pygame
from pygame import *
import json
import math
import time as systime
from Game import Main_game
import sys
import random
from DevTools import DevTools
import os

# Initialize pygame
pygame.init()

dev_tools = DevTools()

# Version
VERSION = "1.0.0-alpha"

# Setup display with hardware acceleration
if hasattr(pygame, 'GL_CONTEXT_PROFILE_CORE'):
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
    pygame.display.gl_set_attribute(pygame.GL_ACCELERATED_VISUAL, 1)
    pygame.display.gl_set_attribute(pygame.GL_DOUBLEBUFFER, 1)
    pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)

# Setup display
screen = display.set_mode((0, 0), FULLSCREEN | HWSURFACE | DOUBLEBUF)
SCREEN_WIDTH = display.Info().current_w
SCREEN_HEIGHT = display.Info().current_h
middleScreen = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

# Load background
try:
    menuBG = transform.scale(image.load("assets\Images\menuBG.png").convert_alpha(), (SCREEN_WIDTH, SCREEN_HEIGHT))
    BGrect = menuBG.get_rect()
    BGrect.center = middleScreen
except Exception as e:
    print(f"Error loading background: {e}")
    menuBG = Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    menuBG.fill((20, 20, 40))
    BGrect = menuBG.get_rect()

# Load logo for startup screen
try:
    logoImg = transform.scale(image.load("assets\Images\logo.png").convert_alpha(), (640, 600))
    logoRect = logoImg.get_rect()
    logoRect.center = (middleScreen[0], middleScreen[1] - 100)
except Exception as e:
    print(f"Error loading logo image: {e}")
    logoImg = None

# Pre-load common UI elements
try:
    button_normal = transform.scale(image.load("assets\Images\\button.png").convert_alpha(), (400, 100))
    button_hover = transform.scale(image.load("assets\Images\\button_hover.png").convert_alpha(), (400, 100))
    slider_bg = transform.scale(image.load("assets\Images\\slider_bg.png").convert_alpha(), (300, 30))
    slider_knob = transform.scale(image.load("assets\Images\\slider_knob.png").convert_alpha(), (40, 40))
except Exception as e:
    print(f"Using fallback UI elements: {e}")
    # Create fallback UI elements
    button_normal = Surface((400, 100), SRCALPHA)
    draw.rect(button_normal, (80, 80, 100, 200), (0, 0, 400, 100), border_radius=20)
    draw.rect(button_normal, (120, 120, 180, 255), (0, 0, 400, 100), width=3, border_radius=20)
    
    button_hover = Surface((400, 100), SRCALPHA)
    draw.rect(button_hover, (100, 100, 150, 230), (0, 0, 400, 100), border_radius=20)
    draw.rect(button_hover, (150, 150, 220, 255), (0, 0, 400, 100), width=3, border_radius=20)
    
    slider_bg = Surface((300, 30), SRCALPHA)
    draw.rect(slider_bg, (80, 80, 100, 200), (0, 0, 300, 30), border_radius=15)
    
    slider_knob = Surface((40, 40), SRCALPHA)
    draw.circle(slider_knob, (150, 150, 220, 255), (20, 20), 20)

# Load assets and settings
try:
    with open("assets/NoteStyles.json") as f:
        availableNoteStyles = json.load(f)["NoteStyles"]
    with open("assets/options.json") as f:
        options = json.load(f)
except (FileNotFoundError, json.JSONDecodeError) as e:
    print(f"Error loading assets: {e}")
    pygame.quit()
    sys.exit(1)

# Fonts - pre-render common text sizes for better performance
Font75 = font.Font("assets\PhantomMuff.ttf", 75)
Font100 = font.Font("assets\PhantomMuff.ttf", 100)
Font125 = font.Font("assets\PhantomMuff.ttf", 125)
Font30 = font.Font("assets\PhantomMuff.ttf", 30)
FNFfont = Font100
FNFfont125 = Font125

visible_top = 0
visible_bottom = SCREEN_HEIGHT

for folder in os.listdir("assets\Music"):
    if os.path.isdir(os.path.join("assets\Music", folder)):
        musicList = str(folder)
        break    
    
# Get list of music folders
musicList = []
for folder in os.listdir("assets\Music"):
    if os.path.isdir(os.path.join("assets\Music", folder)):
        musicList.append(folder)

def get_difficulties(song_name):
    """Get available difficulties for a given song
    
    File format is {song}-{difficulty}.json, where {difficulty} is the difficulty name.
    Returns a list of difficulty names.
    """
    difficulties = []
    
    # Get the path to the song folder
    song_path = os.path.join("assets", "Music", song_name)
    
    # Check if the directory exists
    if not os.path.isdir(song_path):
        return difficulties
    
    try:
        # Scan for difficulty files
        for file in os.listdir(song_path):
            if not file.endswith(".json"):
                continue
            
            if file == "songData.json":
                continue
            
            # Check for chart.json which indicates a single difficulty
            if file == "chart.json":
                print(f"Single difficulty found for {song_name}.")
                return [None]
                
            # Extract difficulty name from file name format: {song}-{difficulty}.json
            if file.startswith(song_name + "-"):
                # Remove song name prefix and .json suffix
                difficulty = file[len(song_name)+1:-5]
                difficulties.append(difficulty)
    except Exception as e:
        print(f"Error getting difficulties for {song_name}: {e}")
    
    print(f"Available difficulties for {song_name}: {difficulties}")
    return difficulties
# Text cache to avoid repeated rendering
text_cache = {}

def cached_text_render(font_obj, text, color, shadow=True, shadow_color=(40, 40, 40), shadow_offset=3):
    """Render text with caching for better performance"""
    key = (id(font_obj), text, color, shadow, shadow_color, shadow_offset)
    if key in text_cache:
        return text_cache[key]
    
    if shadow:
        # Create shadow text
        shadow_surface = font_obj.render(text, True, shadow_color)
        text_surface = font_obj.render(text, True, color)
        
        # Create a composite surface
        size = text_surface.get_size()
        composite = Surface((size[0] + shadow_offset, size[1] + shadow_offset), SRCALPHA)
        composite.blit(shadow_surface, (shadow_offset, shadow_offset))
        composite.blit(text_surface, (0, 0))
        result = composite
    else:
        result = font_obj.render(text, True, color)
    
    # Store in cache (limit cache size to avoid memory issues)
    if len(text_cache) > 100:
        # Clear half the cache when it gets too big
        keys = list(text_cache.keys())
        for k in keys[:50]:
            del text_cache[k]
    
    text_cache[key] = result
    return result

# Menu state variables
selectedMusic = 0
selectedOption = 0
selectedMain = 0
selectedKeybind = 0
selectedDifficulty = None
currentMenu = "Startup"
previousMenu = "Startup"
menuTransition = 0  # 0 = no transition, 1 = fully transitioned in
transitionDirection = 1  # 1 = in, -1 = out
TRANSITION_SPEED = 4.0  # Faster transitions

# Startup screen transition
startupFade = 0  # 0 = black, 1 = fully faded to menu
startupFadeSpeed = 1.5  # Faster startup fade

# Load options
selectedSpeed = options["selectedSpeed"]
playAs = options["playAs"]
selectedNoteStyle = min(options["selectedNoteStyle"], len(availableNoteStyles)-1)
noDeath = options["noDying"]
downscroll = options["downscroll"]
render_scene = options["render_scene"]
modcharts = options["modcharts"]

# Keybinds
K_a = options["keybinds"][0]
K_s = options["keybinds"][1]
K_w = options["keybinds"][2]
K_d = options["keybinds"][3]
K_LEFT = options["keybinds"][4]
K_DOWN = options["keybinds"][5]
K_UP = options["keybinds"][6]
K_RIGHT = options["keybinds"][7]

# Preload menu music
try:
    menuMusic = mixer.Sound("assets\menuMusic.ogg")
    menuMusic.set_volume(0.7)  # Slightly lower volume
    menuMusic.play(-1)
except Exception as e:
    print(f"Error loading menu music: {e}")
    menuMusic = None

# Input handling
preventDoubleEnter = False
waitingForKeyPress = False
last_click_time = 0
last_click_pos = -1

# Animation variables
menuItems = []
cursorPos = [middleScreen[0], middleScreen[1]]
targetCursorPos = [middleScreen[0], middleScreen[1]]
cursorPulse = 0
bgScroll = 0

# Define tooltips for settings
tooltip_texts = {
    "Speed": "Adjust the scrolling speed of notes. Higher values make the game more challenging.",
    "Play as": "Choose whether to play as the Player or the Opponent character.",
    "No Death": "When enabled, you won't lose even if you miss many notes.",
    "Note style": "Change the visual appearance of notes in the game.",
    "Downscroll": "When enabled, notes flow from top to bottom instead of bottom to top.",
    "Render Scene": "Enable or disable background and characters. Turning off may improve performance.",
    "Modcharts": "Enable or disable special note movement patterns in certain songs.",
    "Keybinds": "Customize which keys are used to hit notes during gameplay."
}

# Particle system for visual enhancement
class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = random.uniform(2, 5)
        self.color = (random.randint(100, 255), random.randint(100, 255), random.randint(200, 255), random.randint(50, 150))
        self.speed_x = random.uniform(-0.5, 0.5)
        self.speed_y = random.uniform(-0.5, 0.5)
        self.life = random.uniform(1, 3)
        
    def update(self, dt):
        self.x += self.speed_x * 60 * dt
        self.y += self.speed_y * 60 * dt
        self.life -= dt
        self.size -= dt * 0.5
        return self.life > 0 and self.size > 0
        
    def draw(self, surface):
        alpha = int(min(255, self.life * 100))
        pygame.draw.circle(surface, (self.color[0], self.color[1], self.color[2], alpha), 
                          (int(self.x), int(self.y)), int(self.size))

# Particles container
particles = []

# Easing functions
def ease_out_quad(t):
    return 1 - (1 - t) ** 2

def ease_in_out_quad(t):
    return 2 * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 2 / 2

def ease_in_out_sine(t):
    return -(math.cos(math.pi * t) - 1) / 2

def ease_out_back(t):
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2

# Enhanced Menu item class
class MenuItem:
    def __init__(self, text, position, selected=False, font_normal=Font100, font_selected=Font125, 
                 is_button=True, is_slider=False, slider_value=None, slider_min=0, slider_max=1,
                 tooltip=None):
        self.text = text
        self.position = list(position)
        self.target_position = list(position)
        self.selected = selected
        self.font_normal = font_normal
        self.font_selected = font_selected
        self.scale = 1.0
        self.target_scale = 1.0 if not selected else 1.15
        self.alpha = 255
        self.target_alpha = 255
        self.hover = False
        self.rect = None
        self.button_rect = None
        self.rotation = 0
        self.target_rotation = 0
        self.is_button = is_button
        self.is_slider = is_slider
        self.slider_value = slider_value
        self.slider_min = slider_min
        self.slider_max = slider_max
        self.slider_rect = None
        self.hover_effect = 0
        self.tooltip = tooltip
        self.tooltip_alpha = 0
        
        # Animation properties
        self.pulse = random.uniform(0, math.pi*2)  # Random starting phase
        self.pulse_speed = random.uniform(2, 4)    # Random pulse speed
    
    def update(self, dt):
        # Position animation with improved easing
        self.position[0] += (self.target_position[0] - self.position[0]) * ease_out_quad(min(1, 12 * dt))
        self.position[1] += (self.target_position[1] - self.position[1]) * ease_out_quad(min(1, 12 * dt))
        
        # Scale animation
        self.scale += (self.target_scale - self.scale) * ease_out_quad(min(1, 15 * dt))
        
        # Alpha animation
        self.alpha += (self.target_alpha - self.alpha) * ease_out_quad(min(1, 15 * dt))
        
        # Rotation animation
        self.rotation += (self.target_rotation - self.rotation) * ease_out_quad(min(1, 10 * dt))
        
        # Hover effect
        if self.hover:
            self.hover_effect = min(1.0, self.hover_effect + dt * 5)
            # For tooltip fade-in
            self.tooltip_alpha = min(255, self.tooltip_alpha + dt * 510)  # Fade in over 0.5 seconds
        else:
            self.hover_effect = max(0.0, self.hover_effect - dt * 5)
            # For tooltip fade-out
            self.tooltip_alpha = max(0, self.tooltip_alpha - dt * 510)   # Fade out over 0.5 seconds
            
        # Update pulse animation
        self.pulse = (self.pulse + dt * self.pulse_speed) % (math.pi * 2)
    
    def draw(self, surface):
        # Set colors based on state
        if self.selected:
            text_color = (255, 255, 255)
            glow_effect = 0.7 + 0.3 * math.sin(systime.time() * 4)  # Pulsing effect for selected items
        else:
            base_color = 230 if self.hover else 200
            glow_effect = 0.2 + 0.1 * math.sin(systime.time() * 2)
            # Clamp color values between 0-255
            text_color = (
                min(255, max(0, int(base_color + 25 * self.hover_effect))),
                min(255, max(0, int(base_color + 25 * self.hover_effect))),
                min(255, max(0, int(base_color + 55 * self.hover_effect)))
            )
        
        # Draw button background if this is a button
        if self.is_button:
            btn_img = button_hover if self.hover or self.selected else button_normal
            
            # Scale button based on hover/selection
            scale_factor = 1.0 + 0.1 * self.hover_effect + (0.15 if self.selected else 0)
            scaled_size = (int(btn_img.get_width() * scale_factor), int(btn_img.get_height() * scale_factor))
            scaled_btn = transform.scale(btn_img, scaled_size)
            
            # Create button rectangle
            btn_rect = scaled_btn.get_rect()
            btn_rect.center = self.position
            self.button_rect = btn_rect
            
            # Apply rotation if needed
            if self.rotation != 0:
                scaled_btn = transform.rotate(scaled_btn, self.rotation)
                rotated_rect = scaled_btn.get_rect()
                rotated_rect.center = btn_rect.center
                btn_rect = rotated_rect
            
            # Draw button with glow effect for selected items
            if self.selected:
                glow_size = int(scaled_btn.get_width() * (1.0 + 0.1 * glow_effect))
                glow_btn = transform.scale(scaled_btn, (glow_size, glow_size))
                glow_rect = glow_btn.get_rect()
                glow_rect.center = self.position
                
                # Create a glow surface
                glow_surface = Surface((glow_size, glow_size), SRCALPHA)
                glow_btn.set_alpha(50)  # Semi-transparent
                glow_surface.blit(glow_btn, (0, 0))
                surface.blit(glow_surface, glow_rect)
            
            # Draw the actual button
            surface.blit(scaled_btn, btn_rect)
            self.rect = btn_rect
        
        # Render text with shadow effect
        if self.selected:
            rendered_text = cached_text_render(self.font_selected, self.text, text_color)
        else:
            rendered_text = cached_text_render(self.font_normal, self.text, text_color)
        
        # Apply scale
        if self.scale != 1.0:
            original_size = rendered_text.get_size()
            new_size = (int(original_size[0] * self.scale), int(original_size[1] * self.scale))
            rendered_text = transform.scale(rendered_text, new_size)
        
        # Apply alpha if needed
        if self.alpha < 255:
            rendered_text.set_alpha(int(self.alpha))
        
        # Position text
        text_rect = rendered_text.get_rect()
        if self.is_button:
            # Center text on button
            text_rect.center = self.button_rect.center
        else:
            # Position text directly
            text_rect.center = self.position
        
        # Draw text
        surface.blit(rendered_text, text_rect)
        
        # Use the text rect as the item's rect if not a button
        if not self.is_button:
            self.rect = text_rect
        
        # Draw slider if this is a slider item
        if self.is_slider and self.slider_value is not None:
            # Create slider rectangle
            slider_width = 300
            slider_rect = Rect(0, 0, slider_width, 30)
            slider_rect.midtop = (self.position[0], self.rect.bottom + 20)
            self.slider_rect = slider_rect
            
            # Draw slider background
            surface.blit(slider_bg, slider_rect)
            
            # Calculate knob position
            normalized_val = (self.slider_value - self.slider_min) / (self.slider_max - self.slider_min)
            knob_x = slider_rect.left + normalized_val * slider_width
            
            # Draw knob
            knob_rect = slider_knob.get_rect()
            knob_rect.centerx = knob_x
            knob_rect.centery = slider_rect.centery
            
            # Add subtle animation to knob when selected
            if self.selected:
                knob_pulse = 1.0 + 0.1 * math.sin(systime.time() * 6)
                scaled_knob = transform.scale(slider_knob, 
                                             (int(slider_knob.get_width() * knob_pulse),
                                              int(slider_knob.get_height() * knob_pulse)))
                knob_rect = scaled_knob.get_rect()
                knob_rect.centerx = knob_x
                knob_rect.centery = slider_rect.centery
                surface.blit(scaled_knob, knob_rect)
            else:
                surface.blit(slider_knob, knob_rect)
            
            # Draw value text
            value_text = cached_text_render(Font30, f"{self.slider_value}", (255, 255, 255), shadow=False)
            value_rect = value_text.get_rect()
            value_rect.midtop = (slider_rect.centerx, slider_rect.bottom + 5)
            surface.blit(value_text, value_rect)
        
        # Draw tooltip if hovering and has tooltip text
        if self.hover and self.tooltip and self.tooltip_alpha > 10:
            # Create tooltip text
            tooltip_font = Font30
            tooltip_text = cached_text_render(tooltip_font, self.tooltip, (255, 255, 255), shadow=False)
            
            # Calculate tooltip dimensions with padding
            padding = 15
            tooltip_width = min(500, tooltip_text.get_width() + padding * 2)
            
            # Handle word wrapping for long tooltips
            if tooltip_text.get_width() > tooltip_width - padding * 2:
                words = self.tooltip.split()
                lines = []
                current_line = ""
                
                for word in words:
                    test_line = current_line + word + " "
                    test_text = tooltip_font.render(test_line, True, (255, 255, 255))
                    if test_text.get_width() < tooltip_width - padding * 2:
                        current_line = test_line
                    else:
                        lines.append(current_line)
                        current_line = word + " "
                
                if current_line:
                    lines.append(current_line)
                
                # Create multi-line tooltip surface
                line_height = tooltip_font.get_linesize()
                tooltip_height = line_height * len(lines) + padding * 2
                tooltip_bg = Surface((tooltip_width, tooltip_height), SRCALPHA)
                
                # Create tooltip background with rounded corners
                alpha = int(min(200, self.tooltip_alpha))
                draw.rect(tooltip_bg, (40, 40, 60, alpha), 
                          Rect(0, 0, tooltip_width, tooltip_height), border_radius=10)
                draw.rect(tooltip_bg, (100, 100, 255, alpha), 
                          Rect(0, 0, tooltip_width, tooltip_height), width=2, border_radius=10)
                
                # Add each line to the tooltip
                for i, line in enumerate(lines):
                    line_text = tooltip_font.render(line, True, (255, 255, 255))
                    tooltip_bg.blit(line_text, (padding, padding + i * line_height))
                
                # Position tooltip above the item
                tooltip_x = self.position[0] - tooltip_width // 2
                tooltip_y = self.position[1] - self.rect.height - tooltip_height - 20
                
                # Ensure tooltip stays on screen
                if tooltip_x < 10:
                    tooltip_x = 10
                elif tooltip_x + tooltip_width > SCREEN_WIDTH - 10:
                    tooltip_x = SCREEN_WIDTH - tooltip_width - 10
                
                if tooltip_y < 10:
                    # Place tooltip below the item if not enough space above
                    if self.is_slider:
                        tooltip_y = self.slider_rect.bottom + 40
                    else:
                        tooltip_y = self.rect.bottom + 20
                
                # Add subtle animation to tooltip
                tooltip_y += 5 * math.sin(systime.time() * 2)
                
                # Draw tooltip
                surface.blit(tooltip_bg, (tooltip_x, tooltip_y))
            else:
                # Simple single-line tooltip
                tooltip_height = tooltip_text.get_height() + padding * 2
                tooltip_bg = Surface((tooltip_width, tooltip_height), SRCALPHA)
                
                # Create tooltip background with rounded corners
                alpha = int(min(200, self.tooltip_alpha))
                draw.rect(tooltip_bg, (40, 40, 60, alpha), 
                          Rect(0, 0, tooltip_width, tooltip_height), border_radius=10)
                draw.rect(tooltip_bg, (100, 100, 255, alpha), 
                          Rect(0, 0, tooltip_width, tooltip_height), width=2, border_radius=10)
                
                # Position tooltip text
                tooltip_bg.blit(tooltip_text, (padding, padding))
                
                # Position tooltip above the item
                tooltip_x = self.position[0] - tooltip_width // 2
                tooltip_y = self.position[1] - self.rect.height - tooltip_height - 20
                
                # Ensure tooltip stays on screen
                if tooltip_x < 10:
                    tooltip_x = 10
                elif tooltip_x + tooltip_width > SCREEN_WIDTH - 10:
                    tooltip_x = SCREEN_WIDTH - tooltip_width - 10
                
                if tooltip_y < 10:
                    # Place tooltip below the item if not enough space above
                    if self.is_slider:
                        tooltip_y = self.slider_rect.bottom + 40
                    else:
                        tooltip_y = self.rect.bottom + 20
                
                # Add subtle animation to tooltip
                tooltip_y += 5 * math.sin(systime.time() * 2)
                
                # Draw tooltip
                surface.blit(tooltip_bg, (tooltip_x, tooltip_y))
        
        return self.rect
    
    def set_selected(self, selected):
        self.selected = selected
        self.target_scale = 1.15 if selected else 1.0
        if selected:
            self.target_rotation = random.uniform(-2, 2)  # Small random rotation when selected
        else:
            self.target_rotation = 0
    
    def update_slider_value(self, mouse_x):
        if self.slider_rect:
            normalized_pos = (mouse_x - self.slider_rect.left) / self.slider_rect.width
            normalized_pos = max(0, min(1, normalized_pos))
            raw_value = self.slider_min + normalized_pos * (self.slider_max - self.slider_min)
            
            # For speed, round to nearest 0.1
            if self.text.startswith("Speed:"):
                self.slider_value = round(raw_value * 10) / 10
            else:
                self.slider_value = round(raw_value)

def update_menu_items():
    global menuItems
    menuItems = []
    
    if currentMenu == "Startup":
        # No menu items for the startup screen
        pass
    elif currentMenu == "Main":
        tempText = ["Play", "Options", "Credits"]
        for k in range(len(tempText)):
            item = MenuItem(
                tempText[k], 
                (middleScreen[0], middleScreen[1] + 200 * (k - selectedMain)),
                k == selectedMain,
                FNFfont,
                FNFfont125
            )
            menuItems.append(item)
    
    elif currentMenu == "Select music":
        for k in range(len(musicList)):
            item = MenuItem(
                musicList[k], 
                (middleScreen[0], middleScreen[1] + 180 * (k - selectedMusic)),
                k == selectedMusic,
                FNFfont,
                FNFfont125
            )
            menuItems.append(item)
    
    elif currentMenu == "Select difficulty":
        difficulties = get_difficulties(musicList[selectedMusic])
        for k in range(len(difficulties)):
            # Handle None difficulty case
            difficulty_name = difficulties[k] if difficulties[k] is not None else "Normal"
            item = MenuItem(
                difficulty_name, 
                (middleScreen[0], middleScreen[1] + 180 * (k - selectedDifficulty)),
                k == selectedDifficulty,
                FNFfont,
                FNFfont125
            )
            menuItems.append(item)
    
    elif currentMenu == "Options":
        # Create speed slider
        speed_item = MenuItem(
            f"Speed: {selectedSpeed}", 
            (middleScreen[0], middleScreen[1] + 200 * (0 - selectedOption)),
            0 == selectedOption,
            Font100,
            Font125,
            is_slider=True,
            slider_value=selectedSpeed,
            slider_min=0.1,
            slider_max=3.0,
            tooltip=tooltip_texts["Speed"]
        )
        menuItems.append(speed_item)
        
        # Create toggleable items
        toggle_items = [
            [f"Play as: {playAs}", "Player", "Opponent", tooltip_texts["Play as"]],
            [f"No Death: {noDeath}", False, True, tooltip_texts["No Death"]],
            [f"Note style: {availableNoteStyles[selectedNoteStyle]}", 0, len(availableNoteStyles)-1, tooltip_texts["Note style"], selectedNoteStyle],
            [f"Downscroll: {downscroll}", False, True, tooltip_texts["Downscroll"]],
            [f"Render Scene: {render_scene}", False, True, tooltip_texts["Render Scene"]],
            [f"Modcharts: {modcharts}", False, True, tooltip_texts["Modcharts"]]
        ]
        
        for i, item_data in enumerate(toggle_items, 1):
            is_slider = len(item_data) > 4  # Note style has 5 elements
            
            if is_slider:
                item = MenuItem(
                    item_data[0],
                    (middleScreen[0], middleScreen[1] + 200 * (i - selectedOption)),
                    i == selectedOption,
                    Font100,
                    Font125,
                    is_slider=True,
                    slider_value=item_data[4],  # Current value
                    slider_min=item_data[1],    # Min value
                    slider_max=item_data[2],    # Max value
                    tooltip=item_data[3]        # Tooltip text
                )
            else:
                item = MenuItem(
                    item_data[0],
                    (middleScreen[0], middleScreen[1] + 200 * (i - selectedOption)),
                    i == selectedOption,
                    Font100,
                    Font125,
                    tooltip=item_data[3]        # Tooltip text
                )
            menuItems.append(item)
        
        # Add keybinds button
        keybinds_item = MenuItem(
            "Keybinds",
            (middleScreen[0], middleScreen[1] + 200 * (7 - selectedOption)),
            7 == selectedOption,
            tooltip=tooltip_texts["Keybinds"]
        )
        menuItems.append(keybinds_item)
    
    elif currentMenu == "Keybinds":
        # Format key names
        tempList = [key.name(K_a), key.name(K_s), key.name(K_w), key.name(K_d), 
                key.name(K_LEFT), key.name(K_DOWN), key.name(K_UP), key.name(K_RIGHT)]
        for k in range(len(tempList)):
            tempList[k] = tempList[k].title()
        
        tempText = [
            f"Left: {tempList[0]}", 
            f"Down: {tempList[1]}", 
            f"Up: {tempList[2]}", 
            f"Right: {tempList[3]}", 
            f"Left 2: {tempList[4]}", 
            f"Down 2: {tempList[5]}", 
            f"Up 2: {tempList[6]}", 
            f"Right 2: {tempList[7]}", 
            "Reset keybinds"
        ]
        
        keybind_tooltips = [
            "Key used for left arrows when playing as Player",
            "Key used for down arrows when playing as Player",
            "Key used for up arrows when playing as Player",
            "Key used for right arrows when playing as Player",
            "Key used for left arrows when playing as Opponent",
            "Key used for down arrows when playing as Opponent",
            "Key used for up arrows when playing as Opponent",
            "Key used for right arrows when playing as Opponent",
            "Reset all keybinds to their default values"
        ]
        
        for k in range(len(tempText)):
            item = MenuItem(
                tempText[k], 
                (middleScreen[0], middleScreen[1] + 120 * (k - selectedKeybind)),
                k == selectedKeybind,
                Font75,
                Font100,
                tooltip=keybind_tooltips[k]
            )
            menuItems.append(item)

# Credits data
credits_data = [
    {
        "header": "FUNKIN' TEAM",
        "description": "The people who worked on the original game!",
        "members": [
            {"name": "ninjamuffin99", "role": "Programmer"},
            {"name": "PhantomArcade", "role": "Animator"},
            {"name": "evilsk8r", "role": "Artist"},
            {"name": "Kawaisprite", "role": "Composer"}
        ]
    },
    {
        "header": "MORPHIC TEAM",
        "description": "The people who made the Morphic Engine (this) possible!",
        "members": [
            {"name": "CodeSoft", "role": "Developer"}
        ]
    }
]

# Draw credits menu
def draw_credits_menu():
    """Render the credits menu with efficient scrolling and dynamic layout."""
    
    global visible_top, visible_bottom
    
    # Initialize cache dictionaries if not already created
    if not hasattr(draw_credits_menu, "initialized"):
        draw_credits_menu.text_cache = {}           # Cache rendered text
        draw_credits_menu.wrap_cache = {}           # Cache wrapped text lines
        draw_credits_menu.height_cache = {}         # Cache content height measurements
        draw_credits_menu.total_height = None       # Total scrollable content height
        draw_credits_menu.fade_mask = None          # Gradient fade mask for top/bottom
        draw_credits_menu.background = None         # Pre-rendered background gradient
        draw_credits_menu.initialized = True
    
    # ---------- BACKGROUND RENDERING ----------
    # Create gradient background overlay (only once)
    if not draw_credits_menu.background:
        overlay = Surface((SCREEN_WIDTH, SCREEN_HEIGHT), SRCALPHA)
        for y in range(0, SCREEN_HEIGHT, 2):
            alpha = 150 - 50 * math.sin(y / SCREEN_HEIGHT * math.pi)
            overlay.fill((0, 0, 30, int(alpha)), (0, y, SCREEN_WIDTH, 2))
        draw_credits_menu.background = overlay
    
    screen.blit(draw_credits_menu.background, (0, 0))
    
    # ---------- UTILITY FUNCTIONS ----------
    # Efficient text rendering with caching
    def render_text(font, text, color):
        cache_key = (text, font, color)
        if cache_key not in draw_credits_menu.text_cache:
            draw_credits_menu.text_cache[cache_key] = font.render(text, True, color)
        return draw_credits_menu.text_cache[cache_key]
    
    # Efficient word wrapping with caching
    def wrap_text(text, font, max_width):
        cache_key = (text, font, max_width)
        if cache_key in draw_credits_menu.wrap_cache:
            return draw_credits_menu.wrap_cache[cache_key]
        
        words = text.split()
        wrapped_lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + word + " "
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                wrapped_lines.append(current_line)
                current_line = word + " "
        
        if current_line:
            wrapped_lines.append(current_line)
        
        draw_credits_menu.wrap_cache[cache_key] = wrapped_lines
        return wrapped_lines
    
    # Efficient height calculation with caching
    def get_wrapped_height(text, font, max_width):
        cache_key = (text, font, max_width)
        if cache_key not in draw_credits_menu.height_cache:
            lines = wrap_text(text, font, max_width)
            draw_credits_menu.height_cache[cache_key] = len(lines) * font.get_height()
        return draw_credits_menu.height_cache[cache_key]
    
    # Helper to render text at position with optional alignment
    def draw_text(text, font, color, position, align="midtop", check_visibility=True):
        y_pos = position[1]
        if not check_visibility or (visible_top <= y_pos <= visible_bottom):
            rendered_text = render_text(font, text, color)
            rect = rendered_text.get_rect(**{align: position})
            screen.blit(rendered_text, rect)
            return rect
        return Rect(position[0], position[1], 0, font.get_height())  # Dummy rect
    
    # ---------- HEADER RENDERING ----------
    
    # ---------- SCROLLING SETUP ----------
    # Content layout parameters
    content_margin = 30
    max_text_width = SCREEN_WIDTH - content_margin * 2
    
    # Calculate total content height (only once)
    if draw_credits_menu.total_height is None:
        total_height = 0
        for section in credits_data:
            # Section header height
            total_height += Font75.get_height() + 15
            # Description height
            total_height += get_wrapped_height(section["description"], Font30, max_text_width) + 30
            
            # Member entries heights
            for member in section["members"]:
                name_height = get_wrapped_height(member["name"], Font30, max_text_width)
                role_height = get_wrapped_height(member["role"], Font30, max_text_width)
                total_height += name_height + role_height + 20
            
            # Section spacing
            total_height += 60
        
        draw_credits_menu.total_height = total_height
    
    # Calculate scrolling parameters
    content_height = SCREEN_HEIGHT - 200  # Adjusted for smaller bars
    scroll_step = 20
    max_scroll = max(0, draw_credits_menu.total_height - content_height + 120)
    max_scroll_steps = int(max_scroll / scroll_step)
    
    # Ensure scrolling stays within bounds
    global selectedOption
    selectedOption = max(0, min(selectedOption, max_scroll_steps))
    scroll_offset = selectedOption * scroll_step
    
    # ---------- FADE EFFECTS ----------
    # Create fade mask (only once)
    if draw_credits_menu.fade_mask is None:
        fade_mask = Surface((SCREEN_WIDTH, SCREEN_HEIGHT), SRCALPHA)
        
        # Solid black bar at the top - REDUCED SIZE
        fade_mask.fill((0, 0, 0, 255), (0, 0, SCREEN_WIDTH, 90))
        
        # Top fade gradient (transition from solid to transparent)
        for i in range(60):
            alpha = int(255 * (1 - i / 60))
            fade_mask.fill((0, 0, 0, alpha), (0, 90+i, SCREEN_WIDTH, 1))
        
        # Bottom fade gradient (transition from transparent to solid)
        for i in range(60):
            alpha = int(255 * (i / 60))
            fade_mask.fill((0, 0, 0, alpha), (0, SCREEN_HEIGHT-100+i, SCREEN_WIDTH, 1))
        
        # Solid black bar at the bottom - REDUCED SIZE
        fade_mask.fill((0, 0, 0, 255), (0, SCREEN_HEIGHT-40, SCREEN_WIDTH, 40))
        
        draw_credits_menu.fade_mask = fade_mask
    
    # ---------- CONTENT RENDERING ----------
    # Visibility boundaries for efficient rendering - ADJUSTED
    visible_top = 20
    visible_bottom = SCREEN_HEIGHT
    current_y = 150 - scroll_offset  # Adjusted starting position
    
    # Draw all content sections
    for section in credits_data:
        # Calculate section height for visibility check
        section_height = (Font75.get_height() + 15 +
                         get_wrapped_height(section["description"], Font30, max_text_width) + 30)
        
        for member in section["members"]:
            section_height += (get_wrapped_height(member["name"], Font30, max_text_width) +
                              get_wrapped_height(member["role"], Font30, max_text_width) + 20)
        
        section_height += 60
        
        # Skip rendering if section is not visible
        if current_y + section_height < visible_top or current_y > visible_bottom:
            current_y += section_height
            continue
        
        # Draw section header
        header_rect = draw_text(section["header"], Font75, (220, 220, 255), 
                               (middleScreen[0], current_y))
        current_y += header_rect.height + 15
        
        # Draw description
        wrapped_desc = wrap_text(section["description"], Font30, max_text_width)
        for line in wrapped_desc:
            draw_text(line, Font30, (220, 220, 220), (middleScreen[0], current_y))
            current_y += Font30.get_height()
        current_y += 30
        
        # Draw members
        for member in section["members"]:
            # Calculate member entry height
            name_height = get_wrapped_height(member["name"], Font30, max_text_width)
            role_height = get_wrapped_height(member["role"], Font30, max_text_width)
            member_height = name_height + role_height + 10
            
            # Skip if not visible
            if not (current_y > visible_bottom or current_y + member_height < visible_top):
                # Draw subtle highlight background
                highlight_rect = Rect(middleScreen[0] - 300, current_y, 600, member_height + 16)
                highlight_surface = Surface((600, member_height + 16), SRCALPHA)
                highlight_surface.fill((100, 100, 180, 30))
                draw.rect(highlight_surface, (100, 100, 180, 60), (0, 0, 600, member_height + 16), 
                         width=2, border_radius=15)
                screen.blit(highlight_surface, highlight_rect)
                
                # Draw name
                member_y = current_y + 8
                wrapped_name = wrap_text(member["name"], Font30, max_text_width)
                for line in wrapped_name:
                    draw_text(line, Font30, (255, 255, 255), (middleScreen[0], member_y))
                    member_y += Font30.get_height()
                
                # Draw role
                wrapped_role = wrap_text(member["role"], Font30, max_text_width)
                for line in wrapped_role:
                    draw_text(line, Font30, (150, 150, 255), (middleScreen[0], member_y + 5))
                    member_y += Font30.get_height()
            
            current_y += member_height + 20
        
        current_y += 60  # Section spacing
    
    # Apply fade mask
    screen.blit(draw_credits_menu.fade_mask, (0, 0))
    
    # ---------- UI CONTROLS ----------
    # Draw scroll indicators
    if selectedOption > 0:
        draw_text("▲ Scroll Up", Font30, (200, 200, 255), (middleScreen[0], 20), 
                 check_visibility=False)
    
    if selectedOption < max_scroll_steps:
        draw_text("▼ Scroll Down", Font30, (200, 200, 255), (middleScreen[0], SCREEN_HEIGHT - 20), 
                 align="midbottom", check_visibility=False)
    
    # Draw scrollbar track
    track_height = SCREEN_HEIGHT - 120
    track_surf = Surface((10, track_height), SRCALPHA)
    draw.rect(track_surf, (100, 100, 180, 50), (0, 0, 10, track_height), border_radius=5)
    screen.blit(track_surf, (SCREEN_WIDTH - 25, 60))
    
    # Draw scrollbar thumb
    content_ratio = min(1, content_height / max(1, draw_credits_menu.total_height))
    thumb_height = max(30, track_height * content_ratio)
    scroll_ratio = selectedOption / max(1, max_scroll_steps)
    thumb_y = scroll_ratio * (track_height - thumb_height)
    
    thumb_surf = Surface((10, int(thumb_height)), SRCALPHA)
    draw.rect(thumb_surf, (150, 150, 255, 200), (0, 0, 10, int(thumb_height)), border_radius=5)
    screen.blit(thumb_surf, (SCREEN_WIDTH - 25, 60 + thumb_y))
    
    # Draw return instruction
    draw_text("Press ESC to return", Font30, (220, 220, 255), 
             (SCREEN_WIDTH - 30, SCREEN_HEIGHT - 25), align="bottomright", check_visibility=False)
    
    # ---------- PARTICLES ----------
    # Spawn particles more efficiently
    if random.random() < 0.03:  # Reduced particle generation rate
        particles.append(Particle(
            random.randint(0, SCREEN_WIDTH),
            random.randint(100, SCREEN_HEIGHT - 100)
        ))


# Save options to file
def saveOptions():
    global options
    options["selectedSpeed"] = selectedSpeed
    options["playAs"] = playAs
    options["noDying"] = "True" if noDeath else "False"
    options["downscroll"] = "True" if downscroll else "False"
    options["selectedNoteStyle"] = selectedNoteStyle
    options["render_scene"] = "True" if render_scene else "False"
    options["modcharts"] = "True" if modcharts else "False"
    options["keybinds"] = [K_a, K_s, K_w, K_d, K_LEFT, K_DOWN, K_UP, K_RIGHT]
    
    try:
        json.dump(options, open("assets\options.json", "w"))
    except Exception as e:
        print(f"Error saving options: {e}")

# Change menu with animation
def change_menu(new_menu):
    global currentMenu, previousMenu, menuTransition, transitionDirection, startupFade, selectedDifficulty
    previousMenu = currentMenu
    currentMenu = new_menu
    menuTransition = 0
    transitionDirection = 1
    
    # Initialize selectedDifficulty when entering difficulty selection
    if new_menu == "Select difficulty" and selectedDifficulty is None:
        selectedDifficulty = 0
    
    # Start background transition when leaving startup screen
    if previousMenu == "Startup" and new_menu == "Main":
        startupFade = 0
    
    # Generate particles for menu transition
    generate_menu_transition_particles()
    
    update_menu_items()

# Generate particles for menu transitions
def generate_menu_transition_particles():
    global particles
    
    # Clear existing particles to avoid too many
    particles = []
    
    # Add new transition particles
    for _ in range(50):
        p = Particle(
            random.randint(0, SCREEN_WIDTH),
            random.randint(0, SCREEN_HEIGHT)
        )
        particles.append(p)

# Draw custom animated cursor
def draw_cursor():
    global cursorPulse, particles
    
    # Update cursor position with easing
    cursorPos[0] += (targetCursorPos[0] - cursorPos[0]) * ease_out_quad(0.3)
    cursorPos[1] += (targetCursorPos[1] - cursorPos[1]) * ease_out_quad(0.3)
    
    # Animate cursor pulse
    cursorPulse = (cursorPulse + 0.05) % (2 * math.pi)
    pulse_scale = 1.0 + 0.15 * math.sin(cursorPulse)
    
    # Draw cursor glow
    glow_size = 20 * pulse_scale
    glow_surf = Surface((int(glow_size*2), int(glow_size*2)), SRCALPHA)
    for i in range(3):
        size = glow_size - i*3
        alpha = 100 - i*30
        draw.circle(glow_surf, (150, 150, 255, alpha), (glow_size, glow_size), size)
    screen.blit(glow_surf, (cursorPos[0]-glow_size, cursorPos[1]-glow_size))
    
    # Draw cursor
    size = 12 * pulse_scale
    draw.circle(screen, (255, 255, 255), cursorPos, size)
    draw.circle(screen, (100, 100, 255), cursorPos, size - 3)
    
    # Occasionally spawn particles from cursor
    if random.random() < 0.1:
        particles.append(Particle(cursorPos[0], cursorPos[1]))

# Draw edit keybind screen
def draw_edit_keybind_screen():
    # Background overlay with alpha
    overlay = Surface((SCREEN_WIDTH, SCREEN_HEIGHT), SRCALPHA)
    overlay.fill((0, 0, 0, 230))
    screen.blit(overlay, (0, 0))
    
    # Create box for keybind UI
    box_width, box_height = 800, 400
    box_rect = Rect(0, 0, box_width, box_height)
    box_rect.center = middleScreen
    
    # Draw box with glow effect
    pulse = 0.5 + 0.5 * math.sin(systime.time() * 3)
    glow_width = box_width + 20 * pulse
    glow_height = box_height + 20 * pulse
    
    # Draw glowing outline
    for i in range(5):
        size = i * 4
        alpha = 150 - i * 30
        outline_rect = Rect(0, 0, box_width + size, box_height + size)
        outline_rect.center = middleScreen
        draw.rect(screen, (100, 100, 255, alpha), outline_rect, border_radius=30)
    
    # Draw main box
    draw.rect(screen, (40, 40, 60, 240), box_rect, border_radius=20)
    draw.rect(screen, (100, 100, 255, 200), box_rect, width=3, border_radius=20)
    
    # Instruction text with animation
    pulse = 0.5 + 0.5 * math.sin(systime.time() * 4)
    text_color = (255, 255, 255)
    
    # Title
    title_text = cached_text_render(Font100, "Edit Keybind", text_color)
    title_rect = title_text.get_rect()
    title_rect.midtop = (middleScreen[0], box_rect.top + 40)
    screen.blit(title_text, title_rect)
    
    # Instructions
    instr_text = cached_text_render(Font75, "Press a key to assign", text_color)
    instr_rect = instr_text.get_rect()
    instr_rect.midtop = (middleScreen[0], title_rect.bottom + 40)
    screen.blit(instr_text, instr_rect)
    
    # Escape notice
    escape_text = cached_text_render(Font75, "(Escape to cancel)", 
                                    (200 + 55 * pulse, 200 + 55 * pulse, 200 + 55 * pulse))
    escape_rect = escape_text.get_rect()
    escape_rect.midtop = (middleScreen[0], instr_rect.bottom + 40)
    screen.blit(escape_text, escape_rect)
    
    # Key visualization
    key_box_size = 100 + 20 * pulse
    key_box = Rect(0, 0, key_box_size, key_box_size)
    key_box.midbottom = (middleScreen[0], box_rect.bottom - 40)
    
    # Draw animated key box
    draw.rect(screen, (100, 100, 255, 150), key_box, border_radius=15)
    draw.rect(screen, (200, 200, 255, 200), key_box, width=3, border_radius=15)
    
    # Draw ? symbol in box
    q_text = cached_text_render(Font125, "?", (255, 255, 255))
    q_rect = q_text.get_rect()
    q_rect.center = key_box.center
    screen.blit(q_text, q_rect)

# Draw startup screen
def draw_startup_screen():
    # Gradient background
    gradient = Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    for y in range(SCREEN_HEIGHT):
        # Create a blue to dark blue gradient
        ratio = y / SCREEN_HEIGHT
        color = (
            int(20 + 20 * math.sin(systime.time() * 0.5 + ratio * 3)),
            int(20 + 20 * math.sin(systime.time() * 0.7 + ratio * 2)),
            int(40 + 20 * math.sin(systime.time() * 0.3 + ratio * 4))
        )
        pygame.draw.line(gradient, color, (0, y), (SCREEN_WIDTH, y))
    screen.blit(gradient, (0, 0))
    
    # Add subtle floating particles
    for _ in range(2):
        if random.random() < 0.1:
            particles.append(Particle(
                random.randint(0, SCREEN_WIDTH),
                random.randint(0, SCREEN_HEIGHT)
            ))
    
    # Draw logo with fade-in effect
    if logoImg:
        # Create a pulsing effect
        pulse = 1.0 + 0.05 * math.sin(systime.time() * 2)
        logo_width = int(640 * pulse)
        logo_height = int(600 * pulse)
        pulsed_logo = transform.scale(logoImg, (logo_width, logo_height))
        
        # Apply fade in
        alpha = int(255 * min(1, systime.time() / 1.2))
        pulsed_logo.set_alpha(alpha)
        
        # Center the logo
        logo_rect = pulsed_logo.get_rect()
        logo_rect.center = (middleScreen[0], middleScreen[1] - 100)
        
        # Draw glow effect
        if systime.time() > 1.0:  # Start glow after logo appears
            glow_intensity = 0.5 + 0.5 * math.sin(systime.time() * 1.5)
            glow_size = int(logo_width * (1.0 + 0.05 * glow_intensity))
            glow_logo = transform.scale(logoImg, (glow_size, glow_size))
            glow_logo.set_alpha(50)
            glow_rect = glow_logo.get_rect()
            glow_rect.center = logo_rect.center
            screen.blit(glow_logo, glow_rect)
        
        # Draw the logo
        screen.blit(pulsed_logo, logo_rect)
    
    # Animated "Enter to start" text
    time_offset = systime.time() * 3
    pulse = 0.5 + 0.5 * math.sin(time_offset)
    text_color = (200 + int(55 * pulse), 200 + int(55 * pulse), 255)
    
    # Create pulsing text with shadow
    enter_text = cached_text_render(Font100, "Enter to start", text_color)
    
    # Apply subtle floating movement
    y_offset = math.sin(time_offset * 0.5) * 10
    
    # Position text
    enter_rect = enter_text.get_rect()
    enter_rect.center = (middleScreen[0], middleScreen[1] + 200 + y_offset)
    
    # Draw the text
    screen.blit(enter_text, enter_rect)
    
    # Add occasional particle burst
    if random.random() < 0.02:
        for _ in range(10):
            particles.append(Particle(enter_rect.centerx, enter_rect.centery))

# Initialize menu items for main menu
update_menu_items()

# Create offscreen surfaces for optimized rendering
bg_surface = Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

# Game loop
clock = pygame.time.Clock()
run = True
fps_display = False
fps_font = font.SysFont("Arial", 24)
fps_values = []

while run:
    # Calculate delta time for smooth animations
    dt = min(0.05, clock.tick(0) / 1000.0)  # Cap dt to avoid physics issues, uncap FPS
    
    # FPS calculation
    if fps_display:
        fps = clock.get_fps()
        fps_values.append(fps)
        if len(fps_values) > 30:
            fps_values.pop(0)
    
    # Update mouse position
    targetCursorPos = list(mouse.get_pos())
    
    # Handle events
    for events in event.get():
        if events.type == QUIT:
            saveOptions()
            run = False
            
        if events.type == KEYDOWN:
            if events.key == K_F12:
                dev_tools.toggle()
                continue
            # Toggle FPS display with F3
            if events.key == K_F3:
                fps_display = not fps_display
                
            # Handle escape key for navigation
            if events.key == K_ESCAPE:
                if currentMenu == "Main":
                    saveOptions()
                    run = False
                elif currentMenu == "Startup":
                    saveOptions()
                    run = False
                elif currentMenu == "Keybinds":
                    change_menu("Options")
                elif currentMenu == "Edit keybind":
                    currentMenu = "Keybinds"
                    update_menu_items()
                else:
                    change_menu("Main")
            
            # Handle enter key for selection
            elif events.key == K_RETURN and not preventDoubleEnter:
                if currentMenu == "Startup":
                    change_menu("Main")
                    preventDoubleEnter = True
                elif currentMenu == "Main":
                    if selectedMain == 0:
                        change_menu("Select music")
                    elif selectedMain == 1:
                        change_menu("Options")
                    elif selectedMain == 2:
                        # Reset scroll position when entering credits
                        selectedOption = 0
                        change_menu("Credits")
                    preventDoubleEnter = True
                
                elif currentMenu == "Select music":
                    difficulties = get_difficulties(musicList[selectedMusic])
                    if difficulties:
                        if len(difficulties) == 1 and difficulties[0] is None:
                            # Only one difficulty, launch the game directly
                            selectedDifficulty = None
                            if menuMusic:
                                menuMusic.stop()
                            restart = True
                            currentMenu = "Select music"
                            while restart:
                                restart = Main_game(musicList[selectedMusic], selectedSpeed, playAs, noDeath,
                                                   availableNoteStyles[selectedNoteStyle],
                                                   [K_a, K_s, K_w, K_d, K_LEFT, K_DOWN, K_UP, K_RIGHT], downscroll, render_scene, modcharts, selectedDifficulty)
                            if menuMusic:
                                menuMusic.play(-1)
                            
                            change_menu("Select music")
                        else:
                            # Multiple difficulties, show selection menu
                            selectedDifficulty = 0  # Initialize with first difficulty
                            change_menu("Select difficulty")
                    else:
                        print(f"No difficulties found for {musicList[selectedMusic]}")
                
                elif currentMenu == "Select difficulty":
                    difficulties = get_difficulties(musicList[selectedMusic])
                    if difficulties and 0 <= selectedDifficulty < len(difficulties):
                        if menuMusic:
                            menuMusic.stop()
                        restart = True
                        while restart:
                            # Get the actual difficulty name
                            difficulty_name = difficulties[selectedDifficulty]
                            # If difficulty_name is None, use a default string
                            if difficulty_name is None:
                                difficulty_name = "Normal"
                            restart = Main_game(musicList[selectedMusic], selectedSpeed, playAs, noDeath,
                                              availableNoteStyles[selectedNoteStyle],
                                              [K_a, K_s, K_w, K_d, K_LEFT, K_DOWN, K_UP, K_RIGHT], downscroll, render_scene, modcharts, difficulty_name)
                        if menuMusic:
                            menuMusic.play(-1)
                        # Properly transition back to song select when game exits
                        change_menu("Select music")
                    preventDoubleEnter = True
                
                elif currentMenu == "Options":
                    if selectedOption == 7 and not preventDoubleEnter:
                        change_menu("Keybinds")
                        preventDoubleEnter = True
            
            # Handle navigation keys
            elif currentMenu != "Edit keybind" and currentMenu != "Startup":
                # Up navigation
                if (events.key == K_w or events.key == K_UP):
                    if currentMenu == "Main" and selectedMain > 0:
                        selectedMain -= 1
                    elif currentMenu == "Credits":
                        # Scroll credits up
                        selectedOption = max(0, selectedOption - 1)
                    elif currentMenu == "Select music" and selectedMusic > 0:
                        selectedMusic -= 1
                    elif currentMenu == "Options" and selectedOption > 0:
                        selectedOption -= 1
                    elif currentMenu == "Keybinds" and selectedKeybind > 0:
                        selectedKeybind -= 1
                    update_menu_items()
                
                # Down navigation
                elif (events.key == K_s or events.key == K_DOWN):
                    if currentMenu == "Main" and selectedMain < 2:  # Updated to include Credits
                        selectedMain += 1
                    elif currentMenu == "Credits":
                        # Calculate total content height to determine max scroll
                        total_height = 0
                        for section in credits_data:
                            total_height += Font100.get_height() + 10  # Header
                            total_height += Font30.get_height() + 30   # Description
                            total_height += sum((Font75.get_height() + Font30.get_height() + 20) for _ in section["members"])
                            total_height += 60  # Section spacing
                        
                        content_height = SCREEN_HEIGHT - 200  # Visible area
                        max_scroll = max(0, total_height - content_height)
                        max_scroll_steps = int(max_scroll / 40) + 1  # Each scroll step is 40px
                        
                        # Allow scrolling based on actual content
                        selectedOption = min(max_scroll_steps, selectedOption + 1)
                    elif currentMenu == "Select music" and selectedMusic < len(musicList) - 1:
                        selectedMusic += 1
                    elif currentMenu == "Options" and selectedOption < 7:
                        selectedOption += 1
                    elif currentMenu == "Keybinds" and selectedKeybind < 8:
                        selectedKeybind += 1
                    update_menu_items()
                
                # Left/right for option adjustments
                elif currentMenu == "Options":
                    if selectedOption == 0:  # Speed
                        if (events.key == K_a or events.key == K_LEFT) and selectedSpeed > 0.1:
                            selectedSpeed = round(selectedSpeed - 0.1, 1)
                            menuItems[0].slider_value = selectedSpeed
                            menuItems[0].text = f"Speed: {selectedSpeed}"
                        elif (events.key == K_d or events.key == K_RIGHT):
                            selectedSpeed = round(selectedSpeed + 0.1, 1)
                            menuItems[0].slider_value = selectedSpeed
                            menuItems[0].text = f"Speed: {selectedSpeed}"
                    elif selectedOption == 1:  # Play as
                        if (events.key == K_a or events.key == K_LEFT or events.key == K_d or events.key == K_RIGHT):
                            playAs = "Opponent" if playAs == "Player" else "Player"
                            menuItems[1].text = f"Play as: {playAs}"
                    elif selectedOption == 2:  # No Death
                        if (events.key == K_a or events.key == K_LEFT or events.key == K_d or events.key == K_RIGHT):
                            noDeath = not noDeath
                            menuItems[2].text = f"No Death: {noDeath}"
                    elif selectedOption == 3:  # Note style
                        if (events.key == K_a or events.key == K_LEFT) and selectedNoteStyle > 0:
                            selectedNoteStyle -= 1
                            menuItems[3].slider_value = selectedNoteStyle
                            menuItems[3].text = f"Note style: {availableNoteStyles[selectedNoteStyle]}"
                        elif (events.key == K_d or events.key == K_RIGHT) and selectedNoteStyle < len(availableNoteStyles) - 1:
                            selectedNoteStyle += 1
                            menuItems[3].slider_value = selectedNoteStyle
                            menuItems[3].text = f"Note style: {availableNoteStyles[selectedNoteStyle]}"
                    elif selectedOption == 4:  # Downscroll
                        if (events.key == K_a or events.key == K_LEFT or events.key == K_d or events.key == K_RIGHT):
                            downscroll = not downscroll
                            menuItems[4].text = f"Downscroll: {downscroll}"
                    elif selectedOption == 5:  # Render Scene
                        if (events.key == K_a or events.key == K_LEFT or events.key == K_d or events.key == K_RIGHT):
                            render_scene = not render_scene
                            menuItems[5].text = f"Render Scene: {render_scene}"
                    elif selectedOption == 6:  # Modcharts
                        if (events.key == K_a or events.key == K_LEFT or events.key == K_d or events.key == K_RIGHT):
                            modcharts = not modcharts
                            menuItems[6].text = f"Modcharts: {modcharts}"
            
            # Handle key binding
            elif currentMenu == "Edit keybind" and waitingForKeyPress:
                if events.key != K_ESCAPE and events.key not in [K_RETURN, K_BACKSPACE, K_SPACE, 
                                                                 KMOD_SHIFT, KMOD_CTRL, KMOD_ALT, KMOD_CAPS]:
                    # Store the new keybind
                    if selectedKeybind == 0:
                        K_a = events.key
                    elif selectedKeybind == 1:
                        K_s = events.key
                    elif selectedKeybind == 2:
                        K_w = events.key
                    elif selectedKeybind == 3:
                        K_d = events.key
                    elif selectedKeybind == 4:
                        K_LEFT = events.key
                    elif selectedKeybind == 5:
                        K_DOWN = events.key
                    elif selectedKeybind == 6:
                        K_UP = events.key
                    elif selectedKeybind == 7:
                        K_RIGHT = events.key
                    
                    currentMenu = "Keybinds"
                    waitingForKeyPress = False
                    update_menu_items()
        
        # Mouse handling
        if events.type == MOUSEBUTTONDOWN and events.button == 1:  # Left click
            # If on startup screen, go to main menu
            if currentMenu == "Startup":
                change_menu("Main")
                continue
            
            # Check slider interactions first
            if currentMenu == "Options":
                for i, item in enumerate(menuItems):
                    if item.is_slider and item.slider_rect and item.slider_rect.collidepoint(mouse.get_pos()):
                        item.update_slider_value(mouse.get_pos()[0])
                        
                        # Update game values based on slider
                        if i == 0:  # Speed slider
                            selectedSpeed = item.slider_value
                            item.text = f"Speed: {selectedSpeed}"
                        elif i == 3:  # Note style slider
                            selectedNoteStyle = int(item.slider_value)
                            item.text = f"Note style: {availableNoteStyles[selectedNoteStyle]}"
                        
                        # Start tracking mouse for dragging
                        if not pygame.mouse.get_pressed()[0]:
                            pygame.event.post(pygame.event.Event(MOUSEBUTTONDOWN, {'button': 1, 'pos': mouse.get_pos()}))
            
            # Check button/item clicks
            for i, item in enumerate(menuItems):
                if item.rect and item.rect.collidepoint(mouse.get_pos()):
                    # Add particle burst effect on click
                    for _ in range(15):
                        particles.append(Particle(mouse.get_pos()[0], mouse.get_pos()[1]))
                    
                    if currentMenu == "Main":
                        selectedMain = i
                        if i == 0:  # Play
                            change_menu("Select music")
                        elif i == 1:  # Options
                            change_menu("Options")
                        elif i == 2:  # Credits
                            selectedOption = 0  # Reset credits scroll
                            change_menu("Credits")
                    
                    elif currentMenu == "Select music":
                        selectedMusic = i
                        update_menu_items()
                        # Double click to select music and go to difficulty select
                        if events.button == 1 and pygame.time.get_ticks() - last_click_time < 500 and last_click_pos == i:
                            difficulties = get_difficulties(musicList[selectedMusic])
                            print(difficulties)
                            if difficulties:
                                if len(difficulties) == 1 and difficulties[0] is None:
                                    # Only one difficulty, launch the game directly
                                    selectedDifficulty = None
                                    if menuMusic:
                                        menuMusic.stop()
                                    restart = True
                                    while restart:
                                        restart = Main_game(musicList[selectedMusic], selectedSpeed, playAs, noDeath,
                                                            availableNoteStyles[selectedNoteStyle],
                                                            [K_a, K_s, K_w, K_d, K_LEFT, K_DOWN, K_UP, K_RIGHT], downscroll, render_scene, modcharts, selectedDifficulty)
                                    if menuMusic:
                                        menuMusic.play(-1)
                                else:
                                    # Multiple difficulties, show selection menu
                                    selectedDifficulty = None
                                    change_menu("Select difficulty")
                            else:
                                print(f"No difficulties found for {musicList[selectedMusic]}")
                    
                    elif currentMenu == "Options":
                        selectedOption = i
                        update_menu_items()
                        if i == 7:  # Keybinds
                            change_menu("Keybinds")
                        # Handle option toggle/adjustment with mouse
                        elif i == 0:  # Speed - handled by slider
                            pass
                        elif i == 1:  # Play as
                            playAs = "Opponent" if playAs == "Player" else "Player"
                            menuItems[1].text = f"Play as: {playAs}"
                        elif i == 2:  # No Death
                            noDeath = not noDeath
                            menuItems[2].text = f"No Death: {noDeath}"
                        elif i == 3:  # Note style - handled by slider
                            pass
                        elif i == 4:  # Downscroll
                            downscroll = not downscroll
                            menuItems[4].text = f"Downscroll: {downscroll}"
                        elif i == 5:  # Render Scene
                            render_scene = not render_scene
                            menuItems[5].text = f"Render Scene: {render_scene}"
                        elif i == 6:  # Modcharts
                            modcharts = not modcharts
                            menuItems[6].text = f"Modcharts: {modcharts}"
                    
                    elif currentMenu == "Keybinds":
                        selectedKeybind = i
                        update_menu_items()
                        
                        # Double click to edit or reset keybind
                        if events.button == 1 and pygame.time.get_ticks() - last_click_time < 500 and last_click_pos == i:
                            if i < 8:  # Keybind entry
                                currentMenu = "Edit keybind"
                                waitingForKeyPress = True
                            elif i == 8:  # Reset keybinds
                                # Reset keybinds
                                K_a = 97
                                K_s = 115
                                K_w = 119
                                K_d = 100
                                K_LEFT = 1073741904
                                K_DOWN = 1073741905
                                K_UP = 1073741906
                                K_RIGHT = 1073741903
                                update_menu_items()
                    
                    elif currentMenu == "Select difficulty":
                        selectedDifficulty = i
                        print("Selected difficulty:", selectedDifficulty)
                        update_menu_items()
                        # Double click to select difficulty
                        if events.button == 1 and pygame.time.get_ticks() - last_click_time < 500 and last_click_pos == i:
                            difficulties = get_difficulties(musicList[selectedMusic])
                            if menuMusic:
                                menuMusic.stop()
                            restart = True
                            while restart:
                                # Get the actual difficulty name, not just the index
                                if difficulties and 0 <= selectedDifficulty < len(difficulties):
                                    difficulty_name = difficulties[selectedDifficulty]
                                    # If difficulty_name is None, use a default string
                                    if difficulty_name is None:
                                        difficulty_name = "Normal"
                                else:
                                    difficulty_name = None
                                restart = Main_game(musicList[selectedMusic], selectedSpeed, playAs, noDeath,
                                                    availableNoteStyles[selectedNoteStyle],
                                                    [K_a, K_s, K_w, K_d, K_LEFT, K_DOWN, K_UP, K_RIGHT], downscroll, render_scene, modcharts, difficulty_name)
                            if menuMusic:
                                menuMusic.play(-1)
                            # Add this line to return to song select
                            change_menu("Select music")
        
        if dev_tools.handle_event(events):
            continue
        
        # Mouse drag handling for sliders
        if pygame.mouse.get_pressed()[0] and currentMenu == "Options":
            for i, item in enumerate(menuItems):
                if item.is_slider and item.slider_rect and item.slider_rect.collidepoint(mouse.get_pos()):
                    item.update_slider_value(mouse.get_pos()[0])
                    
                    # Update game values based on slider
                    if i == 0:  # Speed slider
                        selectedSpeed = item.slider_value
                        item.text = f"Speed: {selectedSpeed}"
                    elif i == 3:  # Note style slider
                        selectedNoteStyle = int(item.slider_value)
                        item.text = f"Note style: {availableNoteStyles[selectedNoteStyle]}"
    
    # Handle double enter prevention
    if preventDoubleEnter:
        preventDoubleEnter = pygame.key.get_pressed()[K_RETURN]
    
    # Update particles
    particles = [p for p in particles if p.update(dt)]
    
    # Update menu item positions and hover states
    for item in menuItems:
        item.update(dt)
        
        # Check for hover state
        item.hover = item.rect and item.rect.collidepoint(mouse.get_pos()) or \
                     (item.is_slider and item.slider_rect and item.slider_rect.collidepoint(mouse.get_pos()))
    
    # Update menu transitions
    if transitionDirection > 0:  # Transitioning in
        menuTransition = min(1, menuTransition + dt * TRANSITION_SPEED)
    else:  # Transitioning out
        menuTransition = max(0, menuTransition - dt * TRANSITION_SPEED)
    
    # Update startup fade if needed
    if currentMenu == "Main" and previousMenu == "Startup":
        startupFade = min(1, startupFade + dt * startupFadeSpeed)
    
    # Rendering begins here
    # Update screen
    dev_tools.update(dt, sys.modules[__name__])
    
    # Draw background
    screen.blit(menuBG, BGrect)
    
    # Animate background scroll
    bgScroll = (bgScroll + dt * 20) % SCREEN_WIDTH
    
    # Draw particles
    for p in particles:
        p.draw(screen)
    
    # Draw appropriate menu
    if currentMenu == "Startup":
        draw_startup_screen()
    elif currentMenu == "Credits":
        draw_credits_menu()
    else:
        # Apply subtle hover effects to menu items
        for item in menuItems:
            item.draw(screen)
    
    # Draw keybind overlay if needed
    if currentMenu == "Edit keybind":
        draw_edit_keybind_screen()
    
    # Draw version text
    version_text = cached_text_render(Font30, f"Version {VERSION}", (200, 200, 200), shadow=False)
    version_rect = version_text.get_rect()
    version_rect.bottomright = (SCREEN_WIDTH - 10, SCREEN_HEIGHT - 10)
    screen.blit(version_text, version_rect)
    
    version_text = cached_text_render(Font30, "Morphic Engine", (200, 200, 200), shadow=False)
    version_rect = version_text.get_rect()
    version_rect.bottomright = (SCREEN_WIDTH - 10, SCREEN_HEIGHT - 50)
    screen.blit(version_text, version_rect)
    
    # Draw FPS counter if enabled
    if fps_display and fps_values:
        avg_fps = sum(fps_values) / len(fps_values)
        fps_text = fps_font.render(f"FPS: {avg_fps:.1f}", True, (255, 255, 255))
        screen.blit(fps_text, (10, 10))
    
    # Draw custom cursor
    draw_cursor()
    
    # Hide default cursor
    pygame.mouse.set_visible(False)
    
    # Draw DevTools if visible
    dev_tools.draw(screen)
    
    # Update display
    display.flip()

# Clean up
saveOptions()
pygame.quit()
sys.exit()
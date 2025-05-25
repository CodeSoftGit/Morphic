import pygame
from pygame import Rect, Surface, SRCALPHA, FULLSCREEN, HWSURFACE, DOUBLEBUF, QUIT, KEYDOWN, MOUSEBUTTONDOWN, MOUSEWHEEL, K_F12, K_F3, K_ESCAPE, K_RETURN, K_UP, K_DOWN, K_LEFT, K_RIGHT, K_w, K_s, K_a, K_d, K_b, K_BACKSPACE, K_SPACE, KMOD_SHIFT, KMOD_CTRL, KMOD_ALT, KMOD_CAPS, mouse, display, image, transform, font, draw, mixer, key, event
import json
import math
import time as systime
import sys
import random
from Game import MainMenu # Assuming Game.py and MainMenu class exist
from DevTools import DevTools # Assuming DevTools.py and DevTools class exist
import os

pygame.init()

# --- Constants and Configuration ---
VERSION = '1.0.2-alpha-visual-fx' # Updated version
DEV_TOOLS_ENABLED = True # Set to False to disable DevTools

# Screen setup
if hasattr(pygame, 'GL_CONTEXT_PROFILE_CORE'):
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
    pygame.display.gl_set_attribute(pygame.GL_ACCELERATED_VISUAL, 1)
    pygame.display.gl_set_attribute(pygame.GL_DOUBLEBUFFER, 1)
    pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)

screen = display.set_mode((0, 0), FULLSCREEN | HWSURFACE | DOUBLEBUF)
SCREEN_WIDTH = display.Info().current_w
SCREEN_HEIGHT = display.Info().current_h
middleScreen = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2

# --- Konami Code & Color Scheme ---
KONAMI_CODE_SEQUENCE = [K_UP, K_UP, K_DOWN, K_DOWN, K_LEFT, K_RIGHT, K_LEFT, K_RIGHT, K_b, K_a]
konami_input_buffer = []
konami_mode_active = False

default_colors = {
    "text_primary": (255, 255, 255), "text_secondary": (200, 200, 200), "text_highlight": (220, 220, 255),
    "text_shadow": (40, 40, 40), "text_button": (255, 255, 255),
    "bg_main_fill": (20, 20, 40), "bg_particle_base": (100, 100, 200),
    "button_normal_surf_bg": (80, 80, 100, 200), "button_normal_surf_border": (120, 120, 180, 255),
    "button_hover_surf_bg": (100, 100, 150, 230), "button_hover_surf_border": (150, 150, 220, 255),
    "slider_bg_surf": (80, 80, 100, 200), "slider_knob_surf": (150, 150, 220, 255),
    "tooltip_bg": (40, 40, 60, 200), "tooltip_border": (100, 100, 255, 200),
    "credits_bg_overlay_line_base": (0,0,30), "credits_header": (220,220,255), "credits_text": (200,200,200),
    "credits_member_bg": (100,100,180,30), "credits_member_border": (100,100,180,60),
    "credits_scrollbar_track": (100,100,180,50), "credits_scrollbar_thumb": (150,150,255,200),
    "credits_nav_text": (200, 200, 255),
    "edit_keybind_overlay": (0,0,0,230), "edit_keybind_box_bg": (40,40,60,240), "edit_keybind_box_border": (100,100,255,200),
    "edit_keybind_title": (255,255,255), "edit_keybind_instruction": (255,255,255), "edit_keybind_escape_base": (200,200,200),
    "edit_keybind_q_box": (100,100,255,150), "edit_keybind_q_border": (200,200,255,200), "edit_keybind_q_text": (255,255,255),
    "startup_gradient_base1": (20,20,40), "startup_gradient_base2": (20,20,40), "startup_gradient_base3": (40,20,60),
    "startup_enter_text_base": (200,200,255), "startup_star_color_base": (220, 220, 255), # For starfield
    "cursor_main": (255,255,255), "cursor_secondary": (100,100,255), "cursor_glow": (150,150,255),
    "waveform_color": (100, 100, 255, 150),
    "version_text_color": (200,200,200),
    "fps_text_color": (255,255,255),
    "menu_item_base_color_hover": 230, "menu_item_base_color_normal": 200,
    "menu_item_selected_glow_alpha": 50,
    "logo_glow_color": (255,255,255,50)
}

konami_colors = {
    "text_primary": (255, 105, 180), "text_secondary": (220, 90, 150), "text_highlight": (0, 255, 255),
    "text_shadow": (75, 0, 130), "text_button": (255, 255, 255),
    "bg_main_fill": (48, 25, 52), "bg_particle_base": (255,0,255),
    "button_normal_surf_bg": (75, 0, 130, 200), "button_normal_surf_border": (218, 112, 214, 255),
    "button_hover_surf_bg": (100, 0, 150, 230), "button_hover_surf_border": (255, 20, 147, 255),
    "slider_bg_surf": (75, 0, 130, 200), "slider_knob_surf": (0, 255, 255, 255),
    "tooltip_bg": (60, 30, 70, 200), "tooltip_border": (0, 255, 255, 200),
    "credits_bg_overlay_line_base": (30,0,40), "credits_header": (0,255,255), "credits_text": (255,105,180),
    "credits_member_bg": (138,43,226,30), "credits_member_border": (138,43,226,60),
    "credits_scrollbar_track": (138,43,226,50), "credits_scrollbar_thumb": (0,255,255,200),
    "credits_nav_text": (0, 255, 255),
    "edit_keybind_overlay": (0,0,0,230), "edit_keybind_box_bg": (60,30,70,240), "edit_keybind_box_border": (0,255,255,200),
    "edit_keybind_title": (255,105,180), "edit_keybind_instruction": (255,105,180), "edit_keybind_escape_base": (0,220,220),
    "edit_keybind_q_box": (138,43,226,150), "edit_keybind_q_border": (0,255,255,200), "edit_keybind_q_text": (255,255,255),
    "startup_gradient_base1": (48,25,52), "startup_gradient_base2": (75,0,130), "startup_gradient_base3": (25,25,112),
    "startup_enter_text_base": (0,255,255), "startup_star_color_base": (0, 255, 255), # For starfield
    "cursor_main": (255,105,180), "cursor_secondary": (0,255,255), "cursor_glow": (255,0,255),
    "waveform_color": (255, 0, 255, 150),
    "version_text_color": (220,90,150),
    "fps_text_color": (0,255,0),
    "menu_item_base_color_hover": 230, "menu_item_base_color_normal": 200,
    "menu_item_selected_glow_alpha": 70,
    "logo_glow_color": (0,255,255,70)
}
active_colors = default_colors

def get_color(key, default_value=(255,0,255)):
    return active_colors.get(key, default_value)

def toggle_konami_mode():
    global konami_mode_active, active_colors, text_cache, startup_background_stars
    konami_mode_active = not konami_mode_active
    active_colors = konami_colors if konami_mode_active else default_colors
    text_cache.clear()
    startup_background_stars.clear() # Clear stars to regenerate with new colors
    if hasattr(draw_credits_menu, 'initialized'):
        draw_credits_menu.initialized=False
    if button_normal_fallback:
        create_fallback_ui_elements()

# --- Beat and Pulse Simulation ---
current_beat_time = 0.0
BEAT_FREQUENCY = 1.0
global_pulse_factor = 0.0

# --- Asset Loading ---
def asset_path(relative_path):
    return os.path.join(*relative_path.split('/'))

try:
    menuBG_img = image.load(asset_path('assets/Images/menuBG.png')).convert_alpha()
    menuBG = transform.scale(menuBG_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
    BGrect = menuBG.get_rect(center=middleScreen)
except Exception as e:
    print(f"Error loading background: {e}")
    menuBG_img = None
    menuBG = Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    BGrect = menuBG.get_rect()

try:
    logoImg_orig = image.load(asset_path('assets/Images/logo.png')).convert_alpha()
    logoImg = transform.scale(logoImg_orig, (640, 600))
except Exception as e:
    print(f"Error loading logo image: {e}")
    logoImg_orig = None
    logoImg = None

button_normal_fallback = False
try:
    button_normal_img_orig = image.load(asset_path('assets/Images/button.png')).convert_alpha()
    button_hover_img_orig = image.load(asset_path('assets/Images/button_hover.png')).convert_alpha()
    slider_bg_img_orig = image.load(asset_path('assets/Images/slider_bg.png')).convert_alpha()
    slider_knob_img_orig = image.load(asset_path('assets/Images/slider_knob.png')).convert_alpha()

    button_normal = transform.scale(button_normal_img_orig, (400,100))
    button_hover = transform.scale(button_hover_img_orig, (400,100))
    slider_bg = transform.scale(slider_bg_img_orig, (300,30))
    slider_knob = transform.scale(slider_knob_img_orig, (40,40))
except Exception as e:
    print(f"Button/slider images not found, using fallback UI elements: {e}")
    button_normal_fallback = True
    button_normal, button_hover, slider_bg, slider_knob = None, None, None, None

def create_fallback_ui_elements():
    global button_normal, button_hover, slider_bg, slider_knob
    button_normal_surf = Surface((400, 100), SRCALPHA)
    draw.rect(button_normal_surf, get_color("button_normal_surf_bg"), (0,0,400,100), border_radius=20)
    draw.rect(button_normal_surf, get_color("button_normal_surf_border"), (0,0,400,100), width=3, border_radius=20)
    button_normal = button_normal_surf

    button_hover_surf = Surface((400, 100), SRCALPHA)
    draw.rect(button_hover_surf, get_color("button_hover_surf_bg"), (0,0,400,100), border_radius=20)
    draw.rect(button_hover_surf, get_color("button_hover_surf_border"), (0,0,400,100), width=3, border_radius=20)
    button_hover = button_hover_surf

    slider_bg_surf = Surface((300, 30), SRCALPHA)
    draw.rect(slider_bg_surf, get_color("slider_bg_surf"), (0,0,300,30), border_radius=15)
    slider_bg = slider_bg_surf

    slider_knob_surf = Surface((40, 40), SRCALPHA)
    draw.circle(slider_knob_surf, get_color("slider_knob_surf"), (20,20), 20)
    slider_knob = slider_knob_surf

if button_normal_fallback:
    create_fallback_ui_elements()

try:
    with open(asset_path('assets/NoteStyles.json')) as f:
        availableNoteStyles = json.load(f)['NoteStyles']
    with open(asset_path('assets/options.json')) as f:
        options = json.load(f)
except (FileNotFoundError, json.JSONDecodeError) as e:
    print(f"Error loading JSON assets: {e}")
    options = {
        'selectedSpeed': 1.0, 'playAs': 'Player', 'noDying': 'False',
        'downscroll': 'False', 'selectedNoteStyle': 0, 'render_scene': 'True',
        'modcharts': 'True',
        'keybinds': [K_a, K_s, K_w, K_d, K_LEFT, K_DOWN, K_UP, K_RIGHT]
    }
    availableNoteStyles = ["Default"]
    try:
        with open(asset_path('assets/options.json'), 'w') as f_out:
            json.dump(options, f_out, indent=4)
        print("Created default options.json.")
    except Exception as save_e:
        print(f"Could not save default options.json: {save_e}")

try:
    FONT_PATH = asset_path('assets/PhantomMuff.ttf')
    Font75 = font.Font(FONT_PATH, 75)
    Font100 = font.Font(FONT_PATH, 100)
    Font125 = font.Font(FONT_PATH, 125)
    Font30 = font.Font(FONT_PATH, 30)
except pygame.error as e:
    print(f"Error loading font '{FONT_PATH}': {e}. Using system default.")
    Font75 = font.SysFont(None, 75)
    Font100 = font.SysFont(None, 100)
    Font125 = font.SysFont(None, 125)
    Font30 = font.SysFont(None, 30)

FNFfont = Font100
FNFfont125 = Font125
text_cache = {}

def cached_text_render(font_obj, text, color, shadow=True, shadow_color=None, shadow_offset=3):
    if shadow_color is None:
        shadow_color = get_color("text_shadow")

    color_key = tuple(color) if isinstance(color, pygame.Color) else color
    shadow_color_key = tuple(shadow_color) if isinstance(shadow_color, pygame.Color) else shadow_color

    key = (id(font_obj), text, color_key, shadow, shadow_color_key, shadow_offset)
    if key in text_cache:
        return text_cache[key]

    actual_color = pygame.Color(*color) if not isinstance(color, pygame.Color) else color
    actual_shadow_color = pygame.Color(*shadow_color) if not isinstance(shadow_color, pygame.Color) else shadow_color

    if shadow:
        shadow_surface = font_obj.render(text, True, actual_shadow_color)
        text_surface = font_obj.render(text, True, actual_color)
        size = text_surface.get_size()
        composite_width = size[0] + abs(shadow_offset)
        composite_height = size[1] + abs(shadow_offset)
        composite = Surface((composite_width, composite_height), SRCALPHA)
        shadow_x = shadow_offset if shadow_offset >= 0 else 0
        shadow_y = shadow_offset if shadow_offset >= 0 else 0
        text_x = 0 if shadow_offset >= 0 else abs(shadow_offset)
        text_y = 0 if shadow_offset >= 0 else abs(shadow_offset)
        composite.blit(shadow_surface, (shadow_x, shadow_y))
        composite.blit(text_surface, (text_x, text_y))
        result = composite
    else:
        result = font_obj.render(text, True, actual_color)

    if len(text_cache) > 200:
        keys_to_delete = list(text_cache.keys())[:100]
        for k_del in keys_to_delete:
            del text_cache[k_del]
    text_cache[key] = result
    return result

musicList = []
music_dir_path = asset_path('assets/Music')
if os.path.isdir(music_dir_path):
    for folder_name in os.listdir(music_dir_path):
        if os.path.isdir(os.path.join(music_dir_path, folder_name)):
            musicList.append(folder_name)
if not musicList:
    print("Warning: No music found in assets/Music!")

def get_difficulties(song_name):
    difficulties = []
    song_folder_path = os.path.join(music_dir_path, song_name)
    if not os.path.isdir(song_folder_path):
        return difficulties
    try:
        has_specific_diffs = False
        chart_json_exists = False
        for file_name in os.listdir(song_folder_path):
            if not file_name.endswith('.json'): continue
            if file_name == 'songData.json': continue
            if file_name == 'chart.json':
                chart_json_exists = True
                continue
            if file_name.startswith(song_name + '-') and file_name.endswith('.json'):
                difficulty = file_name[len(song_name) + 1:-5]
                difficulties.append(difficulty)
                has_specific_diffs = True

        if not has_specific_diffs and chart_json_exists:
            return ['Normal']
    except Exception as e:
        print(f"Error getting difficulties for {song_name}: {e}")

    return sorted(difficulties) if difficulties else ([] if not chart_json_exists else ['Normal'])

selectedMusic = 0; selectedOption = 0; selectedMain = 0; selectedKeybind = 0; selectedDifficulty = 0
currentMenu = 'Startup'; previousMenu = 'Startup'
menuTransition = 0; transitionDirection = 1; TRANSITION_SPEED = 4.0
startupFade = 0; startupFadeSpeed = 1.5

selectedSpeed = float(options.get('selectedSpeed', 1.0))
playAs = str(options.get('playAs', 'Player'))
selectedNoteStyle = min(int(options.get('selectedNoteStyle', 0)), max(0, len(availableNoteStyles) - 1 if availableNoteStyles else 0))
noDeath = str(options.get('noDying', 'False')).lower() == 'true'
downscroll = str(options.get('downscroll', 'False')).lower() == 'true'
render_scene = str(options.get('render_scene', 'True')).lower() == 'true'
modcharts = str(options.get('modcharts', 'True')).lower() == 'true'
keybind_list_from_options = options.get('keybinds', [K_a, K_s, K_w, K_d, K_LEFT, K_DOWN, K_UP, K_RIGHT])
K_a, K_s, K_w, K_d, K_LEFT, K_DOWN, K_UP, K_RIGHT = keybind_list_from_options[:8]

try:
    menuMusic_file_path = asset_path('assets/menuMusic.ogg')
    menuMusic = mixer.Sound(menuMusic_file_path)
    menuMusic.set_volume(0.7)
    menuMusic.play(-1)
except Exception as e:
    print(f"Error loading menu music '{menuMusic_file_path}': {e}")
    menuMusic = None

preventDoubleEnter = False; waitingForKeyPress = False
last_click_time = 0; last_click_pos = -1
menuItems = []; cursorPos = list(middleScreen); targetCursorPos = list(middleScreen)
cursorPulse = 0; bgScroll = 0.0 # Changed to float for smoother scrolling

tooltip_texts = {
    'Speed': 'Adjust the scrolling speed of notes. Higher values make the game more challenging.',
    'Play as': 'Choose whether to play as the Player or the Opponent character.',
    'No Death': "When enabled, you won't lose even if you miss many notes.",
    'Note style': 'Change the visual appearance of notes in the game.',
    'Downscroll': 'When enabled, notes flow from top to bottom instead of bottom to top.',
    'Render Scene': 'Enable or disable background and characters. Turning off may improve performance.',
    'Modcharts': 'Enable or disable special note movement patterns in certain songs.',
    'Keybinds': 'Customize which keys are used to hit notes during gameplay.'
}

particles = []
class Particle:
    def __init__(self, x, y, is_beat_particle=False, beat_strength_modifier=1.0):
        self.x = x; self.y = y
        self.is_beat_particle = is_beat_particle
        self.beat_strength_modifier = beat_strength_modifier

        self.drift_x = random.uniform(-0.2, 0.2) 
        self.drift_y = random.uniform(0.05, 0.3) 

        if self.is_beat_particle:
            base_h, base_s, base_l, _ = pygame.Color(*get_color("waveform_color")).hsla
            final_l = min(100, base_l + random.uniform(10,30) + 15 * (self.beat_strength_modifier -1))
            final_s = min(100, base_s + random.uniform(10,30) + 10 * (self.beat_strength_modifier -1))
            final_alpha = random.randint(70, 120) * self.beat_strength_modifier
            final_alpha = min(255, int(final_alpha))

            self.color_start = pygame.Color(0,0,0,0)
            # Clamp HSLA values to valid ranges
            hue = int((base_h + random.uniform(-25, 25)) % 360)
            sat = int(max(0, min(100, final_s)))
            light = int(max(0, min(100, final_l)))
            alpha = int(max(0, min(100, final_alpha * 100 / 255)))  # pygame.Color.hsla alpha is 0-100
            self.color_start.hsla = (hue, sat, light, alpha)
            self.size = random.uniform(2.5, 6.0) * self.beat_strength_modifier
            self.life = random.uniform(0.4, 1.2) * (0.7 + 0.5 * self.beat_strength_modifier)
            angle = random.uniform(0, 2 * math.pi)
            speed_magnitude = random.uniform(0.5, 1.5) * self.beat_strength_modifier
            self.speed_x = math.cos(angle) * speed_magnitude
            self.speed_y = math.sin(angle) * speed_magnitude
        else:
            particle_base_rgb = get_color("bg_particle_base")
            r = random.randint(min(255, particle_base_rgb[0]), 255)
            g = random.randint(min(255, particle_base_rgb[1]), 255)
            b = random.randint(min(255, particle_base_rgb[2]), 255)
            a = random.randint(80, 180)
            self.color_start = pygame.Color(r, g, b, a)
            self.size = random.uniform(2, 5)
            self.life = random.uniform(1, 3)
            self.speed_x = random.uniform(-0.5, 0.5)
            self.speed_y = random.uniform(-0.5, 0.5)

        self.color = self.color_start
        self.initial_life = self.life; self.initial_size = self.size

    def update(self, dt):
        self.speed_x += self.drift_x * dt * 20 
        self.speed_y += self.drift_y * dt * 20

        self.x += self.speed_x * 60 * dt; self.y += self.speed_y * 60 * dt
        self.life -= dt
        life_ratio = max(0, self.life / self.initial_life)

        if self.is_beat_particle:
            self.size = self.initial_size * (life_ratio ** 0.7)
            current_alpha = int(self.color_start[3] * (life_ratio ** 1.5))
        else:
            self.size = self.initial_size * life_ratio
            current_alpha = int(self.color_start[3] * life_ratio**2)

        self.color = (self.color_start[0], self.color_start[1], self.color_start[2], max(0, current_alpha))
        return self.life > 0 and self.size > 0.5

    def draw(self, surface):
        if self.size < 1: return
        temp_surf = Surface((int(self.size * 2), int(self.size * 2)), SRCALPHA)
        draw.circle(temp_surf, self.color, (int(self.size), int(self.size)), int(self.size))
        surface.blit(temp_surf, (int(self.x - self.size), int(self.y - self.size)))

def ease_out_quad(t): return 1-(1-t)**2
def ease_in_out_quad(t): return 2*t*t if t < 0.5 else 1-(-2*t+2)**2/2
def ease_in_out_sine(t): return -(math.cos(math.pi*t)-1)/2
def ease_out_back(t): c1=1.70158; c3=c1+1; return 1+c3*(t-1)**3+c1*(t-1)**2

class MenuItem:
    def __init__(self, text, position, selected=False, font_normal=None, font_selected=None,
                 is_button=True, is_slider=False, slider_value=None, slider_min=0, slider_max=1, tooltip=None):
        self.text = text; self.position = list(position); self.target_position = list(position)
        self.selected = selected
        self.font_normal = font_normal or FNFfont; self.font_selected = font_selected or FNFfont125
        self.scale = 1.0; self.target_scale = 1.15 if selected else 1.0
        self.alpha = 255; self.target_alpha = 255
        self.hover = False; self.rect = None; self.button_rect = None
        self.rotation = 0; self.target_rotation = random.uniform(-2, 2) if selected else 0
        self.is_button = is_button; self.is_slider = is_slider
        self.slider_value = slider_value; self.slider_min = slider_min; self.slider_max = slider_max
        self.slider_rect = None
        self.hover_effect = 0.0; self.tooltip = tooltip; self.tooltip_alpha = 0
        self.item_pulse_angle = random.uniform(0, math.pi * 2)
        self.item_pulse_speed = random.uniform(1.5, 2.5)

    def update(self, dt, global_pulse):
        self.position[0]+=(self.target_position[0]-self.position[0])*ease_out_quad(min(1,12*dt))
        self.position[1]+=(self.target_position[1]-self.position[1])*ease_out_quad(min(1,12*dt))
        self.scale+=(self.target_scale-self.scale)*ease_out_quad(min(1,15*dt))
        self.alpha+=(self.target_alpha-self.alpha)*ease_out_quad(min(1,15*dt))
        self.rotation+=(self.target_rotation-self.rotation)*ease_out_quad(min(1,10*dt))
        if self.hover:
            self.hover_effect=min(1.,self.hover_effect+dt*5); self.tooltip_alpha=min(255,self.tooltip_alpha+dt*510)
        else:
            self.hover_effect=max(.0,self.hover_effect-dt*5); self.tooltip_alpha=max(0,self.tooltip_alpha-dt*510)
        self.item_pulse_angle=(self.item_pulse_angle+dt*self.item_pulse_speed)%(math.pi*2)
        self.combined_pulse_factor = (math.sin(self.item_pulse_angle) + 1) / 2
        self.effective_scale_pulse = 1.0 + 0.02 * self.combined_pulse_factor + 0.03 * global_pulse

    def draw(self, surface, global_pulse):
        text_color_tuple = get_color("text_button")
        item_glow_effect = 0.0 # Initialize

        if self.selected:
            item_glow_effect = 0.7 + 0.3 * math.sin(systime.time() * 4 + self.item_pulse_angle)
            h_sel, s_sel, l_sel, a_sel = pygame.Color(*get_color("text_highlight")).hsla
            lightness_pulse = (item_glow_effect - 1.0) * 30 
            l_sel_mod = l_sel + lightness_pulse
            l_sel_final = max(0, min(100, l_sel_mod))
            pulsing_highlight_color = pygame.Color(0,0,0,0)
            pulsing_highlight_color.hsla = (h_sel, s_sel, l_sel_final, a_sel)
            text_color_tuple = (pulsing_highlight_color.r, pulsing_highlight_color.g, pulsing_highlight_color.b)
        else:
            item_glow_effect = 0.2 + 0.1 * math.sin(systime.time() * 2 + self.item_pulse_angle) # For subtle pulse on non-selected
            h_text,s_text,l_text,a_text = pygame.Color(*get_color("text_primary")).hsla
            l_mod_text = l_text + self.hover_effect * 20 # Increased hover brightness effect
            
            final_text_color_obj = pygame.Color(0,0,0,0)
            final_text_color_obj.hsla = (h_text, s_text, min(100,l_mod_text), a_text)
            
            # Subtle pulse for non-selected text
            l_text_current = final_text_color_obj.hsla[2]
            subtle_pulse_amount = (item_glow_effect - 0.15) * 15 # item_glow_effect (0.1 to 0.3) -> pulse (-0.75 to 2.25)
            l_text_pulsed = min(100, max(0, l_text_current + subtle_pulse_amount))
            final_text_color_obj.hsla = (final_text_color_obj.hsla[0], final_text_color_obj.hsla[1], l_text_pulsed, final_text_color_obj.hsla[3])
            text_color_tuple = (final_text_color_obj.r, final_text_color_obj.g, final_text_color_obj.b)


        current_scale = self.scale * self.effective_scale_pulse

        if self.is_button:
            btn_img_to_use = button_hover if self.hover or self.selected else button_normal
            if btn_img_to_use is None: create_fallback_ui_elements(); btn_img_to_use = button_hover if self.hover or self.selected else button_normal
            scale_factor = current_scale + 0.1 * self.hover_effect + (0.05 if self.selected else 0)
            scaled_size = (max(1,int(btn_img_to_use.get_width() * scale_factor)), max(1,int(btn_img_to_use.get_height() * scale_factor)))
            scaled_btn = transform.scale(btn_img_to_use, scaled_size)
            btn_rect = scaled_btn.get_rect(center=self.position); self.button_rect = btn_rect
            final_btn_surf = scaled_btn
            if self.rotation!=0:
                final_btn_surf = transform.rotate(scaled_btn, self.rotation)
                btn_rect = final_btn_surf.get_rect(center=btn_rect.center)
            if self.selected: # Ensure item_glow_effect is from selected path
                glow_size_factor = 1.0 + 0.1 * (0.7 + 0.3 * math.sin(systime.time() * 4 + self.item_pulse_angle))
                glow_size = (max(1,int(scaled_btn.get_width()*glow_size_factor)), max(1,int(scaled_btn.get_height()*glow_size_factor)))
                if glow_size[0] > 0 and glow_size[1] > 0:
                    glow_btn_base = transform.scale(btn_img_to_use, glow_size)
                    glow_color_with_alpha = pygame.Color(*get_color("text_highlight")); glow_color_with_alpha.a = get_color("menu_item_selected_glow_alpha")
                    temp_glow_surf = Surface(glow_btn_base.get_size(), SRCALPHA); temp_glow_surf.fill(glow_color_with_alpha)
                    temp_glow_surf.blit(glow_btn_base, (0,0), special_flags=pygame.BLEND_RGBA_MULT)
                    surface.blit(temp_glow_surf, temp_glow_surf.get_rect(center=self.position))
            surface.blit(final_btn_surf,btn_rect); self.rect=btn_rect

        active_font = self.font_selected if self.selected else self.font_normal
        rendered_text = cached_text_render(active_font, self.text, text_color_tuple, shadow_color=get_color("text_shadow"))
        if current_scale != 1.:
            original_size = rendered_text.get_size()
            new_size = (max(1,int(original_size[0]*current_scale)), max(1,int(original_size[1]*current_scale)))
            if new_size[0] > 0 and new_size[1] > 0: rendered_text = transform.scale(rendered_text, new_size)
        if self.alpha<255: rendered_text.set_alpha(int(self.alpha))
        text_rect = rendered_text.get_rect()
        if self.is_button and self.button_rect: text_rect.center = self.button_rect.center
        else: text_rect.center=self.position
        if not self.is_button: self.rect=text_rect
        surface.blit(rendered_text,text_rect)

        if self.is_slider and self.slider_value is not None:
            slider_width=300
            base_y_offset = self.rect.height // 2 + 20 if self.rect else 20
            slider_actual_rect = Rect(0,0,slider_width, slider_bg.get_height() if slider_bg else 30)
            slider_actual_rect.midtop = (self.position[0], self.position[1] + base_y_offset)
            self.slider_rect = slider_actual_rect
            surface.blit(slider_bg if slider_bg else create_fallback_ui_elements() or slider_bg, slider_actual_rect)
            normalized_val = (self.slider_value-self.slider_min)/(self.slider_max-self.slider_min) if (self.slider_max-self.slider_min)!=0 else 0
            knob_x = slider_actual_rect.left + normalized_val * slider_width
            knob_to_draw = slider_knob if slider_knob else create_fallback_ui_elements() or slider_knob
            knob_rect = knob_to_draw.get_rect(center=(knob_x, slider_actual_rect.centery))
            if self.selected:
                knob_pulse_scale = 1.+.1*math.sin(systime.time()*6 + self.item_pulse_angle)
                scaled_knob_size = (max(1,int(knob_to_draw.get_width()*knob_pulse_scale)),max(1,int(knob_to_draw.get_height()*knob_pulse_scale)))
                if scaled_knob_size[0]>0 and scaled_knob_size[1]>0:
                    scaled_knob_img = transform.scale(knob_to_draw, scaled_knob_size)
                    knob_rect = scaled_knob_img.get_rect(center=(knob_x, slider_actual_rect.centery))
                    surface.blit(scaled_knob_img,knob_rect)
            else: surface.blit(knob_to_draw,knob_rect)
            value_text_rendered = cached_text_render(Font30, f"{self.slider_value:.1f}" if isinstance(self.slider_value,float) else str(self.slider_value), get_color("text_primary"), shadow=False)
            value_rect = value_text_rendered.get_rect(midtop=(slider_actual_rect.centerx, slider_actual_rect.bottom+5))
            surface.blit(value_text_rendered,value_rect)

        if self.hover and self.tooltip and self.tooltip_alpha > 10:
            tooltip_font_obj = Font30; padding = 15
            max_tooltip_width = min(500, SCREEN_WIDTH - 40)
            words = self.tooltip.split(' '); lines = []; current_line_text = ""
            for word in words:
                test_line = current_line_text + word + " "
                if tooltip_font_obj.size(test_line)[0] < max_tooltip_width - 2 * padding: current_line_text = test_line
                else: lines.append(current_line_text.strip()); current_line_text = word + " "
            if current_line_text: lines.append(current_line_text.strip())
            line_height = tooltip_font_obj.get_linesize(); tooltip_height = line_height * len(lines) + padding * 2
            actual_tooltip_width = 0
            for line_text_str in lines: actual_tooltip_width = max(actual_tooltip_width, tooltip_font_obj.size(line_text_str)[0])
            actual_tooltip_width = min(actual_tooltip_width + padding*2, max_tooltip_width)
            tooltip_bg_surf = Surface((actual_tooltip_width, tooltip_height), SRCALPHA)
            bg_color = get_color("tooltip_bg"); border_color = get_color("tooltip_border")
            final_bg_color = (*bg_color[:3], int(bg_color[3]*(self.tooltip_alpha/255)))
            final_border_color = (*border_color[:3], int(border_color[3]*(self.tooltip_alpha/255)))
            draw.rect(tooltip_bg_surf, final_bg_color, (0,0,actual_tooltip_width,tooltip_height), border_radius=10)
            draw.rect(tooltip_bg_surf, final_border_color, (0,0,actual_tooltip_width,tooltip_height), width=2, border_radius=10)
            text_render_color = get_color("text_primary")
            for i, line_text_str in enumerate(lines):
                line_surf = tooltip_font_obj.render(line_text_str, True, text_render_color)
                line_rect = line_surf.get_rect(centerx=actual_tooltip_width/2, top=padding + i * line_height)
                tooltip_bg_surf.blit(line_surf, line_rect)
            tooltip_x = self.position[0] - actual_tooltip_width // 2
            tooltip_y = self.position[1] - (self.rect.height if self.rect else 0) - tooltip_height - 20
            tooltip_x = max(10, min(tooltip_x, SCREEN_WIDTH - actual_tooltip_width - 10))
            if tooltip_y < 10: tooltip_y = (self.slider_rect.bottom if self.is_slider and self.slider_rect else (self.rect.bottom if self.rect else self.position[1])) + 20
            tooltip_y += 5 * math.sin(systime.time()*2)
            surface.blit(tooltip_bg_surf,(tooltip_x,tooltip_y))
        return self.rect

    def set_selected(self, selected_status):
        self.selected=selected_status; self.target_scale = 1.15 if self.selected else 1.
        self.target_rotation = random.uniform(-2,2) if self.selected else 0

    def update_slider_value(self, mouse_x_pos):
        if self.slider_rect:
            normalized_pos = max(0,min(1,(mouse_x_pos - self.slider_rect.left) / self.slider_rect.width))
            raw_value = self.slider_min + normalized_pos * (self.slider_max - self.slider_min)
            if "Speed" in self.text: self.slider_value = round(raw_value * 10)/10
            else: self.slider_value = round(raw_value)

def update_menu_items():
    global menuItems, selectedMain, selectedMusic, selectedOption, selectedKeybind, selectedDifficulty
    menuItems = []
    y_offset_base = 180
    main_font_normal=FNFfont; main_font_selected=FNFfont125
    options_font_normal=Font100; options_font_selected=Font125
    keybind_font_normal=Font75; keybind_font_selected=Font100

    if currentMenu == 'Startup': pass
    elif currentMenu == 'Main':
        tempText = ['Play','Options','Credits']
        for k, text in enumerate(tempText):
            item_y = middleScreen[1] + y_offset_base * (k - selectedMain)
            menuItems.append(MenuItem(text, (middleScreen[0], item_y), k == selectedMain, main_font_normal, main_font_selected))
    elif currentMenu == 'Select music':
        if not musicList: menuItems.append(MenuItem("No Music Found", middleScreen, True, main_font_normal, main_font_selected, is_button=False)); return
        for k, music_name in enumerate(musicList):
            item_y = middleScreen[1] + y_offset_base * (k - selectedMusic)
            menuItems.append(MenuItem(music_name, (middleScreen[0], item_y), k == selectedMusic, main_font_normal, main_font_selected))
    elif currentMenu == 'Select difficulty':
        current_song_name = musicList[selectedMusic] if musicList and 0 <= selectedMusic < len(musicList) else "Unknown Song"
        difficulties = get_difficulties(current_song_name)
        if not difficulties: menuItems.append(MenuItem("No Difficulties", middleScreen, True, main_font_normal, main_font_selected, is_button=False)); selectedDifficulty=0; return
        if not (0 <= selectedDifficulty < len(difficulties)): selectedDifficulty = 0
        for k, diff_name_raw in enumerate(difficulties):
            difficulty_display_name = diff_name_raw if diff_name_raw else "Normal"
            item_y = middleScreen[1] + y_offset_base * (k - selectedDifficulty)
            menuItems.append(MenuItem(difficulty_display_name, (middleScreen[0], item_y), k == selectedDifficulty, main_font_normal, main_font_selected))
    elif currentMenu == 'Options':
        option_items_config = [
            {"label": "Speed", "type": "slider", "value_var": "selectedSpeed", "min": 0.1, "max": 5.0, "tooltip_key": "Speed"},
            {"label": "Play as", "type": "toggle", "value_var": "playAs", "options": ["Player", "Opponent"], "tooltip_key": "Play as"},
            {"label": "No Death", "type": "toggle", "value_var": "noDeath", "options": [False, True], "tooltip_key": "No Death"},
            {"label": "Note style", "type": "slider", "value_var": "selectedNoteStyle", "min": 0, "max": max(0,len(availableNoteStyles)-1), "display_options": availableNoteStyles, "tooltip_key": "Note style"},
            {"label": "Downscroll", "type": "toggle", "value_var": "downscroll", "options": [False, True], "tooltip_key": "Downscroll"},
            {"label": "Render Scene", "type": "toggle", "value_var": "render_scene", "options": [False, True], "tooltip_key": "Render Scene"},
            {"label": "Modcharts", "type": "toggle", "value_var": "modcharts", "options": [False, True], "tooltip_key": "Modcharts"},
            {"label": "Keybinds", "type": "button", "action": "goto_keybinds", "tooltip_key": "Keybinds"}
        ]
        selectedOption = max(0, min(selectedOption, len(option_items_config) - 1))
        for i, config in enumerate(option_items_config):
            item_y = middleScreen[1] + 150 * (i - selectedOption)
            is_selected_item = (i == selectedOption)
            tooltip_text = tooltip_texts.get(config["tooltip_key"], None)
            current_value = globals().get(config.get("value_var"))
            item = None
            if config["type"] == "slider":
                display_text = f"{config['label']}: "
                if "display_options" in config and config["display_options"] and current_value is not None:
                    style_idx = int(current_value)
                    if not (0 <= style_idx < len(config["display_options"])): style_idx = 0
                    display_text += str(config["display_options"][style_idx])
                elif isinstance(current_value, float): display_text += f"{current_value:.1f}"
                else: display_text += str(current_value)
                item = MenuItem(display_text, (middleScreen[0],item_y), is_selected_item, options_font_normal, options_font_selected, is_slider=True, slider_value=current_value, slider_min=config["min"], slider_max=config["max"], tooltip=tooltip_text)
            elif config["type"] == "toggle":
                val_to_display = "On" if isinstance(current_value, bool) and current_value else ("Off" if isinstance(current_value, bool) else current_value)
                item = MenuItem(f"{config['label']}: {val_to_display}", (middleScreen[0],item_y), is_selected_item, options_font_normal, options_font_selected, tooltip=tooltip_text, is_button=False)
            elif config["type"] == "button":
                item = MenuItem(config["label"],(middleScreen[0],item_y),is_selected_item, options_font_normal, options_font_selected, tooltip=tooltip_text, is_button=True)
            if item: menuItems.append(item)
    elif currentMenu == 'Keybinds':
        key_names = [key.name(k).title() for k in [K_a,K_s,K_w,K_d,K_LEFT,K_DOWN,K_UP,K_RIGHT]]
        keybind_labels = [f"P1 Left: {key_names[0]}", f"P1 Down: {key_names[1]}", f"P1 Up: {key_names[2]}", f"P1 Right: {key_names[3]}", f"P2 Left: {key_names[4]}", f"P2 Down: {key_names[5]}", f"P2 Up: {key_names[6]}", f"P2 Right: {key_names[7]}", "Reset Keybinds"]
        keybind_tooltips_list = ['Key for Player 1 Left.','Key for Player 1 Down.','Key for Player 1 Up.','Key for Player 1 Right.','Key for Player 2 Left.','Key for Player 2 Down.','Key for Player 2 Up.','Key for Player 2 Right.','Reset all keybinds to default.']
        selectedKeybind = max(0, min(selectedKeybind, len(keybind_labels) - 1))
        for k, text in enumerate(keybind_labels):
            item_y = middleScreen[1] + 100 * (k - selectedKeybind)
            menuItems.append(MenuItem(text, (middleScreen[0], item_y), k == selectedKeybind, keybind_font_normal, keybind_font_selected, tooltip=keybind_tooltips_list[k], is_button=True))

credits_data=[{'header':"FUNKIN' TEAM",'description':'The people who worked on the original game!','members':[{'name':'ninjamuffin99','role':'Programmer'},{'name':'PhantomArcade','role':'Animator'},{'name':'evilsk8r','role':'Artist'},{'name':'Kawaisprite','role':'Composer'}]},{'header':'MORPHIC ENGINE TEAM','description':'The people who made the Morphic Engine (this) possible!','members':[{'name':'CodeSoft','role':'Original Developer'},{'name':'AI Assistant','role':'Enhancements & Refinements'}]}]
credits_max_scroll_steps = 0

def draw_credits_menu():
    global visible_top, visible_bottom, selectedOption, particles, credits_max_scroll_steps
    if not hasattr(draw_credits_menu, 'initialized') or not draw_credits_menu.initialized:
        draw_credits_menu.text_cache={}; draw_credits_menu.wrap_cache={}; draw_credits_menu.height_cache={}
        draw_credits_menu.total_height=None
        overlay=Surface((SCREEN_WIDTH,SCREEN_HEIGHT),SRCALPHA)
        base_line_color = get_color("credits_bg_overlay_line_base")
        for y_pos in range(0,SCREEN_HEIGHT,2):
            alpha = 150 - 50 * math.sin(y_pos/SCREEN_HEIGHT*math.pi + systime.time()*0.5)
            line_color_final = (base_line_color[0],base_line_color[1],base_line_color[2],int(alpha*0.5))
            overlay.fill(line_color_final,(0,y_pos,SCREEN_WIDTH,2))
        draw_credits_menu.background = overlay
        fade_mask_surf=Surface((SCREEN_WIDTH,SCREEN_HEIGHT),SRCALPHA)
        fade_mask_surf.fill((0,0,0,255),(0,0,SCREEN_WIDTH,90))
        for i in range(60): alpha_val=int(255*(1-i/60)); fade_mask_surf.fill((0,0,0,alpha_val),(0,90+i,SCREEN_WIDTH,1))
        for i in range(60): alpha_val=int(255*(i/60)); fade_mask_surf.fill((0,0,0,alpha_val),(0,SCREEN_HEIGHT-100+i,SCREEN_WIDTH,1))
        fade_mask_surf.fill((0,0,0,255),(0,SCREEN_HEIGHT-40,SCREEN_WIDTH,40)); draw_credits_menu.fade_mask=fade_mask_surf
        draw_credits_menu.initialized = True
    screen.blit(draw_credits_menu.background,(0,0))

    def render_credits_text(font,text_content,color): return cached_text_render(font,text_content,color,shadow=False)
    def wrap_credits_text(text_content,font,max_w):
        cache_key=(text_content,id(font),max_w,tuple(active_colors.items()))
        if cache_key in draw_credits_menu.wrap_cache: return draw_credits_menu.wrap_cache[cache_key]
        words=text_content.split(' '); wrapped_lines_list=[]; current_line_str=''
        for word_item in words:
            test_line_str = current_line_str + word_item + ' '
            if font.size(test_line_str)[0] <= max_w: current_line_str = test_line_str
            else: wrapped_lines_list.append(current_line_str.strip()); current_line_str = word_item + ' '
        if current_line_str: wrapped_lines_list.append(current_line_str.strip())
        draw_credits_menu.wrap_cache[cache_key]=wrapped_lines_list; return wrapped_lines_list
    def get_wrapped_height(text_content,font,max_w):
        cache_key=(text_content,id(font),max_w,tuple(active_colors.items()))
        if cache_key not in draw_credits_menu.height_cache:
            lines=wrap_credits_text(text_content,font,max_w)
            draw_credits_menu.height_cache[cache_key]=len(lines)*font.get_linesize()
        return draw_credits_menu.height_cache[cache_key]
    def draw_text_credits(text_content,font,color,pos,align='midtop',check_visibility=True):
        y_render_pos = pos[1]
        if check_visibility and (y_render_pos > SCREEN_HEIGHT + font.get_height() or y_render_pos < -font.get_height()): return Rect(pos[0],pos[1],0,font.get_height())
        rendered=render_credits_text(font,text_content,color); rect_val=rendered.get_rect(**{align:pos})
        screen.blit(rendered,rect_val); return rect_val

    content_margin_val=30; max_text_width_val=SCREEN_WIDTH-content_margin_val*2
    if draw_credits_menu.total_height is None:
        current_total_height=0
        for section_item in credits_data:
            current_total_height+=Font75.get_linesize()+15
            current_total_height+=get_wrapped_height(section_item['description'],Font30,max_text_width_val)+30
            for member_item in section_item['members']: current_total_height+=get_wrapped_height(member_item['name'],Font30,max_text_width_val)+get_wrapped_height(member_item['role'],Font30,max_text_width_val)+20
            current_total_height+=60
        draw_credits_menu.total_height=current_total_height

    content_render_height=SCREEN_HEIGHT-200; scroll_step_val=40
    max_scroll_pixels=max(0,draw_credits_menu.total_height-content_render_height+120)
    credits_max_scroll_steps = int(max_scroll_pixels/scroll_step_val) if scroll_step_val > 0 else 0
    selectedOption=max(0,min(selectedOption,credits_max_scroll_steps)); scroll_offset_val=selectedOption*scroll_step_val
    visible_top=20; visible_bottom=SCREEN_HEIGHT-20; current_y_pos=150-scroll_offset_val
    header_color=get_color("credits_header"); text_color=get_color("credits_text")
    member_name_color=get_color("text_primary"); member_role_color=get_color("text_secondary")
    member_box_bg=get_color("credits_member_bg"); member_box_border=get_color("credits_member_border")

    for section_item in credits_data:
        section_render_height = Font75.get_linesize()+15+get_wrapped_height(section_item['description'],Font30,max_text_width_val)+30
        for member_item in section_item['members']: section_render_height+=get_wrapped_height(member_item['name'],Font30,max_text_width_val)+get_wrapped_height(member_item['role'],Font30,max_text_width_val)+20
        section_render_height+=60
        if current_y_pos+section_render_height < visible_top or current_y_pos > visible_bottom: current_y_pos+=section_render_height; continue
        header_rect=draw_text_credits(section_item['header'],Font75,header_color,(middleScreen[0],current_y_pos)); current_y_pos+=header_rect.height+15
        wrapped_desc_lines=wrap_credits_text(section_item['description'],Font30,max_text_width_val)
        for line_str in wrapped_desc_lines: draw_text_credits(line_str,Font30,text_color,(middleScreen[0],current_y_pos)); current_y_pos+=Font30.get_linesize()
        current_y_pos+=30
        for member_item in section_item['members']:
            name_h=get_wrapped_height(member_item['name'],Font30,max_text_width_val); role_h=get_wrapped_height(member_item['role'],Font30,max_text_width_val)
            member_render_height=name_h+role_h+10
            if not (current_y_pos > visible_bottom or current_y_pos + member_render_height < visible_top):
                highlight_box_width=600; highlight_box_height=member_render_height+16
                highlight_rect_obj=Rect(middleScreen[0]-highlight_box_width//2,current_y_pos,highlight_box_width,highlight_box_height)
                highlight_surf=Surface((highlight_box_width,highlight_box_height),SRCALPHA)
                draw.rect(highlight_surf,member_box_bg,(0,0,highlight_box_width,highlight_box_height),border_radius=15)
                draw.rect(highlight_surf,member_box_border,(0,0,highlight_box_width,highlight_box_height),width=2,border_radius=15)
                screen.blit(highlight_surf,highlight_rect_obj)
                member_y_start=current_y_pos+8
                wrapped_name_lines=wrap_credits_text(member_item['name'],Font30,max_text_width_val-20)
                for line_str in wrapped_name_lines: draw_text_credits(line_str,Font30,member_name_color,(middleScreen[0],member_y_start)); member_y_start+=Font30.get_linesize()
                wrapped_role_lines=wrap_credits_text(member_item['role'],Font30,max_text_width_val-20)
                for line_str in wrapped_role_lines: draw_text_credits(line_str,Font30,member_role_color,(middleScreen[0],member_y_start+5)); member_y_start+=Font30.get_linesize()
            current_y_pos+=member_render_height+20
        current_y_pos+=60
    screen.blit(draw_credits_menu.fade_mask,(0,0))
    nav_text_color = get_color("credits_nav_text")
    if selectedOption > 0: draw_text_credits('▲ Scroll Up',Font30,nav_text_color,(middleScreen[0],20),check_visibility=False)
    if selectedOption < credits_max_scroll_steps: draw_text_credits('▼ Scroll Down',Font30,nav_text_color,(middleScreen[0],SCREEN_HEIGHT-20),align='midbottom',check_visibility=False)
    track_h=SCREEN_HEIGHT-120; track_surf_bar=Surface((10,track_h),SRCALPHA)
    draw.rect(track_surf_bar,get_color("credits_scrollbar_track"),(0,0,10,track_h),border_radius=5); screen.blit(track_surf_bar,(SCREEN_WIDTH-25,60))
    if draw_credits_menu.total_height > 0 and content_render_height > 0:
        content_ratio_val = min(1,content_render_height/draw_credits_menu.total_height)
        thumb_h = max(30,track_h*content_ratio_val)
        scroll_ratio_val = selectedOption/max(1,credits_max_scroll_steps)
        thumb_y_pos = scroll_ratio_val * (track_h-thumb_h)
        thumb_surf_bar=Surface((10,int(thumb_h)),SRCALPHA)
        draw.rect(thumb_surf_bar,get_color("credits_scrollbar_thumb"),(0,0,10,int(thumb_h)),border_radius=5); screen.blit(thumb_surf_bar,(SCREEN_WIDTH-25,60+thumb_y_pos))
    draw_text_credits('Press ESC to return',Font30,nav_text_color,(SCREEN_WIDTH-30,SCREEN_HEIGHT-25),align='bottomright',check_visibility=False)
    if random.random() < 0.05: particles.append(Particle(random.randint(0,SCREEN_WIDTH),random.randint(100,SCREEN_HEIGHT-100),is_beat_particle=True, beat_strength_modifier=1.0 + 0.5 * global_pulse_factor))

def saveOptions():
    global options,selectedSpeed,playAs,noDeath,downscroll,selectedNoteStyle,render_scene,modcharts,K_a,K_s,K_w,K_d,K_LEFT,K_DOWN,K_UP,K_RIGHT
    options['selectedSpeed']=selectedSpeed; options['playAs']=playAs
    options['noDying']='True' if noDeath else 'False'; options['downscroll']='True' if downscroll else 'False'
    options['selectedNoteStyle']=selectedNoteStyle; options['render_scene']='True' if render_scene else 'False'
    options['modcharts']='True' if modcharts else 'False'
    options['keybinds']=[K_a,K_s,K_w,K_d,K_LEFT,K_DOWN,K_UP,K_RIGHT]
    try:
        with open(asset_path('assets/options.json'),'w') as f: json.dump(options,f,indent=4)
    except Exception as e: print(f"Error saving options: {e}")

def change_menu(new_menu):
    global currentMenu,previousMenu,menuTransition,transitionDirection,startupFade,selectedDifficulty,selectedOption
    previousMenu=currentMenu; currentMenu=new_menu; menuTransition=0; transitionDirection=1
    if new_menu == 'Select difficulty':
        current_song_name=musicList[selectedMusic] if musicList and 0<=selectedMusic<len(musicList) else None
        if current_song_name:
            diffs=get_difficulties(current_song_name)
            if not(diffs and 0<=selectedDifficulty<len(diffs)): selectedDifficulty=0
        else: selectedDifficulty=0
    elif new_menu == 'Credits': selectedOption = 0
    if previousMenu=='Startup' and new_menu=='Main': startupFade=0
    generate_menu_transition_particles(); update_menu_items()

def generate_menu_transition_particles():
    global particles
    for _ in range(random.randint(40,70)): particles.append(Particle(random.randint(0,SCREEN_WIDTH),random.randint(0,SCREEN_HEIGHT),is_beat_particle=True, beat_strength_modifier=random.uniform(1.0, 1.8)))

waveform_points=[]; WAVEFORM_LENGTH=200; WAVEFORM_HEIGHT_MAX=50; waveform_phase=0.0
def update_waveform(dt, beat_pulse):
    global waveform_points, waveform_phase
    waveform_points = []
    waveform_phase += dt * 5.0
    base_y = SCREEN_HEIGHT - 40

    dynamic_height_factor = 0.5 + 0.7 * beat_pulse
    dynamic_complexity_factor = 0.8 + 0.4 * beat_pulse

    for i in range(WAVEFORM_LENGTH):
        x = (SCREEN_WIDTH / (WAVEFORM_LENGTH -1)) * i
        sine1 = math.sin(i * 0.1 * dynamic_complexity_factor + waveform_phase)
        sine2 = math.sin(i * 0.25 * dynamic_complexity_factor + waveform_phase * 0.5) * 0.5
        amplitude_modulation = (beat_pulse * 0.7 + 0.3)

        y_offset = (sine1 + sine2) * WAVEFORM_HEIGHT_MAX * amplitude_modulation * dynamic_height_factor
        waveform_points.append((x, base_y + y_offset))

def draw_waveform(surface):
    if len(waveform_points) > 1:
        wf_color = get_color("waveform_color")
        pygame.draw.lines(surface, wf_color, False, waveform_points, 3)
        if random.random() < 0.15 * global_pulse_factor:
            pt_idx = random.randint(0, len(waveform_points)-1)
            px, py = waveform_points[pt_idx]
            particles.append(Particle(px, py, is_beat_particle=True, beat_strength_modifier=1.0 + 1.5 * global_pulse_factor))

def draw_cursor():
    global cursorPos,targetCursorPos,cursorPulse,particles
    cursorPos[0]+=(targetCursorPos[0]-cursorPos[0])*ease_out_quad(min(1,.3))
    cursorPos[1]+=(targetCursorPos[1]-cursorPos[1])*ease_out_quad(min(1,.3))
    cursorPulse=(cursorPulse+.15)%(2*math.pi); pulse_scale=1.+.15*math.sin(cursorPulse)
    glow_base_color=get_color("cursor_glow"); glow_size_base=20*pulse_scale
    max_glow_diameter=int(glow_size_base*2*1.5); glow_surf=Surface((max_glow_diameter,max_glow_diameter),SRCALPHA)
    glow_center=max_glow_diameter//2
    for i in range(3):
        size=glow_size_base-i*3;
        if size<=0: continue
        alpha=int(glow_base_color[3]*((100-i*30)/100)) if len(glow_base_color)>3 else int(100-i*30)
        current_glow_color=(glow_base_color[0],glow_base_color[1],glow_base_color[2],max(0,min(255,alpha)))
        draw.circle(glow_surf,current_glow_color,(glow_center,glow_center),int(size))
    screen.blit(glow_surf,(cursorPos[0]-glow_center,cursorPos[1]-glow_center))
    main_dot_size=12*pulse_scale
    draw.circle(screen,get_color("cursor_main"),cursorPos,int(main_dot_size))
    draw.circle(screen,get_color("cursor_secondary"),cursorPos,int(main_dot_size-3))
    if random.random()<.15: particles.append(Particle(cursorPos[0],cursorPos[1])) # Default non-beat particle

def draw_edit_keybind_screen():
    overlay_surf=Surface((SCREEN_WIDTH,SCREEN_HEIGHT),SRCALPHA); overlay_surf.fill(get_color("edit_keybind_overlay"))
    screen.blit(overlay_surf,(0,0))
    box_width,box_height=800,450; box_rect=Rect(0,0,box_width,box_height); box_rect.center=middleScreen
    outline_pulse=.5+.5*math.sin(systime.time()*3+global_pulse_factor*math.pi)
    box_border_color=get_color("edit_keybind_box_border")
    for i in range(5):
        size_offset=i*4*outline_pulse; alpha=int(box_border_color[3]*((150-i*30)/150)) if len(box_border_color)>3 else int(150-i*30)
        alpha=max(0,min(255,alpha)); current_outline_color=(box_border_color[0],box_border_color[1],box_border_color[2],alpha)
        outline_rect=Rect(0,0,box_width+size_offset,box_height+size_offset); outline_rect.center=middleScreen
        draw.rect(screen,current_outline_color,outline_rect,border_radius=30)
    draw.rect(screen,get_color("edit_keybind_box_bg"),box_rect,border_radius=20)
    draw.rect(screen,box_border_color,box_rect,width=3,border_radius=20)
    title_text_color=get_color("edit_keybind_title"); instr_text_color=get_color("edit_keybind_instruction")
    escape_text_base_color=get_color("edit_keybind_escape_base")
    escape_pulse=.5+.5*math.sin(systime.time()*4+global_pulse_factor*math.pi)
    h,s,l,a_orig=pygame.Color(*escape_text_base_color).hsla; l_mod=l+escape_pulse*15
    pulsing_escape_color=pygame.Color(0,0,0); pulsing_escape_color.hsla=(h,s,min(100,max(0,l_mod)),a_orig)
    title_text=cached_text_render(Font100,'Edit Keybind',title_text_color); title_rect=title_text.get_rect(midtop=(middleScreen[0],box_rect.top+40)); screen.blit(title_text,title_rect)
    instr_text=cached_text_render(Font75,'Press a key to assign',instr_text_color); instr_rect=instr_text.get_rect(midtop=(middleScreen[0],title_rect.bottom+50)); screen.blit(instr_text,instr_rect)
    escape_text=cached_text_render(Font75,'(Escape to cancel)',pulsing_escape_color); escape_rect=escape_text.get_rect(midtop=(middleScreen[0],instr_rect.bottom+40)); screen.blit(escape_text,escape_rect)
    key_box_pulse=.5+.5*math.sin(systime.time()*2.5+global_pulse_factor*math.pi); key_box_size=100+20*key_box_pulse
    key_box_display=Rect(0,0,key_box_size,key_box_size); key_box_display.midbottom=(middleScreen[0],box_rect.bottom-40)
    draw.rect(screen,get_color("edit_keybind_q_box"),key_box_display,border_radius=15)
    draw.rect(screen,get_color("edit_keybind_q_border"),key_box_display,width=3,border_radius=15)
    q_text=cached_text_render(Font125,'?',get_color("edit_keybind_q_text")); q_rect=q_text.get_rect(center=key_box_display.center); screen.blit(q_text,q_rect)

startup_background_stars = []
MAX_STARTUP_STARS = 200
STAR_FALL_SPEED_BASE = 20 # Slightly increased base speed
STAR_FALL_SPEED_PULSE_AMP = 40

def manage_startup_stars(dt_arg, current_global_pulse):
    global startup_background_stars
    if len(startup_background_stars) < MAX_STARTUP_STARS and random.random() < 0.9: # Higher chance to spawn
        p_x = random.uniform(0, SCREEN_WIDTH)
        p_y = random.uniform(-60, -10) # Start further off-screen
        p_size = random.uniform(0.5, 1.5) + 2.0 * current_global_pulse # Pulse affects base size more
        p_alpha_base = random.randint(50, 120)
        p_alpha = p_alpha_base + 130 * current_global_pulse
        p_alpha = min(255, int(p_alpha))
        p_speed_y = (STAR_FALL_SPEED_BASE + random.uniform(0, STAR_FALL_SPEED_PULSE_AMP) * current_global_pulse) * (p_size / 1.5 + 0.5) # Speed also depends on size

        star_color_val = get_color("startup_star_color_base")
        h,s,l,a = pygame.Color(*star_color_val).hsla
        star_h = (h + random.uniform(-15,15)) % 360
        star_s = max(0, s - random.uniform(40,70))
        star_l = min(100, l + random.uniform(25,50))

        final_star_color_obj = pygame.Color(0,0,0)
        hlsa_alpha_value = (p_alpha / 255.0) * 100
        final_star_color_obj.hsla = (star_h, star_s, star_l, hlsa_alpha_value)

        startup_background_stars.append({'x': p_x, 'y': p_y, 'size': p_size, 'color': final_star_color_obj, 'speed_y': p_speed_y})

    new_stars_list = []
    for star in startup_background_stars:
        star['y'] += star['speed_y'] * dt_arg
        # Simple fade out or remove when off screen
        if star['y'] < SCREEN_HEIGHT + star['size'] and star['color'].a > 5 :
            new_stars_list.append(star)
            if star['size'] > 0.3:
                # Twinkle effect for stars
                twinkle_alpha_mod = 0.7 + 0.3 * math.sin(systime.time() * (3 + star['size']) + star['x'] * 0.05)
                final_alpha = int(star['color'].a * twinkle_alpha_mod)
                final_alpha = max(0, min(255, final_alpha))
                if final_alpha > 5: # Only draw if somewhat visible
                    draw_color = (star['color'].r, star['color'].g, star['color'].b, final_alpha)
                    pygame.draw.circle(screen, draw_color, (int(star['x']), int(star['y'])), int(star['size']))
    startup_background_stars = new_stars_list

def draw_startup_screen(dt_arg): # Accepts dt from main loop
    gradient_surf=Surface((SCREEN_WIDTH,SCREEN_HEIGHT)); time_factor=systime.time()
    gcol1_base=get_color("startup_gradient_base1"); gcol2_base=get_color("startup_gradient_base2"); gcol3_base=get_color("startup_gradient_base3")
    for y_pos in range(SCREEN_HEIGHT):
        ratio=y_pos/SCREEN_HEIGHT
        r=abs(math.sin(time_factor*.5+ratio*3+global_pulse_factor*math.pi)); g=abs(math.sin(time_factor*.7+ratio*2+global_pulse_factor*math.pi*.5)); b=abs(math.sin(time_factor*.3+ratio*4+global_pulse_factor*math.pi*1.5))
        final_r=int((gcol1_base[0]*r+gcol2_base[0]*(1-r)+gcol3_base[0]*global_pulse_factor)/(1+global_pulse_factor))
        final_g=int((gcol1_base[1]*g+gcol2_base[1]*(1-g)+gcol3_base[1]*global_pulse_factor)/(1+global_pulse_factor))
        final_b=int((gcol1_base[2]*b+gcol2_base[2]*(1-b)+gcol3_base[2]*global_pulse_factor)/(1+global_pulse_factor))
        line_color=(max(0,min(255,final_r)),max(0,min(255,final_g)),max(0,min(255,final_b)))
        pygame.draw.line(gradient_surf,line_color,(0,y_pos),(SCREEN_WIDTH,y_pos))
    screen.blit(gradient_surf,(0,0))

    manage_startup_stars(dt_arg, global_pulse_factor) # Draw stars

    is_beat_particle_chance = random.random() < .3
    if random.random()<.15: particles.append(Particle(random.randint(0,SCREEN_WIDTH),random.randint(0,SCREEN_HEIGHT),is_beat_particle=is_beat_particle_chance, beat_strength_modifier= (1.0 + 0.5 * global_pulse_factor) if is_beat_particle_chance else 1.0))

    if logoImg and logoImg_orig:
        logo_base_pulse=1.+.05*math.sin(time_factor*2); effective_logo_pulse=logo_base_pulse+.03*global_pulse_factor
        logo_width=int(logoImg.get_width()*effective_logo_pulse); logo_height=int(logoImg.get_height()*effective_logo_pulse)
        if logo_width>0 and logo_height>0:
            pulsed_logo=transform.scale(logoImg_orig,(logo_width,logo_height))
            alpha=int(255*min(1,systime.time()/1.2)); pulsed_logo.set_alpha(alpha)
            current_logo_rect=pulsed_logo.get_rect(center=(middleScreen[0],middleScreen[1]-100))
            if systime.time()>1.:
                glow_intensity=.5+.5*math.sin(time_factor*1.5+global_pulse_factor*math.pi); glow_size_factor=1.+.05*glow_intensity
                glow_size=(int(logo_width*glow_size_factor),int(logo_height*glow_size_factor))
                if glow_size[0]>0 and glow_size[1]>0:
                    glow_logo_base=transform.scale(logoImg_orig,glow_size)
                    logo_glow_color_tuple=get_color("logo_glow_color")
                    tinted_glow=glow_logo_base.copy(); tinted_glow.fill(logo_glow_color_tuple[:3]+(0,),special_flags=pygame.BLEND_RGBA_ADD) # Ensure ADD blend for brightness
                    final_glow_alpha = logo_glow_color_tuple[3] if len(logo_glow_color_tuple)>3 else 50
                    tinted_glow.set_alpha(int(final_glow_alpha * glow_intensity)) # Modulate glow alpha by intensity
                    screen.blit(tinted_glow,tinted_glow.get_rect(center=current_logo_rect.center))
            screen.blit(pulsed_logo,current_logo_rect)

    time_offset_text=time_factor*3; text_pulse=.5+.5*math.sin(time_offset_text+global_pulse_factor*math.pi)
    base_text_color_startup=get_color("startup_enter_text_base")
    h_s,s_s,l_s,a_s=pygame.Color(*base_text_color_startup).hsla; l_mod_s=l_s+text_pulse*20
    final_startup_text_color=pygame.Color(0,0,0); final_startup_text_color.hsla=(h_s,s_s,min(100,max(0,l_mod_s)),a_s)
    enter_text_rendered=cached_text_render(Font100,'Enter to start',final_startup_text_color)
    y_offset_text=math.sin(time_offset_text*.5+global_pulse_factor)*10
    enter_rect=enter_text_rendered.get_rect(center=(middleScreen[0],middleScreen[1]+200+y_offset_text)); screen.blit(enter_text_rendered,enter_rect)
    if random.random()<(0.02+0.05*global_pulse_factor):
        for _ in range(random.randint(5,15)): particles.append(Particle(enter_rect.centerx+random.uniform(-20,20),enter_rect.centery+random.uniform(-20,20),is_beat_particle=True, beat_strength_modifier=1.2 + 0.8 * global_pulse_factor))

update_menu_items()
clock=pygame.time.Clock(); run=True
fps_display_active=False; fps_font_obj=font.SysFont('Arial',24); fps_values_list=[]
dev_tools = DevTools() if DEV_TOOLS_ENABLED else None
try:
    while run:
        dt = min(0.05, clock.tick(0) / 1000.0);
        if dt == 0: dt = 1/60.0
        current_beat_time += dt * BEAT_FREQUENCY * math.pi * 2
        global_pulse_factor = (math.sin(current_beat_time) + 1) / 2.0

        if fps_display_active:
            fps=clock.get_fps(); fps_values_list.append(fps)
            if len(fps_values_list)>30: fps_values_list.pop(0)
        targetCursorPos = list(mouse.get_pos())

        for game_event in event.get():
            if DEV_TOOLS_ENABLED and dev_tools and dev_tools.handle_event(game_event): continue
            if game_event.type == QUIT: saveOptions(); run = False

            if game_event.type == MOUSEWHEEL:
                scroll_amount = game_event.y
                if currentMenu == 'Select music' and musicList:
                    if scroll_amount > 0 and selectedMusic > 0: selectedMusic -= 1
                    elif scroll_amount < 0 and selectedMusic < len(musicList) - 1: selectedMusic += 1
                    update_menu_items()
                elif currentMenu == 'Select difficulty':
                    current_song = musicList[selectedMusic] if musicList and 0 <= selectedMusic < len(musicList) else None
                    if current_song:
                        diffs = get_difficulties(current_song)
                        if diffs:
                            if scroll_amount > 0 and selectedDifficulty > 0: selectedDifficulty -= 1
                            elif scroll_amount < 0 and selectedDifficulty < len(diffs) - 1: selectedDifficulty += 1
                            update_menu_items()
                elif currentMenu == 'Credits':
                    if scroll_amount > 0: selectedOption = max(0, selectedOption - 1)
                    elif scroll_amount < 0: selectedOption = min(credits_max_scroll_steps, selectedOption + 1)

            if game_event.type == KEYDOWN:
                konami_input_buffer.append(game_event.key)
                if len(konami_input_buffer) > len(KONAMI_CODE_SEQUENCE): konami_input_buffer.pop(0)
                if konami_input_buffer == KONAMI_CODE_SEQUENCE:
                    toggle_konami_mode(); konami_input_buffer = []
                    for _ in range(100): particles.append(Particle(random.randint(0,SCREEN_WIDTH),random.randint(0,SCREEN_HEIGHT),True, beat_strength_modifier=random.uniform(1.5, 2.5)))

                if game_event.key == K_F12 and DEV_TOOLS_ENABLED and dev_tools: dev_tools.toggle(); continue
                if game_event.key == K_F3: fps_display_active = not fps_display_active
                if game_event.key == K_ESCAPE:
                    if currentMenu=='Edit keybind': currentMenu='Keybinds'; waitingForKeyPress=False; update_menu_items()
                    elif currentMenu in ['Main','Startup']: saveOptions(); run=False
                    elif currentMenu=='Keybinds': change_menu('Options')
                    elif currentMenu=='Credits': change_menu('Main')
                    else: change_menu('Main')
                elif game_event.key == K_RETURN and not preventDoubleEnter:
                    preventDoubleEnter = True
                    if currentMenu == 'Startup': change_menu('Main')
                    elif currentMenu == 'Main':
                        if selectedMain==0: change_menu('Select music')
                        elif selectedMain==1: change_menu('Options')
                        elif selectedMain==2: selectedOption=0; change_menu('Credits')
                    elif currentMenu == 'Select music':
                        if musicList and 0 <= selectedMusic < len(musicList):
                            difficulties = get_difficulties(musicList[selectedMusic])
                            if difficulties:
                                if len(difficulties) == 1:
                                    selectedDifficulty = 0; difficulty_to_play = difficulties[selectedDifficulty]
                                    if menuMusic: menuMusic.stop()
                                    restart_game=True; actual_diff_name = difficulty_to_play if difficulty_to_play is not None else "Normal"
                                    while restart_game: restart_game = MainMenu(musicList[selectedMusic], selectedSpeed, playAs, noDeath, availableNoteStyles[selectedNoteStyle], [K_a,K_s,K_w,K_d,K_LEFT,K_DOWN,K_UP,K_RIGHT], downscroll, render_scene, modcharts, actual_diff_name)
                                    if menuMusic: menuMusic.play(-1); change_menu('Select music')
                                else: selectedDifficulty = 0; change_menu('Select difficulty')
                            else: print(f"No difficulties for {musicList[selectedMusic]}")
                    elif currentMenu == 'Select difficulty':
                        current_song_name = musicList[selectedMusic] if musicList and 0<=selectedMusic<len(musicList) else None
                        if current_song_name:
                            difficulties = get_difficulties(current_song_name)
                            if difficulties and 0 <= selectedDifficulty < len(difficulties):
                                difficulty_to_play = difficulties[selectedDifficulty]
                                if menuMusic: menuMusic.stop()
                                restart_game=True; actual_diff_name = difficulty_to_play if difficulty_to_play is not None else "Normal"
                                while restart_game: restart_game = MainMenu(musicList[selectedMusic], selectedSpeed, playAs, noDeath, availableNoteStyles[selectedNoteStyle], [K_a,K_s,K_w,K_d,K_LEFT,K_DOWN,K_UP,K_RIGHT], downscroll, render_scene, modcharts, actual_diff_name)
                                if menuMusic: menuMusic.play(-1); change_menu('Select music')
                    elif currentMenu == 'Options':
                        if menuItems and 0 <= selectedOption < len(menuItems) and menuItems[selectedOption].text == "Keybinds":
                            change_menu('Keybinds')
                    elif currentMenu == 'Keybinds':
                        if menuItems and 0 <= selectedKeybind < len(menuItems):
                            if selectedKeybind < 8 : currentMenu = 'Edit keybind'; waitingForKeyPress = True
                            elif selectedKeybind == 8:
                                K_a,K_s,K_w,K_d=pygame.K_a,pygame.K_s,pygame.K_w,pygame.K_d; K_LEFT,K_DOWN,K_UP,K_RIGHT=pygame.K_LEFT,pygame.K_DOWN,pygame.K_UP,pygame.K_RIGHT
                                update_menu_items()
                elif currentMenu not in ['Edit keybind','Startup']:
                    num_items = len(menuItems) if menuItems else 0
                    if game_event.key==K_w or game_event.key==K_UP:
                        if currentMenu=='Main' and selectedMain>0: selectedMain-=1
                        elif currentMenu=='Credits': selectedOption=max(0,selectedOption-1)
                        elif currentMenu=='Select music' and musicList and selectedMusic>0: selectedMusic-=1
                        elif currentMenu=='Select difficulty':
                            current_song=musicList[selectedMusic] if musicList and 0<=selectedMusic<len(musicList) else None
                            if current_song and get_difficulties(current_song) and selectedDifficulty > 0: selectedDifficulty -=1
                        elif currentMenu=='Options' and selectedOption>0: selectedOption-=1
                        elif currentMenu=='Keybinds' and selectedKeybind>0: selectedKeybind-=1
                        update_menu_items()
                    elif game_event.key==K_s or game_event.key==K_DOWN:
                        if currentMenu=='Main' and selectedMain<num_items-1: selectedMain+=1
                        elif currentMenu=='Credits': selectedOption=min(credits_max_scroll_steps, selectedOption+1)
                        elif currentMenu=='Select music' and musicList and selectedMusic<len(musicList)-1: selectedMusic+=1
                        elif currentMenu=='Select difficulty':
                            current_song=musicList[selectedMusic] if musicList and 0<=selectedMusic<len(musicList) else None
                            if current_song:
                                diffs = get_difficulties(current_song)
                                if diffs and selectedDifficulty < len(diffs)-1: selectedDifficulty +=1
                        elif currentMenu=='Options' and selectedOption<num_items-1: selectedOption+=1
                        elif currentMenu=='Keybinds' and selectedKeybind<num_items-1: selectedKeybind+=1
                        update_menu_items()
                    elif currentMenu=='Options' and menuItems and 0<=selectedOption<len(menuItems):
                        selected_item_obj = menuItems[selectedOption]
                        is_left=game_event.key==K_a or game_event.key==K_LEFT; is_right=game_event.key==K_d or game_event.key==K_RIGHT
                        if selected_item_obj.is_slider:
                            current_val=selected_item_obj.slider_value; step=0.1 if "Speed" in selected_item_obj.text else 1
                            new_val = max(selected_item_obj.slider_min, current_val-step) if is_left else (min(selected_item_obj.slider_max, current_val+step) if is_right else current_val)
                            if "Speed" in selected_item_obj.text: new_val=round(new_val*10)/10
                            else: new_val=round(new_val)
                            selected_item_obj.slider_value=new_val
                            if selected_item_obj.text.startswith("Speed:"): selectedSpeed=new_val
                            elif selected_item_obj.text.startswith("Note style:"): selectedNoteStyle=int(new_val)
                            update_menu_items()
                        elif not selected_item_obj.is_button and (is_left or is_right):
                            if "Play as:" in selected_item_obj.text: playAs='Opponent' if playAs=='Player' else 'Player'
                            elif "No Death:" in selected_item_obj.text: noDeath=not noDeath
                            elif "Downscroll:" in selected_item_obj.text: downscroll=not downscroll
                            elif "Render Scene:" in selected_item_obj.text: render_scene=not render_scene
                            elif "Modcharts:" in selected_item_obj.text: modcharts=not modcharts
                            update_menu_items()
                elif currentMenu=='Edit keybind' and waitingForKeyPress:
                    excluded_keys=[K_ESCAPE,K_RETURN,K_BACKSPACE,K_SPACE,KMOD_SHIFT,KMOD_CTRL,KMOD_ALT,KMOD_CAPS,pygame.K_LSHIFT,pygame.K_RSHIFT,pygame.K_LCTRL,pygame.K_RCTRL,pygame.K_LALT,pygame.K_RALT]
                    if game_event.key not in excluded_keys:
                        keybind_vars=['K_a','K_s','K_w','K_d','K_LEFT','K_DOWN','K_UP','K_RIGHT']
                        if 0<=selectedKeybind<len(keybind_vars): globals()[keybind_vars[selectedKeybind]]=game_event.key
                        currentMenu='Keybinds'; waitingForKeyPress=False; update_menu_items()

            if game_event.type == MOUSEBUTTONDOWN and game_event.button == 1:
                click_time = pygame.time.get_ticks()
                if currentMenu == 'Startup': change_menu('Main'); continue
                if currentMenu == 'Options':
                    slider_clicked = False
                    for i, item_obj in enumerate(menuItems):
                        if item_obj.is_slider and item_obj.slider_rect and item_obj.slider_rect.collidepoint(mouse.get_pos()):
                            item_obj.update_slider_value(mouse.get_pos()[0])
                            if item_obj.text.startswith("Speed:"): selectedSpeed = item_obj.slider_value
                            elif item_obj.text.startswith("Note style:"): selectedNoteStyle = int(item_obj.slider_value)
                            update_menu_items(); slider_clicked = True; break
                    if slider_clicked: continue

                for i, item_obj in enumerate(menuItems):
                    if item_obj.rect and item_obj.rect.collidepoint(mouse.get_pos()):
                        for _ in range(random.randint(10,20)): particles.append(Particle(mouse.get_pos()[0],mouse.get_pos()[1],True, beat_strength_modifier=random.uniform(1.0, 1.5)))
                        is_double_click = (click_time - last_click_time < 500 and last_click_pos == i)
                        last_click_time = click_time; last_click_pos = i

                        if currentMenu == 'Main':
                            selectedMain=i
                            if i==0: change_menu('Select music')
                            elif i==1: change_menu('Options')
                            elif i==2: selectedOption=0; change_menu('Credits')
                        elif currentMenu == 'Select music':
                            selectedMusic=i; update_menu_items()
                            if is_double_click and musicList and 0 <= selectedMusic < len(musicList):
                                difficulties = get_difficulties(musicList[selectedMusic])
                                if difficulties:
                                    if len(difficulties) == 1:
                                        selectedDifficulty=0; difficulty_to_play = difficulties[selectedDifficulty]
                                        if menuMusic: menuMusic.stop(); restart_game=True; actual_diff_name = difficulty_to_play if difficulty_to_play is not None else "Normal"
                                        while restart_game: restart_game = MainMenu(musicList[selectedMusic],selectedSpeed,playAs,noDeath,availableNoteStyles[selectedNoteStyle],[K_a,K_s,K_w,K_d,K_LEFT,K_DOWN,K_UP,K_RIGHT],downscroll,render_scene,modcharts,actual_diff_name)
                                        if menuMusic: menuMusic.play(-1); change_menu('Select music')
                                    else: selectedDifficulty=0; change_menu('Select difficulty')
                        elif currentMenu == 'Options':
                            selectedOption = i; update_menu_items()
                            option_configs_list = [
                                {"label": "Speed", "type": "slider", "value_var": "selectedSpeed"},
                                {"label": "Play as", "type": "toggle", "value_var": "playAs"},
                                {"label": "No Death", "type": "toggle", "value_var": "noDeath"},
                                {"label": "Note style", "type": "slider", "value_var": "selectedNoteStyle"},
                                {"label": "Downscroll", "type": "toggle", "value_var": "downscroll"},
                                {"label": "Render Scene", "type": "toggle", "value_var": "render_scene"},
                                {"label": "Modcharts", "type": "toggle", "value_var": "modcharts"},
                                {"label": "Keybinds", "type": "button", "action": "goto_keybinds"}
                            ]
                            if 0 <= i < len(option_configs_list):
                                config = option_configs_list[i]
                                if config["type"] == "button" and config.get("action") == "goto_keybinds": change_menu('Keybinds')
                                elif config["type"] == "toggle":
                                    var_name = config["value_var"]
                                    current_val = globals()[var_name]
                                    if isinstance(current_val, bool): globals()[var_name] = not current_val
                                    elif var_name == "playAs": globals()[var_name] = "Opponent" if current_val == "Player" else "Player"
                                    update_menu_items()
                        elif currentMenu == 'Keybinds':
                            selectedKeybind=i; update_menu_items()
                            if is_double_click:
                                if i < 8: currentMenu='Edit keybind'; waitingForKeyPress=True
                                elif i == 8: K_a,K_s,K_w,K_d=pygame.K_a,pygame.K_s,pygame.K_w,pygame.K_d; K_LEFT,K_DOWN,K_UP,K_RIGHT=pygame.K_LEFT,pygame.K_DOWN,pygame.K_UP,pygame.K_RIGHT; update_menu_items()
                        elif currentMenu == 'Select difficulty':
                            selectedDifficulty=i; update_menu_items()
                            if is_double_click:
                                current_song_name = musicList[selectedMusic] if musicList and 0<=selectedMusic<len(musicList) else None
                                if current_song_name:
                                    difficulties = get_difficulties(current_song_name)
                                    if difficulties and 0 <= selectedDifficulty < len(difficulties):
                                        difficulty_to_play = difficulties[selectedDifficulty]
                                        if menuMusic: menuMusic.stop(); restart_game=True; actual_diff_name = difficulty_to_play if difficulty_to_play is not None else "Normal"
                                        while restart_game: restart_game = MainMenu(musicList[selectedMusic],selectedSpeed,playAs,noDeath,availableNoteStyles[selectedNoteStyle],[K_a,K_s,K_w,K_d,K_LEFT,K_DOWN,K_UP,K_RIGHT],downscroll,render_scene,modcharts,actual_diff_name)
                                        if menuMusic: menuMusic.play(-1); change_menu('Select music')
                        break
            if pygame.mouse.get_pressed()[0] and currentMenu == 'Options':
                for i, item_obj in enumerate(menuItems):
                    if item_obj.is_slider and item_obj.slider_rect and item_obj.slider_rect.collidepoint(mouse.get_pos()):
                        if item_obj.selected:
                            item_obj.update_slider_value(mouse.get_pos()[0])
                            if item_obj.text.startswith("Speed:"): selectedSpeed = item_obj.slider_value
                            elif item_obj.text.startswith("Note style:"): selectedNoteStyle = int(item_obj.slider_value)
                            update_menu_items()

        if preventDoubleEnter and not pygame.key.get_pressed()[K_RETURN]: preventDoubleEnter = False
        particles = [p for p in particles if p.update(dt)]
        for item_obj in menuItems:
            item_obj.update(dt, global_pulse_factor)
            item_obj.hover = (item_obj.rect and item_obj.rect.collidepoint(mouse.get_pos())) or \
                            (item_obj.is_slider and item_obj.slider_rect and item_obj.slider_rect.collidepoint(mouse.get_pos()))

        if transitionDirection > 0: menuTransition = min(1, menuTransition + dt * TRANSITION_SPEED)
        else: menuTransition = max(0, menuTransition - dt * TRANSITION_SPEED)
        if currentMenu=='Main' and previousMenu=='Startup': startupFade = min(1, startupFade + dt * startupFadeSpeed)
        if DEV_TOOLS_ENABLED and dev_tools: dev_tools.update(dt, sys.modules[__name__])

        # --- Drawing ---
        if menuBG_img is None: menuBG.fill(get_color("bg_main_fill"))
        screen.blit(menuBG, BGrect)

        if menuBG_img is None:
            overlay_alpha = 30 + 20 * global_pulse_factor; pulsing_overlay = Surface((SCREEN_WIDTH, SCREEN_HEIGHT), SRCALPHA)
            pulse_color_base = get_color("waveform_color")
            pulsing_overlay.fill((pulse_color_base[0],pulse_color_base[1],pulse_color_base[2],int(overlay_alpha)))
            screen.blit(pulsing_overlay,(0,0))
        else: # BG scroll if image exists
            bgScroll = (bgScroll + dt * 2.0 * (0.2 + 0.8 * global_pulse_factor)) % menuBG.get_width()
            screen.blit(menuBG, (bgScroll - menuBG.get_width(), 0))
            screen.blit(menuBG, (bgScroll, 0))

        for p_obj in particles: p_obj.draw(screen)

        if currentMenu == 'Startup': draw_startup_screen(dt) # Pass dt for star updates
        elif currentMenu == 'Credits': draw_credits_menu()
        else:
            for item_obj in menuItems: item_obj.draw(screen, global_pulse_factor)
        if currentMenu == 'Edit keybind': draw_edit_keybind_screen()

        update_waveform(dt, global_pulse_factor); draw_waveform(screen)

        version_text_color_tuple = get_color("version_text_color")
        version_text_surf = cached_text_render(Font30, f"Version {VERSION}", version_text_color_tuple, shadow=False)
        screen.blit(version_text_surf, version_text_surf.get_rect(bottomright=(SCREEN_WIDTH-10, SCREEN_HEIGHT-10)))
        engine_text_surf = cached_text_render(Font30, 'Morphic Engine', version_text_color_tuple, shadow=False)
        screen.blit(engine_text_surf, engine_text_surf.get_rect(bottomright=(SCREEN_WIDTH-10, SCREEN_HEIGHT-40)))

        if fps_display_active and fps_values_list:
            avg_fps = sum(fps_values_list)/len(fps_values_list)
            fps_text_surf = fps_font_obj.render(f"FPS: {avg_fps:.1f}", True, get_color("fps_text_color"))
            screen.blit(fps_text_surf,(10,10))

        draw_cursor(); pygame.mouse.set_visible(False)
        if DEV_TOOLS_ENABLED and dev_tools: dev_tools.draw(screen)
        display.flip()

except Exception as e:
    # Log the error to console for debugging
    print("--- Unhandled Exception Caught in MainMenu ---", file=sys.stderr)
    tb_str = traceback.format_exc()
    print(tb_str, file=sys.stderr)
    print("---------------------------------------------", file=sys.stderr)

    # Attempt to show the graphical exception screen
    try:
        # Import here to avoid issues if ExceptionHandler itself has an import error at startup
        from ErrorScreen import show_exception_screen as display_game_exception
        
        # Ensure all game sounds are stopped
        if 'menuMusic' in globals() and menuMusic and hasattr(menuMusic, 'stop'):
            menuMusic.stop()
        if pygame.mixer.get_init():
            pygame.mixer.music.stop() 
            pygame.mixer.stop() # Stops all channel sounds

        current_screen_surface = pygame.display.get_surface()
        if current_screen_surface: # Check if a display surface exists
            # Pass the pygame module itself and the clock instance
            display_game_exception(current_screen_surface, e, tb_str, VERSION, pygame, clock)
        else:
            # Fallback if no screen is available (e.g., error during pygame.init)
            print("Pygame display not available for graphical error report.", file=sys.stderr)

    except Exception as handler_e:
        # If the exception handler itself fails, print that error too
        print("--- CRITICAL: Exception Handler Failed ---", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr) # Print the handler's own traceback
        print("-----------------------------------------", file=sys.stderr)
    
    # Ensure the main loop flag is set to false so the game attempts a clean exit via finally
    run = False 
finally:
    saveOptions()
    pygame.quit()
    sys.exit()
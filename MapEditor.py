import pygame
import json
import os

# --- Configuration ---
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

# Colors
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_LIGHT_GREY = (200, 200, 200)
COLOR_GREY = (100, 100, 100)
COLOR_DARK_GREY = (50, 50, 50)
COLOR_GREEN = (0, 255, 0)
COLOR_BLUE = (0, 0, 255)
COLOR_RED = (255, 0, 0)
COLOR_YELLOW = (255, 255, 0)

# Editor constants
TAB_HEIGHT = 40
CHART_GRID_COLS = 4  # Lanes per player/opponent
CHART_CELL_WIDTH = 40
CHART_CELL_HEIGHT = 20
STEPS_PER_BEAT = 4
BEATS_PER_MEASURE = 4
STEPS_PER_MEASURE = STEPS_PER_BEAT * BEATS_PER_MEASURE
VISIBLE_MEASURES = 4

# --- Helper Functions ---
def draw_text(surface, text, position, font, color=COLOR_WHITE, center=False):
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    if center:
        text_rect.center = position
    else:
        text_rect.topleft = position
    surface.blit(text_surface, text_rect)
    return text_rect

# --- Editor Data ---
class EditorData:
    def __init__(self, song_name="new_song"):
        self.song_name = song_name
        self.active_tab = "Chart" # Chart, Scene, Export

        # Chart Data
        self.bpm = 128.0
        self.current_measure = 0
        self.notes = []  # List of dicts: {"measure", "step", "lane", "type": "player"/"opponent", "duration_steps": 0}

        # Scene Data
        self.player_char_name = "bf"
        self.opponent_char_name = "dad"
        self.player_pos = [SCREEN_WIDTH * 0.75, SCREEN_HEIGHT * 0.6]
        self.opponent_pos = [SCREEN_WIDTH * 0.25, SCREEN_HEIGHT * 0.6]
        self.stage_name = "stage" # Default stage

        # Export Data / Chart Metadata
        self.use_vocals = True

    def add_note(self, measure, step, lane, note_type):
        # Prevent duplicate notes
        for note in self.notes:
            if note["measure"] == measure and note["step"] == step and \
               note["lane"] == lane and note["type"] == note_type:
                return
        self.notes.append({"measure": measure, "step": step, "lane": lane, "type": note_type, "duration_steps": 0})
        self.notes.sort(key=lambda n: (n["measure"], n["step"]))

    def remove_note(self, measure, step, lane, note_type):
        self.notes = [n for n in self.notes if not (n["measure"] == measure and n["step"] == step and \
                                                    n["lane"] == lane and n["type"] == note_type)]

    def get_notes_in_measure_range(self, start_measure, num_measures):
        return [n for n in self.notes if start_measure <= n["measure"] < start_measure + num_measures]

    def export_data(self, music_folder_path="assets/Music"):
        song_path = os.path.join(music_folder_path, self.song_name)
        os.makedirs(song_path, exist_ok=True)

        # 1. Create songData.json
        song_data_content = {
            "stage": self.stage_name,
            "character1": { # Opponent (left in game)
                "Name": self.opponent_char_name,
                "size": [[1.0, 1.0]] * 5, # Default size
                "pos": [int(self.opponent_pos[0]), int(self.opponent_pos[1])], # Placeholder, game adjusts
                "isCentered": ["False", "False"],
                "centeredOffset": [0, 0]
            },
            "character2": { # Player (right in game)
                "Name": self.player_char_name,
                "size": [[1.0, 1.0]] * 5, # Default size
                "pos": [int(self.player_pos[0]), int(self.player_pos[1])], # Placeholder
                "isCentered": ["False", "False"],
                "centeredOffset": [0, 0]
            },
            "modifications": []
        }
        song_data_filepath = os.path.join(song_path, "songData.json")
        with open(song_data_filepath, "w") as f:
            json.dump(song_data_content, f, indent=2)
        print(f"Exported {song_data_filepath}")

        # 2. Create chart.json (e.g., chart-hard.json or just chart.json)
        # This requires converting editor notes to Psych Engine format
        psych_engine_sections = []
        # Group notes by measure and type (player/opponent)
        # For simplicity, each measure could be a section, or group consecutive same-type measures
        
        # Simplified: Assume one section per measure for now
        # A more robust implementation would group consecutive player/opponent measures
        max_measure = 0
        if self.notes:
            max_measure = max(n["measure"] for n in self.notes)

        for m in range(max_measure + 1):
            player_notes_in_measure = []
            opponent_notes_in_measure = []

            for note in self.notes:
                if note["measure"] == m:
                    timestamp_ms = (note["measure"] * STEPS_PER_MEASURE + note["step"]) * (60000.0 / self.bpm / STEPS_PER_BEAT)
                    sustain_ms = note["duration_steps"] * (60000.0 / self.bpm / STEPS_PER_BEAT)
                    psych_note = [round(timestamp_ms), note["lane"], round(sustain_ms)]
                    if note["type"] == "player":
                        player_notes_in_measure.append(psych_note)
                    else: # opponent
                        opponent_notes_in_measure.append(psych_note)
            
            if player_notes_in_measure:
                psych_engine_sections.append({
                    "mustHitSection": True,
                    "sectionNotes": player_notes_in_measure,
                    "lengthInSteps": STEPS_PER_MEASURE,
                    "altAnim": False,
                    "typeOfSection": 0
                })
            if opponent_notes_in_measure:
                 psych_engine_sections.append({
                    "mustHitSection": False, # Psych engine swaps lanes if this is false
                    "sectionNotes": opponent_notes_in_measure,
                    "lengthInSteps": STEPS_PER_MEASURE,
                    "altAnim": False,
                    "typeOfSection": 0
                })


        chart_content = {
            "song": {
                "song": self.song_name,
                "player1": self.player_char_name,
                "player2": self.opponent_char_name,
                "gfVersion": "gf", # Default
                "bpm": self.bpm,
                "needsVoices": self.use_vocals,
                "speed": 1.0, # Default chart scroll speed
                "notes": psych_engine_sections,
                "events": [],
                "validScore": True
            }
        }
        chart_filepath = os.path.join(song_path, f"{self.song_name.lower().replace(' ','-')}.json") # Or just chart.json
        with open(chart_filepath, "w") as f:
            json.dump(chart_content, f, indent=2)
        print(f"Exported {chart_filepath}")


# --- UI Components ---
class Button:
    def __init__(self, rect, text, font, action=None, color=COLOR_GREY, hover_color=COLOR_LIGHT_GREY, text_color=COLOR_WHITE):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.action = action
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.is_hovered = False

    def handle_event(self, event, editor_data):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.is_hovered and self.action:
                self.action(editor_data)
                return True
        return False

    def draw(self, surface):
        current_color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, current_color, self.rect)
        draw_text(surface, self.text, self.rect.center, self.font, self.text_color, center=True)

class Checkbox:
    def __init__(self, rect, label, font, checked=False, action=None):
        self.rect = pygame.Rect(rect) # Rect for the box itself
        self.label = label
        self.font = font
        self.checked = checked
        self.action = action # Action to call with new checked state
        self.label_rect = None

    def handle_event(self, event, editor_data):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.collidepoint(event.pos):
                self.checked = not self.checked
                if self.action:
                    self.action(editor_data, self.checked)
                return True
        return False

    def draw(self, surface):
        pygame.draw.rect(surface, COLOR_WHITE, self.rect, 2) # Box outline
        if self.checked:
            pygame.draw.line(surface, COLOR_GREEN, (self.rect.left + 3, self.rect.centery), (self.rect.centerx -2, self.rect.bottom - 3), 2)
            pygame.draw.line(surface, COLOR_GREEN, (self.rect.centerx -2, self.rect.bottom - 3), (self.rect.right - 3, self.rect.top + 3), 2)
        
        self.label_rect = draw_text(surface, self.label, (self.rect.right + 10, self.rect.top), self.font, COLOR_WHITE)


class TextInput:
    def __init__(self, rect, font, initial_text="", max_len=30, data_target_func=None, is_numeric=False):
        self.rect = pygame.Rect(rect)
        self.font = font
        self.text = str(initial_text)
        self.max_len = max_len
        self.active = False
        self.data_target_func = data_target_func # func(editor_data, new_text)
        self.is_numeric = is_numeric

    def handle_event(self, event, editor_data):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                self.active = False
                if self.data_target_func: self.data_target_func(editor_data, self.text)
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                char = event.unicode
                if self.is_numeric and not (char.isdigit() or (char == '.' and '.' not in self.text)):
                    return False # Don't add non-numeric
                if len(self.text) < self.max_len and char.isprintable(): # Ensure char is printable
                    self.text += char
            return True
        return False

    def draw(self, surface):
        pygame.draw.rect(surface, COLOR_LIGHT_GREY if self.active else COLOR_GREY, self.rect)
        draw_text(surface, self.text, (self.rect.x + 5, self.rect.y + 5), self.font, COLOR_BLACK)


# --- Main Editor Class ---
class MapEditor:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Morphic Map Editor")
        self.clock = pygame.time.Clock()
        self.font_small = pygame.font.Font(None, 24)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_large = pygame.font.Font(None, 48)

        self.data = EditorData("TestSong") # Default song name

        self.buttons = []
        self.checkboxes = []
        self.text_inputs = []
        self._setup_ui()

        self.running = True

    def _setup_ui(self):
        # Tabs
        tabs = ["Chart", "Scene", "Export"]
        tab_width = SCREEN_WIDTH // len(tabs)
        for i, tab_name in enumerate(tabs):
            rect = (i * tab_width, 0, tab_width, TAB_HEIGHT)
            self.buttons.append(Button(rect, tab_name, self.font_medium, action=lambda data, tn=tab_name: self._set_active_tab(data, tn)))
        
        # Export Tab UI (example)
        y_offset = TAB_HEIGHT + 20
        self.text_inputs.append(TextInput((150, y_offset, 200, 30), self.font_medium, str(self.data.bpm), 
                                          data_target_func=lambda d,t: setattr(d, 'bpm', float(t) if t else 0.0), is_numeric=True))
        y_offset += 40
        self.text_inputs.append(TextInput((150, y_offset, 200, 30), self.font_medium, self.data.player_char_name, 
                                          data_target_func=lambda d,t: setattr(d, 'player_char_name', t)))
        y_offset += 40
        self.text_inputs.append(TextInput((150, y_offset, 200, 30), self.font_medium, self.data.opponent_char_name, 
                                          data_target_func=lambda d,t: setattr(d, 'opponent_char_name', t)))
        y_offset += 40
        self.checkboxes.append(Checkbox((150, y_offset, 20, 20), "Use Vocals", self.font_medium, self.data.use_vocals,
                                        action=lambda d,c: setattr(d, 'use_vocals', c)))
        y_offset += 50
        self.buttons.append(Button((20, y_offset, 200, 40), "Export JSON", self.font_medium, 
                                   action=lambda d: d.export_data()))


    def _set_active_tab(self, editor_data, tab_name):
        editor_data.active_tab = tab_name
        # Potentially refresh UI elements based on tab

    def _handle_chart_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos
            # Check clicks on Player grid
            player_grid_rect = pygame.Rect(50, TAB_HEIGHT + 50, CHART_GRID_COLS * CHART_CELL_WIDTH, VISIBLE_MEASURES * STEPS_PER_MEASURE * CHART_CELL_HEIGHT)
            # Check clicks on Opponent grid
            opponent_grid_rect = pygame.Rect(player_grid_rect.right + 50, TAB_HEIGHT + 50, CHART_GRID_COLS * CHART_CELL_WIDTH, VISIBLE_MEASURES * STEPS_PER_MEASURE * CHART_CELL_HEIGHT)

            if player_grid_rect.collidepoint(mouse_x, mouse_y):
                col = (mouse_x - player_grid_rect.left) // CHART_CELL_WIDTH
                row_abs = (mouse_y - player_grid_rect.top) // CHART_CELL_HEIGHT # Absolute row in visible grid
                measure_offset = row_abs // STEPS_PER_MEASURE
                step_in_measure = row_abs % STEPS_PER_MEASURE
                actual_measure = self.data.current_measure + measure_offset
                
                if 0 <= col < CHART_GRID_COLS:
                    if event.button == 1: # Left click to add
                        self.data.add_note(actual_measure, step_in_measure, col, "player")
                    elif event.button == 3: # Right click to remove
                        self.data.remove_note(actual_measure, step_in_measure, col, "player")

            elif opponent_grid_rect.collidepoint(mouse_x, mouse_y):
                col = (mouse_x - opponent_grid_rect.left) // CHART_CELL_WIDTH
                row_abs = (mouse_y - opponent_grid_rect.top) // CHART_CELL_HEIGHT
                measure_offset = row_abs // STEPS_PER_MEASURE
                step_in_measure = row_abs % STEPS_PER_MEASURE
                actual_measure = self.data.current_measure + measure_offset

                if 0 <= col < CHART_GRID_COLS:
                    if event.button == 1:
                        self.data.add_note(actual_measure, step_in_measure, col, "opponent")
                    elif event.button == 3:
                        self.data.remove_note(actual_measure, step_in_measure, col, "opponent")
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_PAGEUP:
                self.data.current_measure = max(0, self.data.current_measure - VISIBLE_MEASURES)
            if event.key == pygame.K_PAGEDOWN:
                self.data.current_measure += VISIBLE_MEASURES
        
        if event.type == pygame.MOUSEWHEEL: # Scroll measures
            self.data.current_measure = max(0, self.data.current_measure - event.y)


    def _handle_scene_input(self, event):
        # Placeholder for scene interaction (e.g., dragging characters)
        pass

    def _handle_export_input(self, event):
        for btn in self.buttons: # Only handle export-specific buttons if needed, or all general buttons
            if btn.action and "export_data" in str(btn.action): # Crude check
                 if btn.handle_event(event, self.data): return
        for cb in self.checkboxes:
            if cb.handle_event(event, self.data): return
        for ti in self.text_inputs:
            if ti.handle_event(event, self.data): return


    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                
                # Global UI event handling (like tabs)
                for btn in self.buttons:
                    if "set_active_tab" in str(btn.action): # Handle tab buttons first
                        if btn.handle_event(event, self.data): break 
                else: # If no tab button was clicked, pass to tab-specific handlers
                    if self.data.active_tab == "Chart":
                        self._handle_chart_input(event)
                    elif self.data.active_tab == "Scene":
                        self._handle_scene_input(event)
                    elif self.data.active_tab == "Export":
                        self._handle_export_input(event) # Handles its own buttons/inputs

            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()

    def update(self):
        # Update logic if any (e.g., animations, timed events)
        pass

    def _draw_chart_tab(self):
        draw_text(self.screen, "Chart Editor", (SCREEN_WIDTH // 2, TAB_HEIGHT + 20), self.font_medium, center=True)
        
        # Grid parameters
        grid_start_y = TAB_HEIGHT + 50
        player_grid_start_x = 50
        opponent_grid_start_x = player_grid_start_x + CHART_GRID_COLS * CHART_CELL_WIDTH + 50

        # Labels
        draw_text(self.screen, "Player", (player_grid_start_x, grid_start_y - 25), self.font_small)
        draw_text(self.screen, "Opponent", (opponent_grid_start_x, grid_start_y - 25), self.font_small)
        draw_text(self.screen, f"Measure: {self.data.current_measure + 1} / BPM: {self.data.bpm}", (20, SCREEN_HEIGHT - 30), self.font_small)


        # Draw Player Grid
        for m_offset in range(VISIBLE_MEASURES):
            actual_measure = self.data.current_measure + m_offset
            for step in range(STEPS_PER_MEASURE):
                row_y = grid_start_y + (m_offset * STEPS_PER_MEASURE + step) * CHART_CELL_HEIGHT
                # Measure line
                if step == 0:
                    pygame.draw.line(self.screen, COLOR_WHITE, (player_grid_start_x, row_y), (player_grid_start_x + CHART_GRID_COLS * CHART_CELL_WIDTH, row_y), 2 if m_offset > 0 else 3)
                # Beat line
                elif step % STEPS_PER_BEAT == 0:
                     pygame.draw.line(self.screen, COLOR_GREY, (player_grid_start_x, row_y), (player_grid_start_x + CHART_GRID_COLS * CHART_CELL_WIDTH, row_y), 1)
                
                for col in range(CHART_GRID_COLS):
                    cell_rect = pygame.Rect(player_grid_start_x + col * CHART_CELL_WIDTH, row_y, CHART_CELL_WIDTH, CHART_CELL_HEIGHT)
                    pygame.draw.rect(self.screen, COLOR_DARK_GREY, cell_rect, 1) # Cell border
        
        # Draw Opponent Grid (similar to player)
        for m_offset in range(VISIBLE_MEASURES):
            actual_measure = self.data.current_measure + m_offset
            for step in range(STEPS_PER_MEASURE):
                row_y = grid_start_y + (m_offset * STEPS_PER_MEASURE + step) * CHART_CELL_HEIGHT
                if step == 0:
                    pygame.draw.line(self.screen, COLOR_WHITE, (opponent_grid_start_x, row_y), (opponent_grid_start_x + CHART_GRID_COLS * CHART_CELL_WIDTH, row_y), 2 if m_offset > 0 else 3)
                elif step % STEPS_PER_BEAT == 0:
                     pygame.draw.line(self.screen, COLOR_GREY, (opponent_grid_start_x, row_y), (opponent_grid_start_x + CHART_GRID_COLS * CHART_CELL_WIDTH, row_y), 1)

                for col in range(CHART_GRID_COLS):
                    cell_rect = pygame.Rect(opponent_grid_start_x + col * CHART_CELL_WIDTH, row_y, CHART_CELL_WIDTH, CHART_CELL_HEIGHT)
                    pygame.draw.rect(self.screen, COLOR_DARK_GREY, cell_rect, 1)

        # Draw Notes
        visible_notes = self.data.get_notes_in_measure_range(self.data.current_measure, VISIBLE_MEASURES)
        for note in visible_notes:
            m_offset = note["measure"] - self.data.current_measure
            note_y = grid_start_y + (m_offset * STEPS_PER_MEASURE + note["step"]) * CHART_CELL_HEIGHT
            note_x_base = player_grid_start_x if note["type"] == "player" else opponent_grid_start_x
            note_x = note_x_base + note["lane"] * CHART_CELL_WIDTH
            
            note_color = COLOR_GREEN if note["type"] == "player" else COLOR_RED
            note_rect = pygame.Rect(note_x + 2, note_y + 2, CHART_CELL_WIDTH - 4, CHART_CELL_HEIGHT - 4)
            pygame.draw.rect(self.screen, note_color, note_rect)


    def _draw_scene_tab(self):
        draw_text(self.screen, "Scene Editor", (SCREEN_WIDTH // 2, TAB_HEIGHT + 20), self.font_medium, center=True)
        # Placeholder character representations
        pygame.draw.rect(self.screen, COLOR_BLUE, (self.data.opponent_pos[0]-25, self.data.opponent_pos[1]-50, 50, 100))
        draw_text(self.screen, self.data.opponent_char_name, (self.data.opponent_pos[0], self.data.opponent_pos[1]+60), self.font_small, center=True)
        
        pygame.draw.rect(self.screen, COLOR_YELLOW, (self.data.player_pos[0]-25, self.data.player_pos[1]-50, 50, 100))
        draw_text(self.screen, self.data.player_char_name, (self.data.player_pos[0], self.data.player_pos[1]+60), self.font_small, center=True)
        draw_text(self.screen, "Drag functionality not implemented in skeleton.", (20, SCREEN_HEIGHT - 30), self.font_small)


    def _draw_export_tab(self):
        draw_text(self.screen, "Export Settings", (SCREEN_WIDTH // 2, TAB_HEIGHT + 20), self.font_medium, center=True)
        
        y_offset = TAB_HEIGHT + 20
        draw_text(self.screen, "BPM:", (20, y_offset + 5), self.font_medium)
        y_offset += 40
        draw_text(self.screen, "Player Char:", (20, y_offset + 5), self.font_medium)
        y_offset += 40
        draw_text(self.screen, "Opponent Char:", (20, y_offset + 5), self.font_medium)
        y_offset += 40
        # Checkbox label is drawn by the checkbox itself
        
        # Draw text inputs and checkboxes (they draw themselves if visible)
        for ti in self.text_inputs:
            ti.draw(self.screen)
        for cb in self.checkboxes:
            cb.draw(self.screen)
        
        # Draw export button (already in self.buttons, drawn globally)


    def draw(self):
        self.screen.fill(COLOR_BLACK)

        # Draw active tab content
        if self.data.active_tab == "Chart":
            self._draw_chart_tab()
        elif self.data.active_tab == "Scene":
            self._draw_scene_tab()
        elif self.data.active_tab == "Export":
            self._draw_export_tab()
        
        # Draw UI elements (Tabs, specific buttons for export tab)
        for btn in self.buttons:
            # Only draw tab buttons globally, or export buttons if on export tab
            is_tab_button = "set_active_tab" in str(btn.action)
            is_export_button = "export_data" in str(btn.action)

            if is_tab_button:
                 # Highlight active tab
                if self.data.active_tab in btn.text:
                    original_color = btn.color
                    btn.color = COLOR_DARK_GREY 
                    btn.draw(self.screen)
                    btn.color = original_color
                else:
                    btn.draw(self.screen)
            elif self.data.active_tab == "Export" and is_export_button:
                btn.draw(self.screen)


        pygame.display.flip()

if __name__ == "__main__":
    editor = MapEditor()
    editor.run()
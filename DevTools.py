import pygame
import sys
import time
import psutil
import gc
import traceback
from collections import deque
import inspect

class DevTools:
    def __init__(self, game_instance=None):
        self.visible = False
        self.game_instance = game_instance
        self.process = psutil.Process()
        
        # Display properties
        self.screen_width = pygame.display.Info().current_w
        self.screen_height = pygame.display.Info().current_h
        
        # Window properties
        self.width = int(self.screen_width * 0.8)
        self.height = int(self.screen_height * 0.7)
        self.x = (self.screen_width - self.width) // 2
        self.y = (self.screen_height - self.height) // 2
        self.window_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
        # Header height
        self.header_height = 40
        
        # Content area
        self.content_rect = pygame.Rect(
            self.x, 
            self.y + self.header_height, 
            self.width, 
            self.height - self.header_height
        )
        
        # Tabs
        self.tabs = ["Performance", "Objects", "Console", "Input", "Scene"]
        self.active_tab = 0
        self.tab_width = self.width // len(self.tabs)
        
        # Colors
        self.colors = {
            "bg": (30, 30, 40, 220),
            "header": (40, 40, 60, 230),
            "tab": (50, 50, 70, 255),
            "tab_active": (70, 70, 100, 255),
            "text": (220, 220, 220),
            "highlight": (100, 150, 250),
            "graph_bg": (40, 40, 60),
            "fps_graph": (100, 200, 100),
            "memory_graph": (200, 100, 100),
            "border": (100, 100, 150)
        }
        
        # Fonts
        self.fonts = {
            "header": pygame.font.Font(None, 32),
            "tab": pygame.font.Font(None, 28),
            "regular": pygame.font.Font(None, 24),
            "small": pygame.font.Font(None, 20),
            "monospace": pygame.font.Font(None, 22)
        }
        
        # Dragging state
        self.dragging = False
        self.drag_offset = (0, 0)
        
        # Performance tracking
        self.fps_values = deque(maxlen=120)  # 2 seconds at 60fps
        self.memory_values = deque(maxlen=120)
        self.last_time = time.time()
        self.frame_times = deque(maxlen=60)
        
        # Console
        self.console_lines = deque(maxlen=200)
        self.console_input = ""
        self.console_cursor_visible = True
        self.console_cursor_timer = 0
        self.console_history = deque(maxlen=50)
        self.console_history_index = -1
        self.console_scroll = 0
        self.console_log("DevTools initialized")
        
        # Input tracking
        self.key_states = {}
        self.mouse_pos = (0, 0)
        self.mouse_buttons = [False, False, False]
        self.key_history = deque(maxlen=10)
        
        # Object browser
        self.object_categories = {}
        self.object_scroll = 0
        self.selected_object = None
        self.expanded_categories = set()
        
        # Resizing flags
        self.resizing = False
        self.resize_edge = None
        self.resize_min_size = (400, 300)

    def toggle(self):
        self.visible = not self.visible
        if self.visible:
            self.console_log("DevTools opened")
        
    def console_log(self, message, level="INFO"):
        timestamp = time.strftime("%H:%M:%S")
        self.console_lines.append(f"[{timestamp}] [{level}] {message}")
        self.console_scroll = max(0, len(self.console_lines) - self.get_visible_console_lines())
    
    def handle_event(self, event):
        if not self.visible:
            return False
            
        # Handle window dragging
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            
            # Check if click is in header area (for dragging)
            header_rect = pygame.Rect(self.x, self.y, self.width, self.header_height)
            if header_rect.collidepoint(mouse_pos):
                # Check if clicking on tabs
                tab_x = self.x
                for i, tab in enumerate(self.tabs):
                    tab_rect = pygame.Rect(tab_x, self.y, self.tab_width, self.header_height)
                    if tab_rect.collidepoint(mouse_pos):
                        self.active_tab = i
                        return True
                    tab_x += self.tab_width
                
                # Start dragging if not on tabs
                self.dragging = True
                self.drag_offset = (mouse_pos[0] - self.x, mouse_pos[1] - self.y)
                return True
            
            # Check if click is in content area
            elif self.content_rect.collidepoint(mouse_pos):
                return self.handle_content_click(mouse_pos, event)
            
            # Check for resize handles
            elif self.is_on_resize_edge(mouse_pos):
                self.resizing = True
                self.resize_edge = self.get_resize_edge(mouse_pos)
                return True
                
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging or self.resizing:
                self.dragging = False
                self.resizing = False
                return True
                
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                mouse_pos = pygame.mouse.get_pos()
                new_x = mouse_pos[0] - self.drag_offset[0]
                new_y = mouse_pos[1] - self.drag_offset[1]
                
                # Keep window within screen bounds
                new_x = max(0, min(new_x, self.screen_width - self.width))
                new_y = max(0, min(new_y, self.screen_height - self.height))
                
                self.x, self.y = new_x, new_y
                self.update_rects()
                return True
            
            elif self.resizing:
                self.handle_resize(pygame.mouse.get_pos())
                return True
                
        elif event.type == pygame.MOUSEWHEEL:
            # Handle scrolling in content area
            if self.content_rect.collidepoint(pygame.mouse.get_pos()):
                if self.active_tab == 2:  # Console tab
                    self.console_scroll = max(0, min(
                        len(self.console_lines) - self.get_visible_console_lines(),
                        self.console_scroll - event.y * 3
                    ))
                    return True
                elif self.active_tab == 1:  # Objects tab
                    self.object_scroll = max(0, self.object_scroll - event.y * 3)
                    return True
                
        elif event.type == pygame.KEYDOWN:
            # Handle console input when console tab is active
            if self.active_tab == 2:
                if event.key == pygame.K_RETURN:
                    if self.console_input:
                        self.execute_console_command(self.console_input)
                        self.console_history.appendleft(self.console_input)
                        self.console_input = ""
                        self.console_history_index = -1
                    return True
                elif event.key == pygame.K_BACKSPACE:
                    self.console_input = self.console_input[:-1]
                    return True
                elif event.key == pygame.K_UP:
                    if self.console_history and self.console_history_index < len(self.console_history) - 1:
                        self.console_history_index += 1
                        self.console_input = self.console_history[self.console_history_index]
                    return True
                elif event.key == pygame.K_DOWN:
                    if self.console_history_index > 0:
                        self.console_history_index -= 1
                        self.console_input = self.console_history[self.console_history_index]
                    elif self.console_history_index == 0:
                        self.console_history_index = -1
                        self.console_input = ""
                    return True
                elif event.unicode and ord(event.unicode) >= 32:
                    self.console_input += event.unicode
                    return True
                    
        return self.window_rect.collidepoint(pygame.mouse.get_pos())

    def handle_content_click(self, pos, event):
        if self.active_tab == 1:  # Objects tab
            # Handle clicking on object categories
            return True
        return True

    def update_rects(self):
        self.window_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.content_rect = pygame.Rect(
            self.x, 
            self.y + self.header_height, 
            self.width, 
            self.height - self.header_height
        )
        self.tab_width = self.width // len(self.tabs)

    def is_on_resize_edge(self, pos):
        edge_size = 10
        if not self.window_rect.collidepoint(pos):
            return False
            
        on_right = abs(pos[0] - (self.x + self.width)) < edge_size
        on_bottom = abs(pos[1] - (self.y + self.height)) < edge_size
        on_left = abs(pos[0] - self.x) < edge_size
        on_top = abs(pos[1] - self.y) < edge_size
        
        return on_right or on_bottom or on_left or on_top

    def get_resize_edge(self, pos):
        edge_size = 10
        result = []
        
        if abs(pos[0] - (self.x + self.width)) < edge_size:
            result.append("right")
        if abs(pos[1] - (self.y + self.height)) < edge_size:
            result.append("bottom")
        if abs(pos[0] - self.x) < edge_size:
            result.append("left")
        if abs(pos[1] - self.y) < edge_size:
            result.append("top")
            
        return result

    def handle_resize(self, pos):
        if "right" in self.resize_edge:
            new_width = max(self.resize_min_size[0], pos[0] - self.x)
            self.width = new_width
        
        if "bottom" in self.resize_edge:
            new_height = max(self.resize_min_size[1], pos[1] - self.y)
            self.height = new_height
            
        if "left" in self.resize_edge:
            new_x = min(pos[0], self.x + self.width - self.resize_min_size[0])
            new_width = self.x + self.width - new_x
            self.x = new_x
            self.width = new_width
            
        if "top" in self.resize_edge:
            new_y = min(pos[1], self.y + self.height - self.resize_min_size[1])
            new_height = self.y + self.height - new_y
            self.y = new_y
            self.height = new_height
            
        self.update_rects()

    def update(self, dt, game_instance=None):
        if not self.visible:
            return
            
        if game_instance:
            self.game_instance = game_instance
            
        # Update performance metrics
        current_time = time.time()
        frame_time = current_time - self.last_time
        self.last_time = current_time
        
        self.frame_times.append(frame_time)
        if self.frame_times:
            avg_frame_time = sum(self.frame_times) / len(self.frame_times)
            if avg_frame_time > 0:
                fps = 1.0 / avg_frame_time
                self.fps_values.append(fps)
        
        # Update memory usage
        memory_mb = self.process.memory_info().rss / (1024 * 1024)
        self.memory_values.append(memory_mb)
        
        # Update console cursor blink
        self.console_cursor_timer += dt
        if self.console_cursor_timer >= 0.5:
            self.console_cursor_visible = not self.console_cursor_visible
            self.console_cursor_timer = 0
            
        # Update input tracking
        self.mouse_pos = pygame.mouse.get_pos()
        self.mouse_buttons = pygame.mouse.get_pressed(3)
        
        for key, pressed in enumerate(pygame.key.get_pressed()):
            if pressed and key not in self.key_states:
                self.key_states[key] = time.time()
                self.key_history.appendleft((key, pygame.key.name(key), "down"))
            elif not pressed and key in self.key_states:
                held_time = time.time() - self.key_states[key]
                self.key_history.appendleft((key, pygame.key.name(key), f"up ({held_time:.2f}s)"))
                del self.key_states[key]
                
        # Update object counts for object browser
        if self.active_tab == 1 and self.game_instance:
            self.update_object_categories()

    def update_object_categories(self):
        # This would be populated with game objects
        # For now, we'll just count Python objects
        self.object_categories = {
            "System": {
                "FPS": f"{self.get_current_fps():.1f}",
                "Memory (MB)": f"{self.get_current_memory():.1f}",
                "Python Objects": len(gc.get_objects())
            },
            "Game State": {
                "Current Menu": getattr(self.game_instance, "currentMenu", "Unknown"),
                "Selected Option": getattr(self.game_instance, "selectedOption", -1),
                "Transition": getattr(self.game_instance, "menuTransition", 0)
            }
        }
        
        # Add example for demonstration
        if hasattr(self.game_instance, "particles"):
            self.object_categories["Particles"] = {
                "Count": len(self.game_instance.particles)
            }
            
        if hasattr(self.game_instance, "menuItems"):
            self.object_categories["UI"] = {
                "Menu Items": len(self.game_instance.menuItems)
            }

    def get_current_fps(self):
        if self.fps_values:
            return self.fps_values[-1]
        return 0
        
    def get_current_memory(self):
        if self.memory_values:
            return self.memory_values[-1]
        return 0
        
    def get_visible_console_lines(self):
        line_height = self.fonts["monospace"].get_height()
        available_height = self.content_rect.height - 40  # Reserve space for input box
        return available_height // line_height

    def execute_console_command(self, command):
        self.console_log(f">>> {command}", "CMD")
        
        try:
            # Basic command parsing
            if command.startswith("help"):
                self.console_log("Available commands:")
                self.console_log("  help - Show this help")
                self.console_log("  fps - Show current FPS")
                self.console_log("  memory - Show memory usage")
                self.console_log("  gc - Run garbage collection")
                self.console_log("  objects - Count objects")
                self.console_log("  inspect [var] - Inspect a variable")
                
            elif command == "fps":
                self.console_log(f"Current FPS: {self.get_current_fps():.1f}")
                
            elif command == "memory":
                self.console_log(f"Memory usage: {self.get_current_memory():.1f} MB")
                
            elif command == "gc":
                before = len(gc.get_objects())
                collected = gc.collect()
                after = len(gc.get_objects())
                self.console_log(f"Garbage collected: {collected} objects, {before-after} total reduction")
                
            elif command == "objects":
                self.console_log(f"Total Python objects: {len(gc.get_objects())}")
                
            elif command.startswith("inspect "):
                var_name = command.split(" ", 1)[1]
                if hasattr(self.game_instance, var_name):
                    value = getattr(self.game_instance, var_name)
                    self.console_log(f"{var_name} = {repr(value)}")
                    if hasattr(value, "__dict__"):
                        for k, v in value.__dict__.items():
                            self.console_log(f"  .{k} = {repr(v)}")
                else:
                    self.console_log(f"Variable '{var_name}' not found", "ERROR")
            
            else:
                # Try to execute as Python code in the context of the game
                result = eval(command, {"pygame": pygame, "self": self.game_instance, "devtools": self})
                self.console_log(f"Result: {result}")
                
        except Exception as e:
            self.console_log(f"Error: {str(e)}", "ERROR")
            self.console_log(traceback.format_exc(), "ERROR")

    def draw(self, surface):
        if not self.visible:
            return
            
        # Draw window background
        window_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(window_surface, self.colors["bg"], 
                         (0, 0, self.width, self.height), border_radius=5)
        pygame.draw.rect(window_surface, self.colors["border"], 
                         (0, 0, self.width, self.height), width=2, border_radius=5)
        
        # Draw header
        pygame.draw.rect(window_surface, self.colors["header"], 
                         (0, 0, self.width, self.header_height))
        
        # Draw tabs
        tab_x = 0
        for i, tab in enumerate(self.tabs):
            tab_color = self.colors["tab_active"] if i == self.active_tab else self.colors["tab"]
            pygame.draw.rect(window_surface, tab_color, 
                            (tab_x, 0, self.tab_width, self.header_height))
            
            # Draw tab separator
            if i < len(self.tabs) - 1:
                pygame.draw.line(window_surface, self.colors["border"], 
                                (tab_x + self.tab_width, 5), 
                                (tab_x + self.tab_width, self.header_height - 5), 1)
            
            # Draw tab text
            tab_text = self.fonts["tab"].render(tab, True, self.colors["text"])
            tab_text_rect = tab_text.get_rect(center=(tab_x + self.tab_width//2, self.header_height//2))
            window_surface.blit(tab_text, tab_text_rect)
            
            tab_x += self.tab_width
        
        # Draw active tab content
        if self.active_tab == 0:
            self.draw_performance_tab(window_surface)
        elif self.active_tab == 1:
            self.draw_objects_tab(window_surface)
        elif self.active_tab == 2:
            self.draw_console_tab(window_surface)
        elif self.active_tab == 3:
            self.draw_input_tab(window_surface)
        elif self.active_tab == 4:
            self.draw_scene_tab(window_surface)
            
        # Draw to main surface
        surface.blit(window_surface, (self.x, self.y))

    def draw_performance_tab(self, surface):
        content_x = 10
        content_y = self.header_height + 10
        content_width = self.width - 20
        graph_height = 150
        
        # FPS display
        if self.fps_values:
            current_fps = self.fps_values[-1]
            avg_fps = sum(self.fps_values) / len(self.fps_values)
            min_fps = min(self.fps_values)
            max_fps = max(self.fps_values)
            
            fps_text = self.fonts["header"].render(f"FPS: {current_fps:.1f}", True, self.colors["fps_graph"])
            surface.blit(fps_text, (content_x, content_y))
            
            stats_text = self.fonts["regular"].render(
                f"Avg: {avg_fps:.1f} | Min: {min_fps:.1f} | Max: {max_fps:.1f}", 
                True, self.colors["text"])
            surface.blit(stats_text, (content_x + 150, content_y + 5))
            
            # Draw FPS graph
            graph_surface = pygame.Surface((content_width, graph_height))
            graph_surface.fill(self.colors["graph_bg"])
            
            if len(self.fps_values) >= 2:
                max_val = max(max_fps, 60) * 1.1  # Ensure scale includes 60fps
                
                points = []
                for i, fps in enumerate(self.fps_values):
                    x = int(i * content_width / (len(self.fps_values) - 1))
                    y = int(graph_height - (fps / max_val) * graph_height)
                    points.append((x, y))
                
                if len(points) >= 2:
                    pygame.draw.lines(graph_surface, self.colors["fps_graph"], False, points, 2)
                
                # Draw 60fps reference line
                ref_y = int(graph_height - (60 / max_val) * graph_height)
                pygame.draw.line(graph_surface, (100, 100, 100), (0, ref_y), (content_width, ref_y), 1)
                ref_text = self.fonts["small"].render("60", True, (150, 150, 150))
                graph_surface.blit(ref_text, (5, ref_y - 15))
            
            surface.blit(graph_surface, (content_x, content_y + 40))
            
            # Memory usage
            memory_y = content_y + graph_height + 60
            current_memory = self.memory_values[-1] if self.memory_values else 0
            memory_text = self.fonts["header"].render(
                f"Memory: {current_memory:.1f} MB", True, self.colors["memory_graph"])
            surface.blit(memory_text, (content_x, memory_y))
            
            if self.memory_values:
                avg_mem = sum(self.memory_values) / len(self.memory_values)
                stats_text = self.fonts["regular"].render(
                    f"Peak: {max(self.memory_values):.1f} MB", True, self.colors["text"])
                surface.blit(stats_text, (content_x + 230, memory_y + 5))
                
                # Draw memory graph
                graph_surface = pygame.Surface((content_width, graph_height))
                graph_surface.fill(self.colors["graph_bg"])
                
                if len(self.memory_values) >= 2:
                    max_val = max(self.memory_values) * 1.1
                    min_val = min(self.memory_values) * 0.9
                    value_range = max_val - min_val
                    
                    points = []
                    for i, mem in enumerate(self.memory_values):
                        x = int(i * content_width / (len(self.memory_values) - 1))
                        y = int(graph_height - ((mem - min_val) / value_range) * graph_height)
                        points.append((x, y))
                    
                    if len(points) >= 2:
                        pygame.draw.lines(graph_surface, self.colors["memory_graph"], False, points, 2)
                
                surface.blit(graph_surface, (content_x, memory_y + 40))

    def draw_objects_tab(self, surface):
        content_x = 10
        content_y = self.header_height + 10
        line_height = self.fonts["regular"].get_height() + 5
        
        # Draw object categories
        y_offset = content_y - self.object_scroll
        
        for category, items in self.object_categories.items():
            # Check if category is visible
            if not (y_offset < self.height and y_offset + line_height > self.header_height):
                y_offset += line_height
                if category in self.expanded_categories:
                    y_offset += line_height * len(items)
                continue
                
            # Draw category header
            expanded = category in self.expanded_categories
            marker = "▼" if expanded else "▶"
            text = self.fonts["header"].render(f"{marker} {category}", True, self.colors["highlight"])
            text_rect = text.get_rect(topleft=(content_x, y_offset))
            
            # Only draw if in visible area
            if self.header_height <= y_offset <= self.height:
                surface.blit(text, text_rect)
                pygame.draw.line(surface, self.colors["border"], 
                                (content_x, y_offset + line_height - 2), 
                                (self.width - 20, y_offset + line_height - 2), 1)
            
            y_offset += line_height
            
            # Draw items if expanded
            if expanded:
                for name, value in items.items():
                    # Skip if not visible
                    if not (y_offset < self.height and y_offset + line_height > self.header_height):
                        y_offset += line_height
                        continue
                        
                    if self.header_height <= y_offset <= self.height:
                        item_text = self.fonts["regular"].render(f"   {name}: {value}", True, self.colors["text"])
                        surface.blit(item_text, (content_x, y_offset))
                    
                    y_offset += line_height

    def draw_console_tab(self, surface):
        content_x = 10
        content_y = self.header_height + 10
        content_width = self.width - 20
        
        # Draw console output area
        console_output_height = self.height - self.header_height - 40
        console_rect = pygame.Rect(content_x, content_y, content_width, console_output_height)
        pygame.draw.rect(surface, (20, 20, 30), console_rect)
        pygame.draw.rect(surface, self.colors["border"], console_rect, 1)
        
        # Draw console lines
        line_height = self.fonts["monospace"].get_height()
        visible_lines = min(len(self.console_lines), console_output_height // line_height)
        
        for i in range(visible_lines):
            idx = len(self.console_lines) - 1 - self.console_scroll - i
            if idx < 0:
                break
                
            line = self.console_lines[idx]
            
            # Color-code by log level
            if "[ERROR]" in line:
                color = (255, 100, 100)
            elif "[CMD]" in line:
                color = (100, 200, 255)
            elif "[WARNING]" in line:
                color = (255, 200, 100)
            else:
                color = self.colors["text"]
                
            text = self.fonts["monospace"].render(line, True, color)
            y_pos = content_y + console_output_height - (i + 1) * line_height
            
            # Only draw if in visible area
            if content_y <= y_pos <= content_y + console_output_height:
                surface.blit(text, (content_x + 5, y_pos))
        
        # Draw input area
        input_y = content_y + console_output_height + 5
        input_rect = pygame.Rect(content_x, input_y, content_width, 30)
        pygame.draw.rect(surface, (30, 30, 40), input_rect)
        pygame.draw.rect(surface, self.colors["border"], input_rect, 1)
        
        # Draw input text with cursor
        input_text = self.fonts["monospace"].render(self.console_input, True, self.colors["text"])
        surface.blit(input_text, (content_x + 5, input_y + 5))
        
        # Draw blinking cursor
        if self.console_cursor_visible:
            cursor_x = content_x + 5 + input_text.get_width()
            pygame.draw.line(surface, self.colors["text"], 
                          (cursor_x, input_y + 5), 
                          (cursor_x, input_y + 25), 2)

    def draw_input_tab(self, surface):
        content_x = 10
        content_y = self.header_height + 10
        line_height = self.fonts["regular"].get_height() + 5
        
        # Draw mouse info
        mouse_text = self.fonts["header"].render(f"Mouse: {self.mouse_pos}", True, self.colors["highlight"])
        surface.blit(mouse_text, (content_x, content_y))
        
        button_names = ["Left", "Middle", "Right"]
        button_text = "Buttons: " + ", ".join(f"{button_names[i]}={self.mouse_buttons[i]}" 
                                           for i in range(len(self.mouse_buttons)))
        buttons_surf = self.fonts["regular"].render(button_text, True, self.colors["text"])
        surface.blit(buttons_surf, (content_x, content_y + line_height))
        
        # Draw key state visualization
        key_y = content_y + line_height * 3
        keys_title = self.fonts["header"].render("Pressed Keys:", True, self.colors["highlight"])
        surface.blit(keys_title, (content_x, key_y))
        
        # Draw grid of key blocks
        if self.key_states:
            key_blocks_y = key_y + line_height
            block_size = 60
            blocks_per_row = (self.width - 20) // block_size
            
            for i, (key, timestamp) in enumerate(self.key_states.items()):
                row = i // blocks_per_row
                col = i % blocks_per_row
                
                x = content_x + col * block_size
                y = key_blocks_y + row * block_size
                
                # Calculate how long key has been held
                held_time = time.time() - timestamp
                
                # Vary color based on hold time
                if held_time < 0.5:
                    color = (100, 200, 100)  # Green for fresh presses
                elif held_time < 2.0:
                    color = (200, 200, 100)  # Yellow for medium holds
                else:
                    color = (200, 100, 100)  # Red for long holds
                
                pygame.draw.rect(surface, color, (x, y, block_size - 5, block_size - 5))
                pygame.draw.rect(surface, self.colors["border"], (x, y, block_size - 5, block_size - 5), 1)
                
                key_name = pygame.key.name(key)
                key_text = self.fonts["small"].render(key_name, True, (0, 0, 0))
                text_rect = key_text.get_rect(center=(x + (block_size - 5)//2, y + (block_size - 5)//2))
                surface.blit(key_text, text_rect)
                
                time_text = self.fonts["small"].render(f"{held_time:.1f}s", True, (0, 0, 0))
                time_rect = time_text.get_rect(center=(x + (block_size - 5)//2, y + (block_size - 5)//2 + 15))
                surface.blit(time_text, time_rect)
        else:
            no_keys_text = self.fonts["regular"].render("No keys currently pressed", True, self.colors["text"])
            surface.blit(no_keys_text, (content_x, key_y + line_height))
        
        # Draw recent key history
        history_y = key_y + line_height * 7
        history_title = self.fonts["header"].render("Recent Key Events:", True, self.colors["highlight"])
        surface.blit(history_title, (content_x, history_y))
        
        for i, (key, name, action) in enumerate(self.key_history):
            if i >= 8:  # Show only last 8 events
                break
                
            if "down" in action:
                color = (100, 200, 100)
            else:
                color = (200, 100, 100)
                
            history_text = self.fonts["regular"].render(f"{name}: {action}", True, color)
            surface.blit(history_text, (content_x, history_y + line_height * (i + 1)))

    def draw_scene_tab(self, surface):
        content_x = 10
        content_y = self.header_height + 10
        line_height = self.fonts["regular"].get_height() + 5
        
        # This would show a hierarchical view of the scene/game objects
        # For now we'll just show some basic game state info
        title = self.fonts["header"].render("Game State", True, self.colors["highlight"])
        surface.blit(title, (content_x, content_y))
        
        if self.game_instance:
            y = content_y + line_height
            
            # Display attributes of the game instance
            attrs = ["currentMenu", "previousMenu", "menuTransition", "selectedMain", 
                     "selectedMusic", "selectedOption", "selectedKeybind"]
            
            for attr in attrs:
                if hasattr(self.game_instance, attr):
                    value = getattr(self.game_instance, attr)
                    text = self.fonts["regular"].render(f"{attr}: {value}", True, self.colors["text"])
                    surface.blit(text, (content_x, y))
                    y += line_height
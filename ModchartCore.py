# !!! SECURITY WARNING !!!
# Modcharts are executable Python scripts that run with the same privileges as the game.
# While this system attempts to restrict harmful operations:
#  - It cannot guarantee complete security
#  - Malicious code could potentially damage your system or compromise your data
#
# SAFETY GUIDELINES:
# - Only run modcharts from trusted, reputable sources
# - Review the code before execution if possible
# - Consider running the game in a restricted environment for untrusted modcharts

import ast
import builtins # For access to min/max if needed without shadowing

# Placeholder callback functions if not defined in the modchart
def emptyfunc(*args, **kwargs): pass

def create_generic_modchart_funcs():
    """Creates a dictionary of default callback functions."""
    return {
        "onHit": emptyfunc,
        "onMiss": emptyfunc,
        "onKeyPress": emptyfunc,
        "onUpdate": emptyfunc,
        "onBeat": emptyfunc,
        "onStep": emptyfunc,
        "onSongStart": emptyfunc,
        "onSongEnd": emptyfunc,
        "onNoteCreation": emptyfunc,
        # "onSongWillEnd": onSongWillEnd,
        "init": None,  # For mod-specific initialization
    }

def check_modchart(code):
    """
    Checks if the provided modchart code is valid Python code and restricts imports.
    """
    allowed_modules = [
        "pygame", "math", "random", "copy", "time", "datetime", "json",
        "collections", "itertools", "functools", "operator", "re",
        "builtins", # Allow access to built-in functions
        # Add other safe modules as needed
    ]
    disallowed_modules = [
        "os", "sys", "subprocess", "shutil", "pathlib", "io",
        "open", "file", "tempfile", "glob", "socket", "urllib.request",
        "requests", "ftplib", "smtplib", "pickle", "shelve", "dbm",
        "ctypes", "multiprocessing" # Restrict access to lower-level or potentially harmful modules
    ]
    try:
        compile(code, "<string>", "exec")
    except SyntaxError as e:
        raise SyntaxError(f"Syntax error in modchart code: {e.msg} at line {e.lineno}")

    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                module_name_to_check = None
                if isinstance(node, ast.ImportFrom):
                    if node.module: # Handles "from x import y"
                        module_name_to_check = node.module.split('.')[0]
                elif isinstance(node, ast.Import): # Handles "import x"
                     if node.names and node.names[0].name:
                        module_name_to_check = node.names[0].name.split('.')[0]

                if module_name_to_check:
                    if module_name_to_check in disallowed_modules:
                        raise ValueError(f"Explicitly disallowed module import: {module_name_to_check}")
                    if module_name_to_check not in allowed_modules and module_name_to_check not in dir(builtins):
                        raise ValueError(f"Disallowed module import: {module_name_to_check}. Allowed: {allowed_modules}")

    except Exception as e:
        raise ValueError(f"Error analyzing imports: {str(e)}")
    return True


def runModchart(code, game_context=None):
    """
    Runs a modchart string (Python) and returns its defined callback functions.
    The modchart code can call API functions defined within this scope, which
    operate on the provided game_context.

    Args:
        code (str): The modchart code to be executed.
        game_context (dict, optional): Game state and objects to expose to the modchart.
                                       This dictionary will be modified by API calls.
    Returns:
        dict: Dictionary containing callback functions as defined/overridden by the modchart.
    """
    check_modchart(code)

    if game_context is None:
        game_context = {}

    # Initialize modding-specific parts of game_context if not present
    game_context.setdefault('mod_texts', {})
    game_context.setdefault('active_camera_shakes', [])
    game_context.setdefault('song_should_end', False)
    game_context.setdefault('song_should_restart', False)
    game_context.setdefault('song_should_exit', False)
    game_context.setdefault('skip_transition', False)
    game_context.setdefault('score', 0)
    game_context.setdefault('hits', 0)
    # game_context['currentTime'] should be updated by Game.py
    # game_context['health'], game_context['misses'], game_context['combo'] from Game.py
    # game_context['pygame'] should contain pygame modules (display, draw, font, etc.)
    # game_context['character1'], game_context['character2'] from Game.py
    # game_context['keybinds'] from Game.py

    # --- API Functions available to the modchart ---
    # These functions are defined here and will close over `game_context`.

    # --- Song Control ---
    def end_song_api():
        # on_song_will_end_cb = mod_script_globals.get('onSongWillEnd')
        # if on_song_will_end_cb:
        #     try:
        #         if on_song_will_end_cb() == False: # Mod cancelled the song end
        #             return
        #     except Exception as e:
        #         print(f"Error in mod's onSongWillEnd callback: {e}")
        game_context['song_should_end'] = True

    def get_song_position_api():
        return game_context.get('currentTime', 0) * 1000

    def restart_song_api(skip_transition=False):
        game_context['song_should_restart'] = True
        game_context['skip_transition'] = skip_transition

    def exit_song_api(skip_transition=False):
        game_context['song_should_exit'] = True
        game_context['skip_transition'] = skip_transition

    # --- Text Management ---
    def _get_pg_font(font_path=None, size=30):
        pg_font_module = game_context.get('pygame', {}).get('font')
        if not pg_font_module:
            raise ValueError("Pygame font module not found in game_context.")
        try:
            return pg_font_module.Font(font_path, size)
        except: # Fallback to system font
            print(f"Warning: Font '{font_path}' not found or error loading. Falling back to system font.")
            return pg_font_module.SysFont("arial", size)

    def _re_render_text_surface(tag):
        text_obj = game_context['mod_texts'].get(tag)
        if not text_obj: return False
        try:
            text_obj['surface'] = text_obj['pg_font'].render(text_obj['text'], True, text_obj['color'])
            current_topleft = text_obj['rect'].topleft
            text_obj['rect'] = text_obj['surface'].get_rect()
            text_obj['rect'].topleft = current_topleft
            return True
        except Exception as e:
            print(f"Error re-rendering text '{tag}': {e}")
            return False

    def create_text_api(tag, text_content='', width=0, x=0, y=0, font_path=None, size=30, color=(255,255,255), visible=True):
        if tag in game_context['mod_texts']:
            print(f"Modchart Warning: Text tag '{tag}' already exists. Overwriting.")
        try:
            pg_font_obj = _get_pg_font(font_path, size)
            surface = pg_font_obj.render(str(text_content), True, color)
            rect = surface.get_rect(topleft=(x,y))
            game_context['mod_texts'][tag] = {
                'surface': surface, 'rect': rect, 'text': str(text_content),
                'font_path': font_path, 'size': size, 'color': color,
                'visible': visible, 'pg_font': pg_font_obj,
                'width_constraint': width # For future use (e.g., text wrapping)
            }
            return True
        except Exception as e:
            print(f"Modchart Error: Creating text '{tag}': {e}")
            return False

    def show_text_api(tag):
        if tag in game_context['mod_texts']:
            game_context['mod_texts'][tag]['visible'] = True; return True
        return False

    def hide_text_api(tag, destroy=True):
        if tag in game_context['mod_texts']:
            game_context['mod_texts'][tag]['visible'] = False
            if destroy: del game_context['mod_texts'][tag]
            return True
        return False

    def set_text_string_api(tag, text_content):
        if tag in game_context['mod_texts']:
            game_context['mod_texts'][tag]['text'] = str(text_content)
            return _re_render_text_surface(tag)
        return False

    def set_text_size_api(tag, size):
        if tag in game_context['mod_texts'] and isinstance(size, int) and size > 0:
            text_obj = game_context['mod_texts'][tag]
            text_obj['size'] = size
            text_obj['pg_font'] = _get_pg_font(text_obj['font_path'], size)
            return _re_render_text_surface(tag)
        return False

    def set_text_color_api(tag, color_value):
        if tag in game_context['mod_texts']:
            pg = game_context.get('pygame')
            if not pg: print("Pygame not in game_context for color parsing."); return False
            try:
                parsed_color = pg.Color(color_value) # Handles names, hex, tuples
                game_context['mod_texts'][tag]['color'] = (parsed_color.r, parsed_color.g, parsed_color.b)
                return _re_render_text_surface(tag)
            except Exception as e:
                print(f"Modchart Error: Invalid color '{color_value}' for text '{tag}': {e}")
                return False
        return False

    def set_text_font_api(tag, font_path):
        if tag in game_context['mod_texts']:
            text_obj = game_context['mod_texts'][tag]
            text_obj['font_path'] = font_path
            text_obj['pg_font'] = _get_pg_font(font_path, text_obj['size'])
            return _re_render_text_surface(tag)
        return False
        
    def set_text_position_api(tag, x, y):
        if tag in game_context['mod_texts']:
            game_context['mod_texts'][tag]['rect'].topleft = (x,y)
            return True
        return False

    def get_text_string_api(tag):
        return game_context['mod_texts'].get(tag, {}).get('text')

    def text_exists_api(tag):
        return tag in game_context['mod_texts']

    # --- Camera ---
    def camera_shake_api(camera_target, intensity, duration_seconds):
        # Game.py's drawing functions will need to check game_context['active_camera_shakes']
        # and apply offsets based on currentTime, intensity, and duration.
        # camera_target can be 'game', 'hud', or 'other'.
        pg_time = game_context.get('pygame', {}).get('time')
        if not pg_time: print("Pygame time not in game_context for camera_shake."); return
        
        game_context['active_camera_shakes'].append({
            'target': camera_target, 'intensity': intensity,
            'duration': duration_seconds, 'start_time': game_context.get('currentTime', 0),
            'id': pg_time.get_ticks() # Unique ID if needed for management
        })

    # --- Input ---
    _fnf_key_map = None
    def _init_key_map():
        nonlocal _fnf_key_map
        if _fnf_key_map is not None: return
        pg_locals = game_context.get('pygame', {}).get('locals', {})
        if not pg_locals: print("Pygame locals not in game_context for key mapping."); _fnf_key_map = {}; return

        keybinds = game_context.get('keybinds', [None]*8)
        _fnf_key_map = {
            "note_left": keybinds[0] or pg_locals.get('K_a'),
            "note_down": keybinds[1] or pg_locals.get('K_s'),
            "note_up": keybinds[2] or pg_locals.get('K_w'),
            "note_right": keybinds[3] or pg_locals.get('K_d'),
            "opponent_note_left": keybinds[4] or pg_locals.get('K_LEFT'),
            "opponent_note_down": keybinds[5] or pg_locals.get('K_DOWN'),
            "opponent_note_up": keybinds[6] or pg_locals.get('K_UP'),
            "opponent_note_right": keybinds[7] or pg_locals.get('K_RIGHT'),
            "left": pg_locals.get('K_LEFT'), "right": pg_locals.get('K_RIGHT'),
            "up": pg_locals.get('K_UP'), "down": pg_locals.get('K_DOWN'),
            "space": pg_locals.get('K_SPACE'), "enter": pg_locals.get('K_RETURN'),
            "escape": pg_locals.get('K_ESCAPE'),
            # Add more generic key names to pg_locals mappings
        }
        # Filter out None values if a key wasn't found in pg_locals
        _fnf_key_map = {k: v for k, v in _fnf_key_map.items() if v is not None}


    def is_key_pressed_api(button_name):
        _init_key_map()
        pg_key_module = game_context.get('pygame', {}).get('key')
        if not pg_key_module: print("Pygame key module not in game_context."); return False

        key_code = _fnf_key_map.get(button_name.lower())
        if key_code is None:
            # Try to parse as direct K_ constant e.g. "K_x"
            pg_locals = game_context.get('pygame', {}).get('locals', {})
            if button_name.upper() in pg_locals:
                 key_code = pg_locals[button_name.upper()]
            else:
                print(f"Modchart Warning: Unknown key name '{button_name}' for is_key_pressed_api.")
                return False
        
        return pg_key_module.get_pressed()[key_code]

    # keyReleased would require Game.py to populate game_context['released_keys_this_frame'] (a set of key codes)
    # def was_key_released_api(button_name):
    #     _init_key_map()
    #     key_code = _fnf_key_map.get(button_name.lower())
    #     if key_code is None: return False
    #     return key_code in game_context.get('released_keys_this_frame', set())

    # --- Character Control ---
    def _get_char_obj_api(character_tag):
        # In Game.py, player is character2, opponent is character1
        if character_tag.lower() in ['bf', 'player']: return game_context.get('character2')
        if character_tag.lower() in ['dad', 'opponent']: return game_context.get('character1')
        # if character_tag.lower() == 'gf': return game_context.get('gf_character') # If you add GF
        print(f"Modchart Warning: Unknown character tag '{character_tag}'.")
        return None

    def get_character_x_api(character_tag):
        char_obj = _get_char_obj_api(character_tag)
        # This is a simplification. Character.pos is complex.
        # Game.py's drawCharacters would need to use char_obj.mod_x if set.
        if char_obj: return getattr(char_obj, 'mod_x', char_obj.pos[4][0][0] if char_obj.pos and len(char_obj.pos) > 4 and char_obj.pos[4] else 0)
        return 0.0

    def get_character_y_api(character_tag):
        char_obj = _get_char_obj_api(character_tag)
        if char_obj: return getattr(char_obj, 'mod_y', char_obj.pos[4][0][1] if char_obj.pos and len(char_obj.pos) > 4 and char_obj.pos[4] else 0)
        return 0.0

    def set_character_x_api(character_tag, value):
        char_obj = _get_char_obj_api(character_tag)
        if char_obj:
            char_obj.mod_x = float(value) # Game.py drawCharacters needs to use this
            print(f"Modchart Note: setCharacterX for '{character_tag}' requires Game.py drawCharacters to use 'char_obj.mod_x'.")
            return True
        return False

    def set_character_y_api(character_tag, value):
        char_obj = _get_char_obj_api(character_tag)
        if char_obj:
            char_obj.mod_y = float(value) # Game.py drawCharacters needs to use this
            print(f"Modchart Note: setCharacterY for '{character_tag}' requires Game.py drawCharacters to use 'char_obj.mod_y'.")
            return True
        return False

    # --- Game Stats ---
    def get_score_api(): return game_context.get('score', 0)
    def add_score_api(value): game_context['score'] = game_context.get('score', 0) + int(value)
    def set_score_api(value): game_context['score'] = int(value)

    def get_misses_api(): return game_context.get('misses', 0)
    def add_misses_api(value): game_context['misses'] = game_context.get('misses', 0) + int(value) # Game.py also modifies this
    def set_misses_api(value): game_context['misses'] = int(value)

    def get_hits_api(): return game_context.get('hits', 0) # Game.py needs to increment 'hits'
    def add_hits_api(value): game_context['hits'] = game_context.get('hits', 0) + int(value)
    def set_hits_api(value): game_context['hits'] = int(value)

    def get_health_api(): # Game.py health is 0-100. API wants 0-2.
        return game_context.get('health', 50) / 50.0
    def add_health_api(value): # value is in 0-2 range
        current_health_100 = game_context.get('health', 50)
        change_100 = float(value) * 50.0
        game_context['health'] = builtins.min(builtins.max(current_health_100 + change_100, 0), 100)
    def set_health_api(value=1.0): # value is in 0-2 range, default 1.0 (50% health in game)
        game_context['health'] = builtins.min(builtins.max(float(value) * 50.0, 0), 100)


    # --- Prepare execution environment for the mod script ---
    mod_script_globals = {
        # Callbacks (will be overwritten if defined by mod)
        "onHit": emptyfunc, "onMiss": emptyfunc, "onKeyPress": emptyfunc,
        "onUpdate": emptyfunc, "onBeat": emptyfunc, "onStep": emptyfunc,
        "onSongStart": emptyfunc, "onSongEnd": emptyfunc,
        "onNoteCreation": emptyfunc, "init": None,

        # API Functions
        "endSong": end_song_api,
        "getSongPosition": get_song_position_api,
        "restartSong": restart_song_api,
        "exitSong": exit_song_api,

        "makeLuaText": create_text_api, # Legacy name
        "create_text": create_text_api,
        "addLuaText": show_text_api,    # Legacy name
        "show_text": show_text_api,
        "removeLuaText": hide_text_api, # Legacy name
        "hide_text": hide_text_api,
        "setTextString": set_text_string_api,
        "setTextSize": set_text_size_api,
        "setTextColor": set_text_color_api,
        "setTextFont": set_text_font_api,
        "setTextPosition": set_text_position_api, # Added
        # TODO: setTextWidth, setTextHeight, setTextAutoSize, setTextBorder, setTextItalic, setTextAlignment
        "getTextString": get_text_string_api,
        # TODO: getTextSize, getTextFont, getTextWidth
        "luaTextExists": text_exists_api, # Legacy name
        "text_exists": text_exists_api,

        "cameraShake": camera_shake_api,

        "keyPressed": is_key_pressed_api, # Renamed from is_key_pressed_api for mod script
        # "keyReleased": was_key_released_api,

        "getCharacterX": get_character_x_api,
        "getCharacterY": get_character_y_api,
        "setCharacterX": set_character_x_api,
        "setCharacterY": set_character_y_api,

        "getScore": get_score_api,
        "addScore": add_score_api,
        "setScore": set_score_api,
        "getMisses": get_misses_api,
        "addMisses": add_misses_api,
        "setMisses": set_misses_api,
        "getHits": get_hits_api,
        "addHits": add_hits_api,
        "setHits": set_hits_api,
        "getHealth": get_health_api,
        "addHealth": add_health_api,
        "setHealth": set_health_api,
        
        # Expose some safe builtins and modules
        "math": __import__("math"),
        "random": __import__("random"),
        "str": str, "int": int, "float": float, "bool": bool, "list": list, "dict": dict, "tuple": tuple,
        "min": builtins.min, "max": builtins.max, "abs": builtins.abs, "round": round, "len": len, "print": print, # Override print for safety?
        # "game": game_context, # Direct access to game_context (use with caution)
    }
    if game_context.get('pygame'): # Expose pygame modules if available
        mod_script_globals['pygame_display'] = game_context['pygame'].get('display')
        mod_script_globals['pygame_draw'] = game_context['pygame'].get('draw')
        mod_script_globals['pygame_transform'] = game_context['pygame'].get('transform')
        mod_script_globals['pygame_font'] = game_context['pygame'].get('font')
        mod_script_globals['pygame_Rect'] = game_context['pygame'].get('Rect')


    # Execute the modchart code
    try:
        exec(code, mod_script_globals)
    except Exception as e:
        print(f"Error executing modchart code: {e}")
        # Return default functions if execution fails badly
        return create_generic_modchart_funcs()

    # Extract the callback functions that might have been defined/overridden by the modchart
    final_mod_functions = create_generic_modchart_funcs() # Start with defaults
    for cb_name in final_mod_functions:
        if cb_name in mod_script_globals and callable(mod_script_globals[cb_name]):
            final_mod_functions[cb_name] = mod_script_globals[cb_name]

    # Call the mod's init function if it was defined
    if final_mod_functions["init"] and callable(final_mod_functions["init"]):
        try:
            final_mod_functions["init"]()
        except Exception as e:
            print(f"Error in modchart init() function: {e}")

    return final_mod_functions
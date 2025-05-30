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

HEALTH_API_SCALING_FACTOR = 50.0 # Game health 0-100 <-> API health 0-2

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
        "onSongWillEnd": emptyfunc, # Default for the game to call, mod can override
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

def sandboxed_exec(code, globals=None, locals=None):
    """
    Executes the provided code in a restricted environment.
    This function aims to provide a safer alternative to the built-in `exec` function
    by limiting access to potentially harmful built-in functions and modules.

    Args:
        code (str): The Python code to execute.
        globals (dict, optional): Global variables for the execution context. Defaults to a new empty dictionary.
        locals (dict, optional): Local variables for the execution context. Defaults to a new empty dictionary.
    """
    if globals is None:
        globals = {}
    if locals is None:
        locals = {}

    # Define a whitelist of safe built-in functions
    safe_builtins = {
        'abs': abs, 'bool': bool, 'dict': dict, 'float': float, 'int': int,
        'len': len, 'list': list, 'max': max, 'min': min,
        'range': range, 'round': round, 'set': set, 'str': str, 'tuple': tuple,
        # 'print' is handled by a custom wrapper in mod_script_globals
    }

    # Create a restricted environment by explicitly setting __builtins__ to a dictionary
    # containing only the safe built-ins.  This prevents access to the original
    # builtins module and its potentially dangerous functions.
    restricted_globals = {'__builtins__': safe_builtins}
    restricted_globals.update(globals)  # Add any provided globals

    # Remove potentially dangerous names from globals (already restricted by __builtins__ but good for defense in depth)
    restricted_globals.pop('__import__', None) # __import__ in restricted_globals is the safe one if provided by API
    restricted_globals.pop('eval', None)
    restricted_globals.pop('exec', None)
    restricted_globals.pop('compile', None)
    restricted_globals.pop('open', None) # Explicitly remove open from globals, though safe_builtins controls it

    try:
        # Execute the code within the restricted environment
        compiled_code = compile(code, '<string>', 'exec')
        exec(compiled_code, restricted_globals, locals)
    except Exception as e:
        # Consider logging this to a mod-specific log or providing more context
        print(f"Error executing sandboxed code: {type(e).__name__}: {e}")
        raise # Re-raise to be caught by runModchart


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

    # --- Custom Print for Modcharts ---
    def _mod_print(*args, **kwargs):
        print("[MODCHART]", *args, **kwargs)


    # --- Song Control ---
    def end_song_api():
        # This API function is called by the mod.
        # It can optionally call the mod's onSongWillEnd callback.
        on_song_will_end_cb = game_context.get('onSongWillEnd') # Check game_context (locals of script)
        if callable(on_song_will_end_cb) and on_song_will_end_cb is not emptyfunc:
            try:
                # If onSongWillEnd returns False, the song end is cancelled by the mod.
                if on_song_will_end_cb() == False:
                    return
            except Exception as e:
                _mod_print(f"Error in mod's onSongWillEnd callback: {type(e).__name__}: {e}")
        game_context['song_should_end'] = True

    def get_song_position_api():
        return game_context.get('currentTime', 0) * 1000 # Convert seconds to milliseconds

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
            raise ValueError("Pygame font module not found in game_context. Cannot create font.")
        try:
            return pg_font_module.Font(font_path, size)
        except Exception as e: # Catches pygame.error, FileNotFoundError, etc.
            _mod_print(f"Warning: Font '{font_path}' not found or error loading ({type(e).__name__}: {e}). Falling back to system font.")
            try:
                return pg_font_module.SysFont("arial", size)
            except Exception as e_sys:
                _mod_print(f"CRITICAL: System font 'arial' failed to load ({type(e_sys).__name__}: {e_sys}). Text rendering issues likely.")
                raise # Re-raise if system font also fails

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
            _mod_print(f"Error re-rendering text '{tag}': {type(e).__name__}: {e}")
            return False

    def create_text_api(tag, text_content='', width=0, x=0, y=0, font_path=None, size=30, color=(255,255,255), visible=True):
        if tag in game_context['mod_texts']:
            _mod_print(f"Warning: Text tag '{tag}' already exists. Overwriting.")
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
            _mod_print(f"Error creating text '{tag}': {type(e).__name__}: {e}")
            return False

    def show_text_api(tag):
        if tag in game_context['mod_texts']:
            game_context['mod_texts'][tag]['visible'] = True; return True
        _mod_print(f"Warning: Attempted to show non-existent text tag '{tag}'.")
        return False

    def hide_text_api(tag, destroy=True):
        if tag in game_context['mod_texts']:
            game_context['mod_texts'][tag]['visible'] = False
            if destroy: del game_context['mod_texts'][tag]
            return True
        _mod_print(f"Warning: Attempted to hide/destroy non-existent text tag '{tag}'.")
        return False

    def set_text_string_api(tag, text_content):
        if tag in game_context['mod_texts']:
            game_context['mod_texts'][tag]['text'] = str(text_content)
            return _re_render_text_surface(tag)
        _mod_print(f"Warning: Attempted to set string for non-existent text tag '{tag}'.")
        return False

    def set_text_size_api(tag, size):
        if tag in game_context['mod_texts'] and isinstance(size, int) and size > 0:
            text_obj = game_context['mod_texts'][tag]
            text_obj['size'] = size
            try:
                text_obj['pg_font'] = _get_pg_font(text_obj['font_path'], size)
                return _re_render_text_surface(tag)
            except Exception as e:
                _mod_print(f"Error setting text size for '{tag}' (font reload failed): {type(e).__name__}: {e}")
                return False
        if not (isinstance(size, int) and size > 0):
             _mod_print(f"Warning: Invalid size '{size}' for text tag '{tag}'. Must be positive integer.")
        else:
            _mod_print(f"Warning: Attempted to set size for non-existent text tag '{tag}'.")
        return False

    def set_text_color_api(tag, color_value):
        if tag in game_context['mod_texts']:
            pg = game_context.get('pygame')
            if not pg: _mod_print("Pygame not in game_context for color parsing."); return False
            try:
                parsed_color = pg.Color(color_value) # Handles names, hex, tuples
                game_context['mod_texts'][tag]['color'] = (parsed_color.r, parsed_color.g, parsed_color.b)
                return _re_render_text_surface(tag)
            except Exception as e: # Catches ValueError from pg.Color, etc.
                _mod_print(f"Error: Invalid color '{color_value}' for text '{tag}': {type(e).__name__}: {e}")
                return False
        _mod_print(f"Warning: Attempted to set color for non-existent text tag '{tag}'.")
        return False

    def set_text_font_api(tag, font_path):
        if tag in game_context['mod_texts']:
            text_obj = game_context['mod_texts'][tag]
            text_obj['font_path'] = font_path
            try:
                text_obj['pg_font'] = _get_pg_font(font_path, text_obj['size'])
                return _re_render_text_surface(tag)
            except Exception as e:
                _mod_print(f"Error setting text font for '{tag}' (font reload failed): {type(e).__name__}: {e}")
                return False
        _mod_print(f"Warning: Attempted to set font for non-existent text tag '{tag}'.")
        return False
        
    def set_text_position_api(tag, x, y):
        if tag in game_context['mod_texts']:
            try:
                game_context['mod_texts'][tag]['rect'].topleft = (float(x),float(y))
                return True
            except ValueError:
                _mod_print(f"Warning: Invalid x/y coordinates ('{x}', '{y}') for text tag '{tag}'.")
                return False
        _mod_print(f"Warning: Attempted to set position for non-existent text tag '{tag}'.")
        return False

    def get_text_string_api(tag):
        return game_context['mod_texts'].get(tag, {}).get('text')

    def text_exists_api(tag):
        return tag in game_context['mod_texts']

    # --- Camera ---
    def camera_shake_api(camera_target, intensity, duration_seconds):
        pg_time = game_context.get('pygame', {}).get('time')
        if not pg_time: _mod_print("Pygame time not in game_context for camera_shake."); return
        
        game_context['active_camera_shakes'].append({
            'target': camera_target, 'intensity': float(intensity),
            'duration': float(duration_seconds), 'start_time': game_context.get('currentTime', 0),
            'id': pg_time.get_ticks() 
        })

    # --- Input ---
    _fnf_key_map = None
    def _init_key_map():
        nonlocal _fnf_key_map
        if _fnf_key_map is not None: return
        pg_locals = game_context.get('pygame', {}).get('locals', {})
        if not pg_locals: _mod_print("Pygame locals not in game_context for key mapping."); _fnf_key_map = {}; return

        keybinds = game_context.get('keybinds', [None]*8) # Default to list of Nones if not found
        _fnf_key_map = {
            "note_left": keybinds[0] if len(keybinds) > 0 else pg_locals.get('K_a'),
            "note_down": keybinds[1] if len(keybinds) > 1 else pg_locals.get('K_s'),
            "note_up": keybinds[2] if len(keybinds) > 2 else pg_locals.get('K_w'),
            "note_right": keybinds[3] if len(keybinds) > 3 else pg_locals.get('K_d'),
            "opponent_note_left": keybinds[4] if len(keybinds) > 4 else pg_locals.get('K_LEFT'),
            "opponent_note_down": keybinds[5] if len(keybinds) > 5 else pg_locals.get('K_DOWN'),
            "opponent_note_up": keybinds[6] if len(keybinds) > 6 else pg_locals.get('K_UP'),
            "opponent_note_right": keybinds[7] if len(keybinds) > 7 else pg_locals.get('K_RIGHT'),
            "left": pg_locals.get('K_LEFT'), "right": pg_locals.get('K_RIGHT'),
            "up": pg_locals.get('K_UP'), "down": pg_locals.get('K_DOWN'),
            "space": pg_locals.get('K_SPACE'), "enter": pg_locals.get('K_RETURN'),
            "escape": pg_locals.get('K_ESCAPE'),
        }
        _fnf_key_map = {k: v for k, v in _fnf_key_map.items() if v is not None}


    def is_key_pressed_api(button_name):
        _init_key_map()
        pg_key_module = game_context.get('pygame', {}).get('key')
        if not pg_key_module: _mod_print("Pygame key module not in game_context."); return False

        key_code = _fnf_key_map.get(str(button_name).lower())
        if key_code is None:
            pg_locals = game_context.get('pygame', {}).get('locals', {})
            # Check if button_name is a direct K_ constant like "K_x"
            direct_key_code = pg_locals.get(str(button_name).upper())
            if direct_key_code is not None:
                key_code = direct_key_code
            else:
                _mod_print(f"Warning: Unknown key name '{button_name}' for keyPressed.")
                return False
        
        try:
            return pg_key_module.get_pressed()[key_code]
        except IndexError:
            _mod_print(f"Warning: Key code {key_code} for '{button_name}' out of bounds for get_pressed().")
            return False

    # keyReleased would require Game.py to populate game_context['released_keys_this_frame'] (a set of key codes)
    # def was_key_released_api(button_name):
    #     _init_key_map()
    #     key_code = _fnf_key_map.get(str(button_name).lower())
    #     if key_code is None: return False # Potentially add direct K_ constant check here too
    #     return key_code in game_context.get('released_keys_this_frame', set())

    # --- Character Control ---
    def _get_char_obj_api(character_tag):
        char_tag_lower = str(character_tag).lower()
        if char_tag_lower in ['bf', 'player', 'character2']: return game_context.get('character2')
        if char_tag_lower in ['dad', 'opponent', 'character1']: return game_context.get('character1')
        # if char_tag_lower == 'gf': return game_context.get('gf_character')
        _mod_print(f"Warning: Unknown character tag '{character_tag}'.")
        return None

    def _get_char_default_pos_component(char_obj, index):
        """Safely extracts a default position component (0 for X, 1 for Y)."""
        default_val = 0.0
        if hasattr(char_obj, 'pos') and char_obj.pos:
            try:
                # Expected structure: char_obj.pos[4][0] is a (x,y) tuple/list
                if (isinstance(char_obj.pos, (list, tuple)) and len(char_obj.pos) > 4 and
                    isinstance(char_obj.pos[4], (list, tuple)) and len(char_obj.pos[4]) > 0 and
                    isinstance(char_obj.pos[4][0], (list, tuple)) and len(char_obj.pos[4][0]) > index):
                    default_val = float(char_obj.pos[4][0][index])
            except (TypeError, ValueError): # IndexError implicitly handled by len checks
                _mod_print(f"Warning: Could not parse default pos component {index} from char_obj.pos. Using {default_val}.")
                pass # Silently use default_val if structure is not as expected or conversion fails
        return default_val

    def get_character_x_api(character_tag):
        char_obj = _get_char_obj_api(character_tag)
        if char_obj:
            default_x = _get_char_default_pos_component(char_obj, 0)
            return getattr(char_obj, 'mod_x', default_x)
        return 0.0

    def get_character_y_api(character_tag):
        char_obj = _get_char_obj_api(character_tag)
        if char_obj:
            default_y = _get_char_default_pos_component(char_obj, 1)
            return getattr(char_obj, 'mod_y', default_y)
        return 0.0

    def set_character_x_api(character_tag, value):
        char_obj = _get_char_obj_api(character_tag)
        if char_obj:
            try:
                char_obj.mod_x = float(value)
                # _mod_print(f"Note: setCharacterX for '{character_tag}' requires Game.py drawCharacters to use 'char_obj.mod_x'.")
                return True
            except ValueError:
                _mod_print(f"Warning: Invalid value '{value}' for setCharacterX. Must be a number.")
                return False
        return False

    def set_character_y_api(character_tag, value):
        char_obj = _get_char_obj_api(character_tag)
        if char_obj:
            try:
                char_obj.mod_y = float(value)
                # _mod_print(f"Note: setCharacterY for '{character_tag}' requires Game.py drawCharacters to use 'char_obj.mod_y'.")
                return True
            except ValueError:
                _mod_print(f"Warning: Invalid value '{value}' for setCharacterY. Must be a number.")
                return False
        return False

    # --- Game Stats ---
    def get_score_api(): return game_context.get('score', 0)
    def add_score_api(value): game_context['score'] = game_context.get('score', 0) + int(value)
    def set_score_api(value): game_context['score'] = int(value)

    def get_misses_api(): return game_context.get('misses', 0)
    def add_misses_api(value): game_context['misses'] = game_context.get('misses', 0) + int(value)
    def set_misses_api(value): game_context['misses'] = int(value)

    def get_hits_api(): return game_context.get('hits', 0)
    def add_hits_api(value): game_context['hits'] = game_context.get('hits', 0) + int(value)
    def set_hits_api(value): game_context['hits'] = int(value)

    def get_health_api():
        return game_context.get('health', HEALTH_API_SCALING_FACTOR) / HEALTH_API_SCALING_FACTOR

    def add_health_api(value):
        current_health_100 = game_context.get('health', HEALTH_API_SCALING_FACTOR)
        change_100 = float(value) * HEALTH_API_SCALING_FACTOR
        game_context['health'] = builtins.min(builtins.max(current_health_100 + change_100, 0), 100)

    def set_health_api(value=1.0):
        game_context['health'] = builtins.min(builtins.max(float(value) * HEALTH_API_SCALING_FACTOR, 0), 100)


    # --- Prepare execution environment for the mod script ---
    mod_script_globals = {
        # Callbacks (will be overwritten if defined by mod in game_context)
        # These are defaults for the API function map, not for final_mod_functions directly.
        "onHit": emptyfunc, "onMiss": emptyfunc, "onKeyPress": emptyfunc,
        "onUpdate": emptyfunc, "onBeat": emptyfunc, "onStep": emptyfunc,
        "onSongStart": emptyfunc, "onSongEnd": emptyfunc, # This is for the game to call
        "onNoteCreation": emptyfunc, "init": None,
        "onSongWillEnd": emptyfunc, # Mod can define this, end_song_api will check game_context for it

        # API Functions
        "endSong": end_song_api,
        "getSongPosition": get_song_position_api,
        "restartSong": restart_song_api,
        "exitSong": exit_song_api,

        "makeLuaText": create_text_api, "create_text": create_text_api,
        "addLuaText": show_text_api, "show_text": show_text_api,
        "removeLuaText": hide_text_api, "hide_text": hide_text_api,
        "setTextString": set_text_string_api,
        "setTextSize": set_text_size_api,
        "setTextColor": set_text_color_api,
        "setTextFont": set_text_font_api,
        "setTextPosition": set_text_position_api,
        "getTextString": get_text_string_api,
        "luaTextExists": text_exists_api, "text_exists": text_exists_api,

        "cameraShake": camera_shake_api,
        "keyPressed": is_key_pressed_api,
        # "keyReleased": was_key_released_api, # Requires Game.py changes

        "getCharacterX": get_character_x_api, "getCharacterY": get_character_y_api,
        "setCharacterX": set_character_x_api, "setCharacterY": set_character_y_api,

        "getScore": get_score_api, "addScore": add_score_api, "setScore": set_score_api,
        "getMisses": get_misses_api, "addMisses": add_misses_api, "setMisses": set_misses_api,
        "getHits": get_hits_api, "addHits": add_hits_api, "setHits": set_hits_api,
        "getHealth": get_health_api, "addHealth": add_health_api, "setHealth": set_health_api,
        
        "math": __import__("math"), "random": __import__("random"),
        "str": str, "int": int, "float": float, "bool": bool, "list": list, "dict": dict, "tuple": tuple,
        "min": builtins.min, "max": builtins.max, "abs": builtins.abs, "round": round, "len": len,
        "print": _mod_print, # Use the custom, prefixed print
        # "game": game_context, # Direct access to game_context (use with caution, generally prefer APIs)
    }
    if game_context.get('pygame'): # Expose specific pygame modules/functions if available
        pg_data = game_context['pygame']
        mod_script_globals['pygame_display'] = pg_data.get('display')
        mod_script_globals['pygame_draw'] = pg_data.get('draw')
        mod_script_globals['pygame_transform'] = pg_data.get('transform')
        mod_script_globals['pygame_font_module'] = pg_data.get('font') # Renamed to avoid conflict if mod imports pygame.font
        mod_script_globals['PygameRect'] = pg_data.get('Rect') # Capitalized to indicate class

    # Execute the modchart code
    # Functions and global variables defined by the mod script will end up in `game_context` (locals).
    try:
        sandboxed_exec(code, globals=mod_script_globals, locals=game_context)
    except Exception as e:
        # Error already printed by sandboxed_exec, or SyntaxError from check_modchart
        _mod_print(f"Critical error executing modchart code. Mod will not run. Error: {type(e).__name__}: {e}")
        return create_generic_modchart_funcs() # Return default functions

    # Extract the callback functions that might have been defined/overridden by the modchart.
    # These will be in `game_context` as it was the `locals` dict for `sandboxed_exec`.
    final_mod_functions = create_generic_modchart_funcs() # Start with defaults
    for cb_name in final_mod_functions:
        if cb_name in game_context and callable(game_context[cb_name]):
            final_mod_functions[cb_name] = game_context[cb_name]
        elif cb_name in game_context: # Defined but not callable
             _mod_print(f"Warning: Mod defined '{cb_name}' but it is not a callable function. Using default.")


    # Call the mod's init function if it was defined and is callable
    # `final_mod_functions["init"]` will be the mod's init or None (the default)
    if final_mod_functions["init"] and final_mod_functions["init"] is not None: # Ensure it's not the default None
        try:
            final_mod_functions["init"]()
        except Exception as e:
            _mod_print(f"Error in modchart init() function: {type(e).__name__}: {e}")

    return final_mod_functions
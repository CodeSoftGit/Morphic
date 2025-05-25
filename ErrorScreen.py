import pygame
import pyperclip
import webbrowser
import sys
import traceback
import os
import time

def asset_path_handler(relative_path):
    base_dir = os.path.dirname(sys.argv[0])
    return os.path.join(base_dir, *relative_path.split('/'))

GITHUB_ISSUES_URL = "https://github.com/CodeSoftGit/Morphic/issues"
COLOR_BACKGROUND = (45, 45, 45)
COLOR_OVERLAY = (0, 0, 0, 120)
COLOR_TEXT_PRIMARY = (230, 230, 230)
COLOR_TEXT_HEADER = (255, 255, 255)
COLOR_ERROR_MESSAGE = (220, 220, 220)
COLOR_BUTTON_NORMAL = (180, 180, 180)
COLOR_BUTTON_HOVER = (200, 200, 200)
COLOR_BUTTON_TEXT = (10, 10, 10)
COLOR_STATUS = (80, 200, 120)

def show_exception_screen(screen, exception_obj, tb_str, game_version, pg_module, clock):
    if pg_module.mixer.get_init():
        pg_module.mixer.stop()
        pg_module.mixer.music.stop()

    SCREEN_WIDTH = screen.get_width()
    SCREEN_HEIGHT = screen.get_height()

    try:
        font_header = pg_module.font.SysFont(None, 80)
        font_title = pg_module.font.SysFont(None, 48)
        font_body = pg_module.font.SysFont(None, 32)
        font_error_desc = pg_module.font.SysFont(None, 28)
        font_button = pg_module.font.SysFont(None, 30)
        font_version = pg_module.font.SysFont(None, 24)
        font_status = pg_module.font.SysFont(None, 26)
    except Exception as font_e:
        print(f"Critical error: Pygame font module failed in exception handler: {font_e}", file=sys.stderr)
        return

    bf_miss_img = None
    try:
        bf_miss_img_orig = pg_module.image.load(asset_path_handler('assets/Images/bfmiss.png')).convert_alpha()
        img_h = SCREEN_HEIGHT * 0.3
        img_w = int(bf_miss_img_orig.get_width() * (img_h / bf_miss_img_orig.get_height()))
        if img_w > 0 and img_h > 0:
            bf_miss_img = pg_module.transform.smoothscale(bf_miss_img_orig, (int(img_w), int(img_h)))
        bf_miss_rect = bf_miss_img.get_rect(bottomright=(SCREEN_WIDTH - 40, SCREEN_HEIGHT - 70))
    except Exception as img_e:
        print(f"Could not load or scale bfmiss.png for error screen: {img_e}", file=sys.stderr)
        bf_miss_img = None

    sad_face_text = ":("
    title_text_content = "Oops! Something went wrong."
    desc_lines_content = [
        "We're sorry! The game encountered an unexpected issue.",
        "You can help us fix it by reporting the problem below.",
    ]
    error_message_display = f"{type(exception_obj).__name__}: {str(exception_obj)}"
    trace_info_content = "(Stack trace hidden. Click to show/hide details.)"
    version_display_text = f"Game Version {game_version}"

    button_width, button_height = 180, 45
    button_padding_horizontal = 20
    button_padding_vertical = 15

    top_buttons_y = SCREEN_HEIGHT * 0.65
    total_top_width = button_width * 2 + button_padding_horizontal
    start_x_top = (SCREEN_WIDTH - total_top_width) / 2

    copy_button_rect = pg_module.Rect(start_x_top, top_buttons_y, button_width, button_height)
    exit_button_rect = pg_module.Rect(start_x_top + button_width + button_padding_horizontal, top_buttons_y, button_width, button_height)
    report_button_rect = pg_module.Rect(0, 0, button_width, button_height)
    report_button_rect.centerx = SCREEN_WIDTH / 2
    report_button_rect.top = copy_button_rect.bottom + button_padding_vertical

    clipboard_content = f"Game Version: {game_version}\n"
    clipboard_content += f"Error: {type(exception_obj).__name__}: {str(exception_obj)}\n\n"
    clipboard_content += "Traceback:\n"
    clipboard_content += tb_str

    def render_text_surface(font, text, color, antialias=True):
        return font.render(text, antialias, color)

    sad_face_surf = render_text_surface(font_header, sad_face_text, COLOR_TEXT_HEADER)
    title_surf = render_text_surface(font_title, title_text_content, COLOR_TEXT_PRIMARY)
    desc_surfs = [render_text_surface(font_body, line, COLOR_TEXT_PRIMARY) for line in desc_lines_content]

    # Error message wrapping
    error_message_lines = []
    max_text_width = SCREEN_WIDTH * 0.8
    words = error_message_display.split(' ')
    current_line = ""
    for word in words:
        if font_error_desc.size(current_line + word + " ")[0] <= max_text_width:
            current_line += word + " "
        else:
            error_message_lines.append(current_line.strip())
            current_line = word + " "
    if current_line:
        error_message_lines.append(current_line.strip())
    error_surfs = [render_text_surface(font_error_desc, line, COLOR_ERROR_MESSAGE) for line in error_message_lines]

    trace_info_surf = render_text_surface(font_error_desc, trace_info_content, COLOR_TEXT_PRIMARY)
    version_surf = render_text_surface(font_version, version_display_text, COLOR_TEXT_PRIMARY)

    # Status message
    status_message = ""
    status_time = 0

    # Stack trace toggle
    show_trace = False
    trace_rect = None
    trace_surfs = []
    for line in tb_str.splitlines():
        trace_surfs.append(render_text_surface(font_error_desc, line, (180, 180, 255)))

    running = True
    while running:
        mouse_pos = pg_module.mouse.get_pos()
        mouse_hover = None

        for event in pg_module.event.get():
            if event.type == pg_module.QUIT:
                running = False
            if event.type == pg_module.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if copy_button_rect.collidepoint(mouse_pos):
                        try:
                            pyperclip.copy(clipboard_content)
                            status_message = "Copied error details to clipboard!"
                            status_time = time.time()
                        except pyperclip.PyperclipException as clip_err:
                            status_message = "Could not copy to clipboard."
                            status_time = time.time()
                    elif exit_button_rect.collidepoint(mouse_pos):
                        running = False
                    elif report_button_rect.collidepoint(mouse_pos):
                        try:
                            webbrowser.open(GITHUB_ISSUES_URL)
                            status_message = "Opening bug report page..."
                            status_time = time.time()
                        except Exception:
                            status_message = "Could not open browser."
                            status_time = time.time()
                    elif trace_rect and trace_rect.collidepoint(mouse_pos):
                        show_trace = not show_trace

        # --- Drawing ---
        screen.fill(COLOR_BACKGROUND)
        # Overlay for focus
        overlay = pg_module.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pg_module.SRCALPHA)
        overlay.fill(COLOR_OVERLAY)
        screen.blit(overlay, (0, 0))

        # Sad face and Title
        screen.blit(sad_face_surf, (SCREEN_WIDTH * 0.05, SCREEN_HEIGHT * 0.1))
        screen.blit(title_surf, (SCREEN_WIDTH * 0.05 + sad_face_surf.get_width() + 20, SCREEN_HEIGHT * 0.12))

        # Description
        current_y = SCREEN_HEIGHT * 0.25
        for surf in desc_surfs:
            screen.blit(surf, (SCREEN_WIDTH * 0.07, current_y))
            current_y += surf.get_height() + 5

        # Error Message
        current_y += 20
        for surf in error_surfs:
            screen.blit(surf, (SCREEN_WIDTH * 0.07, current_y))
            current_y += surf.get_height() + 2

        # Trace Info (clickable)
        trace_rect = trace_info_surf.get_rect(topleft=(SCREEN_WIDTH * 0.07, current_y + 10))
        screen.blit(trace_info_surf, trace_rect.topleft)
        if trace_rect.collidepoint(mouse_pos):
            mouse_hover = "Click to show/hide stack trace"

        # Stack trace (expand/collapse)
        if show_trace:
            y = trace_rect.bottom + 5
            for surf in trace_surfs:
                screen.blit(surf, (SCREEN_WIDTH * 0.07 + 20, y))
                y += surf.get_height() + 1

        # Version Text (bottom-left)
        screen.blit(version_surf, (20, SCREEN_HEIGHT - version_surf.get_height() - 10))

        # Buttons
        buttons_data = [
            ("Copy", copy_button_rect, "Copy error details"),
            ("Exit", exit_button_rect, "Close the game"),
            ("Report Bug", report_button_rect, "Open bug report page"),
        ]
        for text, rect, tooltip in buttons_data:
            button_color = COLOR_BUTTON_HOVER if rect.collidepoint(mouse_pos) else COLOR_BUTTON_NORMAL
            pg_module.draw.rect(screen, button_color, rect, border_radius=8)
            pg_module.draw.rect(screen, (120, 120, 120), rect, 2, border_radius=8)
            text_surf = render_text_surface(font_button, text, COLOR_BUTTON_TEXT)
            text_rect = text_surf.get_rect(center=rect.center)
            screen.blit(text_surf, text_rect)
            if rect.collidepoint(mouse_pos):
                mouse_hover = tooltip

        # Character Image
        if bf_miss_img:
            screen.blit(bf_miss_img, bf_miss_rect)

        # Status message (fade after 2 seconds)
        if status_message and time.time() - status_time < 2.5:
            status_surf = render_text_surface(font_status, status_message, COLOR_STATUS)
            status_rect = status_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT * 0.6))
            screen.blit(status_surf, status_rect)
        elif status_message:
            status_message = ""

        # Tooltip
        if mouse_hover:
            tooltip_surf = render_text_surface(font_version, mouse_hover, (255, 255, 180))
            mx, my = mouse_pos
            screen.blit(tooltip_surf, (mx + 12, my + 8))

        pg_module.display.flip()
        clock.tick(30)

if __name__ == "__main__":
    pg_module = pygame
    pg_module.init()
    screen = pg_module.display.set_mode((800, 600))
    clock = pg_module.time.Clock()
    show_exception_screen(
        screen,
        Exception("Test exception"),
        "Traceback (most recent call last):\n  File \"<stdin>\", line 1, in <module>\nException: Test exception",
        "1.0.0",
        pg_module,
        clock
    )
    pg_module.quit()
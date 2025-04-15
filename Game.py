from pygame import *
import json
from random import *
import time as Time
import sys
import copy
import os
import ModchartCore
from DevTools import DevTools
import builtins

# Add these global variables
Inst = None
Vocals = None
chart = None
misses = 0
health = 50
BG = None
opponentAnimation = ["Up", -10]
playerAnimation = ["Up", -10]
hasPlayedMicDrop = False
combo = 0
modchart_functions = None  # Add this to store modchart functions
autoplayerEnabled = False


def Main_game(musicName, speed, playAs, noDying, arrowSkinID, keybinds, downscroll, render_scene=True, modchart=True, difficulty=None):
    global Inst
    global Vocals
    global chart
    global misses
    global health
    global BG
    global opponentAnimation
    global playerAnimation
    global options
    global hasPlayedMicDrop
    global combo
    global modchart_functions
    global autoplayerEnabled
    
    print(difficulty)
    
    # Add this after other initializations (around line 79)
    # Initialize DevTools
    dev_tools = DevTools(sys.modules[__name__])  # Pass current module as game instance
    
    if not render_scene:
        modchart = False  # Disable modchart if render_scene is False to avoid errors
    
    # Add this after other global variables
    cached_surfaces = {}
    dirty_rects = []
    use_dirty_rects = True
    last_frame_time = 0
    
    autoplayerEnabled = False
    modchart_functions = ModchartCore.create_generic_modchart_funcs()
    
    misses = 0
    health = 50
    combo = 0
    keyPressed = []

    init()

    K_a = keybinds[0]
    K_s = keybinds[1]
    K_w = keybinds[2]
    K_d = keybinds[3]
    K_LEFT = keybinds[4]
    K_DOWN = keybinds[5]
    K_UP = keybinds[6]
    K_RIGHT = keybinds[7]

    # region loading
    # region screen and loading screen
    screen = display.set_mode((0, 0), FULLSCREEN)
    mouse.set_visible(False)
    middleScreen = (display.Info().current_w // 2, display.Info().current_h // 2)

    def loadingscreen(progress):
        screen.fill((0, 0, 0))
        temp = font.Font(os.path.join("assets", "vcr.ttf"), 100).render("Loading...", 1, (255, 255, 255))
        temp1 = temp.get_rect()
        temp1.center = (middleScreen[0], middleScreen[1])
        screen.blit(temp, temp1)

        draw.line(screen, (255, 255, 255), (95, display.Info().current_h - 95),
                  (display.Info().current_w - 95, display.Info().current_h - 95), 3)
        draw.line(screen, (255, 255, 255), (95, display.Info().current_h - 155),
                  (display.Info().current_w - 95, display.Info().current_h - 155), 3)
        draw.line(screen, (255, 255, 255), (95, display.Info().current_h - 95), (95, display.Info().current_h - 155), 3)
        draw.line(screen, (255, 255, 255), (display.Info().current_w - 95, display.Info().current_h - 95),
                  (display.Info().current_w - 95, display.Info().current_h - 155), 3)
        if progress > 0:
            temp = (display.Info().current_w - 200) / 3
            draw.rect(screen, (255, 255, 255), Rect(100, display.Info().current_h - 150, temp * progress, 50))

        display.flip()

    loadingscreen(0)
    # endregion

    # region variables
    sys.setrecursionlimit(1000000)
    useMustHitSection = False
    clock = time.Clock()
    if 690 >= display.Info().current_w - 690:
        singlePlayer = True
    else:
        singlePlayer = False

    fpsQuality = 100
    fpsList = []
    fpsTime = Time.time()

    accuracy = 0
    accuracyDisplayTime = 0
    showAccuracy = False
    accuracyIndicator = ""
    accuracyIndicatorTime = Time.time()
    accuracyPercentList = []

    Font40 = font.Font("assets\\vcr.ttf", 40)
    Font25 = font.Font("assets\\vcr.ttf", 25)

    longNotesChart = []

    bpm = 240 / 100

    opponentHitTimes = [-10 for k in range(4)]
    opponentAnimation = ["Up", -10]
    playerAnimation = ["Up", -10]

    try:
        modifications = json.load(open("assets\Music\{0}\songData.json".format(musicName)))["modifications"]
    except:
        modifications = []

    hasPlayedMicDrop = False
    # endregion

    keyPressed = []
    
    def handle_autoplayer(current_time):
        global playerAnimation, combo, health
        nonlocal keyPressed, accuracyPercentList
        
        if not autoplayerEnabled:
            return
            
        # Increased window size to ensure we never miss notes while still getting "sick" ratings
        perfect_window = 20  # ms around the perfect hit time
        
        # Key mapping for columns
        column_to_key = {
            "Left": K_a,
            "Down": K_s,
            "Up": K_w,
            "Right": K_d
        }
        
        # Track notes hit this frame to avoid duplicates
        hit_notes = []
        
        # Process all player notes in hit window
        for note in list(notesChart):  # Use list() to create a copy so we can safely remove items
            if note.side == "Player":
                time_diff = abs(note.pos - current_time * 1000)
                
                # Hit notes slightly early to ensure perfect timing
                if time_diff <= perfect_window:
                    # Simulate key press if not already pressed
                    key = column_to_key.get(note.column)
                    if key and key not in keyPressed:
                        keyPressed.append(key)
                    
                    # Record animation
                    playerAnimation = [note.column, current_time]
                    
                    # Perfect accuracy
                    accuracyPercentList.append(1)
                    health = builtins.min(100, health + 2.3)  # Ensure health doesn't exceed 100
                    combo += 1
                    
                    # Call onHit callback if it exists
                    if modchart_functions and modchart_functions["onHit"]:
                        try:
                            modchart_functions["onHit"](
                                note=note,
                                accuracy="0.0",
                                rating="sick",
                                combo=combo,
                                column=note.column,
                                currentTime=current_time
                            )
                        except Exception as e:
                            print(f"Error in autoplayer onHit callback: {e}")
                    
                    # Remove the note only if we haven't already hit it this frame
                    if note not in hit_notes:
                        hit_notes.append(note)
                        notesChart.remove(note)
        
        # Look ahead for upcoming notes to be ready for them
        upcoming_notes = []
        for note in notesChart:
            if note.side == "Player":
                # Identify notes coming soon (within next 100ms)
                time_till_note = note.pos - current_time * 1000
                if 0 < time_till_note < 100:
                    upcoming_notes.append((note.column, time_till_note))
        
        # Handle long notes - more aggressive approach to never miss them
        for noteGroup in list(longNotesChart):
            if noteGroup.canDealDamage and len(noteGroup.notes) > 0:
                active_long_note = False
                
                for longNote in list(noteGroup.notes):
                    if longNote.side == "Player":
                        time_diff = abs(longNote.pos - current_time * 1000)
                        
                        # Hit the long note segment if in range
                        if time_diff <= perfect_window:
                            key = column_to_key.get(longNote.column)
                            if key and key not in keyPressed:
                                keyPressed.append(key)
                            
                            playerAnimation = [longNote.column, current_time]
                            
                            # Keep key pressed for long notes
                            active_long_note = True
                            noteGroup.notes.remove(longNote)
                
                # If no active long note segments, we can release the key
                if not active_long_note:
                    for column, key in column_to_key.items():
                        if key in keyPressed:
                            keyPressed.remove(key)
        
        # Clean up keyPressed for notes that have been hit
        # Only remove keys that aren't needed for upcoming or long notes
        for column, key in column_to_key.items():
            if key in keyPressed:
                # Check if we need to keep this key pressed for upcoming/long notes
                keep_pressed = False
                
                # Check upcoming notes
                for col, _ in upcoming_notes:
                    if col == column:
                        keep_pressed = True
                        break
                        
                # Check long notes
                for noteGroup in longNotesChart:
                    if len(noteGroup.notes) > 0:
                        for longNote in noteGroup.notes:
                            if longNote.side == "Player" and longNote.column == column:
                                time_diff = abs(longNote.pos - current_time * 1000)
                                if time_diff < 200:  # Keep key pressed if long note is coming soon
                                    keep_pressed = True
                                    break
                
                # If we don't need this key anymore, release it
                if not keep_pressed:
                    keyPressed.remove(key)
    
    # region images loading
    # region load images
    import xml.etree.ElementTree as ET

    def getAttibuteRect(element):
        return Rect(int(element.attrib["x"]), int(element.attrib["y"]), int(element.attrib["width"]), int(element.attrib["height"]))

    def loadArrows(skinName):
        skinData = json.load(open(os.path.join("assets", "Images", "ArrowStyles", skinName, "arrowData.json")))
        XMLPath = os.path.join("assets", "Images", "ArrowStyles", skinName, "arrowSkin.xml")
        XMLFile = ET.parse(XMLPath).getroot()
        imagePath = os.path.join("assets", "Images", "ArrowStyles", skinName, "arrowSkin.png")
        skinImage = image.load(imagePath).convert_alpha()
        result = {"arrowsSkin": [None for k in range(4)], "pressedArrowsSkins": [None for k in range(4)], "greyArrow": [None for k in range(4)], "longNotesImg": [None for k in range(4)], "longNotesEnd": [None for k in range(4)]}
        tempArrows = ["purple alone0000", "blue alone0000", "green alone0000", "red alone0000"]
        tempPressed = ["left press0000", "down press0000", "up press0000", "right press0000"]
        tempGrey = ["arrowLEFT0000", "arrowDOWN0000", "arrowUP0000", "arrowRIGHT0000"]
        tempLong = ["purple hold0000", "blue hold0000", "green hold0000", "red hold0000"]
        tempLongEnd = ["purple tail0000", "blue tail0000", "green tail0000", "red tail0000"]
        for data in XMLFile:
            if data.attrib["name"] in tempArrows:
                try:
                    temp = skinData["Size"]["arrowsSkin"][tempArrows.index(data.attrib["name"])]
                except:
                    temp = 1
                tempImage = skinImage.subsurface(getAttibuteRect(data)).convert_alpha()
                tempImage = transform.scale(tempImage, (tempImage.get_width() * temp, tempImage.get_height() * temp))
                result["arrowsSkin"][tempArrows.index(data.attrib["name"])] = tempImage
            if data.attrib["name"] in tempPressed:
                try:
                    temp = skinData["Size"]["pressedArrowsSkin"][tempPressed.index(data.attrib["name"])]
                except:
                    temp = 1
                tempImage = skinImage.subsurface(getAttibuteRect(data)).convert_alpha()
                tempImage = transform.scale(tempImage, (tempImage.get_width() * temp, tempImage.get_height() * temp))
                result["pressedArrowsSkins"][tempPressed.index(data.attrib["name"])] = tempImage
            if data.attrib["name"] in tempGrey:
                try:
                    temp = skinData["Size"]["greyArrow"][tempGrey.index(data.attrib["name"])]
                except:
                    temp = 1
                tempImage = skinImage.subsurface(getAttibuteRect(data)).convert_alpha()
                tempImage = transform.scale(tempImage, (tempImage.get_width() * temp, tempImage.get_height() * temp))
                result["greyArrow"][tempGrey.index(data.attrib["name"])] = tempImage
            if data.attrib["name"] in tempLong:
                try:
                    temp = skinData["Size"]["greyArrow"][tempLong.index(data.attrib["name"])]
                except:
                    temp = 1
                tempImage = skinImage.subsurface(getAttibuteRect(data)).convert_alpha()
                tempImage = transform.scale(tempImage, (tempImage.get_width() * temp, tempImage.get_height() * temp))
                result["longNotesImg"][tempLong.index(data.attrib["name"])] = tempImage
            if data.attrib["name"] in tempLongEnd:
                try:
                    temp = skinData["Size"]["greyArrow"][tempLongEnd.index(data.attrib["name"])]
                except:
                    temp = 1
                tempImage = skinImage.subsurface(getAttibuteRect(data)).convert_alpha()
                tempImage = transform.scale(tempImage, (tempImage.get_width() * temp, tempImage.get_height() * temp))
                result["longNotesEnd"][tempLongEnd.index(data.attrib["name"])] = tempImage
        return result
    
    # Load arrows using the new function
    arrowsData = loadArrows(arrowSkinID)
    arrowsSkins = arrowsData["arrowsSkin"]
    pressedArrowsSkins = arrowsData["pressedArrowsSkins"]
    greyArrow = arrowsData["greyArrow"]
    longNotesImg = arrowsData["longNotesImg"]
    longNotesEnd = arrowsData["longNotesEnd"]
    
    # If downscroll is enabled, flip the long notes
    if downscroll:
        for k in range(len(longNotesImg)):
            longNotesImg[k] = transform.flip(longNotesImg[k], False, True)
        for k in range(len(longNotesEnd)):
            longNotesEnd[k] = transform.flip(longNotesEnd[k], False, True)

    accuracyIndicatorImages = [
        transform.scale(image.load(os.path.join("assets", "Images", "Accuracy indicator", "sick.png")).convert_alpha(), (225, 100)),
        transform.scale(image.load(os.path.join("assets", "Images", "Accuracy indicator", "good.png")).convert_alpha(), (225, 100)),
        transform.scale(image.load(os.path.join("assets", "Images", "Accuracy indicator", "bad.png")).convert_alpha(), (225, 100)),
        transform.scale(image.load(os.path.join("assets", "Images", "Accuracy indicator", "shit.png")).convert_alpha(), (225, 100))
    ]

    try:
        backgroundName = json.load(open(os.path.join("assets", "Music", musicName, "songData.json")))["stage"]
    except:
        backgroundName = "None"

    if backgroundName != "None":
        Background = []
        for k in range(
                json.load(open("assets" + os.path.sep + "Images" + os.path.sep + "Backgrounds" + os.path.sep + "{0}".format(backgroundName) + os.path.sep + "stageData.json"))["numFrames"]):
            if not display.Info().current_w / display.Info().current_h == 1920 / 1080:
                Background.append(transform.scale(
                    image.load("assets" + os.path.sep + "Images" + os.path.sep + "Backgrounds" + os.path.sep + "{0}".format(backgroundName) + os.path.sep + "Background{1}.png".format(backgroundName, k)),
                    (1920, 1080)).convert_alpha())
            else:
                Background.append(transform.scale(
                    image.load("assets" + os.path.sep + "Images" + os.path.sep + "Backgrounds" + os.path.sep + "{0}".format(backgroundName) + os.path.sep + "Background{1}.png".format(backgroundName, k)),
                    (display.Info().current_w, display.Info().current_h)).convert_alpha())
    else:
        Background = [Font40.render("", 1, (255, 255, 255))]
    BGrect = Background[0].get_rect()
    BGrect.center = (middleScreen[0], middleScreen[1])

    BFdead = image.load("assets" + os.path.sep + "Images" + os.path.sep + "Death screen" + os.path.sep + "BF dead.png").convert_alpha()

    # endregion

    # region create image rect
    accuracyIndicatorRect = accuracyIndicatorImages[0].get_rect()
    accuracyIndicatorRect.center = (middleScreen[0], middleScreen[1] - 75)

    arrowRect = arrowsSkins[0].get_rect()

    deathScreenRect = BFdead.get_rect()
    deathScreenRect.midbottom = (middleScreen[0], display.Info().current_h - 50)
    # endregion

    musicList = []
    for folder in os.listdir("assets\Music"):
        if os.path.isdir(os.path.join("assets\Music", folder)):
            musicList.append(folder)

    loadingscreen(1)

    # endregion

    # region music and chart loading
    deathScreenMusic = mixer.Sound(os.path.join("assets", "Images", "Death screen", "gameOver.ogg"))
    deathScreenMusicEnd = mixer.Sound(os.path.join("assets", "Images", "Death screen", "gameOverEnd.ogg"))
    deathScreenMusicStart = mixer.Sound(os.path.join("assets", "Images", "Death screen", "micDrop.ogg"))

    def open_file(music, difficulty=difficulty):
        global Inst
        global Vocals
        global chart
        global modchart_functions
        
        print(difficulty)
        
        if difficulty is None:
            difficulty = ""
            filename = "chart"
        else:
            difficulty = "-" + difficulty
            filename = music
        
        Inst = mixer.Sound(os.path.join("assets", "Music", music, "Inst.ogg"))
        Vocals = mixer.Sound(os.path.join("assets", "Music", music, "Voices.ogg"))
        
        try:
            chart_path = os.path.join("assets", "Music", music, f"{filename}{difficulty}.json")
            chart_data = json.load(open(chart_path))
            
            # Support both old format (notes array) and new format (notes.normal array)
            if "song" in chart_data:
                if "player1" and "player2" in chart_data["song"]:
                    player1 = chart_data["song"]["player1"]
                    player2 = chart_data["song"]["player2"]
                if "notes" in chart_data["song"]:
                    if isinstance(chart_data["song"]["notes"], dict) and "normal" in chart_data["song"]["notes"]:
                        # New format: chart_data["song"]["notes"]["normal"]
                        chart = chart_data["song"]["notes"]["normal"]
                        print("Using new chart format (notes.normal)")
                    else:
                        # Old format: chart_data["song"]["notes"]
                        chart = chart_data["song"]["notes"]
                        print("Using old chart format")
            else:
                # Handle legacy format that needed conversion
                chart = {"song": chart_data}
                json.dump(chart, open(f"assets\Music\{music}\{filename}{difficulty}.json", "w"))
                
                # Check if the converted format uses the new structure
                if isinstance(chart["song"]["notes"], dict) and "normal" in chart["song"]["notes"]:
                    chart = chart["song"]["notes"]["normal"]
                else:
                    chart = chart["song"]["notes"]
        except Exception as e:
            print(f"Error loading chart: {e}")
            chart = []  # Fallback to empty chart
            
        try:
            # Try to get BPM from the chart file
            bpm = json.load(open(f"assets\Music\{music}\{filename}{difficulty}.json"))["song"]["bpm"]
            bpm = 240 / bpm
        except:
            bpm = 240 / 100
                
        # Initialize modchart_functions to None first
        modchart_functions = ModchartCore.create_generic_modchart_funcs()
        
        if modchart is False:
            print("Modchart disabled")
            return
        
        # Load modchart if it exists
        modchart_path = os.path.join("assets", "Music", music, "modchart.py")
        if os.path.exists(modchart_path):
            try:
                with open(modchart_path, "r") as f:
                    modchart_code = f.read()
                    
                if ModchartCore.check_modchart(modchart_code):
                    print(f"Loading modchart for {music}")
                    # Initialize with default empty callbacks
                    modchart_functions = ModchartCore.create_generic_modchart_funcs()
                    # Add the modchart code to the dictionary
                    modchart_functions["code"] = modchart_code
                else:
                    print(f"Modchart for {music} failed validation, running without modchart")
            except Exception as e:
                print(f"Error loading modchart: {e}")
                print("Running without modchart")
        else:
            print(f"No modchart found for {music}, running standard game")

    def play(music=False):
        if not music:
            open_file(musicList[randint(0, len(musicList) - 1)])
        else:
            open_file(music)

    play(musicName)

    temp1 = Inst.get_length()
    temp2 = Vocals.get_length()
    if temp1 > temp2:
        musicLen = temp1
    else:
        musicLen = temp2

    loadingscreen(2)

    # endregion

    # region chart managment
    class Note:
        def __init__(self, pos, column, side, length, noteId):
            self.pos = pos
            self.column = column
            self.side = side
            self.length = length
            self.id = noteId

    class LongNote:
        def __init__(self, pos, column, side, isEnd):
            self.pos = pos
            self.column = column
            self.side = isEnd

    class LongNoteGroup:
        def __init__(self, groupId):
            self.id = groupId
            self.notes = []
            self.size = 0
            self.canDealDamage = True

        def setSize(self):
            self.notes.remove(self.notes[0])
            self.size = len(self.notes)

    # region tests if chart uses mustHitSection
    notesChart = []

    for section in chart:
        if not section["mustHitSection"]:
            useMustHitSection = True
    # endregion

    # region create notes
    # Column meaning:
    #   If not useMustHitSection:
    #       0 = player left
    #       1 = player down
    #       2 = player up
    #       3 = player right
    #       4 = opponent down
    #       5 = opponent left
    #       6 = opponent up
    #       7 = opponent right
    #
    #   If useMustHitSection:
    #       If mustHit:
    #           0 = player left
    #           1 = player down
    #           2 = player up
    #           3 = player right
    #           4 = opponent left
    #           5 = opponent down
    #           6 = opponent up
    #           7 = opponent right
    #       If not mustHit:
    #           0 = opponent down
    #           1 = opponent left
    #           2 = opponent up
    #           3 = opponent right
    #           4 = player left
    #           5 = player down
    #           6 = player up
    #           7 = player right

    if playAs == "Player":
        tempPlayAs = ["Player", "Opponent"]
    else:
        tempPlayAs = ["Opponent", "Player"]

    tempNoteId = 0
    for section in chart:
        if not useMustHitSection:
            tempMustHit = True
        else:
            tempMustHit = section["mustHitSection"]
        for note in section["sectionNotes"]:
            tempUser = ""
            tempDirection = ""
            if type(note[2]) == int or type(note[2]) == float:
                if not useMustHitSection:
                    if 3 >= note[1] >= 0:
                        tempUser = tempPlayAs[0]
                    elif 7 >= note[1] >= 4:
                        tempUser = tempPlayAs[1]
                    if note[1] == 0 or note[1] == 5:
                        tempDirection = "Left"
                    if note[1] == 1 or note[1] == 4:
                        tempDirection = "Down"
                    if note[1] == 2 or note[1] == 6:
                        tempDirection = "Up"
                    if note[1] == 3 or note[1] == 7:
                        tempDirection = "Right"
                if useMustHitSection:
                    if tempMustHit:
                        if 3 >= note[1] >= 0:
                            tempUser = tempPlayAs[0]
                        if 7 >= note[1] >= 4:
                            tempUser = tempPlayAs[1]
                        if note[1] == 0 or note[1] == 4:
                            tempDirection = "Left"
                        if note[1] == 1 or note[1] == 5:
                            tempDirection = "Down"
                        if note[1] == 2 or note[1] == 6:
                            tempDirection = "Up"
                        if note[1] == 3 or note[1] == 7:
                            tempDirection = "Right"
                    if not tempMustHit:
                        if 3 >= note[1] >= 0:
                            tempUser = tempPlayAs[1]
                        if 7 >= note[1] >= 4:
                            tempUser = tempPlayAs[0]
                        if note[1] == 1 or note[1] == 5:
                            tempDirection = "Down"
                        if note[1] == 0 or note[1] == 4:
                            tempDirection = "Left"
                        if note[1] == 2 or note[1] == 6:
                            tempDirection = "Up"
                        if note[1] == 3 or note[1] == 7:
                            tempDirection = "Right"
                # After creating a new note but before adding it to notesChart
                tempNote = Note(note[0], tempDirection, tempUser, note[2], tempNoteId)

                # Call onNoteCreation callback
                if modchart_functions and modchart_functions["onNoteCreation"]:
                    try:
                        modchart_functions["onNoteCreation"](note=tempNote)
                    except Exception as e:
                        print(f"Error in onNoteCreation callback: {e}")
                        
                notesChart.append(tempNote)
                tempNoteId += 1
    # endregion

    # region sort notes and create long notes
    notesChart.sort(key=lambda s: s.pos)

    longNotesLen = 42 // speed
    for note in notesChart:
        if note.length >= longNotesLen > 0 and int(round(note.length // longNotesLen)):
            tempGroup = LongNoteGroup(note.id)
            for k in range(1, int(round(note.length // longNotesLen))):
                tempGroup.notes.append(LongNote(note.pos + k * longNotesLen, note.column, note.side, False))
            tempGroup.notes.append(
                LongNote(note.pos + (note.length // longNotesLen) * longNotesLen, note.column, note.side, True))
            tempGroup.setSize()
            longNotesChart.append(tempGroup)

    longNotesChart.sort(key=lambda s: s.id)
    for element in longNotesChart:
        element.notes.sort(key=lambda s: s.pos)

    loadingscreen(3)

    # endregion
    # endregion

# region characters
    def getNfirstCharacters(text, n):
        result = ""
        if n < len(text):
            for k in range(n):
                result = "{0}{1}".format(result, text[k])
            return result
        else:
            return text

    def getNlastCharacters(text, n):
        result = ""
        for k in range(n):
            result = "{1}{0}".format(result, text[-k - 1])
        return result

    def getXmlData(characterName):
        XMLpath = os.path.join("assets", "Images", "Characters", characterName, "character.xml")
        characterImage = image.load(os.path.join("assets", "Images", "Characters", characterName, "character.png")).convert_alpha()
        XMLfile = ET.parse(XMLpath).getroot()
        result = [[] for _ in range(5)]
        for data in XMLfile:
            name = data.attrib["name"]
            tempResult = ""
            for k in range(len(name)):
                if name[k] == "_":
                    tempResult = "{0}{1}".format(tempResult, " NOTE ")
                else:
                    tempResult = "{0}{1}".format(tempResult, name[k].upper())
            data.attrib["name"] = tempResult
        for data in XMLfile:
            name = data.attrib["name"]
            tempResult = ""
            temp = False
            for k in range(len(name)):
                if temp:
                    tempResult = "{0}{1}".format(tempResult, name[k])
                if name[k] == " ":
                    temp = True
            if tempResult != "":
                data.attrib["name"] = tempResult
        for data in XMLfile:
            name = data.attrib["name"]
            if getNfirstCharacters(name, 9) == "NOTE IDLE" or getNfirstCharacters(name, 4) == "IDLE":
                name = "idle dance{0}".format(getNlastCharacters(name, 4))
            data.attrib["name"] = name
        for data in XMLfile:
            name = data.attrib["name"]
            if getNfirstCharacters(name, 10) == "IDLE DANCE":
                data.attrib["name"] = name.lower()
        for data in XMLfile:
            name = data.attrib["name"]
            if getNfirstCharacters(name, 2) == "UP":
                name = "NOTE UP{0}".format(getNlastCharacters(name, 4))
            if getNfirstCharacters(name, 4) == "DOWN":
                name = "NOTE DOWN{0}".format(getNlastCharacters(name, 4))
            if getNfirstCharacters(name, 4) == "LEFT":
                name = "NOTE LEFT{0}".format(getNlastCharacters(name, 4))
            if getNfirstCharacters(name, 5) == "RIGHT":
                name = "NOTE RIGHT{0}".format(getNlastCharacters(name, 4))
            data.attrib["name"] = name
        for data in XMLfile:
            if getNfirstCharacters(data.attrib["name"], 9) == "NOTE LEFT" and len(data.attrib["name"]) == 13:
                result[0].append(characterImage.subsurface(getAttibuteRect(data)))
            if getNfirstCharacters(data.attrib["name"], 9) == "NOTE DOWN" and len(data.attrib["name"]) == 13:
                result[1].append(characterImage.subsurface(getAttibuteRect(data)))
            if getNfirstCharacters(data.attrib["name"], 7) == "NOTE UP" and len(data.attrib["name"]) == 11:
                result[2].append(characterImage.subsurface(getAttibuteRect(data)))
            if getNfirstCharacters(data.attrib["name"], 10) == "NOTE RIGHT" and len(data.attrib["name"]) == 14:
                result[3].append(characterImage.subsurface(getAttibuteRect(data)))
            if getNfirstCharacters(data.attrib["name"], 10) == "idle dance" and len(data.attrib["name"]) == 14:
                result[4].append(characterImage.subsurface(getAttibuteRect(data)))
        return result

    class Character:
        def __init__(self, name, characterNum, loadedFromModchart=False):
            if name != "None":
                if playAs == "Opponent":
                    if characterNum == 1:
                        temp = 2
                    else:
                        temp = 1
                else:
                    temp = characterNum
                # Load size and texture
                if not loadedFromModchart:
                    self.size = \
                        json.load(open("assets" + os.path.sep + "Music" + os.path.sep + "{0}".format(
                            musicName) + os.path.sep + "songData.json"))["character{0}".format(temp)][
                            "size"]
                else:
                    self.size = json.load(open("assets" + os.path.sep + "Music" + os.path.sep + "{0}".format(
                        musicName) + os.path.sep + "songData.json"))["modchartCharacters"][name]["size"]
                # Parse XML file and get texture based on XML indications
                self.texture = getXmlData(name)
                # Get offset
                try:
                    self.offset = json.load(open(
                        "assets" + os.path.sep + "Images" + os.path.sep + "Characters" + os.path.sep + "{0}".format(
                            name) + os.path.sep + "offset.json"))["offset"]
                except:
                    self.offset = [[] for _ in range(5)]
                    for k in range(5):
                        for x in range(len(self.texture[k])):
                            self.offset[k].append([0, 0])
                try:
                    textureDirection = json.load(open(
                        "assets" + os.path.sep + "Images" + os.path.sep + "Characters" + os.path.sep + "{0}".format(
                            name) + os.path.sep + "characterData.json"))["texture_direction"]
                except:
                    textureDirection = "Right"
                # Multiply offset by size
                for k in range(len(self.offset)):
                    for x in range(len(self.offset[k])):
                        self.offset[k][x][0] *= self.size[k][0]
                        self.offset[k][x][1] *= self.size[k][1]
                # Get pos
                if not loadedFromModchart:
                    self.pos = \
                        json.load(open("assets" + os.path.sep + "Music" + os.path.sep + "{0}".format(
                            musicName) + os.path.sep + "songData.json"))["character{0}".format(temp)][
                            "pos"]
                else:
                    self.pos = json.load(open("assets" + os.path.sep + "Music" + os.path.sep + "{0}".format(
                        musicName) + os.path.sep + "songData.json"))["modchartCharacters"][name]["pos"]
                # Handle centered character
                try:
                    if not loadedFromModchart:
                        self.isCentered = json.load(open("assets" + os.path.sep + "Music" + os.path.sep + "{0}".format(
                            musicName) + os.path.sep + "songData.json"))["character{0}".format(characterNum)][
                            "isCentered"]
                    else:
                        self.isCentered = json.load(open("assets" + os.path.sep + "Music" + os.path.sep + "{0}".format(
                            musicName) + os.path.sep + "songData.json"))["modchartCharacters"][name]["isCentered"]
                except:
                    self.isCentered = ["False", "False"]
                if self.isCentered[0] == "True" or self.isCentered[1] == "True":
                    try:
                        if not loadedFromModchart:
                            self.centeredOffset = json.load(open(
                                "assets" + os.path.sep + "Music" + os.path.sep + "{0}".format(
                                    musicName) + os.path.sep + "songData.json"))["character{0}".format(characterNum)][
                                "centeredOffset"]
                        else:
                            self.centeredOffset = json.load(open(
                                "assets" + os.path.sep + "Music" + os.path.sep + "{0}".format(
                                    musicName) + os.path.sep + "songData.json"))["modchartCharacters"][name][
                                "centeredOffset"]
                    except:
                        self.centeredOffset = [0, 0]
                    if characterNum == 1:
                        if self.isCentered[0] == "True":
                            self.pos[0] = display.Info().current_w / 2 + self.centeredOffset[0]
                        if self.isCentered[1] == "True":
                            self.pos[1] = display.Info().current_h / 2 + self.centeredOffset[1]
                    else:
                        if self.isCentered[0] == "True":
                            self.pos[0] = display.Info().current_w / 2 - self.centeredOffset[0]
                        if self.isCentered[1] == "True":
                            self.pos[1] = display.Info().current_h / 2 + self.centeredOffset[1]
                # Invert texture and offset when necessary
                if (textureDirection == "Left" and characterNum == 1) or (
                        textureDirection == "Right" and characterNum == 2):
                    for k in range(5):
                        for x in range(len(self.offset[k])):
                            self.offset[k][x][0] *= -1
                    for k in range(5):
                        for x in range(len(self.texture[k])):
                            self.texture[k][x] = transform.flip(self.texture[k][x], True, False)
                    temp1 = self.texture[0]
                    self.texture[0] = self.texture[3]
                    self.texture[3] = temp1
                    temp1 = self.offset[0]
                    self.offset[0] = self.offset[3]
                    self.offset[3] = temp1
                # Add offset to pos
                for k in range(5):
                    for x in range(len(self.offset[k])):
                        if characterNum == 1:
                            self.offset[k][x][0] = self.pos[0] + self.offset[k][x][0]
                            self.offset[k][x][1] = self.pos[1] + self.offset[k][x][1]
                        else:
                            self.offset[k][x][0] = self.pos[0] - self.offset[k][x][0]
                            self.offset[k][x][1] = self.pos[1] + self.offset[k][x][1]
                self.pos = self.offset
                # Scale texture to size
                for k in range(5):
                    for x in range(len(self.texture[k])):
                        self.texture[k][x] = transform.scale(self.texture[k][x], (
                            int(self.texture[k][x].get_width() * self.size[k][0]),
                            int(self.texture[k][x].get_height() * self.size[k][1])))
            # Handle no character
            else:
                self.texture = [[Font40.render("", 1, (255, 255, 255))] for _ in range(5)]
                self.pos = [[[0, 0]] for _ in range(5)]

    # Create a dictionary to store loaded characters
    loadedCharacters = {}

    # Load characters
    if playAs == "Player":
        try:
            characterName = json.load(open("assets" + os.path.sep + "Music" + os.path.sep + "{0}".format(
                musicName) + os.path.sep + "songData.json"))["character1"]["Name"]
            try:
                alias = json.load(open("assets" + os.path.sep + "Music" + os.path.sep + "{0}".format(
                    musicName) + os.path.sep + "songData.json"))["character1"]["alias"]
            except:
                alias = None
            if alias is None:
                loadedCharacters[characterName] = Character(characterName, 1)
                character1 = loadedCharacters[characterName]
            else:
                loadedCharacters[alias] = Character(characterName, 1)
                character1 = loadedCharacters[alias]
        except Exception as e:
            print("Opponent character loading failed, skipping loading")
            print(e)
            character1 = Character("None", 1)
        try:
            characterName = json.load(open("assets" + os.path.sep + "Music" + os.path.sep + "{0}".format(
                musicName) + os.path.sep + "songData.json"))["character2"]["Name"]
            try:
                alias = json.load(open("assets" + os.path.sep + "Music" + os.path.sep + "{0}".format(
                    musicName) + os.path.sep + "songData.json"))["character2"]["alias"]
            except:
                alias = None
            if alias is None:
                loadedCharacters[characterName] = Character(characterName, 2)
                character2 = loadedCharacters[characterName]
            else:
                loadedCharacters[alias] = Character(characterName, 2)
                character2 = loadedCharacters[alias]
        except Exception as e:
            print("Player character loading failed, skipping loading")
            print(e)
            character2 = Character("None", 2)
    else:
        try:
            characterName = json.load(open("assets" + os.path.sep + "Music" + os.path.sep + "{0}".format(
                musicName) + os.path.sep + "songData.json"))["character2"]["Name"]
            try:
                alias = json.load(open("assets" + os.path.sep + "Music" + os.path.sep + "{0}".format(
                    musicName) + os.path.sep + "songData.json"))["character2"]["alias"]
            except:
                alias = None
            if alias is None:
                loadedCharacters[characterName] = Character(characterName, 1)
                character1 = loadedCharacters[characterName]
            else:
                loadedCharacters[alias] = Character(characterName, 1)
                character1 = loadedCharacters[alias]
        except Exception as e:
            print("Opponent character loading failed, skipping loading")
            print(e)
            character1 = Character("None", 1)
        try:
            characterName = json.load(open("assets" + os.path.sep + "Music" + os.path.sep + "{0}".format(
                musicName) + os.path.sep + "songData.json"))["character1"]["Name"]
            try:
                alias = json.load(open("assets" + os.path.sep + "Music" + os.path.sep + "{0}".format(
                    musicName) + os.path.sep + "songData.json"))["character1"]["alias"]
            except:
                alias = None
            if alias is None:
                loadedCharacters[characterName] = Character(characterName, 2)
                character2 = loadedCharacters[characterName]
            else:
                loadedCharacters[alias] = Character(characterName, 2)
                character2 = loadedCharacters[alias]
        except Exception as e:
            print("Player character loading failed, skipping loading")
            print(e)
            character2 = Character("None", 2)

    if singlePlayer:
        print("Resolution too low to display both characters, using singleplayer mode")
        character1 = Character("None", 1)
# endregion

    game_context = {
        
    }
        # Create game context for modchart and initialize it
    if modchart_functions and "code" in modchart_functions:
        try:
            game_context = {
                # Game state
                "screen": screen,
                "clock": clock,
                "bpm": bpm,
                "speed": speed,
                "health": health,
                "combo": combo,
                "misses": misses,
                "playAs": playAs,
                "downscroll": downscroll,
                
                # Game assets
                "arrowsSkins": arrowsSkins,
                "pressedArrowsSkins": pressedArrowsSkins,
                "greyArrow": greyArrow,
                "longNotesImg": longNotesImg,
                "longNotesEnd": longNotesEnd,
                "Background": Background,
                
                # Characters
                "character1": character1,
                "character2": character2,
                
                # Notes
                "notesChart": notesChart,
                "longNotesChart": longNotesChart,
                
                # Pygame modules
                "pygame": {
                    "display": display,
                    "draw": draw,
                    "transform": transform,
                    "mixer": mixer,
                    "font": font,
                    "image": image,
                    "Rect": Rect,
                },
                
                # Screen dimensions
                "screen_width": display.Info().current_w,
                "screen_height": display.Info().current_h,
                "middleScreen": middleScreen,
            }
            
            # Run the modchart with the game context
            modchart_functions = ModchartCore.runModchart(modchart_functions["code"], game_context)
            print("Modchart initialized successfully")
        except Exception as e:
            print(f"Error initializing modchart: {e}")
            modchart_functions = None

    # endregion
    # endregion

    # region screen and notes update
    def drawGreyNotes():
        width = display.Info().current_w
        height = display.Info().current_h
        currentTime = Time.time() - startTime
        if "hideNotes2" not in modifications:
            temp = arrowRect
            if not downscroll:
                temp.topright = (width - 540, 50)
            else:
                temp.bottomright = (width - 540, height - 50)
            if K_a in keyPressed or K_LEFT in keyPressed:
                screen.blit(pressedArrowsSkins[0], temp)
            else:
                screen.blit(greyArrow[0], temp)
            temp = arrowRect
            if not downscroll:
                temp.topright = (width - 380, 50)
            else:
                temp.bottomright = (width - 380, height - 50)
            if K_s in keyPressed or K_DOWN in keyPressed:
                screen.blit(pressedArrowsSkins[1], temp)
            else:
                screen.blit(greyArrow[1], temp)
            temp = arrowRect
            if not downscroll:
                temp.topright = (width - 220, 50)
            else:
                temp.bottomright = (width - 220, height - 50)
            if K_w in keyPressed or K_UP in keyPressed:
                screen.blit(pressedArrowsSkins[2], temp)
            else:
                screen.blit(greyArrow[2], temp)
            temp = arrowRect
            if not downscroll:
                temp.topright = (width - 60, 50)
            else:
                temp.bottomright = (width - 60, height - 50)
            if K_d in keyPressed or K_RIGHT in keyPressed:
                screen.blit(pressedArrowsSkins[3], temp)
            else:
                screen.blit(greyArrow[3], temp)
        if not singlePlayer and "hideNotes1" not in modifications:
            temp = arrowRect
            if not downscroll:
                temp.topleft = (60, 50)
            else:
                temp.bottomleft = (60, height - 50)
            if currentTime - opponentHitTimes[0] > 0.15:
                screen.blit(greyArrow[0], temp)
            else:
                screen.blit(pressedArrowsSkins[0], temp)
            temp = arrowRect
            if not downscroll:
                temp.topleft = (220, 50)
            else:
                temp.bottomleft = (220, height - 50)
            if currentTime - opponentHitTimes[1] > 0.15:
                screen.blit(greyArrow[1], temp)
            else:
                screen.blit(pressedArrowsSkins[1], temp)
            temp = arrowRect
            if not downscroll:
                temp.topleft = (380, 50)
            else:
                temp.bottomleft = (380, height - 50)
            if currentTime - opponentHitTimes[2] > 0.15:
                screen.blit(greyArrow[2], temp)
            else:
                screen.blit(pressedArrowsSkins[2], temp)
            temp = arrowRect
            if not downscroll:
                temp.topleft = (540, 50)
            else:
                temp.bottomleft = (540, height - 50)
            if currentTime - opponentHitTimes[3] > 0.15:
                screen.blit(greyArrow[3], temp)
            else:
                screen.blit(pressedArrowsSkins[3], temp)

    def drawNotes():
        global misses
        global health
        global opponentAnimation
        global combo
        currentTime = Time.time() - startTime
        width = display.Info().current_w
        height = display.Info().current_h
        renderNotes = True
        for note in notesChart:
            if renderNotes:
                if note.side == "Opponent" and currentTime * 1000 >= note.pos:
                    opponentAnimation = [note.column, currentTime]
                    opponentHitTimes[["Left", "Down", "Up", "Right"].index(note.column)] = currentTime
                    notesChart.remove(note)
                if currentTime * 1000 - 133 >= note.pos and note.side == "Player" and note.column in ["Left", "Down", "Up", "Right"]:
                    for noteGroup in longNotesChart:
                        if noteGroup.id == note.id:
                            noteGroup.canDealDamage = False
                            break
                            
                    # Call onMiss callback before removing the note
                    if modchart_functions and modchart_functions["onMiss"]:
                        try:
                            modchart_functions["onMiss"](
                                note=note,
                                currentTime=currentTime,
                                column=note.column
                            )
                        except Exception as e:
                            print(f"Error in onMiss callback: {e}")
                            
                    notesChart.remove(note)
                    misses += 1
                    health -= 4
                    accuracyPercentList.append(0)
                    combo = 0
                if 50 + (note.pos - currentTime * 1000) * speed < display.Info().current_h + 100:
                    if not singlePlayer and "hideNotes1" not in modifications:
                        if note.side == "Opponent" and note.column == "Down":
                            temp = arrowRect
                            if not downscroll:
                                temp.topleft = (220, 50 + (note.pos - currentTime * 1000) * speed)
                            else:
                                temp.bottomleft = (220, height - 50 - (note.pos - currentTime * 1000) * speed)
                            screen.blit(arrowsSkins[1], temp)
                        elif note.side == "Opponent" and note.column == "Left":
                            temp = arrowRect
                            if not downscroll:
                                temp.topleft = (60, 50 + (note.pos - currentTime * 1000) * speed)
                            else:
                                temp.bottomleft = (60, height - 50 - (note.pos - currentTime * 1000) * speed)
                            screen.blit(arrowsSkins[0], temp)
                        elif note.side == "Opponent" and note.column == "Up":
                            temp = arrowRect
                            if not downscroll:
                                temp.topleft = (380, 50 + (note.pos - currentTime * 1000) * speed)
                            else:
                                temp.bottomleft = (380, height - 50 - (note.pos - currentTime * 1000) * speed)
                            screen.blit(arrowsSkins[2], temp)
                        elif note.side == "Opponent" and note.column == "Right":
                            temp = arrowRect
                            if not downscroll:
                                temp.topleft = (540, 50 + (note.pos - currentTime * 1000) * speed)
                            else:
                                temp.bottomleft = (540, height - 50 - (note.pos - currentTime * 1000) * speed)
                            screen.blit(arrowsSkins[3], temp)
                    if "hideNotes2" not in modifications:
                        if note.side == "Player" and note.column == "Down":
                            temp = arrowRect
                            if not downscroll:
                                temp.topright = (width - 380, 50 + (note.pos - currentTime * 1000) * speed)
                            else:
                                temp.bottomright = (width - 380, height - 50 - (note.pos - currentTime * 1000) * speed)
                            screen.blit(arrowsSkins[1], temp)
                        elif note.side == "Player" and note.column == "Left":
                            temp = arrowRect
                            if not downscroll:
                                temp.topright = (width - 540, 50 + (note.pos - currentTime * 1000) * speed)
                            else:
                                temp.bottomright = (width - 540, height - 50 - (note.pos - currentTime * 1000) * speed)
                            screen.blit(arrowsSkins[0], temp)
                        elif note.side == "Player" and note.column == "Up":
                            temp = arrowRect
                            if not downscroll:
                                temp.topright = (width - 220, 50 + (note.pos - currentTime * 1000) * speed)
                            else:
                                temp.bottomright = (width - 220, height - 50 - (note.pos - currentTime * 1000) * speed)
                            screen.blit(arrowsSkins[2], temp)
                        elif note.side == "Player" and note.column == "Right":
                            temp = arrowRect
                            if not downscroll:
                                temp.topright = (width - 60, 50 + (note.pos - currentTime * 1000) * speed)
                            else:
                                temp.bottomright = (width - 60, height - 50 - (note.pos - currentTime * 1000) * speed)
                            screen.blit(arrowsSkins[3], temp)

                else:
                    renderNotes = False

    def drawLongNotes():
        global opponentAnimation
        global playerAnimation
        global misses
        global health
        global combo
        currentTime = Time.time() - startTime
        width = display.Info().current_w
        height = display.Info().current_h
        deleteList = []
        run = True
        for noteGroup in longNotesChart:
            deleteGroup = False
            if len(noteGroup.notes) == 0:
                run = False
                deleteGroup = True
            if run and 50 + (noteGroup.notes[0].pos - currentTime * 1000) * speed < height + 100:
                for longNote in noteGroup.notes:
                    transparent = False
                    if currentTime * 1000 - 133 >= longNote.pos:
                        if longNote.side == "Player":
                            if (noteGroup.size - len(noteGroup.notes)) / noteGroup.size >= 0.75:
                                noteGroup.canDealDamage = False
                            if noteGroup.canDealDamage:
                                misses += 1
                                health -= 4
                                accuracyPercentList.append(0)
                                combo = 0
                                noteGroup.canDealDamage = False
                            noteGroup.notes.remove(longNote)
                    else:
                        if noteGroup.canDealDamage:
                            transparent = False
                        else:
                            transparent = True
                        if longNote.side == "Opponent" and currentTime * 1000 >= longNote.pos:
                            if currentTime - opponentAnimation[1] > 0.7:
                                opponentAnimation = [longNote.column, currentTime]
                            opponentHitTimes[["Left", "Down", "Up", "Right"].index(longNote.column)] = currentTime
                            noteGroup.notes.remove(longNote)
                        if longNote.side == "Player" and currentTime * 1000 >= longNote.pos and longNote.column in ["Left",
                                                                                                                    "Down",
                                                                                                                    "Up",
                                                                                                                    "Right"]:
                            if ((K_LEFT in keyPressed or K_a in keyPressed) and longNote.column == "Left") or (
                                    (K_DOWN in keyPressed or K_s in keyPressed) and longNote.column == "Down") or (
                                    (K_UP in keyPressed or K_w in keyPressed) and longNote.column == "Up") or (
                                    (K_RIGHT in keyPressed or K_d in keyPressed) and longNote.column == "Right"):
                                if currentTime - playerAnimation[1] > 0.7:
                                    playerAnimation = [longNote.column, currentTime]
                                noteGroup.notes.remove(longNote)
                        if 50 + (longNote.pos - currentTime * 1000) * speed < height + 100:
                            if not singlePlayer and longNote.side == "Opponent" and "hideNotes1" not in modifications:
                                if longNote.column == "Down":
                                    temp = arrowRect
                                    if not downscroll:
                                        temp.center = (220 + 125, 50 + (longNote.pos - currentTime * 1000) * speed + 100)
                                    else:
                                        temp.center = (220 + 125, height - 50 - (longNote.pos - currentTime * 1000) * speed)
                                    if longNote.isEnd:
                                        screen.blit(longNotesEnd[1], temp)
                                    else:
                                        screen.blit(longNotesImg[1], temp)
                                if longNote.column == "Left":
                                    temp = arrowRect
                                    if not downscroll:
                                        temp.center = (60 + 125, 50 + (longNote.pos - currentTime * 1000) * speed + 100)
                                    else:
                                        temp.center = (60 + 125, height - 50 - (longNote.pos - currentTime * 1000) * speed)
                                    if longNote.isEnd:
                                        screen.blit(longNotesEnd[0], temp)
                                    else:
                                        screen.blit(longNotesImg[0], temp)
                                if longNote.column == "Up":
                                    temp = arrowRect
                                    if not downscroll:
                                        temp.center = (380 + 125, 50 + (longNote.pos - currentTime * 1000) * speed + 100)
                                    else:
                                        temp.center = (380 + 125, height - 50 - (longNote.pos - currentTime * 1000) * speed)
                                    if longNote.isEnd:
                                        screen.blit(longNotesEnd[2], temp)
                                    else:
                                        screen.blit(longNotesImg[2], temp)
                                if longNote.column == "Right":
                                    temp = arrowRect
                                    if not downscroll:
                                        temp.center = (540 + 125, 50 + (longNote.pos - currentTime * 1000) * speed + 100)
                                    else:
                                        temp.center = (540 + 125, height - 50 - (longNote.pos - currentTime * 1000) * speed)
                                    if longNote.isEnd:
                                        screen.blit(longNotesEnd[3], temp)
                                    else:
                                        screen.blit(longNotesImg[3], temp)
                            if longNote.side == "Player" and "hideNotes2" not in modifications:
                                if longNote.column == "Up":
                                    temp = arrowRect
                                    if not downscroll:
                                        temp.center = (width - 220 - 25, 50 + (longNote.pos - currentTime * 1000) * speed + 100)
                                    else:
                                        temp.center = (width - 220 - 25, height - 50 - (longNote.pos - currentTime * 1000) * speed)
                                    if longNote.isEnd:
                                        img = copy.copy(longNotesEnd[2])
                                    else:
                                        img = copy.copy(longNotesImg[2])
                                    if transparent:
                                        img.set_alpha(100)
                                    screen.blit(img, temp)
                                if longNote.column == "Down":
                                    temp = arrowRect
                                    if not downscroll:
                                        temp.center = (width - 380 - 25, 50 + (longNote.pos - currentTime * 1000) * speed + 100)
                                    else:
                                        temp.center = (width - 380 - 25, height - 50 - (longNote.pos - currentTime * 1000) * speed)
                                    if longNote.isEnd:
                                        img = copy.copy(longNotesEnd[1])
                                    else:
                                        img = copy.copy(longNotesImg[1])
                                    if transparent:
                                        img.set_alpha(100)
                                    screen.blit(img, temp)
                                if longNote.column == "Left":
                                    temp = arrowRect
                                    if not downscroll:
                                        temp.center = (width - 540 - 25, 50 + (longNote.pos - currentTime * 1000) * speed + 100)
                                    else:
                                        temp.center = (width - 540 - 25, height - 50 - (longNote.pos - currentTime * 1000) * speed)
                                    if longNote.isEnd:
                                        img = copy.copy(longNotesEnd[0])
                                    else:
                                        img = copy.copy(longNotesImg[0])
                                    if transparent:
                                        img.set_alpha(100)
                                    screen.blit(img, temp)
                                if longNote.column == "Right":
                                    temp = arrowRect
                                    if not downscroll:
                                        temp.center = (width - 60 - 25, 50 + (longNote.pos - currentTime * 1000) * speed + 100)
                                    else:
                                        temp.center = (width - 60 - 25, height - 50 - (longNote.pos - currentTime * 1000) * speed)
                                    if longNote.isEnd:
                                        img = copy.copy(longNotesEnd[3])
                                    else:
                                        img = copy.copy(longNotesImg[3])
                                    if transparent:
                                        img.set_alpha(100)
                                    screen.blit(img, temp)
            if deleteGroup:
                deleteList.append(noteGroup.id)
        for element in longNotesChart:
            if element.id in deleteList:
                deleteList.remove(element.id)
                longNotesChart.remove(element)
            if len(deleteList) == 0:
                break

    def drawHealthBar():
        global health
        if health > 100:
            health = 100
        if health < 0:
            health = 0
        width = display.Info().current_w
        height = display.Info().current_h
        if not downscroll:
            draw.rect(screen, (255, 255, 255), Rect(45, height - 115, width - 90, 60))
        else:
            draw.rect(screen, (255, 255, 255), Rect(45, 55, width - 90, 60))
        if health < 100:
            if not downscroll:
                draw.rect(screen, (255, 0, 0), Rect(50, height - 110, (width - 100) / 100 * (100 - health), 50))
            else:
                draw.rect(screen, (255, 0, 0), Rect(50, 60, (width - 100) / 100 * (100 - health), 50))
        if health > 0:
            if not downscroll:
                draw.rect(screen, (0, 255, 0),
                        Rect(50 + (width - 100) / 100 * (100 - health), height - 110, (width - 100) / 100 * health, 50))
            else:
                draw.rect(screen, (0, 255, 0), Rect(50 + (width - 100) / 100 * (100 - health), 60, (width - 100) / 100 * health, 50))

    def drawCharacters():
        currentTime = Time.time() - startTime
        
        # Store last successful frames
        if not hasattr(drawCharacters, "last_opponent_frame"):
            drawCharacters.last_opponent_frame = None
            drawCharacters.last_player_frame = None
            drawCharacters.last_opponent_temp = None
            drawCharacters.last_player_temp = None
        
        # Determine animation direction for opponent
        if currentTime - opponentAnimation[1] > 0.75:
            animationDirection = 4  # Idle animation
        else:
            animationDirection = ["Left", "Down", "Up", "Right"].index(opponentAnimation[0])
        
        # Calculate frame for opponent animation
        frameCount = len(character1.texture[animationDirection])
        if frameCount > 0:
            try:
                # Double animation speed: changed from *10 to *20
                frameIndex = int((currentTime * 20) % frameCount)
                frame = character1.texture[animationDirection][frameIndex]
                
                # Get rect and position
                temp = frame.get_rect()
                temp.midbottom = [character1.pos[animationDirection][frameIndex][0],
                                 display.Info().current_h - character1.pos[animationDirection][frameIndex][1]]
                
                # Store successful frame and temp
                drawCharacters.last_opponent_frame = frame
                drawCharacters.last_opponent_temp = temp
            except:
                # Use last successful frame if available
                if drawCharacters.last_opponent_frame is not None:
                    frame = drawCharacters.last_opponent_frame
                    temp = drawCharacters.last_opponent_temp
                else:
                    # Skip rendering if no frame is available
                    frame = None
                    temp = None
            
            # Render if we have a valid frame
            if frame is not None:
                screen.blit(frame, temp)
        
        # Determine animation direction for player
        if currentTime - playerAnimation[1] > 0.75:
            animationDirection = 4  # Idle animation
        else:
            animationDirection = ["Left", "Down", "Up", "Right"].index(playerAnimation[0])
        
        # Calculate frame for player animation
        frameCount = len(character2.texture[animationDirection])
        if frameCount > 0:
            try:
                # Double animation speed: changed from *10 to *20
                frameIndex = int((currentTime * 20) % frameCount)
                frame = character2.texture[animationDirection][frameIndex]
                
                # Get rect and position
                temp = frame.get_rect()
                temp.midbottom = [display.Info().current_w - character2.pos[animationDirection][frameIndex][0],
                                 display.Info().current_h - character2.pos[animationDirection][frameIndex][1]]
                
                # Store successful frame and temp
                drawCharacters.last_player_frame = frame
                drawCharacters.last_player_temp = temp
            except:
                # Use last successful frame if available
                if drawCharacters.last_player_frame is not None:
                    frame = drawCharacters.last_player_frame
                    temp = drawCharacters.last_player_temp
                else:
                    # Skip rendering if no frame is available
                    frame = None
                    temp = None
            
            # Render if we have a valid frame
            if frame is not None:
                screen.blit(frame, temp)

    # endregion

    # region death screen
    def death():
        global hasPlayedMicDrop
        startDeathTime = Time.time()
        deathScreenMusicStart.play()
        while True:
            for events in event.get():
                # Handle DevTools events
                if dev_tools.handle_event(events):
                    continue
                # Add F12 toggle for DevTools
                if events.type == KEYDOWN and events.key == K_F12:
                    dev_tools.toggle()
                    continue
                if events.type == QUIT:
                    deathScreenMusic.stop()
                    deathScreenMusicEnd.stop()
                    quit()
                    exit()
                if events.type == KEYDOWN:
                    if events.key == K_ESCAPE or events.key == K_BACKSPACE:
                        deathScreenMusic.stop()
                        return False
                    if events.key == K_SPACE or events.key == K_RETURN:
                        deathScreenMusic.stop()
                        deathScreenMusicEnd.play()
                        Time.sleep(deathScreenMusicEnd.get_length() - 2.5)
                        deathScreenMusicEnd.stop()
                        return True
            screen.fill((0, 0, 0))
            if Time.time() - startDeathTime > deathScreenMusicStart.get_length() - 1.5 and not hasPlayedMicDrop:
                deathScreenMusic.play(-1)
                hasPlayedMicDrop = True
            screen.blit(BFdead, deathScreenRect)
            display.flip()
    # endregion

    # Add this function to Game.py after the death() function
    def show_results_screen(accuracy_percent, misses, combo, accuracyPercentList):
        """Display the results screen after a song is completed"""
        import math  # For sin function in animations
        import builtins  # Import builtins to access min function
        
        # Calculate middle of the screen
        middleScreen = (display.Info().current_w // 2, display.Info().current_h // 2)
        
        # Try to load the MainMenu font
        try:
            ResultsFont75 = font.Font("assets\\PhantomMuff.ttf", 75)
            ResultsFont125 = font.Font("assets\\PhantomMuff.ttf", 125)
            ResultsFont50 = font.Font("assets\\PhantomMuff.ttf", 50)
        except Exception as e:
            # Fallback to VCR font if not available
            ResultsFont75 = Font25
            ResultsFont125 = Font40
            ResultsFont50 = Font25
        
        # Parse the accuracy value
        if accuracy_percent == "NA":
            acc_value = 0
        else:
            # Strip '%' and convert to float
            acc_value = float(accuracy_percent.strip('%'))
        
        # Determine letter rank
        if acc_value >= 90:
            rank = "SS"
            rank_color = (255, 215, 0)  # Gold
        elif acc_value >= 80:
            rank = "S"
            rank_color = (255, 215, 0)  # Gold
        elif acc_value >= 70:
            rank = "A"
            rank_color = (0, 255, 0)  # Green
        elif acc_value >= 60:
            rank = "B"
            rank_color = (0, 200, 255)  # Light Blue
        elif acc_value >= 50:
            rank = "C"
            rank_color = (150, 150, 255)  # Purple-ish
        elif acc_value >= 40:
            rank = "D"
            rank_color = (255, 150, 0)  # Orange
        else:
            rank = "F"
            rank_color = (255, 0, 0)  # Red
        
        # Calculate total hits (not using combo which can be broken)
        hits = len(accuracyPercentList) - misses
        
        # Animation variables
        start_time = Time.time()
        show_rank = False
        show_stats = False
        show_continue = False
        
        # Animation timing
        rank_delay = 0.5  # When to show the rank
        stats_delay = 1.5  # When to show the stats
        continue_delay = 2.5  # When to show the continue message
        
        # Start the results screen loop
        while True:
            current_time = Time.time() - start_time
            
            # Handle events
            for events in event.get():
                # Handle DevTools events
                if dev_tools.handle_event(events):
                    continue
                if events.type == KEYDOWN and events.key == K_F12:
                    dev_tools.toggle()
                    continue
                if events.type == QUIT:
                    quit()
                    exit()
                if events.type == KEYDOWN:
                    if events.key == K_RETURN and current_time > continue_delay:
                        return  # Exit the results screen
            
            # Update animation timers
            if current_time > rank_delay:
                show_rank = True
            if current_time > stats_delay:
                show_stats = True
            if current_time > continue_delay:
                show_continue = True
            
            # Draw background with overlay
            screen.fill((0, 0, 0))
            overlay = Surface((display.Info().current_w, display.Info().current_h), SRCALPHA)
            overlay.fill((0, 0, 20, 220))
            screen.blit(overlay, (0, 0))
            
            # Display the rank
            if show_rank:
                # Scale animation - use built-ins.min to avoid name conflicts
                scale = builtins.min(1.0, (current_time - rank_delay) * 2)
                
                # Pulsing effect
                pulse = 1.0 + 0.1 * math.sin(current_time * 3)
                
                # Create rank text
                rank_text = ResultsFont125.render(rank, True, rank_color)
                rank_text = transform.scale(rank_text, 
                                           (int(rank_text.get_width() * scale * pulse),
                                            int(rank_text.get_height() * scale * pulse)))
                
                # Create glow effect
                glow_surface = Surface((rank_text.get_width() + 30, rank_text.get_height() + 30), SRCALPHA)
                for i in range(10):
                    alpha = 150 - i * 15
                    size = i * 2
                    draw.rect(glow_surface, (rank_color[0], rank_color[1], rank_color[2], alpha), 
                              Rect(15-size//2, 15-size//2, 
                                   rank_text.get_width()+size, 
                                   rank_text.get_height()+size), 
                              border_radius=10)
                
                # Position and draw
                rank_rect = rank_text.get_rect()
                rank_rect.center = (middleScreen[0], middleScreen[1] - 100)
                glow_rect = glow_surface.get_rect()
                glow_rect.center = rank_rect.center
                
                screen.blit(glow_surface, glow_rect)
                screen.blit(rank_text, rank_rect)
                
                # Add "RANK" label
                if scale > 0.5:
                    label_opacity = builtins.min(255, int((scale - 0.5) * 510))
                    rank_label = ResultsFont50.render("RANK", True, (255, 255, 255))
                    rank_label.set_alpha(label_opacity)
                    label_rect = rank_label.get_rect()
                    label_rect.midbottom = (rank_rect.centerx, rank_rect.top - 10)
                    screen.blit(rank_label, label_rect)
            
            # Display the stats
            if show_stats:
                stats_opacity = builtins.min(255, int((current_time - stats_delay) * 510))
                
                # Stats text
                accuracy_text = ResultsFont75.render(f"Accuracy: {accuracy_percent}", True, (255, 255, 255))
                accuracy_text.set_alpha(stats_opacity)
                
                hits_text = ResultsFont75.render(f"Hits: {hits}", True, (100, 255, 100))
                hits_text.set_alpha(stats_opacity)
                
                misses_text = ResultsFont75.render(f"Misses: {misses}", True, (255, 100, 100))
                misses_text.set_alpha(stats_opacity)
                
                max_combo_text = ResultsFont75.render(f"Max Combo: {combo}", True, (255, 255, 100))
                max_combo_text.set_alpha(stats_opacity)
                
                # Position stats with staggered animation
                acc_rect = accuracy_text.get_rect()
                acc_rect.centerx = middleScreen[0]
                acc_rect.top = middleScreen[1] + 50
                
                hits_rect = hits_text.get_rect()
                hits_rect.centerx = middleScreen[0]
                hits_rect.top = acc_rect.bottom + 15
                
                misses_rect = misses_text.get_rect()
                misses_rect.centerx = middleScreen[0]
                misses_rect.top = hits_rect.bottom + 15
                
                combo_rect = max_combo_text.get_rect()
                combo_rect.centerx = middleScreen[0]
                combo_rect.top = misses_rect.bottom + 15
                
                screen.blit(accuracy_text, acc_rect)
                screen.blit(hits_text, hits_rect)
                screen.blit(misses_text, misses_rect)
                screen.blit(max_combo_text, combo_rect)
            
            # Display continue message
            if show_continue:
                continue_pulse = 0.7 + 0.3 * math.sin(current_time * 4)
                continue_color = (int(255 * continue_pulse), 
                                 int(255 * continue_pulse), 
                                 int(255 * continue_pulse))
                
                continue_text = ResultsFont50.render("Press Enter to continue", True, continue_color)
                continue_rect = continue_text.get_rect()
                continue_rect.centerx = middleScreen[0]
                continue_rect.bottom = display.Info().current_h - 50
                
                screen.blit(continue_text, continue_rect)
            
            # Update and draw DevTools
            dev_tools.update(0.016, sys.modules[__name__])
            dev_tools.draw(screen)
            
            # Update display
            display.flip()
            clock.tick(60)

    keyPressed = []

    Inst.play()
    Vocals.play()
    
    startTime = Time.time()
    
    # Call onSongStart callback
    if modchart_functions and modchart_functions["onSongStart"]:
        try:
            modchart_functions["onSongStart"](startTime=startTime)
        except Exception as e:
            print(f"Error in onSongStart callback: {e}")
    
    

    startTime = Time.time()
    while True:
        notesToClear = [[], [], [], []]
        # Calculate current beat and step
        currentTime = Time.time() - startTime
        try:
            songBpm = json.load(open("assets\Music\{0}\chart.json".format(musicName)))["song"]["bpm"]
            currentBeat = (currentTime / 60.0) * songBpm
            currentStep = currentBeat * 4
            
            # Store previous beat/step to detect changes
            if not hasattr(Main_game, "prev_beat"):
                Main_game.prev_beat = int(currentBeat)
                Main_game.prev_step = int(currentStep)
            
            # Call onBeat callback when the beat changes
            if int(currentBeat) > Main_game.prev_beat and modchart_functions and modchart_functions["onBeat"]:
                try:
                    modchart_functions["onBeat"](
                        beat=int(currentBeat),
                        currentTime=currentTime
                    )
                except Exception as e:
                    print(f"Error in onBeat callback: {e}")
                Main_game.prev_beat = int(currentBeat)
            
            # Call onStep callback when the step changes
            if int(currentStep) > Main_game.prev_step and modchart_functions and modchart_functions["onStep"]:
                try:
                    modchart_functions["onStep"](
                        step=int(currentStep),
                        currentTime=currentTime
                    )
                except Exception as e:
                    print(f"Error in onStep callback: {e}")
                Main_game.prev_step = int(currentStep)
        except Exception as e:
            pass  # Silently fail if BPM data is missing
        
        # Call onUpdate callback
        if modchart_functions and modchart_functions["onUpdate"]:
            try:
                modchart_functions["onUpdate"](
                    currentTime=currentTime,
                    health=health,
                    combo=combo,
                    misses=misses,
                    keyPressed=keyPressed
                )
            except Exception as e:
                print(f"Error in onUpdate callback: {e}")
                
        # Update game context for modchart
        if modchart_functions:
            try:
                game_context.update({
                    "health": health,
                    "combo": combo,
                    "misses": misses,
                    "currentTime": currentTime,
                    "notesChart": notesChart,
                    "longNotesChart": longNotesChart,
                })
            except Exception as e:
                print(f"Error updating game context: {e}")
                
        for events in event.get():
            if events.type == QUIT:
                quit()
                exit()
            if events.type == KEYDOWN and events.key == K_ESCAPE:
                Inst.stop()
                Vocals.stop()
                return False
            if events.type == KEYDOWN:
                # Add F8 check for autoplayer toggle
                if events.key == K_F8:
                    autoplayerEnabled = not autoplayerEnabled
                    # Reset game stats when enabling autoplayer
                    if autoplayerEnabled:
                        misses = 0
                        combo = 0
                        health = 50
                
                keyPressed.append(events.key)
                
                # Call onKeyPress callback
                if modchart_functions and modchart_functions["onKeyPress"]:
                    try:
                        modchart_functions["onKeyPress"](
                            key=events.key,
                            currentTime=Time.time() - startTime
                        )
                    except Exception as e:
                        print(f"Error in onKeyPress callback: {e}")
            if events.type == KEYDOWN and events.key == K_SPACE:
                print("Debug: Current song position: {0}".format((Time.time() - startTime) * 1000))
            if events.type == KEYUP and events.key in keyPressed:
                keyPressed.remove(events.key)
            if events.type == KEYDOWN:
                currentTime = Time.time() - startTime
                testNotes = True
                for note in notesChart:
                    if testNotes:
                        if note.pos <= currentTime * 1000 + 133:
                            if note.side == "Player" and currentTime * 1000 - 133 <= note.pos <= currentTime * 1000 + 133 and note.column in [
                                "Left", "Down", "Up", "Right"]:
                                if (events.key == K_a or events.key == K_LEFT) and note.column == "Left":
                                    notesToClear[0].append(note)
                                if (events.key == K_s or events.key == K_DOWN) and note.column == "Down":
                                    notesToClear[1].append(note)
                                if (events.key == K_w or events.key == K_UP) and note.column == "Up":
                                    notesToClear[2].append(note)
                                if (events.key == K_d or events.key == K_RIGHT) and note.column == "Right":
                                    notesToClear[3].append(note)
                        else:
                            testNotes = False
        # Run autoplayer if enabled
        if autoplayerEnabled:
            handle_autoplayer(currentTime)
        
        currentTime = Time.time() - startTime
        for k in range(4):
            if len(notesToClear[k]) > 0:
                min = notesToClear[k][0].pos
                minX = 0
                x = 0
                for element in notesToClear[k]:
                    if element.pos < min:
                        min = element.pos
                        minX = x
                    x += 1
                accuracy = str(round(notesToClear[k][minX].pos - currentTime * 1000, 2))
                showAccuracy = True
                accuracyDisplayTime = Time.time()
                # region Accuracy timings info
                # Sick: <= 47
                # Good: <= 79
                # Bad: <= 109
                # Shit: <= 133
                # endregion
                if currentTime * 1000 + 47 >= notesToClear[k][minX].pos >= currentTime * 1000 - 47:
                    accuracyIndicator = accuracyIndicatorImages[0]
                    accuracyPercentList.append(1)
                    health += 2.3
                    combo += 1
                elif currentTime * 1000 + 79 >= notesToClear[k][minX].pos >= currentTime * 1000 - 79:
                    accuracyIndicator = accuracyIndicatorImages[1]
                    accuracyPercentList.append(0.75)
                    health += 0.4
                    combo += 1
                elif currentTime * 1000 + 109 >= notesToClear[k][minX].pos >= currentTime * 1000 - 109:
                    accuracyIndicator = accuracyIndicatorImages[2]
                    accuracyPercentList.append(0.5)
                    health += 0.4
                    combo += 1
                else:
                    accuracyIndicator = accuracyIndicatorImages[3]
                    accuracyPercentList.append(-1)
                    misses += 1
                    health -= 4
                    combo = 0
                # After determining accuracy and before removing the note
                playerAnimation = [notesToClear[k][minX].column, currentTime]
                
                # Call onHit callback
                if modchart_functions and modchart_functions["onHit"]:
                    try:
                        modchart_functions["onHit"](
                            note=notesToClear[k][minX],
                            accuracy=accuracy,
                            rating=["sick", "good", "bad", "shit"][accuracyPercentList[-1] == 1 and 0 or accuracyPercentList[-1] == 0.75 and 1 or accuracyPercentList[-1] == 0.5 and 2 or 3],
                            combo=combo,
                            column=notesToClear[k][minX].column,
                            currentTime=currentTime
                        )
                    except Exception as e:
                        print(f"Error in onHit callback: {e}")
                
                notesChart.remove(notesToClear[k][minX])

        screen.fill((0, 0, 0))
        
        # Only render background and characters if render_scene is True
        if render_scene:
            # Calculate the current beat for pulsing effect
            try:
                songBpm = json.load(open("assets\Music\{0}\chart.json".format(musicName)))["song"]["bpm"]
                currentBeat = (currentTime / 60.0) * songBpm
                
                # Calculate pulse intensity based on beat
                beatFraction = currentBeat - int(currentBeat)
                # Create a pulse that peaks at the beat and diminishes afterward
                pulseScale = 1.0 + 0.08 * (1 - min(1, beatFraction * 3))
            except:
                # Fallback if BPM data is missing
                pulseScale = 1.05  # Default slight scale
                
            # Get the background frame
            backgroundFrameNum = int(((Time.time() - startTime) / (bpm / len(Background))) % len(Background))
            originalBG = Background[backgroundFrameNum]
            
            # Scale the background based on the pulse
            scaledWidth = int(originalBG.get_width() * pulseScale)
            scaledHeight = int(originalBG.get_height() * pulseScale)
            scaledBG = transform.scale(originalBG, (scaledWidth, scaledHeight))
            
            # Center the scaled background
            bgRect = scaledBG.get_rect()
            bgRect.center = (middleScreen[0], middleScreen[1])
            
            # Draw the background with pulse effect
            screen.blit(scaledBG, bgRect)
            
            # Draw characters
            drawCharacters()
        
        # Always render UI elements
        drawGreyNotes()
        drawLongNotes()
        drawNotes()
        
        # region draw bottom info bar
        if autoplayerEnabled:
            temp = Font40.render("Autoplayer Enabled", 1, (255, 255, 0))  # Yellow text for visibility
        else:
            if len(accuracyPercentList) == 0:
                tempAccuracy = "NA"
            else:
                temp = 0
                for element in accuracyPercentList:
                    temp += element
                temp /= len(accuracyPercentList)
                tempAccuracy = "{0}%".format(round(temp * 100, 2))
            temp = Font40.render("Combo: {0} | Misses: {1} | Accuracy: {2}".format(combo, misses, tempAccuracy), 1, (255, 255, 255))
            
        temp1 = temp.get_rect()
        if not downscroll:
            temp1.midbottom = (middleScreen[0], display.Info().current_h - 15)
        else:
            temp1.midtop = (middleScreen[0], 0)
        screen.blit(temp, temp1)
        # endregion
        
        # region accuracy display
        if Time.time() - accuracyDisplayTime > 0.5:
            showAccuracy = False
        if showAccuracy:
            temp = Font40.render(accuracy+ " ms", 1, (255, 255, 255))
            temp1 = temp.get_rect()
            temp1.center = (middleScreen[0], middleScreen[1])
            screen.blit(temp, temp1)

            screen.blit(accuracyIndicator, accuracyIndicatorRect)
        # endregion
        
        # region FPS
        fps = 1 / max((Time.time() - fpsTime), 0.00001)
        fpsTime = Time.time()
        fpsList.append(fps)
        temp = 0
        for element in fpsList:
            temp += element
        temp /= len(fpsList)
        while len(fpsList) > fpsQuality:
            fpsList.remove(fpsList[0])
        screen.blit(Font40.render(str(round(temp, 2)), 1, (255, 255, 255)), Rect(5, 0, 0, 0))
        # endregion
        
        # region health bar
        drawHealthBar()
        # endregion
        
        # Add this before rendering (around line 1101)
        # Calculate delta time for DevTools
        current_frame_time = Time.time()
        dt = current_frame_time - last_frame_time if 'last_frame_time' in locals() else 0.016
        last_frame_time = current_frame_time
        
        # Update DevTools
        dev_tools.update(dt, sys.modules[__name__])
        
        # Add this right before display.flip() (around line 1212)
        # Draw DevTools
        dev_tools.draw(screen)
        
        display.flip()
        if Time.time() - startTime > musicLen:
            # Call onSongEnd callback
            if modchart_functions and modchart_functions["onSongEnd"]:
                try:
                    modchart_functions["onSongEnd"](
                        misses=misses,
                        accuracy=tempAccuracy,
                        combo=combo
                    )
                except Exception as e:
                    print(f"Error in onSongEnd callback: {e}")
                    
            Inst.stop()
            Vocals.stop()
            
            show_results_screen(tempAccuracy, misses, combo, accuracyPercentList)
            
            return False
        if health <= 0 and not noDying:
            Inst.stop()
            Vocals.stop()
            return death()

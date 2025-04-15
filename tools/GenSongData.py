import json

# Define constants for reused values
DEFAULT_SIZE = [[0.75, 0.75]] * 5
DEFAULT_POS = {"character1": [430, 70], "character2": [340, 70]}

def generate_song_data(stage, character1, character2, pos1=None, pos2=None):
    """Generate song data with optional position overrides."""
    return {
        "stage": stage,
        "character1": {
            "Name": character1,
            "pos": pos1 or DEFAULT_POS["character1"],
            "size": DEFAULT_SIZE
        },
        "character2": {
            "Name": character2,
            "pos": pos2 or DEFAULT_POS["character2"],
            "size": DEFAULT_SIZE
        }
    }

def generate_song_data_from_file(file_path):
    """Reads song data from a JSON file and returns it as a dictionary."""
    try:
        with open(file_path, 'r') as file:
            song_data = json.load(file)
        return generate_song_data(
            song_data["song"]["stageDefault"],
            song_data["song"]["character1"],
            song_data["song"]["character2"]
        )
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        print(f"Error processing song data: {e}")
        return None

def gen_song_data_from_dir_and_save(directory):
    """Generates song data for all songs in a given directory, formatted
    as:
    folder/
        map1/
            song-diff.json
            chart.json   # Either chart.json or multiple {song}-{diff}.json files
        map2/
            song-diff.json
            chart.json   # Either chart.json or multiple {song}-{diff}.json files
    """
    import os

    song_data_list = []
    # Process both types of files in a single pass
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".json"):
                file_path = os.path.join(root, file)
                
                # Process song files for the song_data_list
                if "song" in file:
                    song_data = generate_song_data_from_file(file_path)
                    if song_data:
                        song_data_list.append(song_data)
                
                # Process chart files to save song data
                if "chart" in file:
                    song_data = generate_song_data_from_file(file_path)
                    if song_data:
                        # Save the song data to a new JSON file
                        song_data_file = os.path.splitext(file_path)[0] + "_songData.json"
                        with open(song_data_file, 'w') as f:
                            json.dump(song_data, f, indent=4)

    return song_data_list

if __name__ == "__main__":
    # Example usage
    directory = "assets/Music"  # Replace with your directory path
    song_data = gen_song_data_from_dir_and_save(directory)
    print("Generated song data:", song_data)
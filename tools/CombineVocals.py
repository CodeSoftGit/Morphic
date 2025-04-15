# Goes in every folder in assets/music and combines
# all ogg files starting with Voices into a single ogg file, Voices.ogg

def combine_voices_in_directory(directory):
    import os
    from pydub import AudioSegment
    from tqdm import tqdm

    # Create a new AudioSegment for the combined audio
    combined = AudioSegment.silent(duration=0)
    
    # Track the files we're combining
    combined_files = []

    # Get all valid voice files
    voice_files = [f for f in os.listdir(directory) 
                  if f.startswith("Voices") and f.endswith(".ogg") and f != "Voices.ogg"]
    
    # Iterate through all files in the directory with a progress bar
    for filename in tqdm(voice_files, desc=f"Processing {os.path.basename(directory)}", unit="file"):
        file_path = os.path.join(directory, filename)
        audio_segment = AudioSegment.from_ogg(file_path)
        combined = combined.overlay(audio_segment)
        combined_files.append(filename)

    # Only export if we found files to combine
    if combined_files:
        # Export the combined audio to Voices.ogg
        output_path = os.path.join(directory, "Voices.ogg")
        combined.export(output_path, format="ogg")
        print(f"Combined {len(combined_files)} voice files in {directory}")

if __name__ == "__main__":
    import os

    # Get the current working directory
    base_directory = os.getcwd()

    # Iterate through all subdirectories in assets/music
    for root, dirs, files in os.walk(os.path.join(base_directory, "assets/music")):
        combine_voices_in_directory(root)
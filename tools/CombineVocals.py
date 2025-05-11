# Goes in every folder in assets/music and combines
# all ogg files starting with Voices into a single ogg file, Voices.ogg

def combine_voices_in_directory(directory):
    import os
    import subprocess
    import sys
    from tqdm import tqdm

    # Check if ffmpeg is installed
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except (subprocess.SubprocessError, FileNotFoundError):
        print("Error: FFmpeg not found. Please install FFmpeg first.")
        print("Visit: https://ffmpeg.org/download.html")
        return
        
    # Get all valid voice files
    voice_files = [f for f in os.listdir(directory) 
                  if f.startswith("Voices") and f.endswith(".ogg") and f != "Voices.ogg"]
    
    # Only proceed if we found files to combine
    if not voice_files:
        return
        
    # Prepare ffmpeg command
    output_path = os.path.join(directory, "Voices.ogg")
    
    # Build the filter complex string for mixing
    inputs = []
    for filename in voice_files:
        file_path = os.path.join(directory, filename)
        inputs.append("-i")
        inputs.append(file_path)
    
    filter_complex = f"amix=inputs={len(voice_files)}:duration=longest"
    
    # Execute ffmpeg command
    command = ["ffmpeg", "-y"] + inputs + ["-filter_complex", filter_complex, output_path]
    
    print(f"Processing {os.path.basename(directory)} ({len(voice_files)} files)...")
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(f"Combined {len(voice_files)} voice files in {directory}")

if __name__ == "__main__":
    import os

    # Get the current working directory
    base_directory = os.getcwd()

    # Iterate through all subdirectories in assets/music
    for root, dirs, files in os.walk(os.path.join(base_directory, "assets/music")):
        combine_voices_in_directory(root)
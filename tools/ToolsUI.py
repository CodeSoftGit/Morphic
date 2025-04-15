import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import sys

# Add the tools directory to path to import the modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from GenSongData import generate_song_data, generate_song_data_from_file
from GenCharacterOffset import gen_character_offsets

class MorphicDataGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Morphic Data Generator")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Set theme and styling
        self.style = ttk.Style()
        self.style.theme_use('clam')  # Use a modern theme
        
        # Configure styles
        self.configure_styles()
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.tab_control = ttk.Notebook(self.main_frame)
        
        # Create Song Data tab
        self.song_tab = ttk.Frame(self.tab_control, padding=15)
        self.tab_control.add(self.song_tab, text="Song Data Generator")
        
        # Create Character Offset tab
        self.char_tab = ttk.Frame(self.tab_control, padding=15)
        self.tab_control.add(self.char_tab, text="Character Offset Generator")
        
        self.tab_control.pack(fill=tk.BOTH, expand=True)
        
        # Initialize tabs
        self.init_song_tab()
        self.init_character_tab()
    
    def configure_styles(self):
        """Configure custom styles for the application"""
        self.style.configure('TFrame', background='#f0f0f0')
        self.style.configure('TNotebook', background='#e0e0e0')
        self.style.configure('TNotebook.Tab', padding=[10, 5], font=('Segoe UI', 10))
        self.style.configure('TButton', font=('Segoe UI', 10), padding=5)
        self.style.configure('TLabel', font=('Segoe UI', 10), background='#f0f0f0')
        self.style.configure('Header.TLabel', font=('Segoe UI', 14, 'bold'), background='#f0f0f0')
        self.style.configure('Output.TLabel', font=('Consolas', 10), background='#ffffff')
        self.style.configure('TEntry', font=('Segoe UI', 10))
        
        # Create colored buttons
        self.style.configure('Generate.TButton', background='#4CAF50', foreground='white')
        self.style.configure('Load.TButton', background='#2196F3', foreground='white')
        self.style.configure('Export.TButton', background='#FF9800', foreground='white')
    
    def init_song_tab(self):
        """Initialize the Song Data Generator tab"""
        # Title
        ttk.Label(self.song_tab, text="Song Data Generator", style='Header.TLabel').grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 10))
        
        # Input frame
        input_frame = ttk.LabelFrame(self.song_tab, text="Song Parameters", padding=10)
        input_frame.grid(row=1, column=0, columnspan=4, sticky="ew", padx=5, pady=5)
        
        # Stage
        ttk.Label(input_frame, text="Stage:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.stage_var = tk.StringVar(value="stage")
        ttk.Entry(input_frame, textvariable=self.stage_var, width=30).grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        # Character 1
        ttk.Label(input_frame, text="Character 1:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.char1_var = tk.StringVar(value="boyfriend")
        ttk.Entry(input_frame, textvariable=self.char1_var, width=30).grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        
        # Character 2
        ttk.Label(input_frame, text="Character 2:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.char2_var = tk.StringVar(value="dad")
        ttk.Entry(input_frame, textvariable=self.char2_var, width=30).grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        
        # Character 1 Position
        ttk.Label(input_frame, text="Char 1 Position (X, Y):").grid(row=1, column=2, sticky="w", padx=5, pady=5)
        self.pos1_x_var = tk.StringVar(value="430")
        self.pos1_y_var = tk.StringVar(value="70")
        pos1_frame = ttk.Frame(input_frame)
        pos1_frame.grid(row=1, column=3, sticky="ew", padx=5, pady=5)
        ttk.Entry(pos1_frame, textvariable=self.pos1_x_var, width=5).pack(side=tk.LEFT, padx=2)
        ttk.Label(pos1_frame, text=",").pack(side=tk.LEFT)
        ttk.Entry(pos1_frame, textvariable=self.pos1_y_var, width=5).pack(side=tk.LEFT, padx=2)
        
        # Character 2 Position
        ttk.Label(input_frame, text="Char 2 Position (X, Y):").grid(row=2, column=2, sticky="w", padx=5, pady=5)
        self.pos2_x_var = tk.StringVar(value="340")
        self.pos2_y_var = tk.StringVar(value="70")
        pos2_frame = ttk.Frame(input_frame)
        pos2_frame.grid(row=2, column=3, sticky="ew", padx=5, pady=5)
        ttk.Entry(pos2_frame, textvariable=self.pos2_x_var, width=5).pack(side=tk.LEFT, padx=2)
        ttk.Label(pos2_frame, text=",").pack(side=tk.LEFT)
        ttk.Entry(pos2_frame, textvariable=self.pos2_y_var, width=5).pack(side=tk.LEFT, padx=2)
        
        # Configure grid columns
        input_frame.columnconfigure(1, weight=1)
        input_frame.columnconfigure(3, weight=1)
        
        # Buttons
        button_frame = ttk.Frame(self.song_tab)
        button_frame.grid(row=2, column=0, columnspan=4, sticky="ew", padx=5, pady=10)
        
        ttk.Button(button_frame, text="Generate Song Data", command=self.generate_song_data, style='Generate.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Load from File", command=self.load_song_data, style='Load.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Export to File", command=self.export_song_data, style='Export.TButton').pack(side=tk.LEFT, padx=5)
        
        # Output
        output_frame = ttk.LabelFrame(self.song_tab, text="Generated Song Data", padding=10)
        output_frame.grid(row=3, column=0, columnspan=4, sticky="nsew", padx=5, pady=5)
        
        self.song_output = tk.Text(output_frame, height=12, width=60, font=('Consolas', 10), wrap=tk.WORD)
        self.song_output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Make output rows expandable
        self.song_tab.rowconfigure(3, weight=1)
        
    def init_character_tab(self):
        """Initialize the Character Offset Generator tab"""
        # Title
        ttk.Label(self.char_tab, text="Character Offset Generator", style='Header.TLabel').grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))
        
        # Input frame
        input_frame = ttk.LabelFrame(self.char_tab, text="Character Parameters", padding=10)
        input_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        
        # Character type selection
        ttk.Label(input_frame, text="Character Style:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.char_style_var = tk.StringVar(value="Boyfriend")
        
        style_frame = ttk.Frame(input_frame)
        style_frame.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Radiobutton(style_frame, text="Boyfriend", variable=self.char_style_var, value="Boyfriend").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(style_frame, text="Dad", variable=self.char_style_var, value="Dad").pack(side=tk.LEFT, padx=5)
        
        # Buttons
        button_frame = ttk.Frame(self.char_tab)
        button_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=5, pady=10)
        
        ttk.Button(button_frame, text="Generate Offsets", command=self.generate_character_offsets, style='Generate.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Export to File", command=self.export_character_offsets, style='Export.TButton').pack(side=tk.LEFT, padx=5)
        
        # Output
        output_frame = ttk.LabelFrame(self.char_tab, text="Generated Character Offsets", padding=10)
        output_frame.grid(row=3, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)
        
        # Create a scrollable text widget
        self.char_output = tk.Text(output_frame, height=12, width=60, font=('Consolas', 10), wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(output_frame, orient="vertical", command=self.char_output.yview)
        self.char_output.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.char_output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Make output rows expandable
        self.char_tab.rowconfigure(3, weight=1)
    
    def generate_song_data(self):
        """Generate song data and display it"""
        try:
            stage = self.stage_var.get()
            char1 = self.char1_var.get()
            char2 = self.char2_var.get()
            
            # Get positions if provided
            try:
                pos1 = [int(self.pos1_x_var.get()), int(self.pos1_y_var.get())]
            except ValueError:
                pos1 = None
                
            try:
                pos2 = [int(self.pos2_x_var.get()), int(self.pos2_y_var.get())]
            except ValueError:
                pos2 = None
            
            song_data = generate_song_data(stage, char1, char2, pos1, pos2)
            
            # Display formatted JSON
            self.song_output.delete(1.0, tk.END)
            self.song_output.insert(tk.END, json.dumps(song_data, indent=4))
            
            self.song_data = song_data  # Save for export
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate song data: {str(e)}")
    
    def load_song_data(self):
        """Load song data from a file"""
        file_path = filedialog.askopenfilename(
            title="Select Song Data File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                song_data = generate_song_data_from_file(file_path)
                if song_data:
                    # Update UI fields
                    self.stage_var.set(song_data["stage"])
                    self.char1_var.set(song_data["character1"]["Name"])
                    self.char2_var.set(song_data["character2"]["Name"])
                    
                    # Update positions
                    pos1 = song_data["character1"]["pos"]
                    pos2 = song_data["character2"]["pos"]
                    self.pos1_x_var.set(str(pos1[0]))
                    self.pos1_y_var.set(str(pos1[1]))
                    self.pos2_x_var.set(str(pos2[0]))
                    self.pos2_y_var.set(str(pos2[1]))
                    
                    # Display formatted JSON
                    self.song_output.delete(1.0, tk.END)
                    self.song_output.insert(tk.END, json.dumps(song_data, indent=4))
                    
                    self.song_data = song_data  # Save for export
                    
                    messagebox.showinfo("Success", "Song data loaded successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load song data: {str(e)}")
    
    def export_song_data(self):
        """Export song data to a file"""
        if not hasattr(self, 'song_data'):
            messagebox.showwarning("Warning", "No song data to export. Generate data first.")
            return
            
        file_path = filedialog.asksaveasfilename(
            title="Save Song Data",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump(self.song_data, f, indent=4)
                messagebox.showinfo("Success", f"Song data exported to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export song data: {str(e)}")
    
    def generate_character_offsets(self):
        """Generate character offsets and display them"""
        try:
            char_style = self.char_style_var.get()
            offsets = gen_character_offsets(char_style)
            
            # Display formatted JSON
            self.char_output.delete(1.0, tk.END)
            self.char_output.insert(tk.END, json.dumps(offsets, indent=4))
            
            self.char_offsets = offsets  # Save for export
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate character offsets: {str(e)}")
    
    def export_character_offsets(self):
        """Export character offsets to a file"""
        if not hasattr(self, 'char_offsets'):
            messagebox.showwarning("Warning", "No character offsets to export. Generate data first.")
            return
            
        file_path = filedialog.asksaveasfilename(
            title="Save Character Offsets",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump(self.char_offsets, f, indent=4)
                messagebox.showinfo("Success", f"Character offsets exported to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export character offsets: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = MorphicDataGeneratorApp(root)
    root.mainloop()
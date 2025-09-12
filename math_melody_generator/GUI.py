import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import scrolledtext
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from main import function_to_midi
import os
import time
from pygame import mixer
import tempfile

class MelodyGeneratorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Math Melody Generator")
        self.root.geometry("900x650")
        self.root.minsize(820, 560)
        
        # Initialize pygame mixer for audio playback
        mixer.init()
        
        # UI state and theme
        self.is_dark_mode = True
        self.temp_midi_path = None
        
        # Styles
        self.style = ttk.Style()
        try:
            self.style.theme_use('clam')
        except tk.TclError:
            pass
        self.apply_theme(self.is_dark_mode)
        
        self.create_widgets()
        self.bind_shortcuts()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Menu bar
        self.menu = tk.Menu(self.root)
        file_menu = tk.Menu(self.menu, tearoff=0)
        file_menu.add_command(label="Generate	Ctrl+G", command=self.generate_midi)
        file_menu.add_command(label="Save...", command=self.save_midi)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_close)
        self.menu.add_cascade(label="File", menu=file_menu)
        help_menu = tk.Menu(self.menu, tearoff=0)
        help_menu.add_command(label="About", command=lambda: messagebox.showinfo("About", "Math Melody Generator\nwith microtonal export"))
        help_menu.add_command(label="Function Help", command=self.show_function_help)
        self.menu.add_cascade(label="Help", menu=help_menu)
        self.root.config(menu=self.menu)

        # Header with title and theme toggle
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 8))
        header_label = ttk.Label(header_frame, text="🎵 Math Melody Generator", style='Header.TLabel')
        header_label.pack(side=tk.LEFT)
        self.theme_var = tk.BooleanVar(value=self.is_dark_mode)
        self.theme_toggle = ttk.Checkbutton(header_frame, text="Dark mode", variable=self.theme_var, command=self.toggle_theme, style='Toggle.TCheckbutton')
        self.theme_toggle.pack(side=tk.RIGHT)

        # Input frame
        input_frame = ttk.LabelFrame(main_frame, text="Function Parameters", padding="10")
        input_frame.pack(fill=tk.X, pady=5)
        
        # Preset and Function input
        ttk.Label(input_frame, text="Preset:").grid(row=0, column=0, sticky=tk.W)
        self.preset_combo = ttk.Combobox(input_frame, state='readonly', values=[
            "sin(x)",
            "cos(x)",
            "sin(x) + cos(2*x)",
            "exp(-abs(x)) * sin(5*x)",
            "sqrt(abs(x)) * sin(2*x)",
            "tan(x)"
        ], width=37)
        self.preset_combo.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        self.preset_combo.bind('<<ComboboxSelected>>', self.on_preset_change)

        ttk.Label(input_frame, text="Function (use x as variable):").grid(row=1, column=0, sticky=tk.W)
        self.function_entry = ttk.Entry(input_frame, width=40)
        self.function_entry.grid(row=1, column=1, padx=5, pady=5)
        self.function_entry.insert(0, "sin(x)")
        
        # X range
        ttk.Label(input_frame, text="X Range (min,max):").grid(row=2, column=0, sticky=tk.W)
        self.x_range_entry = ttk.Entry(input_frame, width=40)
        self.x_range_entry.grid(row=2, column=1, padx=5, pady=5)
        self.x_range_entry.insert(0, "-6.28,6.28")  # -2π to 2π
        self.x_range_entry.bind('<KeyRelease>', self.on_x_range_entry_change)
        
        # Min/Max sliders
        slider_frame = ttk.Frame(input_frame)
        slider_frame.grid(row=3, column=0, columnspan=3, sticky=tk.EW, pady=(0,5))
        
        # Configure columns for proper spacing
        slider_frame.columnconfigure(1, weight=1)
        slider_frame.columnconfigure(3, weight=1)
        
        ttk.Label(slider_frame, text="Min:").grid(row=0, column=0, sticky=tk.W, padx=(0,5))
        self.x_min_scale = ttk.Scale(slider_frame, from_=-20, to=20, orient=tk.HORIZONTAL, command=self.on_x_range_slider)
        self.x_min_scale.grid(row=0, column=1, sticky=tk.EW)
        self.x_min_scale.set(-6.28)
        
        ttk.Label(slider_frame, text="Max:").grid(row=0, column=2, sticky=tk.W, padx=(10,5))
        self.x_max_scale = ttk.Scale(slider_frame, from_=-20, to=20, orient=tk.HORIZONTAL, command=self.on_x_range_slider)
        self.x_max_scale.grid(row=0, column=3, sticky=tk.EW)
        self.x_max_scale.set(6.28)
        
        self.reset_range_btn = ttk.Button(input_frame, text="Reset", command=self.reset_range)
        self.reset_range_btn.grid(row=2, column=2, padx=5)
        input_frame.columnconfigure(1, weight=1)
        
        # Number of notes
        ttk.Label(input_frame, text="Number of notes:").grid(row=3, column=0, sticky=tk.W)
        self.notes_entry = ttk.Entry(input_frame, width=10)
        self.notes_entry.grid(row=3, column=1, padx=(5, 10), pady=5, sticky=tk.W)
        self.notes_entry.insert(0, "32")
        self.notes_scale = ttk.Scale(input_frame, from_=8, to=128, orient=tk.HORIZONTAL, command=self.on_notes_scale)
        self.notes_scale.set(32)
        self.notes_scale.grid(row=3, column=1, padx=(100, 5), pady=5, sticky=tk.EW)
        input_frame.columnconfigure(1, weight=1)

        # Playback & synthesis parameters
        ttk.Label(input_frame, text="Tempo (BPM):").grid(row=4, column=0, sticky=tk.W)
        self.tempo_spin = ttk.Spinbox(input_frame, from_=40, to=240, width=8)
        self.tempo_spin.grid(row=4, column=1, sticky=tk.W, padx=5, pady=5)
        self.tempo_spin.insert(0, "120")

        ttk.Label(input_frame, text="Velocity (0-127):").grid(row=5, column=0, sticky=tk.W)
        self.velocity_spin = ttk.Spinbox(input_frame, from_=0, to=127, width=8)
        self.velocity_spin.grid(row=5, column=1, sticky=tk.W, padx=5, pady=5)
        self.velocity_spin.insert(0, "100")

        ttk.Label(input_frame, text="Duration (beats):").grid(row=6, column=0, sticky=tk.W)
        self.duration_spin = ttk.Spinbox(input_frame, from_=0.1, to=4.0, increment=0.1, width=8)
        self.duration_spin.grid(row=6, column=1, sticky=tk.W, padx=5, pady=5)
        self.duration_spin.insert(0, "0.5")

        # MIDI instrument names (General MIDI 1)
        self.midi_instruments = [
            "Acoustic Grand Piano", "Bright Acoustic Piano", "Electric Grand Piano", 
            "Honky-tonk Piano", "Electric Piano 1", "Electric Piano 2", "Harpsichord", 
            "Clavinet", "Celesta", "Glockenspiel", "Music Box", "Vibraphone", 
            "Marimba", "Xylophone", "Tubular Bells", "Dulcimer", "Drawbar Organ", 
            "Percussive Organ", "Rock Organ", "Church Organ", "Reed Organ", 
            "Accordion", "Harmonica", "Tango Accordion", "Acoustic Guitar (nylon)", 
            "Acoustic Guitar (steel)", "Electric Guitar (jazz)", "Electric Guitar (clean)", 
            "Electric Guitar (muted)", "Overdriven Guitar", "Distortion Guitar", 
            "Guitar Harmonics", "Acoustic Bass", "Electric Bass (finger)", 
            "Electric Bass (pick)", "Fretless Bass", "Slap Bass 1", "Slap Bass 2", 
            "Synth Bass 1", "Synth Bass 2", "Violin", "Viola", "Cello", "Contrabass", 
            "Tremolo Strings", "Pizzicato Strings", "Orchestral Harp", "Timpani", 
            "String Ensemble 1", "String Ensemble 2", "Synth Strings 1", "Synth Strings 2", 
            "Choir Aahs", "Voice Oohs", "Synth Voice", "Orchestra Hit", "Trumpet", 
            "Trombone", "Tuba", "Muted Trumpet", "French Horn", "Brass Section", 
            "Synth Brass 1", "Synth Brass 2", "Soprano Sax", "Alto Sax", "Tenor Sax", 
            "Baritone Sax", "Oboe", "English Horn", "Bassoon", "Clarinet", "Piccolo", 
            "Flute", "Recorder", "Pan Flute", "Blown Bottle", "Shakuhachi", "Whistle", 
            "Ocarina", "Lead 1 (square)", "Lead 2 (sawtooth)", "Lead 3 (calliope)", 
            "Lead 4 (chiff)", "Lead 5 (charang)", "Lead 6 (voice)", "Lead 7 (fifths)", 
            "Lead 8 (bass + lead)", "Pad 1 (new age)", "Pad 2 (warm)", "Pad 3 (polysynth)", 
            "Pad 4 (choir)", "Pad 5 (bowed)", "Pad 6 (metallic)", "Pad 7 (halo)", 
            "Pad 8 (sweep)", "FX 1 (rain)", "FX 2 (soundtrack)", "FX 3 (crystal)", 
            "FX 4 (atmosphere)", "FX 5 (brightness)", "FX 6 (goblins)", "FX 7 (echoes)", 
            "FX 8 (sci-fi)", "Sitar", "Banjo", "Shamisen", "Koto", "Kalimba", 
            "Bagpipe", "Fiddle", "Shanai", "Tinkle Bell", "Agogo", "Steel Drums", 
            "Woodblock", "Taiko Drum", "Melodic Tom", "Synth Drum", "Reverse Cymbal", 
            "Guitar Fret Noise", "Breath Noise", "Seashore", "Bird Tweet", "Telephone Ring", 
            "Helicopter", "Applause", "Gunshot"
        ]

        ttk.Label(input_frame, text="Instrument:").grid(row=7, column=0, sticky=tk.W)
        instrument_frame = ttk.Frame(input_frame)
        instrument_frame.grid(row=7, column=1, sticky=tk.W, padx=5, pady=5)
        
        self.instrument_spin = ttk.Spinbox(instrument_frame, from_=0, to=127, width=3, command=self.update_instrument_name)
        self.instrument_spin.pack(side=tk.LEFT)
        self.instrument_spin.insert(0, "0")
        
        self.instrument_label = ttk.Label(instrument_frame, text=self.midi_instruments[0])
        self.instrument_label.pack(side=tk.LEFT, padx=5)

        ttk.Label(input_frame, text="Transpose (semitones):").grid(row=8, column=0, sticky=tk.W)
        self.transpose_spin = ttk.Spinbox(input_frame, from_=-24, to=24, width=8)
        self.transpose_spin.grid(row=8, column=1, sticky=tk.W, padx=5, pady=5)
        self.transpose_spin.insert(0, "0")

        self.loop_var = tk.BooleanVar(value=False)
        self.loop_check = ttk.Checkbutton(input_frame, text="Loop playback", variable=self.loop_var)
        self.loop_check.grid(row=9, column=1, sticky=tk.W, padx=5, pady=(0,5))

        # Microtonal export
        self.microtonal_var = tk.BooleanVar(value=False)
        self.microtonal_check = ttk.Checkbutton(input_frame, text="Enable microtonal (pitch bend)", variable=self.microtonal_var)
        self.microtonal_check.grid(row=10, column=1, sticky=tk.W, padx=5, pady=(0,5))

        ttk.Label(input_frame, text="Bend range (±semitones):").grid(row=11, column=0, sticky=tk.W)
        self.bend_range_spin = ttk.Spinbox(input_frame, from_=1, to=24, width=8)
        self.bend_range_spin.grid(row=11, column=1, sticky=tk.W, padx=5, pady=5)
        self.bend_range_spin.insert(0, "2")

        # Reset bend toggle
        self.reset_bend_var = tk.BooleanVar(value=True)
        self.reset_bend_check = ttk.Checkbutton(input_frame, text="Reset bend after note", variable=self.reset_bend_var)
        self.reset_bend_check.grid(row=12, column=1, sticky=tk.W, padx=5, pady=(0,5))

        # Auto-save controls
        autosave_frame = ttk.Frame(input_frame)
        autosave_frame.grid(row=13, column=0, columnspan=3, sticky=tk.EW, pady=(5,0))
        self.autosave_var = tk.BooleanVar(value=False)
        autosave_check = ttk.Checkbutton(autosave_frame, text="Auto-save to", variable=self.autosave_var)
        autosave_check.pack(side=tk.LEFT)
        self.autosave_entry = ttk.Entry(autosave_frame, width=32)
        self.autosave_entry.pack(side=tk.LEFT, padx=6)
        self.autosave_entry.insert(0, "output/generated_melody.mid")
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        self.generate_btn = ttk.Button(button_frame, text="Generate MIDI", command=self.generate_midi, style='Accent.TButton')
        self.generate_btn.pack(side=tk.LEFT, padx=5)
        
        self.play_btn = ttk.Button(button_frame, text="Play", command=self.play_midi, state=tk.DISABLED)
        self.play_btn.pack(side=tk.LEFT, padx=5)
        self.stop_btn = ttk.Button(button_frame, text="Stop", command=self.stop_midi, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        self.save_btn = ttk.Button(button_frame, text="Save...", command=self.save_midi, state=tk.DISABLED)
        self.save_btn.pack(side=tk.LEFT, padx=5)

        # Volume control
        vol_container = ttk.Frame(button_frame)
        vol_container.pack(side=tk.RIGHT)
        vol_label = ttk.Label(vol_container, text="Volume")
        vol_label.pack(side=tk.LEFT, padx=(0,4))
        self.volume_scale = ttk.Scale(vol_container, from_=0, to=100, orient=tk.HORIZONTAL, command=self.on_volume_change)
        self.volume_scale.set(70)
        self.volume_scale.pack(side=tk.LEFT, padx=(0,10))
        
        # Plot frame
        plot_frame = ttk.LabelFrame(main_frame, text="Function Plot", padding="10")
        plot_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.figure = plt.Figure(figsize=(6, 4), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Log panel
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="4")
        log_frame.pack(fill=tk.BOTH, expand=False, pady=5)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=5)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Status bar
        self.status = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W, style='Status.TLabel')
        self.status.pack(fill=tk.X)

        # Initial plot theme
        self.update_plot_theme()
        self.log("UI initialized")
        
    def parse_x_range(self, x_range_str):
        """Parse X range input with validation
        
        Args:
            x_range_str: String in format "min,max"
            
        Returns:
            tuple: (min, max) values
            
        Raises:
            ValueError: If input is invalid or min >= max
        """
        try:
            parts = x_range_str.split(',')
            if len(parts) != 2:
                raise ValueError("Please enter range as 'min,max'")
                
            x_min, x_max = map(float, parts)
            
            if x_min >= x_max:
                raise ValueError("Min value must be less than max value")
                
            return (x_min, x_max)
            
        except ValueError as e:
            raise ValueError(f"Invalid range: {str(e)}")
        except Exception:
            raise ValueError("Invalid range format")
    
    def generate_midi(self):
        """Generate MIDI from mathematical function with input validation"""
        function = self.function_entry.get().strip()
        if not function:
            self.status.config(text="Error: Please enter a function")
            self.log("Error: Empty function")
            return
            
        try:
            x_range = self.parse_x_range(self.x_range_entry.get())
        except ValueError as e:
            self.status.config(text=f"Error: {str(e)}")
            self.log(f"Error: Invalid X range - {str(e)}")
            return
            
        try:
            num_notes = int(self.notes_entry.get())
            if num_notes < 8 or num_notes > 128:
                raise ValueError("Number of notes must be between 8 and 128")
        except ValueError as e:
            self.status.config(text=f"Error: {str(e)}")
            self.log(f"Error: Invalid note count - {str(e)}")
            return
            
        # Generate MIDI
        # Collect parameters
        try:
            tempo = int(self.tempo_spin.get())
            if tempo < 40 or tempo > 240:
                raise ValueError("Tempo must be between 40 and 240 BPM")
        except ValueError as e:
            self.status.config(text=f"Error: {str(e)}")
            self.log(f"Error: Invalid tempo - {str(e)}")
            return
            
        try:
            velocity = int(self.velocity_spin.get())
            if velocity < 0 or velocity > 127:
                raise ValueError("Velocity must be between 0 and 127")
        except ValueError as e:
            self.status.config(text=f"Error: {str(e)}")
            self.log(f"Error: Invalid velocity - {str(e)}")
            return
            
        try:
            note_duration = float(self.duration_spin.get())
            if note_duration <= 0 or note_duration > 4.0:
                raise ValueError("Duration must be between 0.1 and 4.0 beats")
        except ValueError as e:
            self.status.config(text=f"Error: {str(e)}")
            self.log(f"Error: Invalid duration - {str(e)}")
            return
            
        try:
            instrument = int(self.instrument_spin.get())
            if instrument < 0 or instrument > 127:
                raise ValueError("Instrument must be between 0 and 127")
        except ValueError as e:
            self.status.config(text=f"Error: {str(e)}")
            self.log(f"Error: Invalid instrument - {str(e)}")
            return
            
        try:
            transpose = int(self.transpose_spin.get())
            if transpose < -24 or transpose > 24:
                raise ValueError("Transpose must be between -24 and 24 semitones")
        except ValueError as e:
            self.status.config(text=f"Error: {str(e)}")
            self.log(f"Error: Invalid transpose - {str(e)}")
            return

        try:
            microtonal = bool(self.microtonal_var.get())
        except Exception:
            microtonal = False
            
        try:
            bend_range = int(self.bend_range_spin.get())
            if bend_range < 1 or bend_range > 24:
                raise ValueError("Bend range must be between 1 and 24 semitones")
        except ValueError as e:
            self.status.config(text=f"Error: {str(e)}")
            self.log(f"Error: Invalid bend range - {str(e)}")
            return
            
        try:
            reset_bend = bool(self.reset_bend_var.get())
        except Exception:
            reset_bend = True

        midi = function_to_midi(
            function,
            x_range,
            num_notes,
            tempo=tempo,
            velocity=velocity,
            note_duration=note_duration,
            instrument=instrument,
            transpose=transpose,
            microtonal=microtonal,
            bend_range_semitones=bend_range,
            reset_bend_after_note=reset_bend,
        )
        
        # Save to temp file (don't auto-delete)
        temp_path = os.path.join(tempfile.gettempdir(), f"melody_{int(time.time())}.mid")
        self.temp_midi_path = temp_path
        with open(temp_path, 'wb') as output_file:
            midi.writeFile(output_file)
            
        # Auto-save if enabled
        if self.autosave_var.get():
            target = self.autosave_entry.get().strip()
            if target:
                try:
                    os.makedirs(os.path.dirname(target), exist_ok=True)
                    with open(self.temp_midi_path, 'rb') as src, open(target, 'wb') as dst:
                        dst.write(src.read())
                    self.log(f"Auto-saved: {target}")
                except OSError as e:
                    self.log(f"Auto-save failed: {e}")

        # Update plot
        self.update_plot(function, x_range, num_notes)
        
        # Enable play button
        self.play_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.NORMAL)
        self.save_btn.config(state=tk.NORMAL)
        self.status.config(text="MIDI generated successfully")
        self.log("MIDI generated")
        
    def update_plot(self, function, x_range, num_notes):
        self.ax.clear()
        
        # Use the SafeMathEvaluator from main.py
        from main import SafeMathEvaluator
        evaluator = SafeMathEvaluator()
        
        # Plot the function
        x_vals = np.linspace(x_range[0], x_range[1], 1000)
        y_vals = [evaluator.eval_expression(function, x) for x in x_vals]
        line_color = '#5B9BD5' if not self.is_dark_mode else '#7FB3FF'
        self.ax.plot(x_vals, y_vals, color=line_color, linewidth=2)
        
        # Plot the sampled points
        x_samples = np.linspace(x_range[0], x_range[1], num_notes)
        y_samples = [evaluator.eval_expression(function, x) for x in x_samples]
        self.ax.plot(x_samples, y_samples, 'o', color='#E57373')
        
        self.ax.set_title(f"Function: {function}")
        self.ax.grid(True, alpha=0.3)
        self.canvas.draw()
        
        # Ensure theme persists
        self.update_plot_theme()
        
    def play_midi(self):
        try:
            if not hasattr(self, 'temp_midi_path') or not os.path.exists(self.temp_midi_path):
                self.status.config(text="MIDI file not found")
                return
                
            mixer.music.set_volume(self.volume_scale.get()/100.0)
            mixer.music.load(self.temp_midi_path)
            loops = -1 if self.loop_var.get() else 0
            mixer.music.play(loops=loops)
            self.status.config(text=f"Playing {self.temp_midi_path}...")
            self.log(f"Playing: {self.temp_midi_path}")
        except (FileNotFoundError, Exception) as e:
            self.status.config(text=f"Error: {str(e)}")
            # Print error to console for debugging
            print(f"MIDI playback error: {e}")
            self.log(f"Playback error: {e}")

    def stop_midi(self):
        try:
            mixer.music.stop()
            self.status.config(text="Stopped")
            self.log("Stopped")
        except Exception as e:
            self.status.config(text=f"Error: {str(e)}")

    def save_midi(self):
        if not hasattr(self, 'temp_midi_path') or not os.path.exists(self.temp_midi_path):
            self.status.config(text="Generate a MIDI first")
            return
        
        initial_dir = os.path.abspath(os.path.join(os.getcwd(), "output"))
        os.makedirs(initial_dir, exist_ok=True)
        file_path = filedialog.asksaveasfilename(
            initialdir=initial_dir,
            title="Save MIDI",
            defaultextension=".mid",
            filetypes=(("MIDI files", "*.mid"), ("All files", "*.*")),
            initialfile="generated_melody.mid"
        )
        if file_path:
            try:
                with open(self.temp_midi_path, 'rb') as src, open(file_path, 'wb') as dst:
                    dst.write(src.read())
                self.status.config(text=f"Saved to {file_path}")
                self.log(f"Saved: {file_path}")
            except OSError as e:
                self.status.config(text=f"Save error: {str(e)}")
                self.log(f"Save error: {e}")

    def on_volume_change(self, _value):
        try:
            mixer.music.set_volume(self.volume_scale.get()/100.0)
        except Exception:
            pass

    def bind_shortcuts(self):
        self.root.bind_all('<Control-g>', lambda e: self.generate_midi())
        self.root.bind_all('<Control-s>', lambda e: self.save_midi())
        self.root.bind_all('<space>', lambda e: self.toggle_playback())

    def toggle_playback(self):
        try:
            if mixer.music.get_busy():
                self.stop_midi()
            else:
                self.play_midi()
        except Exception:
            pass

    def on_close(self):
        try:
            mixer.music.stop()
        except Exception:
            pass
        try:
            mixer.quit()
        except Exception:
            pass
        self.root.destroy()

    def log(self, message: str):
        try:
            self.log_text.insert(tk.END, f"{message}\n")
            self.log_text.see(tk.END)
        except Exception:
            pass

    def on_notes_scale(self, value):
        val = int(float(value))
        self.notes_entry.delete(0, tk.END)
        self.notes_entry.insert(0, str(val))
        
    def on_x_range_slider(self, _value):
        min_val = self.x_min_scale.get()
        max_val = self.x_max_scale.get()
        
        # Ensure min < max
        if min_val >= max_val:
            if _value == self.x_min_scale:
                self.x_min_scale.set(max_val - 0.1)
            else:
                self.x_max_scale.set(min_val + 0.1)
            return
            
        self.x_range_entry.delete(0, tk.END)
        self.x_range_entry.insert(0, f"{min_val:.2f},{max_val:.2f}")
        
    def on_x_range_entry_change(self, _event):
        try:
            min_val, max_val = map(float, self.x_range_entry.get().split(','))
            if min_val >= max_val:
                return
            self.x_min_scale.set(min_val)
            self.x_max_scale.set(max_val)
        except ValueError:
            pass

    def on_preset_change(self, _event=None):
        preset = self.preset_combo.get()
        self.function_entry.delete(0, tk.END)
        self.function_entry.insert(0, preset)

    def reset_range(self):
        self.x_range_entry.delete(0, tk.END)
        self.x_range_entry.insert(0, "-6.28,6.28")
        self.x_min_scale.set(-6.28)
        self.x_max_scale.set(6.28)

    def update_instrument_name(self):
        """Update the instrument name label when the instrument number changes"""
        try:
            instrument_num = int(self.instrument_spin.get())
            if 0 <= instrument_num <= 127:
                self.instrument_label.config(text=self.midi_instruments[instrument_num])
            else:
                self.instrument_label.config(text="Invalid instrument")
        except ValueError:
            self.instrument_label.config(text="Invalid instrument")

    def toggle_theme(self):
        self.is_dark_mode = bool(self.theme_var.get())
        self.apply_theme(self.is_dark_mode)
        self.update_plot_theme()

    def apply_theme(self, dark: bool):
        bg = '#121212' if dark else '#F7F7F7'
        fg = '#FFFFFF' if dark else '#222222'
        accent = '#4F8EF7'
        frame_bg = '#1E1E1E' if dark else '#FFFFFF'
        muted = '#A0A0A0' if dark else '#555555'

        self.style.configure('TFrame', background=bg)
        self.style.configure('TLabelframe', background=bg, foreground=fg)
        self.style.configure('TLabelframe.Label', background=bg, foreground=fg)
        self.style.configure('TLabel', background=bg, foreground=fg)
        self.style.configure('Header.TLabel', background=bg, foreground=fg, font=('Segoe UI', 16, 'bold'))
        self.style.configure('TButton', padding=6)
        self.style.configure('Accent.TButton', padding=6, foreground=fg)
        self.style.map('Accent.TButton', background=[('!disabled', accent), ('active', '#3F7DE0')])
        self.style.configure('TEntry', fieldbackground=frame_bg)
        self.style.configure('TCombobox', fieldbackground=frame_bg)
        self.style.configure('Status.TLabel', background=frame_bg, foreground=muted)
        self.style.configure('Toggle.TCheckbutton', background=bg, foreground=fg)

        self.root.configure(background=bg)

    def show_function_help(self):
        """Show detailed help about all functions and parameters"""
        help_text = """Math Melody Generator - Function Help

Function Input:
- Enter a mathematical function using 'x' as the variable
- Supports: +, -, *, /, ** (power), sin, cos, tan, exp, log, sqrt, abs
- Example: "sin(x) + cos(2*x) * exp(-abs(x))"

X Range:
- The range of x values to evaluate the function over
- Format: min,max (e.g. -6.28,6.28 for -2π to 2π)
- Larger ranges will create more dramatic pitch changes

Number of Notes:
- How many discrete notes to generate from the function
- More notes = smoother melody but longer duration
- Range: 8-128 notes

Playback Parameters:
- Tempo: Beats per minute (40-240 BPM)
- Velocity: Note loudness (0-127)
- Duration: Length of each note in beats (0.1-4.0)
- Instrument: Select from 128 General MIDI instruments
- Transpose: Shift pitch up/down in semitones (-24 to +24)

Microtonal Options:
- Enable pitch bend for continuous pitch changes
- Bend range: Maximum pitch deviation (± semitones)
- Reset bend: Return to center pitch after each note

Auto-save:
- Automatically save generated MIDI to specified path
- Path can be relative or absolute

Keyboard Shortcuts:
- Ctrl+G: Generate MIDI
- Ctrl+S: Save MIDI
- Space: Play/Stop
"""
        messagebox.showinfo("Function Help", help_text)

    def update_plot_theme(self):
        if self.is_dark_mode:
            self.figure.set_facecolor('#121212')
            self.ax.set_facecolor('#0E0E0E')
            for spine in self.ax.spines.values():
                spine.set_color('#777777')
            self.ax.tick_params(colors='#DDDDDD')
            self.ax.title.set_color('#FFFFFF')
        else:
            self.figure.set_facecolor('#F7F7F7')
            self.ax.set_facecolor('#FFFFFF')
            for spine in self.ax.spines.values():
                spine.set_color('#999999')
            self.ax.tick_params(colors='#333333')
            self.ax.title.set_color('#222222')
        self.canvas.draw_idle()

def main():
    root = tk.Tk()
    MelodyGeneratorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()

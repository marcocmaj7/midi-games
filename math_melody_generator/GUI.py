import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import tempfile
import time
import numpy as np
from pygame import mixer
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from main import SafeMathEvaluator
from src.midi_synthesizer.midi_generator import function_to_midi


class MelodyGeneratorGUI:
    # MIDI Program/Instrument names
    midi_instruments = [
        "Acoustic Grand Piano", "Bright Acoustic Piano", "Electric Grand Piano", "Honky-tonk Piano",
        "Electric Piano 1", "Electric Piano 2", "Harpsichord", "Clavinet", "Celesta", "Glockenspiel",
        "Music Box", "Vibraphone", "Marimba", "Xylophone", "Tubular Bells", "Dulcimer",
        "Drawbar Organ", "Percussive Organ", "Rock Organ", "Church Organ", "Reed Organ", "Accordion",
        "Harmonica", "Tango Accordion", "Acoustic Guitar (nylon)", "Acoustic Guitar (steel)",
        "Electric Guitar (jazz)", "Electric Guitar (clean)", "Electric Guitar (muted)", 
        "Overdriven Guitar", "Distortion Guitar", "Guitar harmonics", "Acoustic Bass",
        "Electric Bass (finger)", "Electric Bass (pick)", "Fretless Bass", "Slap Bass 1",
        "Slap Bass 2", "Synth Bass 1", "Synth Bass 2", "Violin", "Viola", "Cello",
        "Contrabass", "Tremolo Strings", "Pizzicato Strings", "Orchestral Harp", "Timpani",
        "String Ensemble 1", "String Ensemble 2", "Synth Strings 1", "Synth Strings 2",
        "Choir Aahs", "Voice Oohs", "Synth Voice", "Orchestra Hit", "Trumpet", "Trombone",
        "Tuba", "Muted Trumpet", "French Horn", "Brass Section", "Synth Brass 1", 
        "Synth Brass 2", "Soprano Sax", "Alto Sax", "Tenor Sax", "Baritone Sax", "Oboe",
        "English Horn", "Bassoon", "Clarinet", "Piccolo", "Flute", "Recorder", "Pan Flute",
        "Blown Bottle", "Shakuhachi", "Whistle", "Ocarina", "Lead 1 (square)", 
        "Lead 2 (sawtooth)", "Lead 3 (calliope)", "Lead 4 (chiff)", "Lead 5 (charang)",
        "Lead 6 (voice)", "Lead 7 (fifths)", "Lead 8 (bass + lead)", "Pad 1 (new age)",
        "Pad 2 (warm)", "Pad 3 (polysynth)", "Pad 4 (choir)", "Pad 5 (bowed)",
        "Pad 6 (metallic)", "Pad 7 (halo)", "Pad 8 (sweep)", "FX 1 (rain)", 
        "FX 2 (soundtrack)", "FX 3 (crystal)", "FX 4 (atmosphere)", "FX 5 (brightness)",
        "FX 6 (goblins)", "FX 7 (echoes)", "FX 8 (sci-fi)", "Sitar", "Banjo", "Shamisen",
        "Koto", "Kalimba", "Bag pipe", "Fiddle", "Shanai", "Tinkle Bell", "Agogo",
        "Steel Drums", "Woodblock", "Taiko Drum", "Melodic Tom", "Synth Drum",
        "Reverse Cymbal", "Guitar Fret Noise", "Breath Noise", "Seashore", "Bird Tweet",
        "Telephone Ring", "Helicopter", "Applause", "Gunshot"
    ]

    def __init__(self, root):
        """Initialize the application"""
        self.root = root
        self.root.title("Math Melody Generator")
        
        # Initialize mixer for MIDI playback
        mixer.init()
        
        # Initialize variables
        self.temp_midi_path = None
        self.is_dark_mode = False
        
        # Create required directories
        os.makedirs(os.path.join(os.getcwd(), "output"), exist_ok=True)
        os.makedirs(os.path.join(os.getcwd(), "presets"), exist_ok=True)
        
        # Create matplotlib figure
        self.fig, self.ax = plt.subplots(figsize=(8, 4))
        
        # Setup style
        self.style = ttk.Style()
        self.theme_var = tk.BooleanVar(value=False)
        
        # Create widgets and bind shortcuts
        self.create_widgets()
        self.bind_shortcuts()
        
        # Setup window close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Function input frame
        function_frame = ttk.LabelFrame(main_frame, text="Function", padding="5")
        function_frame.pack(fill=tk.X, pady=5)
        
        self.function_entry = ttk.Entry(function_frame, width=40)
        self.function_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.function_entry.insert(0, "sin(x)")
        
        # X range frame
        range_frame = ttk.LabelFrame(main_frame, text="X Range", padding="5")
        range_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(range_frame, text="Start:").pack(side=tk.LEFT, padx=5)
        self.x_start = ttk.Spinbox(range_frame, from_=-100, to=100, increment=0.1, width=10)
        self.x_start.pack(side=tk.LEFT, padx=5)
        self.x_start.insert(0, "0")
        
        ttk.Label(range_frame, text="End:").pack(side=tk.LEFT, padx=5)
        self.x_end = ttk.Spinbox(range_frame, from_=-100, to=100, increment=0.1, width=10)
        self.x_end.pack(side=tk.LEFT, padx=5)
        self.x_end.insert(0, "6.28")
        
        # Note parameters frame
        note_frame = ttk.LabelFrame(main_frame, text="Note Parameters", padding="5")
        note_frame.pack(fill=tk.X, pady=5)
        
        # Number of notes
        ttk.Label(note_frame, text="Number of notes:").grid(row=0, column=0, padx=5)
        self.notes_entry = ttk.Spinbox(note_frame, from_=8, to=128, width=10)
        self.notes_entry.grid(row=0, column=1, padx=5)
        self.notes_entry.insert(0, "32")
        
        # Tempo
        ttk.Label(note_frame, text="Tempo (BPM):").grid(row=0, column=2, padx=5)
        self.tempo_spin = ttk.Spinbox(note_frame, from_=40, to=240, width=10)
        self.tempo_spin.grid(row=0, column=3, padx=5)
        self.tempo_spin.insert(0, "120")
        
        # Note velocity
        ttk.Label(note_frame, text="Velocity:").grid(row=1, column=0, padx=5)
        self.velocity_spin = ttk.Spinbox(note_frame, from_=0, to=127, width=10)
        self.velocity_spin.grid(row=1, column=1, padx=5)
        self.velocity_spin.insert(0, "100")
        
        # Note duration
        ttk.Label(note_frame, text="Duration:").grid(row=1, column=2, padx=5)
        self.duration_spin = ttk.Spinbox(note_frame, from_=0.1, to=4.0, increment=0.1, width=10)
        self.duration_spin.grid(row=1, column=3, padx=5)
        self.duration_spin.insert(0, "0.5")
        
        # Instrument selection
        ttk.Label(note_frame, text="Instrument:").grid(row=2, column=0, padx=5)
        self.instrument_spin = ttk.Spinbox(note_frame, from_=0, to=127, width=10)
        self.instrument_spin.grid(row=2, column=1, padx=5)
        self.instrument_spin.insert(0, "0")
        
        # Transpose
        ttk.Label(note_frame, text="Transpose:").grid(row=2, column=2, padx=5)
        self.transpose_spin = ttk.Spinbox(note_frame, from_=-24, to=24, width=10)
        self.transpose_spin.grid(row=2, column=3, padx=5)
        self.transpose_spin.insert(0, "0")
        
        # Microtonal options
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding="5")
        options_frame.pack(fill=tk.X, pady=5)
        
        self.microtonal_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Microtonal", variable=self.microtonal_var).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(options_frame, text="Bend range:").pack(side=tk.LEFT, padx=5)
        self.bend_range_spin = ttk.Spinbox(options_frame, from_=1, to=24, width=5)
        self.bend_range_spin.pack(side=tk.LEFT, padx=5)
        self.bend_range_spin.insert(0, "2")
        
        self.reset_bend_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Reset bend", variable=self.reset_bend_var).pack(side=tk.LEFT, padx=5)
        
        # Plot frame
        plot_frame = ttk.Frame(main_frame)
        plot_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Control buttons frame
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=5)
        
        self.generate_btn = ttk.Button(control_frame, text="Generate", command=self.generate_midi)
        self.generate_btn.pack(side=tk.LEFT, padx=5)
        
        self.play_btn = ttk.Button(control_frame, text="Play", command=self.play_midi, state=tk.DISABLED)
        self.play_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(control_frame, text="Stop", command=self.stop_midi, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.save_btn = ttk.Button(control_frame, text="Save", command=self.save_midi, state=tk.DISABLED)
        self.save_btn.pack(side=tk.LEFT, padx=5)
        
        # Volume control
        ttk.Label(control_frame, text="Volume:").pack(side=tk.LEFT, padx=5)
        self.volume_scale = ttk.Scale(control_frame, from_=0, to=100, orient=tk.HORIZONTAL)
        self.volume_scale.pack(side=tk.LEFT, padx=5)
        self.volume_scale.set(80)
        
        self.loop_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(control_frame, text="Loop", variable=self.loop_var).pack(side=tk.LEFT, padx=5)
        
        # Status bar
        self.status = ttk.Label(main_frame, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status.pack(fill=tk.X, pady=5)
        
        # Auto-save frame
        autosave_frame = ttk.Frame(main_frame)
        autosave_frame.pack(fill=tk.X, pady=5)
        
        self.autosave_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(autosave_frame, text="Auto-save to:", variable=self.autosave_var).pack(side=tk.LEFT, padx=5)
        
        self.autosave_entry = ttk.Entry(autosave_frame)
        self.autosave_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.autosave_entry.insert(0, os.path.join(os.getcwd(), "output", "generated_melody.mid"))
            
    def log(self, message):
        print(f"[MelodyGen] {message}")
        
    def generate_midi(self):
        """Generate MIDI file from current function and parameters"""
        self.temp_midi_path = None # Ensure temp_midi_path is reset
        function = self.function_entry.get().strip()
        if not function:
            self.status.config(text="Please enter a function")
            return

        try:
            # Get X range
            x_start = float(self.x_start.get())
            x_end = float(self.x_end.get())
            if x_end <= x_start:
                raise ValueError("End X must be greater than Start X")
            x_range = (x_start, x_end)
            
            # Get number of notes and validate
            num_notes = int(self.notes_entry.get())
            if num_notes < 8 or num_notes > 128:
                raise ValueError("Number of notes must be between 8 and 128")
                
            # Create evaluator and sample function
            evaluator = SafeMathEvaluator()
            x_samples = np.linspace(x_range[0], x_range[1], num_notes)
            y_values = [evaluator.eval_expression(function, x) for x in x_samples]
            
            # Check for invalid values
            if any(y is None for y in y_values):
                raise ValueError("Function evaluation failed")
                
            # Get MIDI parameters
            tempo = int(self.tempo_spin.get())
            if tempo < 40 or tempo > 240:
                raise ValueError("Tempo must be between 40 and 240 BPM")
                
            velocity = int(self.velocity_spin.get())
            if velocity < 0 or velocity > 127:
                raise ValueError("Velocity must be between 0 and 127")
                
            note_duration = float(self.duration_spin.get())
            if note_duration <= 0 or note_duration > 4.0:
                raise ValueError("Duration must be between 0.1 and 4.0 beats")
                
            instrument = int(self.instrument_spin.get())
            if instrument < 0 or instrument > 127:
                raise ValueError("Instrument must be between 0 and 127")
                
            transpose = int(self.transpose_spin.get())
            if transpose < -24 or transpose > 24:
                raise ValueError("Transpose must be between -24 and 24 semitones")
                
            microtonal = bool(self.microtonal_var.get())
                
            bend_range = int(self.bend_range_spin.get())
            if bend_range < 1 or bend_range > 24:
                raise ValueError("Bend range must be between 1 and 24 semitones")
                
            reset_bend = bool(self.reset_bend_var.get())
            
            # If all validations passed, proceed to MIDI generation and saving
            midi = function_to_midi(
                y_values,
                tempo=tempo,
                velocity=velocity,
                note_duration=note_duration,
                instrument=instrument,
                transpose=transpose,
                microtonal=microtonal
            )
            
            temp_path = os.path.join(tempfile.gettempdir(), f"melody_{int(time.time())}.mid")
            self.temp_midi_path = temp_path # Assign temp_path here
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

        except Exception as e: # Catch errors during any part of the process
            self.status.config(text=f"Error: {str(e)}")
            self.log(f"Error: {str(e)}")
            self.temp_midi_path = None # Ensure path is None if any error occurs
            self.play_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.DISABLED)
            self.save_btn.config(state=tk.DISABLED)
            return
        
    def update_plot(self, function, x_range, num_notes):
        self.ax.clear()
        
        # Plot the function
        x_vals = np.linspace(x_range[0], x_range[1], 1000)
        evaluator = SafeMathEvaluator()
        y_vals = [evaluator.eval_expression(function, x) for x in x_vals]
        
        if any(y is None for y in y_vals):
            self.status.config(text="Error: Function evaluation failed")
            return
            
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
        
    def update_plot_theme(self):
        if self.is_dark_mode:
            plt.style.use('dark_background')
            self.fig.set_facecolor('#2D2D2D')
            self.ax.set_facecolor('#2D2D2D')
        else:
            plt.style.use('default')
            self.fig.set_facecolor('white')
            self.ax.set_facecolor('white')
        self.canvas.draw()
        
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
        """Save the generated MIDI file to a user-selected location"""
        if not hasattr(self, 'temp_midi_path') or not os.path.exists(self.temp_midi_path):
            self.status.config(text="Generate a MIDI first")
            return
        
        # Setup save dialog
        initial_dir = os.path.abspath(os.path.join(os.getcwd(), "output"))
        os.makedirs(initial_dir, exist_ok=True)
        
        # Get save path from user
        file_path = filedialog.asksaveasfilename(
            initialdir=initial_dir,
            title="Save MIDI",
            defaultextension=".mid",
            filetypes=(("MIDI files", "*.mid"), ("All files", "*.*")),
            initialfile="generated_melody.mid"
        )
        
        if file_path:
            try:
                with open(self.temp_midi_path, 'rb') as src:
                    midi_data = src.read()
                with open(file_path, 'wb') as dst:
                    dst.write(midi_data)
                self.status.config(text=f"Saved: {file_path}")
                self.log(f"Saved: {file_path}")
            except OSError as e:
                self.status.config(text=f"Save error: {str(e)}")
                self.log(f"Save error: {e}")

    def on_volume_change(self, _value):
        """Handle volume slider changes"""
        try:
            mixer.music.set_volume(self.volume_scale.get()/100.0)
        except Exception:
            pass

    def bind_shortcuts(self):
        """Setup keyboard shortcuts"""
        self.root.bind_all('<Control-g>', lambda e: self.generate_midi())
        self.root.bind_all('<Control-s>', lambda e: self.save_midi())
        self.root.bind_all('<space>', lambda e: self.toggle_playback())
        
    def toggle_playback(self):
        """Toggle between playing and stopping the MIDI"""
        if not hasattr(self, 'temp_midi_path'):
            return
            
        try:
            if mixer.music.get_busy():
                self.stop_midi()
            else:
                self.play_midi()
        except Exception as e:
            self.status.config(text=f"Playback error: {str(e)}")
            self.log(f"Playback error: {e}")

    def on_close(self):
        """Handle window closing"""
        try:
            # Stop any playing music
            if mixer.music.get_busy():
                mixer.music.stop()
            mixer.quit()
        except Exception:
            pass
            
        # Clean up temp files
        if self.temp_midi_path:
            try:
                os.remove(self.temp_midi_path)
            except OSError: # Catch OSError specifically for file operations
                pass
            except Exception: # Catch any other unexpected exceptions
                pass
                
        # Close matplotlib figure
        try:
            plt.close(self.fig)
        except Exception:
            pass
            
        # Destroy the window
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = MelodyGeneratorGUI(root)
    root.mainloop()

    def on_notes_scale(self, value):
        val = int(float(value))
        self.notes_entry.delete(0, tk.END)
        self.notes_entry.insert(0, str(val))
        
    def on_x_range_slider(self, slider_type, value):
        min_val = self.x_min_scale.get()
        max_val = self.x_max_scale.get()
        
        # Ensure min < max
        if min_val >= max_val:
            if slider_type == 'min':
                min_val = max_val - 0.1
                self.x_min_scale.set(min_val)
            else:
                max_val = min_val + 0.1
                self.x_max_scale.set(max_val)
            
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

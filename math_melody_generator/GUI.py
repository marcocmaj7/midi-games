import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import tempfile
import time
import numpy as np
from pygame import mixer
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
# Support both package execution (python -m math_melody_generator.GUI)
# and direct script execution (python math_melody_generator/GUI.py)
try:
    from .main import SafeMathEvaluator
    from .src.midi_synthesizer.midi_generator import function_to_midi
    from .src.midi_synthesizer.scales import SCALES
except ImportError:
    import os, sys
    pkg_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(pkg_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from math_melody_generator.main import SafeMathEvaluator
    from math_melody_generator.src.midi_synthesizer.midi_generator import function_to_midi
    from math_melody_generator.src.midi_synthesizer.scales import SCALES

KEY_TO_OFFSET = {
    "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4,
    "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9,
    "A#": 10, "Bb": 10, "B": 11
}
KEY_NAMES = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]


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
        # Reuse a single evaluator instance (avoid repeated instantiation)
        self.evaluator = SafeMathEvaluator()

        # Initialize scale selection variable
        self.scale_var = tk.StringVar(value="chromatic")
        self.available_scales = list(SCALES.keys())

        # Tonality
        self.key_var = tk.StringVar(value="C")
        self.octave_var = tk.IntVar(value=4)
        
        # Function presets and selector state
        self.function_presets = [
            "sin(x)",
            "cos(x)",
            "sin(2*x)",
            "sin(x) + 0.5*sin(2*x)",
            "sin(x)^2",
            "abs(sin(x))",
            "sqrt(abs(sin(x)))",
            "sin(x)*exp(-0.2*x)",
            "1/(1+exp(-x))",
            "sin(x)+sin(3*x)/3+sin(5*x)/5",
            "cos(x)+cos(3*x)/3+cos(5*x)/5",
        ]
        self.function_preset_var = tk.StringVar(value=self.function_presets[0])
        
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
        
        ttk.Label(function_frame, text="Preset:").pack(side=tk.LEFT, padx=5)
        self.function_select = ttk.Combobox(
            function_frame,
            textvariable=self.function_preset_var,
            values=self.function_presets + ["Custom"],
            state="readonly",
            width=28
        )
        self.function_select.pack(side=tk.LEFT, padx=5)
        self.function_select.bind("<<ComboboxSelected>>", self.on_function_preset_changed)
        
        self.function_entry = ttk.Entry(function_frame, width=30)
        self.function_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.function_entry.insert(0, "sin(x)")
        
        # Initialize entry state based on selected preset
        self.on_function_preset_changed()
        
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
        ttk.Label(note_frame, text="Duration (beats):").grid(row=1, column=2, padx=5)
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

        # Tonality frame (Root = Key + Octave)
        tonality_frame = ttk.LabelFrame(main_frame, text="Tonality", padding="5")
        tonality_frame.pack(fill=tk.X, pady=5)
        ttk.Label(tonality_frame, text="Key:").pack(side=tk.LEFT, padx=5)
        self.key_combo = ttk.Combobox(tonality_frame, textvariable=self.key_var, values=KEY_NAMES, state="readonly", width=6)
        self.key_combo.pack(side=tk.LEFT, padx=5)
        ttk.Label(tonality_frame, text="Octave:").pack(side=tk.LEFT, padx=5)
        self.octave_spin = ttk.Spinbox(tonality_frame, from_=-1, to=8, width=6)
        self.octave_spin.pack(side=tk.LEFT, padx=5)
        self.octave_spin.delete(0, tk.END)
        self.octave_spin.insert(0, str(self.octave_var.get()))

        # Range frame (register)
        reg_frame = ttk.LabelFrame(main_frame, text="Register / Range", padding="5")
        reg_frame.pack(fill=tk.X, pady=5)
        ttk.Label(reg_frame, text="Min note:").pack(side=tk.LEFT, padx=5)
        self.min_note_spin = ttk.Spinbox(reg_frame, from_=0, to=127, width=6)
        self.min_note_spin.pack(side=tk.LEFT, padx=5)
        self.min_note_spin.insert(0, "36")
        ttk.Label(reg_frame, text="Max note:").pack(side=tk.LEFT, padx=5)
        self.max_note_spin = ttk.Spinbox(reg_frame, from_=0, to=127, width=6)
        self.max_note_spin.pack(side=tk.LEFT, padx=5)
        self.max_note_spin.insert(0, "96")

        # Scale selection
        scale_frame = ttk.LabelFrame(main_frame, text="Scale", padding="5")
        scale_frame.pack(fill=tk.X, pady=5)
        ttk.Label(scale_frame, text="Scale:").pack(side=tk.LEFT, padx=5)
        self.scale_combo = ttk.Combobox(scale_frame, textvariable=self.scale_var, values=self.available_scales, state="readonly")
        self.scale_combo.pack(side=tk.LEFT, padx=5)

        # Harmony (Chord mode)
        harmony_frame = ttk.LabelFrame(main_frame, text="Harmony", padding="5")
        harmony_frame.pack(fill=tk.X, pady=5)
        ttk.Label(harmony_frame, text="Chord mode:").pack(side=tk.LEFT, padx=5)
        self.chord_mode_var = tk.StringVar(value="none")
        self.chord_combo = ttk.Combobox(harmony_frame, textvariable=self.chord_mode_var, values=["none","power","triad","seventh"], state="readonly", width=10)
        self.chord_combo.pack(side=tk.LEFT, padx=5)
        self.chord_combo.bind("<<ComboboxSelected>>", self.on_chord_mode_changed)

        # Rhythm & Humanization
        rh_frame = ttk.LabelFrame(main_frame, text="Rhythm & Humanization", padding="5")
        rh_frame.pack(fill=tk.X, pady=5)
        ttk.Label(rh_frame, text="Rhythm pattern (beats, comma sep):").pack(side=tk.LEFT, padx=5)
        self.rhythm_entry = ttk.Entry(rh_frame, width=28)
        self.rhythm_entry.pack(side=tk.LEFT, padx=5)
        self.rhythm_entry.insert(0, "")  # empty = use Duration
        
        ttk.Label(rh_frame, text="Swing (0..1):").pack(side=tk.LEFT, padx=5)
        self.swing_scale = ttk.Scale(rh_frame, from_=0.0, to=1.0, orient=tk.HORIZONTAL)
        self.swing_scale.pack(side=tk.LEFT, padx=5)
        self.swing_scale.set(0.0)

        ttk.Label(rh_frame, text="Humanize timing (beats):").pack(side=tk.LEFT, padx=5)
        self.hum_time_spin = ttk.Spinbox(rh_frame, from_=0.0, to=0.5, increment=0.01, width=6)
        self.hum_time_spin.pack(side=tk.LEFT, padx=5)
        self.hum_time_spin.insert(0, "0.00")

        ttk.Label(rh_frame, text="Humanize velocity (+/-):").pack(side=tk.LEFT, padx=5)
        self.hum_vel_spin = ttk.Spinbox(rh_frame, from_=0, to=40, width=6)
        self.hum_vel_spin.pack(side=tk.LEFT, padx=5)
        self.hum_vel_spin.insert(0, "0")

        # Microtonal options
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding="5")
        options_frame.pack(fill=tk.X, pady=5)
        
        self.microtonal_var = tk.BooleanVar(value=False)
        self.microtonal_cb = ttk.Checkbutton(options_frame, text="Microtonal", variable=self.microtonal_var)
        self.microtonal_cb.pack(side=tk.LEFT, padx=5)
        
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
        self.volume_scale = ttk.Scale(control_frame, from_=0, to=100, orient=tk.HORIZONTAL, command=self.on_volume_change)
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

        # Ensure controls state coherence
        self.on_chord_mode_changed()
            
    def log(self, message):
        print(f"[MelodyGen] {message}")

    # Helpers
    def set_controls_enabled(self, enabled: bool):
        state = tk.NORMAL if enabled else tk.DISABLED
        try:
            self.play_btn.config(state=state)
            self.stop_btn.config(state=state)
            self.save_btn.config(state=state)
        except Exception:
            pass

    def error(self, message: str):
        self.status.config(text=message)
        self.log(message)
        self.set_controls_enabled(False)

    def on_function_preset_changed(self, event=None):
        """Handle changes in the function preset combobox."""
        selected = self.function_preset_var.get() if hasattr(self, "function_preset_var") else None
        if selected == "Custom":
            # Allow manual editing
            try:
                self.function_entry.config(state=tk.NORMAL)
            except Exception:
                pass
            if not self.function_entry.get().strip():
                self.function_entry.insert(0, "sin(x)")
            if hasattr(self, "status"):
                self.status.config(text="Custom function mode")
        else:
            # Apply preset and lock entry to avoid accidental edits
            try:
                self.function_entry.config(state=tk.NORMAL)
                self.function_entry.delete(0, tk.END)
                expr = self.function_select.get() if hasattr(self, "function_select") else (selected or "sin(x)")
                self.function_entry.insert(0, expr)
                self.function_entry.config(state="readonly")
            except Exception:
                pass
            if hasattr(self, "status"):
                self.status.config(text=f"Selected preset: {self.function_entry.get()}")

    # Input helpers
    def _get_x_range(self):
        x_start = float(self.x_start.get())
        x_end = float(self.x_end.get())
        if x_end <= x_start:
            raise ValueError("End X must be greater than Start X")
        return (x_start, x_end)

    def _get_num_notes(self):
        num_notes = int(self.notes_entry.get())
        if num_notes < 8 or num_notes > 128:
            raise ValueError("Number of notes must be between 8 and 128")
        return num_notes

    def _get_midi_params(self):
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

        return {
            "tempo": tempo,
            "velocity": velocity,
            "note_duration": note_duration,
            "instrument": instrument,
            "transpose": transpose,
        }

    def _get_microtonal_params(self):
        microtonal = bool(self.microtonal_var.get())

        bend_range = int(self.bend_range_spin.get())
        if bend_range < 1 or bend_range > 24:
            raise ValueError("Bend range must be between 1 and 24 semitones")

        reset_bend = bool(self.reset_bend_var.get())

        return {
            "microtonal": microtonal,
            "bend_range": bend_range,
            "reset_bend": reset_bend,
        }

    def _get_tonality_params(self):
        key = self.key_var.get()
        if key not in KEY_TO_OFFSET:
            raise ValueError("Invalid key")
        try:
            octave = int(self.octave_spin.get())
        except Exception:
            octave = self.octave_var.get()
        if octave < -1 or octave > 8:
            raise ValueError("Octave must be between -1 and 8")
        # MIDI: C4 = 60 => 12 * (4 + 1) = 60
        root = 12 * (octave + 1) + KEY_TO_OFFSET[key]
        return {"root": root}

    def _get_range_params(self):
        min_n = int(self.min_note_spin.get())
        max_n = int(self.max_note_spin.get())
        if not (0 <= min_n <= 127 and 0 <= max_n <= 127):
            raise ValueError("Min/Max note must be between 0 and 127")
        if min_n >= max_n:
            raise ValueError("Min note must be less than Max note")
        return {"min_note": min_n, "max_note": max_n}

    def _get_rhythm_params(self):
        txt = self.rhythm_entry.get().strip()
        if txt == "":
            return {"rhythm_pattern": None}
        try:
            parts = [p.strip() for p in txt.replace(";", ",").split(",") if p.strip() != ""]
            pattern = [float(p) for p in parts]
            if any(d <= 0 for d in pattern):
                raise ValueError
            return {"rhythm_pattern": pattern}
        except Exception:
            raise ValueError("Invalid rhythm pattern. Use comma-separated positive numbers (beats), e.g. 0.5,0.5,1.0")

    def _get_humanize_params(self):
        try:
            swing = float(self.swing_scale.get())
        except Exception:
            swing = 0.0
        try:
            hum_t = float(self.hum_time_spin.get())
        except Exception:
            hum_t = 0.0
        try:
            hum_v = int(self.hum_vel_spin.get())
        except Exception:
            hum_v = 0
        if swing < 0 or swing > 1:
            raise ValueError("Swing must be between 0 and 1")
        if hum_t < 0 or hum_t > 0.5:
            raise ValueError("Humanize timing must be between 0.0 and 0.5 beats")
        if hum_v < 0 or hum_v > 40:
            raise ValueError("Humanize velocity must be between 0 and 40")
        return {"swing": swing, "humanize_timing": hum_t, "humanize_velocity": hum_v}

    def _get_chord_mode(self):
        mode = self.chord_mode_var.get()
        if mode not in ["none","power","triad","seventh"]:
            raise ValueError("Invalid chord mode")
        return {"chord_mode": mode}
        
    def _evaluate_function_samples(self, function: str, x_range, num_notes):
        x_samples = np.linspace(x_range[0], x_range[1], num_notes)
        y_values = [self.evaluator.eval_expression(function, x) for x in x_samples]
        if any(y is None for y in y_values):
            raise ValueError("Function evaluation failed")
        return y_values

    def on_chord_mode_changed(self, event=None):
        try:
            mode = self.chord_mode_var.get()
            if mode != "none":
                # Disable microtonal in chords context (engine ignores microtonal with chords)
                self.microtonal_var.set(False)
                self.microtonal_cb.configure(state=tk.DISABLED)
            else:
                self.microtonal_cb.configure(state=tk.NORMAL)
        except Exception:
            pass
        
    def generate_midi(self):
        """Generate MIDI file from current function and parameters"""
        self.temp_midi_path = None  # Ensure temp_midi_path is reset
        function = self.function_entry.get().strip()
        if not function:
            self.status.config(text="Please enter a function")
            return

        try:
            # Read and validate inputs
            x_range = self._get_x_range()
            num_notes = self._get_num_notes()
            midi_params = self._get_midi_params()
            micro_params = self._get_microtonal_params()
            ton_params = self._get_tonality_params()
            range_params = self._get_range_params()
            rhythm_params = self._get_rhythm_params()
            human_params = self._get_humanize_params()
            chord_params = self._get_chord_mode()

            # Evaluate function samples
            y_values = self._evaluate_function_samples(function, x_range, num_notes)

            # Generate MIDI
            midi = function_to_midi(
                y_values,
                tempo=midi_params["tempo"],
                velocity=midi_params["velocity"],
                note_duration=midi_params["note_duration"],
                instrument=midi_params["instrument"],
                transpose=midi_params["transpose"],
                microtonal=micro_params["microtonal"],
                bend_range_semitones=micro_params["bend_range"],
                reset_bend_after_note=micro_params["reset_bend"],
                scale=self.scale_var.get(),
                root=ton_params["root"],
                min_note=range_params["min_note"],
                max_note=range_params["max_note"],
                rhythm_pattern=rhythm_params["rhythm_pattern"],
                swing=human_params["swing"],
                humanize_timing=human_params["humanize_timing"],
                humanize_velocity=human_params["humanize_velocity"],
                chord_mode=chord_params["chord_mode"],
            )

            # Save temp file
            temp_path = os.path.join(tempfile.gettempdir(), f"melody_{int(time.time())}.mid")
            self.temp_midi_path = temp_path
            with open(temp_path, "wb") as output_file:
                midi.writeFile(output_file)

            # Auto-save if enabled
            if self.autosave_var.get():
                target = self.autosave_entry.get().strip()
                if target:
                    try:
                        os.makedirs(os.path.dirname(target), exist_ok=True)
                        with open(self.temp_midi_path, "rb") as src, open(target, "wb") as dst:
                            dst.write(src.read())
                        self.log(f"Auto-saved: {target}")
                    except OSError as e:
                        self.log(f"Auto-save failed: {e}")

            # Update plot and controls
            self.update_plot(function, x_range, num_notes)
            self.set_controls_enabled(True)
            self.status.config(text="MIDI generated successfully")
            self.log("MIDI generated")

        except Exception as e:  # Catch errors during any part of the process
            self.temp_midi_path = None
            self.error(f"Error: {str(e)}")
            return
        
    def update_plot(self, function, x_range, num_notes):
        self.ax.clear()
        
        # Plot the function
        x_vals = np.linspace(x_range[0], x_range[1], 1000)
        y_vals = [self.evaluator.eval_expression(function, x) for x in x_vals]
        
        if any(y is None for y in y_vals):
            self.status.config(text="Error: Function evaluation failed")
            return
            
        line_color = '#5B9BD5' if not self.is_dark_mode else '#7FB3FF'
        self.ax.plot(x_vals, y_vals, color=line_color, linewidth=2)
        
        # Plot the sampled points
        x_samples = np.linspace(x_range[0], x_range[1], num_notes)
        y_samples = [self.evaluator.eval_expression(function, x) for x in x_samples]
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

def main():
    root = tk.Tk()
    app = MelodyGeneratorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()

<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# **Prompt Specializzato: Generatore di Melodie da Funzioni Matematiche**

## **Concetto dell'Applicazione**

Sviluppa un sistema Python interattivo che converte funzioni matematiche in composizioni musicali MIDI attraverso algoritmi di mappatura configurabili, con visualizzazione real-time e controlli parametrici dinamici.

## **Architettura Tecnica Modulare**

### **1. Struttura del Progetto**

```python
math_melody_generator/
├── src/
│   ├── function_engine/       # Parser e valutatore di funzioni matematiche
│   ├── music_mappers/         # Algoritmi di conversione math → MIDI
│   ├── midi_synthesizer/      # Generazione MIDI e sintesi audio
│   ├── visualizers/           # Grafici real-time e piano roll
│   └── controllers/           # Interfaccia utente e controlli
├── presets/                   # Configurazioni predefinite per diverse funzioni
├── examples/                  # Funzioni matematiche di esempio
└── output/                    # File MIDI e audio generati
```


### **2. Tipi di Funzioni Matematiche Supportate**[^1][^2][^3]

#### **Funzioni Trigonometriche**[^2][^1]

```python
# Esempi di funzioni base
functions = {
    "sine_wave": "sin(x)",
    "complex_trig": "sin(x) * cos(x/2) + tan(x/4)",
    "modulated_sine": "sin(x) * sin(x/3)",
    "harmonic_series": "sin(x) + sin(2*x)/2 + sin(3*x)/3"
}
```


#### **Funzioni Frattali e Ricorsive**[^4][^5][^6]

```python
# Algoritmi frattali per pattern musicali
def fibonacci_sequence_to_notes(n_terms):
    """Converte sequenza Fibonacci in melodia"""
    fib_seq = [fibonacci(i) for i in range(n_terms)]
    return scale_to_midi_notes(fib_seq, scale="pentatonic")

def mandelbrot_melody(c_real, c_imag, iterations=100):
    """Genera melodia da insieme di Mandelbrot"""
    escape_times = []
    for x in range(-20, 21):  # griglia di punti
        z = complex(x/10, 0)
        escape_time = mandelbrot_escape_time(z, complex(c_real, c_imag), iterations)
        escape_times.append(escape_time)
    return escape_times_to_notes(escape_times)
```


#### **Funzioni Ellittiche e Serie Matematiche**[^3][^7]

```python
# Implementazione di funzioni Weierstrass per sintesi sonora
def weierstrass_function(x, a=0.5, b=7):
    """Funzione di Weierstrass per texture sonore complesse"""
    result = 0
    for n in range(20):  # numero di armoniche
        result += (a**n) * math.cos((b**n) * math.pi * x)
    return result

def elliptic_orbit_melody(omega1, omega2, steps=100):
    """Melodia basata su orbite ellittiche"""
    orbit_points = []
    for t in np.linspace(0, 2*np.pi, steps):
        x = math.cos(440 * 2 * np.pi * t)  # 440 Hz frequency
        y = math.sin(440 * 2 * np.pi * t)
        orbit_points.append((x, y))
    return orbit_to_midi_notes(orbit_points)
```


### **3. Algoritmi di Mappatura Avanzati**[^8][^2]

#### **Mappatura Diretta: Funzione → Altezza Nota**[^9][^1]

```python
def direct_pitch_mapping(func_str, x_range, scale_type="chromatic"):
    """
    Mappa direttamente y = f(x) a note MIDI
    - Valore Y normalizzato → Altezza nota (C1-C8)
    - Derivata prima → Velocità MIDI
    - Derivata seconda → Modulazioni/Pitch Bend
    """
    x_vals = np.linspace(x_range, x_range[^40], 128)
    y_vals = [eval_function(func_str, x) for x in x_vals]
    
    # Normalizzazione su range MIDI
    y_normalized = normalize_to_midi_range(y_vals, min_note=24, max_note=96)
    
    # Calcolo derivate per parametri musicali aggiuntivi
    velocities = calculate_velocity_from_derivative(func_str, x_vals)
    modulations = calculate_modulation_from_second_derivative(func_str, x_vals)
    
    return generate_midi_sequence(y_normalized, velocities, modulations, scale_type)
```


#### **Mappatura Parametrica Complessa**[^10][^3]

```python
def parametric_mapping(x_func, y_func, t_range, musical_params):
    """
    Mapping parametrico x(t), y(t) → parametri musicali multipli
    - x(t) → Altezza nota
    - y(t) → Durata nota  
    - t → Timeline temporale
    - |dx/dt| → Intensità
    """
    t_vals = np.linspace(t_range, t_range[^40], musical_params['num_notes'])
    
    notes = []
    for t in t_vals:
        x_val = eval_function(x_func, t)
        y_val = eval_function(y_func, t)
        
        pitch = map_to_scale(x_val, musical_params['scale'], musical_params['root'])
        duration = map_duration(y_val, musical_params['min_dur'], musical_params['max_dur'])
        velocity = calculate_parametric_velocity(x_func, y_func, t)
        
        notes.append(MidiNote(pitch, duration, velocity, t))
    
    return notes
```


### **4. Sintesi Audio Real-Time**[^11][^12][^9]

#### **Oscillatori Basati su Funzioni Matematiche**[^13][^9]

```python
class MathematicalOscillator:
    """Oscillatore che usa funzioni matematiche come forme d'onda"""
    
    def __init__(self, function_str, sample_rate=44100):
        self.function = function_str
        self.sample_rate = sample_rate
        self.phase = 0
        
    def generate_samples(self, frequency, num_samples):
        """Genera campioni audio dalla funzione matematica"""
        samples = []
        phase_increment = 2 * np.pi * frequency / self.sample_rate
        
        for i in range(num_samples):
            # Valuta la funzione nel dominio normalizzato [0, 2π]
            normalized_phase = (self.phase % (2 * np.pi))
            amplitude = eval_function(self.function, normalized_phase)
            
            # Clipping e normalizzazione
            amplitude = np.clip(amplitude, -1.0, 1.0)
            samples.append(amplitude)
            
            self.phase += phase_increment
            
        return np.array(samples)

# Esempio di utilizzo per sintesi additiva
def additive_synthesis_from_function(base_func, harmonics=5):
    """Sintesi additiva usando la funzione come oscillatore base"""
    oscillators = []
    for harmonic in range(1, harmonics + 1):
        # Modifica la funzione per ogni armonica
        harmonic_func = f"({base_func}) * sin({harmonic} * x)"
        oscillators.append(MathematicalOscillator(harmonic_func))
    
    return oscillators
```


### **5. Interfaccia Interattiva Specializzata**[^1][^2]

#### **Editor di Funzioni con Anteprima Real-Time**

```python
class FunctionEditor:
    """Editor interattivo per funzioni matematiche con anteprima musicale"""
    
    def __init__(self):
        self.current_function = "sin(x)"
        self.x_range = (-2*np.pi, 2*np.pi)
        self.mapping_params = {
            'scale': 'pentatonic_major',
            'root_note': 'C4',
            'tempo': 120,
            'note_duration': 0.25
        }
        
    def preview_function_graph(self):
        """Mostra grafico della funzione in tempo reale"""
        x_vals = np.linspace(self.x_range, self.x_range[^40], 1000)
        y_vals = [self.eval_safe(x) for x in x_vals]
        
        plt.clf()
        plt.plot(x_vals, y_vals, 'b-', linewidth=2)
        plt.title(f"f(x) = {self.current_function}")
        plt.xlabel("x")
        plt.ylabel("f(x)")
        plt.grid(True, alpha=0.3)
        plt.pause(0.01)  # Update in real-time
        
    def preview_piano_roll(self):
        """Mostra anteprima delle note generate"""
        notes = self.function_to_midi_notes()
        piano_roll_display(notes, self.mapping_params)
        
    def live_audio_preview(self):
        """Riproduzione audio in tempo reale durante la modifica"""
        oscillator = MathematicalOscillator(self.current_function)
        audio_stream = create_audio_stream(oscillator)
        return audio_stream
```


### **6. Controlli Parametrici Avanzati**[^14][^10]

#### **Modulazione Dinamica dei Parametri**

```python
class ParameterController:
    """Controllo dinamico dei parametri durante la riproduzione"""
    
    def __init__(self):
        self.parameters = {
            'frequency_multiplier': 1.0,    # Modifica velocità di esecuzione
            'amplitude_scaling': 1.0,       # Scala dinamica delle note
            'harmonic_content': 1.0,        # Contenuto armonico
            'phase_offset': 0.0,            # Offset di fase
            'function_morphing': 0.0        # Morphing tra funzioni diverse
        }
        
    def morph_functions(self, func1, func2, morph_factor):
        """Interpola tra due funzioni matematiche"""
        # Esempio: morph tra sin(x) e cos(x)
        return f"({1-morph_factor}) * ({func1}) + ({morph_factor}) * ({func2})"
        
    def real_time_parameter_control(self, midi_controller=None):
        """Controllo parametri via MIDI controller o interfaccia"""
        if midi_controller:
            # Mappa controller MIDI a parametri
            cc_mappings = {
                1: 'frequency_multiplier',    # Modulation Wheel
                74: 'amplitude_scaling',      # Filter Cutoff
                71: 'harmonic_content',       # Resonance
                91: 'phase_offset'            # Reverb
            }
            
            for cc, param in cc_mappings.items():
                if midi_controller.get_cc(cc) is not None:
                    value = midi_controller.get_cc(cc) / 127.0
                    self.parameters[param] = value
```


### **7. Esempi di Implementazione Specifica**

#### **Scenario 1: Onde Sinusoidali Complesse**[^9][^1]

```python
# Generatore di melodie da funzioni trigonometriche complesse
def complex_trigonometric_melody():
    functions = [
        "sin(x) + 0.5*sin(2*x) + 0.25*sin(4*x)",  # Serie armonica
        "sin(x) * cos(x/3)",                        # Modulazione di ampiezza
        "sin(x + sin(x/2))",                        # Modulazione di frequenza
        "sin(x) * exp(-x/10)"                       # Decay esponenziale
    ]
    
    for i, func in enumerate(functions):
        melody = function_to_melody(func, x_range=(-2*np.pi, 2*np.pi))
        export_midi(melody, f"trig_melody_{i+1}.mid")
```


#### **Scenario 2: Frattali Musicali**[^6][^4]

```python
# Generatore di pattern musicali frattali
def fractal_music_generator():
    # Albero frattale → Struttura ritmica
    tree_structure = generate_fractal_tree(depth=5, branching_factor=2)
    rhythm_pattern = tree_to_rhythm(tree_structure)
    
    # Sequenza di Fibonacci → Melodia
    fib_melody = fibonacci_to_melody(20)  # 20 numeri di Fibonacci
    
    # Mandelbrot set → Armonia
    mandelbrot_chords = mandelbrot_to_chords(iterations=50)
    
    # Combina tutti gli elementi
    composition = combine_musical_elements(fib_melody, rhythm_pattern, mandelbrot_chords)
    return composition
```


### **8. Funzionalità Tecniche Avanzate**

#### **Parser di Funzioni Sicuro**[^1]

```python
import ast
import operator

class SafeMathEvaluator:
    """Valutatore sicuro per espressioni matematiche"""
    
    allowed_operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
    }
    
    allowed_functions = {
        'sin': math.sin,
        'cos': math.cos,
        'tan': math.tan,
        'exp': math.exp,
        'log': math.log,
        'sqrt': math.sqrt,
        'abs': abs,
        'floor': math.floor,
        'ceil': math.ceil
    }
    
    def eval_expression(self, expression_str, x_value):
        """Valuta espressione matematica in modo sicuro"""
        try:
            # Sostituisce 'x' con il valore numerico
            expr = expression_str.replace('x', str(x_value))
            # Parse AST e valutazione controllata
            node = ast.parse(expr, mode='eval')
            return self._eval_node(node.body)
        except:
            return 0.0  # Valore di fallback sicuro
```


#### **Esportazione Multi-Formato**[^15][^16]

```python
class MultiFormatExporter:
    """Esportazione in diversi formati audio e MIDI"""
    
    def export_midi(self, notes, filename, track_name="Math Function"):
        """Esporta come file MIDI standard"""
        from midiutil import MIDIFile
        
        midi_file = MIDIFile(1)
        midi_file.addTempo(0, 0, 120)
        midi_file.addTrackName(0, 0, track_name)
        
        for note in notes:
            midi_file.addNote(0, 0, note.pitch, note.start_time, 
                            note.duration, note.velocity)
        
        with open(filename, 'wb') as f:
            midi_file.writeFile(f)
    
    def export_wav(self, audio_samples, filename, sample_rate=44100):
        """Esporta come file WAV audio"""
        import wave
        
        with wave.open(filename, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            
            # Converti a 16-bit integers
            audio_int16 = (audio_samples * 32767).astype(np.int16)
            wav_file.writeframes(audio_int16.tobytes())
```


### **9. Interfaccia Utente Consigliata**

#### **Layout Principale**

```
┌─────────────────┬──────────────────┬──────────────────┐
│  Function Input │   Parameter      │   Output Control │
│  - Text Editor  │   Controls       │   - MIDI Export  │
│  - Syntax Check │   - X Range      │   - WAV Export   │
│  - Function Lib │   - Scale Select │   - Live Play    │
├─────────────────┼──────────────────┼──────────────────┤
│  Graph Preview  │   Piano Roll     │   Audio Controls │
│  - Real-time    │   - Note Display │   - Volume       │
│  - Zoom/Pan     │   - Edit Notes   │   - Tempo        │
│  - Multiple     │   - Timeline     │   - Instrument   │
└─────────────────┴──────────────────┴──────────────────┘
```


### **10. Librerie Python Richieste**

```python
# Core matematico e MIDI
import numpy as np
import matplotlib.pyplot as plt
import mido
from midiutil import MIDIFile
import math
import cmath  # Per numeri complessi

# Audio real-time
import pyaudio
import wave
import scipy.signal

# Interfaccia utente
import tkinter as tk
from tkinter import ttk
import matplotlib.backends.backend_tkagg as tkagg

# Parser sicuro
import ast
import operator

# Optional: Controllo MIDI real-time
import python_rtmidi
```

Questo sistema offrirebbe un approccio profondamente matematico alla generazione musicale, permettendo l'esplorazione creativa di pattern sonori derivati direttamente da funzioni matematiche, con la flessibilità di modificare parametri in tempo reale e visualizzare sia la matematica che la musica risultante.[^2][^3][^1]
<span style="display:none">[^17][^18][^19][^20][^21][^22][^23][^24][^25][^26][^27][^28][^29][^30][^31][^32][^33][^34][^35][^36][^37][^38][^39][^41][^42]</span>

<div style="text-align: center">⁂</div>


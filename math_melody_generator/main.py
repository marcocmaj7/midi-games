import math
import numpy as np
import ast
import operator
from typing import List, Optional

from .src.midi_synthesizer.midi_generator import function_to_midi as synth_function_to_midi
from .src.midi_synthesizer.scales import SCALES

# Mapping per calcolo Root da tonalità (Key + Octave)
KEY_TO_OFFSET = {
    "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4,
    "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9,
    "A#": 10, "Bb": 10, "B": 11
}
KEY_NAMES = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]


class SafeMathEvaluator:
    """Valutatore sicuro per espressioni matematiche
    
    Implementa un parser di espressioni matematiche con:
    - Operatori base (+, -, *, /, ^)
    - Funzioni matematiche comuni (sin, cos, tan, exp, log, sqrt, abs)
    - Controllo di sicurezza per evitare codice arbitrario
    
    Esempio:
        evaluator = SafeMathEvaluator()
        result = evaluator.eval_expression("sin(x) + 2", 1.57)  # ~3.0
    """
    
    def __init__(self):
        self.allowed_operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
        }
        
        self.allowed_functions = {
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
        self.allowed_constants = {
            'pi': math.pi,
            'e': math.e
        }
    
    def eval_expression(self, expression_str, x_value):
        """Valuta espressione matematica in modo sicuro"""
        try:
            if not expression_str.strip():
                raise ValueError("Empty expression")
                
            # Support caret for power by translating to Python exponent operator
            expr = expression_str.replace('^', '**')
            node = ast.parse(expr, mode='eval')
            result = self._eval_node(node.body, x_value)
            
            # Controllo valori non numerici
            if not isinstance(result, (int, float)):
                raise ValueError("Expression must evaluate to a number")
                
            return result
            
        except (SyntaxError, ValueError, TypeError, ZeroDivisionError) as e:
            error_type = type(e).__name__
            error_msg = str(e) if str(e) else f"Invalid expression: {expression_str}"
            print(f"[MathEval Error] {error_type}: {error_msg}")
            return None
    
    def _eval_node(self, node, x_value):
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Name):
            if node.id == 'x':
                return x_value
            if node.id in self.allowed_constants:
                return self.allowed_constants[node.id]
            if node.id in self.allowed_functions:
                return self.allowed_functions[node.id]
            else:
                raise ValueError(f"Name {node.id} not allowed")
        elif isinstance(node, ast.Call):
            func = self._eval_node(node.func, x_value)
            args = [self._eval_node(arg, x_value) for arg in node.args]
            return func(*args)
        elif isinstance(node, ast.BinOp):
            op = self.allowed_operators[type(node.op)]
            left = self._eval_node(node.left, x_value)
            right = self._eval_node(node.right, x_value)
            return op(left, right)
        elif isinstance(node, ast.UnaryOp):
            op = self.allowed_operators[type(node.op)]
            operand = self._eval_node(node.operand, x_value)
            return op(operand)
        else:
            raise TypeError(f"Unsupported node type: {type(node)}")


def _compute_root_from_key_octave(key: Optional[str], octave: Optional[int], fallback_root: int = 60) -> int:
    """
    Calcola il MIDI root partendo da Key + Octave (C4 = 60).
    Se key è None o invalida, ritorna fallback_root.
    """
    try:
        if key and key in KEY_TO_OFFSET and octave is not None:
            return 12 * (int(octave) + 1) + KEY_TO_OFFSET[key]
    except Exception:
        pass
    return fallback_root


def _parse_rhythm_pattern(pattern_str: Optional[str]) -> Optional[List[float]]:
    """
    Parsing semplice: stringa con numeri separati da virgole o punti e virgola, es. '0.5,0.5,1'
    """
    if not pattern_str:
        return None
    txt = pattern_str.strip()
    if txt == "":
        return None
    parts = [p.strip() for p in txt.replace(";", ",").split(",") if p.strip() != ""]
    try:
        out = [float(p) for p in parts]
        if any(d <= 0 for d in out):
            return None
        return out
    except Exception:
        return None


def generate_midi_from_function_string(
    function_str,
    x_range=(-2*np.pi, 2*np.pi),
    num_notes=32,
    tempo=120,
    velocity=100,
    note_duration=0.5,
    instrument=0,
    transpose=0,
    microtonal=False,
    bend_range_semitones=2,
    reset_bend_after_note=True,
    scale="chromatic",
    root=60,
    # Estensioni artistiche
    min_note=36,
    max_note=96,
    rhythm_pattern: Optional[List[float]] = None,
    swing: float = 0.0,
    humanize_timing: float = 0.0,
    humanize_velocity: int = 0,
    chord_mode: str = "none",
    track_name: str = "Math Function Melody",
    channel: int = 0,
):
    """Evaluate a function string over x and delegate MIDI creation to the synthesizer module."""
    evaluator = SafeMathEvaluator()
    x_vals = np.linspace(x_range[0], x_range[1], num_notes)
    y_vals = [evaluator.eval_expression(function_str, x) for x in x_vals]
    if any(v is None for v in y_vals):
        raise ValueError("Function evaluation failed")
    return synth_function_to_midi(
        y_vals,
        tempo=tempo,
        velocity=velocity,
        note_duration=note_duration,
        instrument=instrument,
        transpose=transpose,
        microtonal=microtonal,
        bend_range_semitones=bend_range_semitones,
        reset_bend_after_note=reset_bend_after_note,
        scale=scale,
        root=root,
        min_note=min_note,
        max_note=max_note,
        rhythm_pattern=rhythm_pattern,
        swing=swing,
        humanize_timing=humanize_timing,
        humanize_velocity=humanize_velocity,
        chord_mode=chord_mode,
        track_name=track_name,
        channel=channel,
    )

import os

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Math Melody Generator")
    parser.add_argument('--gui', action='store_true', help='Launch graphical interface')

    # Function sampling
    parser.add_argument('--function', type=str, default="sin(x)", help='Mathematical function to convert')
    parser.add_argument('--notes', type=int, default=32, help='Number of sampled notes (8-128)')
    parser.add_argument('--x-start', type=float, default=-2*math.pi, help='Start of x range')
    parser.add_argument('--x-end', type=float, default=2*math.pi, help='End of x range')

    # Musical parameters
    parser.add_argument('--tempo', type=int, default=120, help='Tempo in BPM (40-240)')
    parser.add_argument('--velocity', type=int, default=100, help='MIDI note velocity 0-127')
    parser.add_argument('--duration', type=float, default=0.5, help='Default note duration in beats (0.1-4.0)')
    parser.add_argument('--instrument', type=int, default=0, help='MIDI program/instrument 0-127')
    parser.add_argument('--transpose', type=int, default=0, help='Semitone transpose (-24..24)')
    parser.add_argument('--scale', type=str, choices=list(SCALES.keys()), default='chromatic', help='Scale for quantization when not microtonal')

    # Tonality: either key+octave or root
    parser.add_argument('--key', type=str, choices=KEY_NAMES, help='Key (tonic) name e.g., C, D#, F# ...')
    parser.add_argument('--octave', type=int, default=4, help='Octave for the key (C4 = 60)')
    parser.add_argument('--root', type=int, help='Root MIDI note. If provided, overrides key+octave')

    # Register / range
    parser.add_argument('--min-note', type=int, default=36, help='Minimum MIDI note (0-127)')
    parser.add_argument('--max-note', type=int, default=96, help='Maximum MIDI note (0-127)')

    # Rhythm & humanization
    parser.add_argument('--rhythm', type=str, default='', help='Comma-separated beat pattern, e.g. "0.5,0.5,1.0"')
    parser.add_argument('--swing', type=float, default=0.0, help='Swing amount 0..1 (affects offbeats)')
    parser.add_argument('--hum-timing', type=float, default=0.0, help='Humanize timing jitter in beats (0..0.5)')
    parser.add_argument('--hum-velocity', type=int, default=0, help='Humanize velocity +/- range (0..40)')

    # Harmony
    parser.add_argument('--chord-mode', type=str, choices=['none','power','triad','seventh'], default='none', help='Chord generation mode')

    # Microtonal
    parser.add_argument('--microtonal', action='store_true', help='Enable microtonal monophonic mode (uses pitch bend)')
    parser.add_argument('--bend-range', type=int, default=2, help='Pitch bend range in semitones (1-24)')
    parser.add_argument('--no-reset-bend', dest='reset_bend', action='store_false', help='Do not reset pitch bend after each note (default: reset)')
    parser.set_defaults(reset_bend=True)

    # Output
    parser.add_argument('--output', type=str, default=os.path.join("output", "generated_melody.mid"), help='Output MIDI path')
    args = parser.parse_args()
    
    if args.gui:
        from .GUI import main as gui_main
        gui_main()
    else:
        # Validate and compute derived params
        if args.notes < 8 or args.notes > 128:
            raise ValueError("Number of notes must be between 8 and 128")
        if args.x_end <= args.x_start:
            raise ValueError("x-end must be greater than x-start")
        if args.tempo < 40 or args.tempo > 240:
            raise ValueError("Tempo must be between 40 and 240 BPM")
        if args.velocity < 0 or args.velocity > 127:
            raise ValueError("Velocity must be between 0 and 127")
        if args.duration <= 0 or args.duration > 4.0:
            raise ValueError("Duration must be between 0.1 and 4.0 beats")
        if args.instrument < 0 or args.instrument > 127:
            raise ValueError("Instrument must be between 0 and 127")
        if args.transpose < -24 or args.transpose > 24:
            raise ValueError("Transpose must be between -24 and 24 semitones")
        if args.min_note < 0 or args.min_note > 127 or args.max_note < 0 or args.max_note > 127 or args.min_note >= args.max_note:
            raise ValueError("Min/Max note must be in 0..127 and min < max")
        if args.swing < 0 or args.swing > 1:
            raise ValueError("Swing must be between 0 and 1")
        if args.hum_timing < 0 or args.hum_timing > 0.5:
            raise ValueError("Humanize timing must be between 0.0 and 0.5 beats")
        if args.hum_velocity < 0 or args.hum_velocity > 40:
            raise ValueError("Humanize velocity must be between 0 and 40")
        if args.bend_range < 1 or args.bend_range > 24:
            raise ValueError("Bend range must be between 1 and 24 semitones")

        root = args.root if args.root is not None else _compute_root_from_key_octave(args.key, args.octave, 60)
        rhythm_pattern = _parse_rhythm_pattern(args.rhythm)

        print("Math Melody Generator")
        print(f"Function: {args.function}")
        print(f"Scale: {args.scale}, Root: {root} ({args.key if args.key else 'root'})")
        print(f"Range: {args.min_note}-{args.max_note}, Chord mode: {args.chord_mode}")
        print(f"Rhythm: {rhythm_pattern if rhythm_pattern else f'default {args.duration} beats'}, Swing: {args.swing}, Humanize T/V: {args.hum_timing}/{args.hum_velocity}")
        print(f"Microtonal: {args.microtonal}")

        midi = generate_midi_from_function_string(
            args.function,
            x_range=(args.x_start, args.x_end),
            num_notes=args.notes,
            tempo=args.tempo,
            velocity=args.velocity,
            note_duration=args.duration,
            instrument=args.instrument,
            transpose=args.transpose,
            microtonal=args.microtonal,
            bend_range_semitones=args.bend_range,
            reset_bend_after_note=args.reset_bend,
            scale=args.scale,
            root=root,
            min_note=args.min_note,
            max_note=args.max_note,
            rhythm_pattern=rhythm_pattern,
            swing=args.swing,
            humanize_timing=args.hum_timing,
            humanize_velocity=args.hum_velocity,
            chord_mode=args.chord_mode,
            track_name="Math Function Melody",
            channel=0,
        )
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        
        with open(args.output, "wb") as output_file:
            midi.writeFile(output_file)
        print(f"MIDI file saved to {args.output}")

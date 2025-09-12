import math
import numpy as np
from midiutil import MIDIFile
import ast
import operator

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
    
    def eval_expression(self, expression_str, x_value):
        """Valuta espressione matematica in modo sicuro
        
        Args:
            expression_str (str): Espressione matematica con variabile 'x'
            x_value (float): Valore da sostituire a 'x'
            
        Returns:
            float: Risultato dell'espressione valutata
            None: Se l'espressione non è valida
            
        Raises:
            ValueError: Se l'espressione contiene funzioni non permesse
            SyntaxError: Se l'espressione ha errori di sintassi
        """
        try:
            if not expression_str.strip():
                raise ValueError("Empty expression")
                
            expr = expression_str.replace('x', str(x_value))
            node = ast.parse(expr, mode='eval')
            result = self._eval_node(node.body)
            
            # Controllo valori non numerici
            if not isinstance(result, (int, float)):
                raise ValueError("Expression must evaluate to a number")
                
            return result
            
        except (SyntaxError, ValueError, TypeError, ZeroDivisionError) as e:
            error_type = type(e).__name__
            error_msg = str(e) if str(e) else f"Invalid expression: {expression_str}"
            print(f"[MathEval Error] {error_type}: {error_msg}")
            return None
    
    def _eval_node(self, node):
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Name):
            if node.id in self.allowed_functions:
                return self.allowed_functions[node.id]
            else:
                raise ValueError(f"Function {node.id} not allowed")
        elif isinstance(node, ast.Call):
            func = self._eval_node(node.func)
            args = [self._eval_node(arg) for arg in node.args]
            return func(*args)
        elif isinstance(node, ast.BinOp):
            op = self.allowed_operators[type(node.op)]
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            return op(left, right)
        elif isinstance(node, ast.UnaryOp):
            op = self.allowed_operators[type(node.op)]
            operand = self._eval_node(node.operand)
            return op(operand)
        else:
            raise TypeError(f"Unsupported node type: {type(node)}")

def function_to_midi(
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
):
    """Convert a mathematical function to MIDI notes.

    Parameters:
    - function_str: expression using variable x
    - x_range: tuple (min, max)
    - num_notes: number of sampled notes
    - tempo: BPM
    - velocity: MIDI velocity (0-127)
    - note_duration: note length in beats
    - instrument: program number (0-127)
    - transpose: semitone shift applied to all notes
    """
    evaluator = SafeMathEvaluator()
    x_vals = np.linspace(x_range[0], x_range[1], num_notes)
    y_vals = [evaluator.eval_expression(function_str, x) for x in x_vals]
    
    # Normalize to MIDI note range (0-127)
    y_min, y_max = min(y_vals), max(y_vals)
    if y_min == y_max:
        midi_notes = [64] * num_notes  # Middle C if no variation
        midi_notes_float = [64.0] * num_notes
    else:
        midi_notes_float = [64.0 + 48.0 * (y - y_min)/(y_max - y_min) for y in y_vals]
        midi_notes = [int(round(n)) for n in midi_notes_float]
    
    # Create MIDI file
    midi = MIDIFile(1)
    track = 0
    channel = 0
    time = 0
    midi.addTempo(track, time, int(tempo))
    try:
        midi.addProgramChange(track, channel, time, int(instrument))
    except (TypeError, ValueError):
        # Fallback silently if instrument is invalid in the environment
        pass

    # Configure pitch bend range via RPN 0,0 if microtonal
    if microtonal:
        # Select RPN 0 (Pitch Bend Range)
        midi.addControllerEvent(track, channel, time, 101, 0)  # RPN MSB
        midi.addControllerEvent(track, channel, time, 100, 0)  # RPN LSB
        # Set range (Data Entry): MSB = semitoni, LSB = cents (0)
        midi.addControllerEvent(track, channel, time, 6, int(max(0, min(24, bend_range_semitones))))
        midi.addControllerEvent(track, channel, time, 38, 0)
        # (Optional) Deselect RPN
        midi.addControllerEvent(track, channel, time, 101, 127)
        midi.addControllerEvent(track, channel, time, 100, 127)
    
    for i in range(len(midi_notes)):
        start_time = i * float(note_duration)
        duration = float(note_duration)
        base_note = max(0, min(127, midi_notes[i] + int(transpose)))

        if microtonal:
            # Compute deviation in semitones from the rounded note
            deviation = (midi_notes_float[i] + int(transpose)) - base_note
            # Map deviation to 14-bit pitch bend around center 8192
            # Clamp deviation to bend range
            if bend_range_semitones <= 0:
                bend_range_semitones = 2
            ratio = max(-1.0, min(1.0, deviation / float(bend_range_semitones)))
            bend14 = int(round(8192 + ratio * 8192))
            bend14 = max(0, min(16383, bend14))
            # Send pitch bend at note start
            midi.addPitchWheelEvent(track, channel, start_time, bend14)

        midi.addNote(track, channel, base_note, start_time, duration, int(velocity))

        if microtonal and reset_bend_after_note:
            # Reset bend to center at note end to avoid carryover
            midi.addPitchWheelEvent(track, channel, start_time + duration, 8192)
    
    return midi

import os

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Math Melody Generator")
    parser.add_argument('--gui', action='store_true', help='Launch graphical interface')
    parser.add_argument('--function', type=str, default="sin(x)", help='Mathematical function to convert')
    parser.add_argument('--tempo', type=int, default=120, help='Tempo in BPM')
    parser.add_argument('--velocity', type=int, default=100, help='MIDI note velocity 0-127')
    parser.add_argument('--duration', type=float, default=0.5, help='Note duration in beats')
    parser.add_argument('--instrument', type=int, default=0, help='MIDI program/instrument 0-127')
    parser.add_argument('--transpose', type=int, default=0, help='Semitone transpose')
    args = parser.parse_args()
    
    if args.gui:
        from GUI import main as gui_main
        gui_main()
    else:
        print("Math Melody Generator")
        print(f"Using function: {args.function}")
        midi = function_to_midi(
            args.function,
            tempo=args.tempo,
            velocity=args.velocity,
            note_duration=args.duration,
            instrument=args.instrument,
            transpose=args.transpose,
        )
        
        # Ensure output directory exists
        os.makedirs("output", exist_ok=True)
        
        with open("output/generated_melody.mid", "wb") as output_file:
            midi.writeFile(output_file)
        print("MIDI file saved to output/generated_melody.mid")

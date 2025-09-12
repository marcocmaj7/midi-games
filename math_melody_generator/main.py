import math
import numpy as np
from midiutil import MIDIFile
import ast
import operator

class SafeMathEvaluator:
    """Valutatore sicuro per espressioni matematiche"""
    
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
        """Valuta espressione matematica in modo sicuro"""
        try:
            expr = expression_str.replace('x', str(x_value))
            node = ast.parse(expr, mode='eval')
            return self._eval_node(node.body)
        except:
            return 0.0
    
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

def function_to_midi(function_str, x_range=(-2*np.pi, 2*np.pi), num_notes=32):
    """Convert a mathematical function to MIDI notes"""
    evaluator = SafeMathEvaluator()
    x_vals = np.linspace(x_range[0], x_range[1], num_notes)
    y_vals = [evaluator.eval_expression(function_str, x) for x in x_vals]
    
    # Normalize to MIDI note range (0-127)
    y_min, y_max = min(y_vals), max(y_vals)
    if y_min == y_max:
        midi_notes = [64] * num_notes  # Middle C if no variation
    else:
        midi_notes = [int(64 + 48 * (y - y_min)/(y_max - y_min)) for y in y_vals]
    
    # Create MIDI file
    midi = MIDIFile(1)
    midi.addTempo(0, 0, 120)
    
    for i, note in enumerate(midi_notes):
        midi.addNote(0, 0, note, i * 0.5, 0.5, 100)
    
    return midi

import os

if __name__ == "__main__":
    print("Math Melody Generator")
    # Test with a sine function
    function = "sin(x)"
    print(f"Using test function: {function}")
    midi = function_to_midi(function)
    
    # Ensure output directory exists
    os.makedirs("output", exist_ok=True)
    
    with open("output/sine_wave.mid", "wb") as output_file:
        midi.writeFile(output_file)
    print("MIDI file saved to output/sine_wave.mid")

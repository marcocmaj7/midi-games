# Musical scales dictionary
# Each scale is defined as semitone intervals from the root

SCALES = {
    "chromatic": [i for i in range(12)],
    "major": [0, 2, 4, 5, 7, 9, 11],
    "minor": [0, 2, 3, 5, 7, 8, 10],
    "pentatonic_major": [0, 2, 4, 7, 9],
    "pentatonic_minor": [0, 3, 5, 7, 10],
    "dorian": [0, 2, 3, 5, 7, 9, 10],
    "phrygian": [0, 1, 3, 5, 7, 8, 10],
    "lydian": [0, 2, 4, 6, 7, 9, 11],
    "mixolydian": [0, 2, 4, 5, 7, 9, 10],
    "locrian": [0, 1, 3, 5, 6, 8, 10],
    "blues": [0, 3, 5, 6, 7, 10],
    "harmonic_minor": [0, 2, 3, 5, 7, 8, 11],
    "melodic_minor": [0, 2, 3, 5, 7, 9, 11],
}

def quantize_to_scale(note: int, root: int = 60, scale: str = "chromatic") -> int:
    """
    Map a MIDI note to the closest note in the given scale.

    Args:
        note (int): MIDI note (0-127)
        root (int): Root note (default = 60 => Middle C)
        scale (str): Name of the scale

    Returns:
        int: MIDI note adjusted to the nearest note in the chosen scale
    """
    if scale not in SCALES:
        return note  # fallback to unchanged note

    scale_intervals = SCALES[scale]
    octave = (note - root) // 12
    semitone = (note - root) % 12

    # Find closest interval in scale
    closest = min(scale_intervals, key=lambda x: abs(x - semitone))

    return root + octave * 12 + closest

from typing import List, Optional
import random
from midiutil import MIDIFile

from .scales import quantize_to_scale, SCALES


def _scale_values_to_range(function_values: List[float], min_note: int, max_note: int) -> List[float]:
    """
    Linearly scale a list of values to the MIDI note range [min_note, max_note].
    """
    if min_note > max_note:
        min_note, max_note = max_note, min_note

    if not function_values:
        return []

    min_val = min(function_values)
    max_val = max(function_values)
    range_val = max_val - min_val

    if range_val == 0:
        center = (min_note + max_note) / 2.0
        return [center] * len(function_values)

    span = max_note - min_note
    return [
        min_note + ((val - min_val) / range_val) * span
        for val in function_values
    ]


def _fit_to_range(note: int, min_note: int, max_note: int) -> int:
    """
    Wrap a note into [min_note, max_note] by octave transposition, then clamp.
    """
    if min_note > max_note:
        min_note, max_note = max_note, min_note
    while note < min_note:
        note += 12
    while note > max_note:
        note -= 12
    return max(min_note, min(max_note, note))


def _build_diatonic_chord_notes(note_quantized: int, root: int, scale_name: str, chord_mode: str) -> List[int]:
    """
    Build chord notes relative to a quantized note using the given scale.
    chord_mode: 'none' | 'power' | 'triad' | 'seventh'
    """
    if not chord_mode or chord_mode == "none":
        return [note_quantized]

    intervals = SCALES.get(scale_name)
    if not intervals:
        return [note_quantized]

    # Ensure base note is in-scale
    base_semitone = (note_quantized - root) % 12
    if base_semitone not in intervals:
        note_quantized = quantize_to_scale(note_quantized, root=root, scale=scale_name)
        base_semitone = (note_quantized - root) % 12

    try:
        idx = intervals.index(base_semitone)
    except ValueError:
        # Fallback to closest interval index
        idx = min(range(len(intervals)), key=lambda j: abs(intervals[j] - base_semitone))

    if chord_mode == "power":
        # Root + fifth (perfect 5th)
        return [note_quantized, note_quantized + 7]

    degrees = []
    if chord_mode == "triad":
        degrees = [idx, idx + 2, idx + 4]
    elif chord_mode == "seventh":
        degrees = [idx, idx + 2, idx + 4, idx + 6]
    else:
        return [note_quantized]

    notes: List[int] = []
    base_oct = (note_quantized - root) // 12
    n_scale = len(intervals)
    for d in degrees:
        deg_oct = d // n_scale
        deg_idx = d % n_scale
        semit = intervals[deg_idx]
        n = root + (base_oct + deg_oct) * 12 + semit
        notes.append(n)
    return notes


def function_to_midi(
    function_values: List[float],
    tempo: int = 120,
    velocity: int = 100,
    note_duration: float = 0.5,
    instrument: int = 0,
    transpose: int = 0,
    microtonal: bool = False,
    bend_range_semitones: int = 2,
    reset_bend_after_note: bool = True,
    scale: str = "chromatic",
    root: int = 60,
    # New artistic parameters
    min_note: int = 36,
    max_note: int = 96,
    rhythm_pattern: Optional[List[float]] = None,
    swing: float = 0.0,                  # 0.0..1.0 fraction of an 8th-note delay on offbeats
    humanize_timing: float = 0.0,        # +- beats jitter
    humanize_velocity: int = 0,          # +- velocity range
    chord_mode: str = "none",
    track_name: str = "Math Function Melody",
    channel: int = 0,
) -> MIDIFile:
    """
    Convert a list of function values to a musically-usable MIDI clip.

    Args:
        function_values: Y-values from function sampling.
        tempo: BPM (40-240).
        velocity: Base MIDI velocity (0-127).
        note_duration: Default duration in beats if no rhythm_pattern is provided.
        instrument: MIDI program number (0-127).
        transpose: Semitone transpose applied before quantization.
        microtonal: Use pitch bend for microtonal notes (only for monophonic lines).
        bend_range_semitones: Pitch bend range (1-24).
        reset_bend_after_note: Reset pitch bend to center after each note.
        scale: Scale name for quantization when microtonal is False.
        root: Root MIDI note (tonal center).
        min_note, max_note: Register/range mapping for pitch output.
        rhythm_pattern: Optional list of beat durations (cycled).
        swing: 0..1, delays every offbeat 8th by swing*0.5 beats.
        humanize_timing: Random +- jitter in beats added to note start time.
        humanize_velocity: Random +- added to base velocity (clamped 1..127).
        chord_mode: 'none' | 'power' | 'triad' | 'seventh'.
        track_name: Track name.
        channel: MIDI channel.

    Returns:
        MIDIFile: The generated MIDIFile object.
    """
    # Create MIDI file with 1 track
    midi = MIDIFile(1)
    track = 0
    time = 0.0

    # Setup track name and tempo
    midi.addTrackName(track, time, track_name)
    midi.addTempo(track, time, tempo)

    # Set instrument
    midi.addProgramChange(track, channel, time, instrument)

    # Configure microtonal pitch bend range (per-channel)
    if microtonal and (not chord_mode or chord_mode == "none"):
        midi.addControllerEvent(track, channel, time, 101, 0)  # RPN MSB
        midi.addControllerEvent(track, channel, time, 100, 0)  # RPN LSB
        midi.addControllerEvent(track, channel, time, 6, int(max(0, min(24, bend_range_semitones))))  # Data MSB
        midi.addControllerEvent(track, channel, time, 38, 0)   # Data LSB
        midi.addControllerEvent(track, channel, time, 101, 127)  # Deselect RPN
        midi.addControllerEvent(track, channel, time, 100, 127)

    # Scale function values to target MIDI range
    midi_notes = _scale_values_to_range(function_values, min_note=min_note, max_note=max_note)

    # Time scheduling
    current_time = time
    pattern = rhythm_pattern if (rhythm_pattern and len(rhythm_pattern) > 0) else None

    for i, note in enumerate(midi_notes):
        # Duration for this step
        duration = float(pattern[i % len(pattern)]) if pattern else float(note_duration)
        if duration <= 0:
            duration = max(0.1, float(note_duration))

        # Start time with swing and humanization
        start_time = current_time
        if swing and swing > 0.0:
            # Simple 8th-note swing: delay every offbeat by swing*0.5 beats
            if i % 2 == 1:
                start_time += max(0.0, min(1.0, swing)) * 0.5

        if humanize_timing and humanize_timing > 0.0:
            start_time += random.uniform(-humanize_timing, humanize_timing)

        vel = int(velocity)
        if humanize_velocity and humanize_velocity > 0:
            vel = max(1, min(127, int(round(velocity + random.randint(-humanize_velocity, humanize_velocity)))))

        # Apply transpose and compute base note
        note_float = note + transpose
        base_note = int(round(note_float))

        if microtonal and (not chord_mode or chord_mode == "none"):
            # Microtonal monophonic path
            deviation = note_float - base_note
            if bend_range_semitones <= 0:
                bend_range_semitones = 2
            ratio = max(-1.0, min(1.0, deviation / float(bend_range_semitones)))
            bend14 = int(round(8192 + ratio * 8192))
            bend14 = max(0, min(16383, bend14))

            midi.addPitchWheelEvent(track, channel, start_time, bend14)
            note_clamped = _fit_to_range(base_note, min_note, max_note)
            midi.addNote(track, channel, note_clamped, start_time, duration, vel)

            if reset_bend_after_note:
                midi.addPitchWheelEvent(track, channel, start_time + duration, 8192)
        else:
            # Quantized + chords path
            note_rounded = int(round(note_float))
            note_quantized = quantize_to_scale(note_rounded, root=root, scale=scale)

            chord_notes = _build_diatonic_chord_notes(note_quantized, root=root, scale_name=scale, chord_mode=chord_mode)
            for nn in chord_notes:
                nn = _fit_to_range(nn, min_note, max_note)
                nn = max(0, min(127, nn))
                midi.addNote(track, channel, nn, start_time, duration, vel)

        # Advance time by duration (pattern-driven)
        current_time += duration

    return midi

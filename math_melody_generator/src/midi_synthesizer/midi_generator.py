from midiutil import MIDIFile

def function_to_midi(function_values, tempo=120, velocity=100, note_duration=0.5,
                    instrument=0, transpose=0, microtonal=False,
                    bend_range_semitones=2, reset_bend_after_note=True):
    """
    Convert a list of function values to MIDI notes
    
    Args:
        function_values (list): List of y values from function evaluation
        tempo (int): Beats per minute (40-240)
        velocity (int): Note velocity (0-127)
        note_duration (float): Duration in beats (0.1-4.0)
        instrument (int): MIDI program number (0-127)
        transpose (int): Semitones to transpose (-24 to +24)
        microtonal (bool): Use pitch bend for microtonal notes
        bend_range_semitones (int): Pitch bend range in semitones (1-24)
        reset_bend_after_note (bool): Reset pitch bend after each note
        
    Returns:
        MIDIFile object
    """
    # Create MIDI file with 1 track
    midi = MIDIFile(1)
    track = 0
    time = 0
    channel = 0
    
    # Setup track name and tempo
    midi.addTrackName(track, time, "Math Function Melody")
    midi.addTempo(track, time, tempo)
    
    # Set instrument
    midi.addProgramChange(track, channel, time, instrument)
    
    # Scale function values to MIDI note range (0-127)
    min_val = min(function_values)
    max_val = max(function_values)
    range_val = max_val - min_val
    
    if range_val == 0:
        # Handle constant functions
        midi_notes = [60] * len(function_values)  # Middle C
    else:
        # Scale to MIDI range 36-96 (C2 to C7)
        midi_notes = [
            36 + ((val - min_val) / range_val) * 60
            for val in function_values
        ]
    
    # Add notes to track
    for i, note in enumerate(midi_notes):
        # Apply transpose
        note += transpose
        
        if microtonal:
            # Get integer and fractional parts
            note_int = int(note)
            note_frac = note - note_int
            
            # Calculate pitch bend value (-8192 to +8191)
            # Scale fractional part to pitch bend range
            bend_value = int(note_frac * 8192 / bend_range_semitones)
            
            # Add pitch bend
            midi.addPitchWheelEvent(track, channel, time + (i * note_duration), bend_value)
            
            # Add note (integer part only)
            midi.addNote(track, channel, note_int, time + (i * note_duration),
                        note_duration, velocity)
            
            # Reset pitch bend if needed
            if reset_bend_after_note:
                midi.addPitchWheelEvent(track, channel,
                                     time + ((i + 1) * note_duration), 0)
        else:
            # Round to nearest semitone
            note = round(note)
            midi.addNote(track, channel, note, time + (i * note_duration),
                        note_duration, velocity)
    
    return midi

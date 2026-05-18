"""
Changes the pitch of a sound effect.

Path: pitch_changer.py
Project: amoginarium
Created: 07.04.2026
Authors: Nilusink
"""

import os

import librosa
import soundfile as sf


def generate_pitch_variants(
    input_path: str, output_dir: str, semitone_steps: list[float], prefix: str = None
) -> list[str]:
    """
    Generate pitch-shifted variants of an audio file while preserving duration.

    Args:
        input_path: path to source audio file
        output_dir: directory where outputs will be written
        semitone_steps: list of pitch shifts (in semitones, e.g. [-2, -1, 0, 1, 2])
        prefix: optional filename prefix (defaults to input filename)

    Returns:
        List of output file paths
    """

    os.makedirs(output_dir, exist_ok=True)

    # --- Load audio ---
    y, sr = librosa.load(input_path, sr=None, mono=False)

    # Normalize shape → (channels, samples)
    if y.ndim == 1:
        y = y.reshape(1, -1)

    output_files = []

    # --- Generate variants ---
    i = 0
    for step in semitone_steps:
        y_shifted = librosa.effects.pitch_shift(y, sr=sr, n_steps=step)

        # Back to (samples, channels) for writing
        y_out = y_shifted.T

        # Build filename
        filename = f"{i}.wav"
        i += 1
        out_path = os.path.join(output_dir, filename)

        # Write file
        sf.write(out_path, y_out, sr)

        output_files.append(out_path)

    return output_files


if __name__ == "__main__":
    input_file = "./assets/audio/effects/explosions/explosion_large/explosion_large.mp3"
    files = generate_pitch_variants(
        input_path=input_file,
        output_dir=os.path.join("/".join(input_file.split("/")[:-1]), ""),
        semitone_steps=[-1, -0.5, 0, 0.5, 1],
    )

    print(files)

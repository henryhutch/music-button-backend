import matplotlib.pyplot as plt
import numpy as np
import wave

with wave.open(r"C:\Users\henry\OneDrive\Documents\Personal\Projects\music-button\python\backend\recordings\ESP32-1_20250716_111625.wav", "rb") as wf:
    frames = wf.readframes(wf.getnframes())
    samples = np.frombuffer(frames, dtype=np.int16)

plt.plot(samples)
plt.title("Waveform")
plt.show()

import pyaudio
import numpy as np
from openwakeword.model import Model

print("Loading wake-word model...")

model = Model(
    wakeword_models=["hey_jarvis"],
    inference_framework="onnx"
)

pa = pyaudio.PyAudio()

stream = pa.open(
    rate=16000,
    channels=1,
    format=pyaudio.paInt16,
    input=True,
    frames_per_buffer=1280
)

print("\nListening... Say 'Jarvis' clearly.")
print("Press Ctrl+C to stop.\n")

try:
    while True:
        audio = np.frombuffer(
            stream.read(1280, exception_on_overflow=False),
            dtype=np.int16
        )

        model.predict(audio)

        for name, scores in model.prediction_buffer.items():
            if "hey_jarvis" in name.lower():
                score = scores[-1]

                print(
                    f"\rConfidence: {score:.3f}",
                    end="",
                    flush=True
                )

                if score >= 0.5:
                    print(
                        f"\n\nJARVIS DETECTED! Confidence: {score:.3f}"
                    )
                    break

except KeyboardInterrupt:
    print("\n\nStopped.")

finally:
    stream.stop_stream()
    stream.close()
    pa.terminate()
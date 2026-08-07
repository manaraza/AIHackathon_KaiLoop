"""
Loads the trained SecondCrop model once at startup and exposes a single
grade_image() function the API routes call.
"""

from pathlib import Path

import numpy as np
from PIL import Image

MODEL_PATH = Path(__file__).resolve().parent.parent / "model" / "secondcrop_model.keras"
IMG_SIZE = (224, 224)

# Score thresholds -> grade/route. The source training data is binary
# (fresh/rotten), so a real "Grade B" model doesn't exist yet — mid-range
# scores are routed to manual review as a stand-in until the supermarket
# photo shoot provides real blemished-produce training data.
GRADE_A_THRESHOLD = 0.7
GRADE_C_THRESHOLD = 0.3

_model = None


def _patch_keras_compat():
    """Some Keras 3.x builds emit a 'quantization_config' key in layer
    configs that older/newer Dense constructors on other machines don't
    accept. Strip it defensively so a model trained in one Colab/Keras
    version still loads wherever the backend runs."""
    import keras

    original_init = keras.layers.Dense.__init__
    if getattr(original_init, "_secondcrop_patched", False):
        return

    def patched_init(self, *args, **kwargs):
        kwargs.pop("quantization_config", None)
        original_init(self, *args, **kwargs)

    patched_init._secondcrop_patched = True
    keras.layers.Dense.__init__ = patched_init


def get_model():
    global _model
    if _model is None:
        _patch_keras_compat()
        import keras

        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Model not found at {MODEL_PATH}. Train it via "
                f"model/train_secondcrop.ipynb and drop the .keras file there."
            )
        _model = keras.models.load_model(MODEL_PATH)
    return _model


def preprocess(image_bytes: bytes) -> np.ndarray:
    from tensorflow.keras.applications.mobilenet_v2 import preprocess_input

    img = Image.open(__import__("io").BytesIO(image_bytes)).convert("RGB")
    img = img.resize(IMG_SIZE)
    arr = np.array(img, dtype=np.float32)
    arr = preprocess_input(arr)
    return np.expand_dims(arr, axis=0)


def grade_image(image_bytes: bytes) -> dict:
    model = get_model()
    arr = preprocess(image_bytes)
    score = float(model.predict(arr, verbose=0)[0][0])

    if score >= GRADE_A_THRESHOLD:
        grade, route = "A", "retail"
    elif score <= GRADE_C_THRESHOLD:
        grade, route = "C", "rescue"
    else:
        grade, route = "B", "processing_review"

    return {"score": round(score, 4), "grade": grade, "route": route}

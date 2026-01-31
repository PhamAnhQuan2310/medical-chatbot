import io
from pathlib import Path
from typing import Tuple, Optional

import numpy as np
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image, ImageOps   


BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_DIR = BASE_DIR / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

# Các model
ROUTER_MODEL_PATH = MODEL_DIR / "router_resnet18_4domains.pth"
CHEST_MODEL_PATH  = MODEL_DIR / "lung.onnx"   # Pneumonia (NORMAL / PNEUMONIA)
EYE_MODEL_PATH    = MODEL_DIR / "eyes.onnx"   # OCT2017 (CNV / DME / DRUSEN / NORMAL)
SKIN_MODEL_PATH   = MODEL_DIR / "skin.onnx"   # DermNet 23 classes
TEETH_MODEL_PATH  = MODEL_DIR / "teeth.onnx"  
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Nhãn của router
CLASS_NAMES = ["chest_xray", "retina_oct", "skin_derm", "teeth_cavity"]

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD  = [0.229, 0.224, 0.225]



def build_router_model(num_classes: int = 4, device: str = DEVICE) -> nn.Module:
    """
    Tạo kiến trúc ResNet18 giống lúc train router.
    """
    m = models.resnet18(weights=None)
    in_f = m.fc.in_features
    m.fc = nn.Linear(in_f, num_classes)
    state = torch.load(ROUTER_MODEL_PATH, map_location=device)
    m.load_state_dict(state)
    m.to(device)
    m.eval()
    return m



ROUTER_TRANSFORM = transforms.Compose(
    [
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ]
)


try:
    ROUTER_MODEL = build_router_model()
    print(f"[disease_router] ✅ Loaded router model from {ROUTER_MODEL_PATH}")
except Exception as e:
    print(f"[disease_router] ⚠ Không load được router model: {e}")
    ROUTER_MODEL = None




try:
    import onnxruntime as ort
except ImportError:
    ort = None
    print("[disease_router] ⚠ onnxruntime chưa được cài. Hãy chạy: pip install onnxruntime-gpu hoặc onnxruntime")


def build_onnx_session(path: Path) -> Optional["ort.InferenceSession"]:
    if ort is None:
        return None
    if not path.exists():
        print(f"[disease_router] ⚠ Không tìm thấy file ONNX: {path}")
        return None
    providers = (
        ["CUDAExecutionProvider", "CPUExecutionProvider"]
        if torch.cuda.is_available()
        else ["CPUExecutionProvider"]
    )
    try:
        sess = ort.InferenceSession(str(path), providers=providers)
        print(f"[disease_router] ✅ Loaded ONNX model: {path.name}")
        return sess
    except Exception as e:
        print(f"[disease_router] ⚠ Lỗi load ONNX {path}: {e}")
        return None


CHEST_SESSION = build_onnx_session(CHEST_MODEL_PATH)
EYE_SESSION   = build_onnx_session(EYE_MODEL_PATH)
SKIN_SESSION  = build_onnx_session(SKIN_MODEL_PATH)
# TEETH_SESSION = build_onnx_session(TEETH_MODEL_PATH)  # Sau này sẽ train lại cái này 


# =========================
# TIỀN XỬ LÝ RIÊNG CHO TỪNG MODEL
# =========================

# Phổi (Pneumonia)

CHEST_IMG_SIZE = 224
CHEST_TRANSFORM = transforms.Compose(
    [
        transforms.Grayscale(num_output_channels=3),
        transforms.Resize(256),
        transforms.CenterCrop(CHEST_IMG_SIZE),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ]
)

def preprocess_chest(image: Image.Image) -> np.ndarray:
    x = CHEST_TRANSFORM(image).unsqueeze(0).numpy().astype("float32")  # [1,3,224,224]
    return x


# Mắt (OCT2017) 

def _keep_aspect_resize_pad_eye(
    img: Image.Image,
    size: int = 512,
    fill: int = 0,
) -> Image.Image:
    """Giữ tỉ lệ, resize theo cạnh dài rồi pad về (size, size) – giống keep_aspect_resize_pad."""
    w, h = img.size
    if w == 0 or h == 0:
        return Image.new("L", (size, size), color=fill)

    scale = size / max(w, h)
    new_w, new_h = int(round(w * scale)), int(round(h * scale))
    img = img.resize((new_w, new_h), resample=Image.BILINEAR)

    pad_left = (size - new_w) // 2
    pad_right = size - new_w - pad_left
    pad_top = (size - new_h) // 2
    pad_bottom = size - new_h - pad_top

    return ImageOps.expand(img, border=(pad_left, pad_top, pad_right, pad_bottom), fill=fill)


def _normalize_brightness_eye(img_gray: Image.Image) -> Image.Image:
    """Chuẩn hóa độ sáng – tương đương ImageOps.equalize như lúc train."""
    return ImageOps.equalize(img_gray)


EYE_IMG_SIZE = 512
EYE_TRANSFORM = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
])

def preprocess_eye(image: Image.Image) -> np.ndarray:
    """
    OCT preprocess giống pipeline train:
      - convert L
      - equalize brightness
      - keep_aspect_resize_pad -> 512x512
      - nhân 3 kênh grayscale
      - ToTensor + Normalize
    """
   
    gray = image.convert("L")
 
    gray = _normalize_brightness_eye(gray)
 
    gray = _keep_aspect_resize_pad_eye(gray, size=EYE_IMG_SIZE, fill=0)
  
    rgb = Image.merge("RGB", (gray, gray, gray))
  
    x = EYE_TRANSFORM(rgb).unsqueeze(0).numpy().astype("float32")  # [1,3,512,512]
    return x


# Da (DermNet)

SKIN_IMG_SIZE = 512
SKIN_TRANSFORM = transforms.Compose(
    [
        transforms.Resize((SKIN_IMG_SIZE, SKIN_IMG_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ]
)

def preprocess_skin(image: Image.Image) -> np.ndarray:
    x = SKIN_TRANSFORM(image).unsqueeze(0).numpy().astype("float32")  # [1,3,512,512]
    return x




def run_onnx_classification(
    session: "ort.InferenceSession",
    x: np.ndarray
) -> Tuple[int, float]:
    """
    Chạy model ONNX classification với input x đã được preprocess sẵn:
      x shape: [1, C, H, W]
    """
    if session is None:
        raise RuntimeError("ONNX session is None (model chưa được load).")

    inp_name = session.get_inputs()[0].name
    outputs = session.run(None, {inp_name: x})

    logits = np.array(outputs[0])
    logits = logits.reshape(1, -1)  # [1, num_classes]

    exps = np.exp(logits - logits.max(axis=1, keepdims=True))
    probs = exps / exps.sum(axis=1, keepdims=True)

    idx = int(probs.argmax(axis=1)[0])
    conf = float(probs[0, idx])
    return idx, conf


# =========================
# ROUTER
# =========================

def load_image_from_bytes(data: bytes) -> Image.Image:
    """Đọc bytes → PIL RGB (các transform sẽ tự convert grayscale nếu cần)."""
    img = Image.open(io.BytesIO(data)).convert("RGB")
    return img


def run_router(image: Image.Image) -> Tuple[str, float]:
    """
    Chạy router, trả về:
      - domain: tên lớp ('chest_xray' / 'retina_oct' / 'skin_derm' / 'teeth_cavity')
      - confidence: xác suất của lớp đó
    """
    if ROUTER_MODEL is None:
        raise RuntimeError("Router model chưa được load (ROUTER_MODEL is None).")

    x = ROUTER_TRANSFORM(image).unsqueeze(0).to(DEVICE)  # [1,3,224,224]
    with torch.no_grad():
        logits = ROUTER_MODEL(x)
        probs = torch.softmax(logits, dim=1)[0].cpu().numpy()

    idx = int(probs.argmax())
    domain = CLASS_NAMES[idx]
    confidence = float(probs[idx])
    return domain, confidence


# =========================
# CHẨN ĐOÁN 3 DOMAIN CLASSIFICATION
# =========================

def diagnose_chest(image: Image.Image) -> str:
    """
    Model phổi – lung.onnx
    Binary: output 1 logit (PNEUMONIA)
    """
    try:
        x = preprocess_chest(image)       # [1,3,224,224]
        sess = CHEST_SESSION
        if sess is None:
            raise RuntimeError("CHEST_SESSION is None")

        inp_name = sess.get_inputs()[0].name
        outputs = sess.run(None, {inp_name: x})

        logits = np.array(outputs[0]).reshape(-1)[0]
        prob_pneu = 1.0 / (1.0 + np.exp(-logits))   # sigmoid

        if prob_pneu >= 0.5:
            label = "PNEUMONIA"
            conf = prob_pneu
        else:
            label = "NORMAL"
            conf = 1.0 - prob_pneu

    except Exception as e:
        return f"Lỗi chạy model phổi: {e}"

    return f"🫁 Phổi: {label} (p = {conf:.3f})"


def diagnose_eye(image: Image.Image) -> str:
    """
    Model OCT mắt – eyes.onnx
    OCT2017: 4 lớp [CNV, DME, DRUSEN, NORMAL]
    """
    try:
        x = preprocess_eye(image)
        idx, conf = run_onnx_classification(EYE_SESSION, x)
    except Exception as e:
        return f"Lỗi chạy model mắt: {e}"

    labels = ["CNV", "DME", "DRUSEN", "NORMAL"]

    label = labels[idx] if idx < len(labels) else f"Lớp {idx}"
    return f"👁️ OCT: {label} (p = {conf:.3f})"


def diagnose_skin(image: Image.Image) -> str:
    """
    Model da – skin.onnx (DermNet 23 classes)
    """
    try:
        x = preprocess_skin(image)
        idx, conf = run_onnx_classification(SKIN_SESSION, x)
    except Exception as e:
        return f"Lỗi chạy model da: {e}"

    labels = [
        "Acne and Rosacea Photos",
        "Actinic Keratosis Basal Cell Carcinoma and other Malignant Lesions",
        "Atopic Dermatitis Photos",
        "Bullous Disease Photos",
        "Cellulitis Impetigo and other Bacterial Infections",
        "Eczema Photos",
        "Exanthems and Drug Eruptions",
        "Hair Loss Photos Alopecia and other Hair Diseases",
        "Herpes HPV and other STDs Photos",
        "Light Diseases and Disorders of Pigmentation",
        "Lupus and other Connective Tissue diseases",
        "Melanoma Skin Cancer Nevi and Moles",
        "Nail Fungus and other Nail Disease",
        "Poison Ivy Photos and other Contact Dermatitis",
        "Psoriasis pictures Lichen Planus and related diseases",
        "Scabies Lyme Disease and other Infestations and Bites",
        "Seborrheic Keratoses and other Benign Tumors",
        "Systemic Disease",
        "Tinea Ringworm Candidiasis and other Fungal Infections",
        "Urticaria Hives",
        "Vascular Tumors",
        "Vasculitis Photos",
        "Warts Molluscum and other Viral Infections",
    ]

    label = labels[idx] if idx < len(labels) else f"Lớp {idx}"
    return f"🧴 Da liễu: {label} (p = {conf:.3f})"




def diagnose_teeth(image: Image.Image) -> str:
    """
    Bạn đã bỏ YOLO răng, nên tạm thời trả về thông báo placeholder.
    """
    return "🦷 Chức năng chẩn đoán răng đang được cập nhật, hiện chưa hỗ trợ."

import os
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parent.parent
STUDENTS_DIR = BASE_DIR / "demo_data" / "students"
STUDENTS_DIR.mkdir(parents=True, exist_ok=True)

FONT_CANDIDATES = [
    "C:/Windows/Fonts/segoepr.ttf",   # Segoe Print
    "C:/Windows/Fonts/Inkfree.ttf",   # Ink Free
    "C:/Windows/Fonts/segoesc.ttf",   # Segoe Script
    "C:/Windows/Fonts/comic.ttf",     # Comic Sans
    "C:/Windows/Fonts/arial.ttf"      # Fallback
]

def get_font(size: int, font_path: str = None) -> ImageFont.FreeTypeFont:
    if font_path and os.path.exists(font_path):
        try:
            return ImageFont.truetype(font_path, size)
        except Exception:
            pass
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()

def draw_ruled_notebook_sheet(width: int = 1400, height: int = 2200) -> Image.Image:
    """Draws a ruled college notebook sheet with margins and paper texture."""
    img = Image.new("RGB", (width, height), (252, 251, 247))
    draw = ImageDraw.Draw(img)

    line_spacing = 34
    margin_top = 110
    rule_color = (210, 222, 238)  # Faint blue horizontal lines
    
    y = margin_top
    while y < height - 50:
        draw.line([(50, y), (width - 50, y)], fill=rule_color, width=1)
        y += line_spacing

    # Double red margin on left
    margin_left = 130
    draw.line([(margin_left, 30), (margin_left, height - 30)], fill=(245, 175, 180), width=2)
    draw.line([(margin_left + 4, 30), (margin_left + 4, height - 30)], fill=(245, 175, 180), width=1)

    # Top header separator
    draw.line([(50, margin_top - 20), (width - 50, margin_top - 20)], fill=(225, 160, 165), width=2)

    return img

def create_alice_assignment():
    """Alice: Full, rigorous derivations, math calculations, and high legibility."""
    img = draw_ruled_notebook_sheet(1400, 2300)
    draw = ImageDraw.Draw(img)
    
    font_main = get_font(21, "C:/Windows/Fonts/segoepr.ttf")
    font_header = get_font(23, "C:/Windows/Fonts/segoeprb.ttf")
    ink = (18, 35, 75)

    # Header
    draw.text((150, 45), "Alice Johnson  |  Roll: CS-2026-081  |  Course: Advanced ML (CS 482)", fill=ink, font=font_header)
    draw.text((1080, 45), "Final Exam (50 M)", fill=ink, font=font_header)

    lines = [
        ("Q1 (a) Scaled Dot-Product Attention Derivation:", True),
        ("Attention(Q, K, V) = softmax((Q * K^T) / sqrt(d_k)) * V, where Q, K in R^(n x d_k), V in R^(n x d_v).", False),
        ("Justification for 1/sqrt(d_k): Assume components of q and k are independent random variables with", False),
        ("mean 0 and variance 1. Then their dot-product q.k = sum_{i=1}^{d_k} q_i k_i has mean 0 and variance d_k.", False),
        ("For large d_k, dot-products grow large in magnitude, pushing softmax into extreme regions with tiny gradients", False),
        ("(vanishing gradient saturation). Scaling by 1/sqrt(d_k) normalizes variance back to 1, stabilizing training.", False),
        ("(b) Complexity: Self-Attention is O(n^2 * d) per layer with O(1) sequential steps (fully parallel).", False),
        ("RNN is O(n * d^2) per layer with O(n) sequential steps. When n < d, Attention is faster and parallelizable.", False),
        ("", False),
        ("Q2 (a) Vanishing Gradients via Chain Rule:", True),
        ("dL/dw_1 = (dL/da_L) * prod_{l=2}^L (da_l/da_{l-1}) * (da_1/dw_1). For Sigmoid sigma(z)=1/(1+e^-z),", False),
        ("the derivative sigma'(z) = sigma(z)(1-sigma(z)) <= 0.25. Multiplying L terms with values <= 0.25 causes", False),
        ("gradients to vanish exponentially: (0.25)^L -> 0. ReLU avoids this because d/dz max(0,z) = 1 for z > 0.", False),
        ("(b) Adam Update Equations: m_t = beta_1 m_{t-1} + (1-beta_1) g_t  (first moment / momentum)", False),
        ("v_t = beta_2 v_{t-1} + (1-beta_2) g_t^2  (second moment / uncentered variance)", False),
        ("Bias correction due to zero initialization: m_hat_t = m_t / (1 - beta_1^t), v_hat_t = v_t / (1 - beta_2^t).", False),
        ("Weight update: theta_{t+1} = theta_t - (alpha / (sqrt(v_hat_t) + eps)) * m_hat_t.", False),
        ("", False),
        ("Q3 Medical Model Evaluation & Trade-off Analysis:", True),
        ("Given: TP = 85, FN = 15, FP = 170, TN = 9730. Total = 10,000 patients.", False),
        ("1) Accuracy = (TP + TN) / Total = (85 + 9730) / 10000 = 9815 / 10000 = 98.15%.", False),
        ("2) Precision = TP / (TP + FP) = 85 / (85 + 170) = 85 / 255 = 1/3 = 33.33%.", False),
        ("3) Recall (Sensitivity) = TP / (TP + FN) = 85 / (85 + 15) = 85 / 100 = 85.00%.", False),
        ("4) F1-Score = 2 * (P * R) / (P + R) = 2*(0.3333 * 0.85) / (0.3333 + 0.85) = 0.5666 / 1.1833 = 47.88%.", False),
        ("Analysis: Accuracy is misleading because a dummy all-negative model gets 99% accuracy while detecting 0 cases.", False),
        ("In medical screening, Recall is paramount: False Negatives mean diseased patients go untreated (fatal risk).", False),
        ("", False),
        ("Q4 Distributed LLM Training & Ring-AllReduce:", True),
        ("(a) Data Parallelism duplicates model and splits mini-batch across GPUs; gradients averaged via AllReduce.", False),
        ("Model Parallelism splits weights: Tensor Parallelism partitions individual weight matrices (Megatron-LM),", False),
        ("while Pipeline Parallelism partitions layers sequentially across GPUs with micro-batch schedules (GPipe).", False),
        ("(b) Parameter Server has central bottleneck O(P * M) communication. In Ring-AllReduce, each of P nodes", False),
        ("splits buffer into P chunks, sending 2 * ((P-1)/P) * M data across Scatter-Reduce & AllGather steps.", False),
        ("Communication volume per GPU is ~ 2M, which is completely independent of the number of GPUs P.", False),
        ("", False),
        ("Q5 Regularization & Normalization Architectures:", True),
        ("(a) Geometry: L1 constraint ||w||_1 <= C forms a diamond with sharp corners on axes; expanding loss ellipses", False),
        ("touch diamond vertices first, setting weights strictly to zero (sparsity). L2 constraint is a smooth circle.", False),
        ("(b) Batch Norm normalizes across batch dimension N for each channel: depends on batch size, fails for RNNs.", False),
        ("Layer Norm normalizes across features C for each individual token: independent of batch size, ideal for Transformers.", False)
    ]

    y = 125
    for text, is_header in lines:
        if not text:
            y += 16
            continue
        f = font_header if is_header else font_main
        draw.text((150 + random.randint(-1, 1), y), text, fill=ink, font=f)
        y += 38

    output_path = STUDENTS_DIR / "student_alice.png"
    img.save(output_path, "PNG")
    print(f"Generated: {output_path}")

def create_bob_assignment():
    """Bob: Average student, misses tensor parallelism, makes calculation mistake in Q3."""
    img = draw_ruled_notebook_sheet(1400, 2300)
    draw = ImageDraw.Draw(img)

    font_main = get_font(21, "C:/Windows/Fonts/Inkfree.ttf")
    font_header = get_font(23, "C:/Windows/Fonts/Inkfree.ttf")
    ink = (15, 15, 20)

    draw.text((150, 45), "Bob Martinez  |  ID: CS-2026-082  |  CS 482 Advanced ML", fill=ink, font=font_header)

    lines = [
        ("Ans 1 (Attention):", True),
        ("Attention = softmax(Q * K^T / sqrt(d_k)) * V. Q and K are projections of sequence embeddings.", False),
        ("We divide by sqrt(d_k) to prevent dot products from getting too big which slows down softmax.", False),
        ("Self-attention has O(n^2 * d) complexity because we compute the full n x n attention matrix.", False),
        ("RNN complexity is O(n * d^2) because of recurrence.", False),
        ("", False),
        ("Ans 2 (Gradients & Adam):", True),
        ("Vanishing gradient is caused by repeatedly multiplying small derivatives in backprop chain rule.", False),
        ("Sigmoid max derivative is 0.25, so for many layers gradients vanish. ReLU derivative is 1 so it solves it.", False),
        ("Adam equations: m_t = beta_1 m_{t-1} + (1 - beta_1) g_t (momentum), v_t = beta_2 v_{t-1} + (1 - beta_2) g_t^2.", False),
        ("We use bias correction m_hat and v_hat to fix zero initialization at start, then update theta.", False),
        ("", False),
        ("Ans 3 (Confusion Matrix):", True),
        ("TP = 85, FN = 15, FP = 170, TN = 9730. Total = 10,000.", False),
        ("Accuracy = (85 + 9730) / 10000 = 98.15%.", False),
        ("Precision = TP / (TP + FN) = 85 / (85 + 15) = 85 / 100 = 85.0%   [Notice: Confused formula with Recall!]", False),
        ("Recall = TP / (TP + FP) = 85 / (85 + 170) = 85 / 255 = 33.3%.", False),
        ("F1 = 2 * (0.85 * 0.333) / (0.85 + 0.333) = 0.566 / 1.183 = 47.8%.", False),
        ("Accuracy is misleading because negative cases dominate. In hospital tests Recall is most important.", False),
        ("", False),
        ("Ans 4 (Parallelism & Ring AllReduce):", True),
        ("Data Parallelism copies model on all workers and splits data batches.", False),
        ("Pipeline Parallelism splits network layers across multiple GPUs in a line.", False),
        ("Parameter Server is slow because the master server gets overwhelmed with gradient traffic.", False),
        ("Ring AllReduce organizes GPUs in a circle ring so communication is shared across workers.", False),
        ("", False),
        ("Ans 5 (L1 vs L2 & Normalization):", True),
        ("L1 regularization forces weights to 0 because of absolute value penalty, while L2 shrinks them.", False),
        ("Batch Norm normalizes along batch dimension, but depends heavily on having large batch size.", False),
        ("Layer Norm normalizes across feature dimensions per sample, so it works better for Transformers.", False)
    ]

    y = 125
    for text, is_header in lines:
        if not text:
            y += 20
            continue
        f = font_header if is_header else font_main
        draw.text((150 + random.randint(-2, 2), y), text, fill=ink, font=f)
        y += 40

    output_path = STUDENTS_DIR / "student_bob.png"
    img.save(output_path, "PNG")
    print(f"Generated: {output_path}")

def create_charlie_assignment():
    """Charlie: Struggling, messy handwriting, omitted formulas, incorrect accuracy conclusion."""
    img = draw_ruled_notebook_sheet(1400, 2300)
    draw = ImageDraw.Draw(img)

    font_main = get_font(20, "C:/Windows/Fonts/segoesc.ttf")
    font_header = get_font(22, "C:/Windows/Fonts/segoescb.ttf")
    ink = (35, 45, 95)

    draw.text((140, 45), "Charlie Davis  CS 482 Exam", fill=ink, font=font_header)

    lines = [
        ("Q1:", True),
        ("Attention = softmax(Q * K) * V.", False),
        ("Scale factor sqrt(d_k) is used to scale down numbers.", False),
        ("Attention is O(n^2) and RNN is O(n).", False),
        ("", False),
        ("Q2:", True),
        ("Vanishing gradient is when gradients get small during backpropagation.", False),
        ("Sigmoid makes gradients small. ReLU is better.", False),
        ("Adam optimizer uses momentum and RMSprop gradient steps.", False),
        ("", False),
        ("Q3:", True),
        ("Total samples = 10000. TP=85, TN=9730.", False),
        ("Accuracy = (85 + 9730)/10000 = 98.15%.", False),
        ("The model accuracy is 98.15% which is very high and sufficient for patients.", False),
        ("Precision and Recall are around 50%.", False),
        ("", False),
        ("Q4:", True),
        ("Data parallelism divides data. Model parallelism divides model.", False),
        ("Ring all reduce connects GPUs in ring to reduce parameter server overload.", False),
        ("", False),
        ("Q5:", True),
        ("L1 gives sparse weights. L2 gives small weights.", False),
        ("Batch norm is for batches. Layer norm is for layers.", False)
    ]

    y = 130
    for text, is_header in lines:
        if not text:
            y += 24
            continue
        f = font_header if is_header else font_main
        # Add slight wobble
        draw.text((145 + random.randint(-4, 4), y + random.randint(-1, 2)), text, fill=ink, font=f)
        if "The model accuracy is 98.15%" in text:
            draw.line([(145, y + 15), (450, y + 15)], fill=(130, 25, 25), width=2)
        y += 46

    # Rotate slightly
    img = img.rotate(1.0, resample=Image.Resampling.BICUBIC, expand=False, fillcolor=(250, 248, 245))

    output_path = STUDENTS_DIR / "student_charlie.png"
    img.save(output_path, "PNG")
    print(f"Generated: {output_path}")

if __name__ == "__main__":
    create_alice_assignment()
    create_bob_assignment()
    create_charlie_assignment()
    print("Successfully generated advanced handwritten student papers!")

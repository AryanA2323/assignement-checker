import os
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parent.parent
STUDENTS_DIR = BASE_DIR / "demo_data" / "students"
STUDENTS_DIR.mkdir(parents=True, exist_ok=True)

# Select best available handwriting-like fonts on Windows
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

def draw_lined_notebook_sheet(width: int = 1200, height: int = 1600) -> Image.Image:
    """Draws a realistic ruled paper notebook page with margin lines and paper texture."""
    # Warm slightly off-white notebook paper color
    img = Image.new("RGB", (width, height), (252, 251, 248))
    draw = ImageDraw.Draw(img)

    # Ruled lines
    line_spacing = 38
    margin_top = 120
    rule_color = (205, 220, 240)  # Faint blue rule lines
    
    y = margin_top
    while y < height - 60:
        draw.line([(60, y), (width - 60, y)], fill=rule_color, width=1)
        y += line_spacing

    # Vertical red margin line
    margin_left = 140
    margin_color = (245, 180, 185)
    draw.line([(margin_left, 40), (margin_left, height - 40)], fill=margin_color, width=2)

    # Perforated border or header rule
    draw.line([(60, margin_top - 30), (width - 60, margin_top - 30)], fill=(220, 170, 175), width=2)

    return img

def create_alice_assignment():
    """Generates Alice's submission: High-scoring, neat handwriting, complete answers."""
    img = draw_lined_notebook_sheet(1200, 1500)
    draw = ImageDraw.Draw(img)
    
    font_main = get_font(24, "C:/Windows/Fonts/segoepr.ttf")
    font_header = get_font(26, "C:/Windows/Fonts/segoeprb.ttf")
    ink_color = (20, 35, 75)  # Royal blue pen ink

    # Header
    draw.text((160, 55), "Name: Alice Johnson", fill=ink_color, font=font_header)
    draw.text((650, 55), "Roll No: STU-1001", fill=ink_color, font=font_header)
    draw.text((950, 55), "Date: 12-Oct", fill=ink_color, font=font_header)

    lines = [
        ("Q1. Ans:", True),
        ("Supervised learning is trained on labeled data with known target outcomes.", False),
        ("It maps input features to predefined labels (e.g., spam detection & house pricing).", False),
        ("Unsupervised learning uses unlabeled data to discover hidden patterns and groupings", False),
        ("without human guidance (e.g., K-Means customer segmentation and PCA).", False),
        ("", False),
        ("Q2. Ans:", True),
        ("Overfitting occurs when a machine learning model memorizes training noise and details,", False),
        ("yielding high training accuracy but failing to generalize on unseen test data.", False),
        ("Two prevention techniques:", False),
        (" 1) Regularization: Adding L1 (Lasso) or L2 (Ridge) weight penalties, or Dropout.", False),
        (" 2) Early Stopping or K-fold Cross-Validation to halt before validation loss rises.", False),
        ("", False),
        ("Q3. Ans:", True),
        ("CNNs use convolutional kernels and spatial pooling designed for grid data like images.", False),
        ("RNNs use recurrent feedback loops and hidden states to process sequential / time-series data.", False),
        ("", False),
        ("Q4. Ans:", True),
        ("Gradient Descent is an optimization algorithm that minimizes the loss function by iteratively", False),
        ("updating weights in the opposite direction of the gradient: w = w - alpha * grad.", False),
        ("Learning rate (alpha) determines step size: if too large, it diverges; if too small, it converges very slowly.", False),
    ]

    y = 135
    for text, is_header in lines:
        if not text:
            y += 20
            continue
        f = font_header if is_header else font_main
        # Slight jitter to mimic real hand
        x_jitter = random.randint(-1, 1)
        y_jitter = random.randint(-1, 1)
        draw.text((160 + x_jitter, y + y_jitter), text, fill=ink_color, font=f)
        y += 42

    output_path = STUDENTS_DIR / "student_alice.png"
    img.save(output_path, "PNG")
    print(f"Generated: {output_path}")

def create_bob_assignment():
    """Generates Bob's submission: Average score, casual handwriting, missing a few keywords."""
    img = draw_lined_notebook_sheet(1200, 1500)
    draw = ImageDraw.Draw(img)

    font_main = get_font(23, "C:/Windows/Fonts/Inkfree.ttf")
    font_header = get_font(25, "C:/Windows/Fonts/Inkfree.ttf")
    ink_color = (15, 15, 20)  # Black ballpoint ink

    draw.text((160, 55), "Name: Bob Martinez", fill=ink_color, font=font_header)
    draw.text((650, 55), "Roll: STU-1002", fill=ink_color, font=font_header)

    lines = [
        ("Ans 1:", True),
        ("Supervised learning uses labeled datasets to predict outputs from inputs.", False),
        ("Unsupervised learning groups unlabeled data into clusters without labels.", False),
        ("Example: classification for supervised, clustering for unsupervised.", False),
        ("", False),
        ("Ans 2:", True),
        ("Overfitting is when the model performs very well on train data but badly on test data.", False),
        ("This is caused by fitting to the noise.", False),
        ("Prevention: We can use Dropout layers in the network, and collect more data.", False),
        ("", False),
        ("Ans 3:", True),
        ("CNN has convolutional layers which are used for 2D image processing.", False),
        ("RNN has internal loops which are used for text sentences and audio sequences.", False),
        ("", False),
        ("Ans 4:", True),
        ("Gradient descent is an iterative algorithm to find minimum error of the model.", False),
        ("The learning rate decides the speed of steps. If it is high it can jump over the minimum.", False),
    ]

    y = 135
    for text, is_header in lines:
        if not text:
            y += 24
            continue
        f = font_header if is_header else font_main
        x_jitter = random.randint(-2, 2)
        y_jitter = random.randint(-1, 2)
        draw.text((160 + x_jitter, y + y_jitter), text, fill=ink_color, font=f)
        y += 44

    output_path = STUDENTS_DIR / "student_bob.png"
    img.save(output_path, "PNG")
    print(f"Generated: {output_path}")

def create_charlie_assignment():
    """Generates Charlie's submission: Low score, messy handwriting, incomplete answers, crossed out text."""
    img = draw_lined_notebook_sheet(1200, 1500)
    draw = ImageDraw.Draw(img)

    font_main = get_font(22, "C:/Windows/Fonts/segoesc.ttf")
    font_header = get_font(24, "C:/Windows/Fonts/segoescb.ttf")
    ink_color = (30, 45, 90)  # Messier blue ink

    draw.text((155, 55), "Charlie Davis", fill=ink_color, font=font_header)
    draw.text((650, 55), "STU-1003", fill=ink_color, font=font_header)

    lines = [
        ("Ans 1:", True),
        ("Supervised has labels. Unsupervised doesn't have labels.", False),
        ("Machine learning learns patterns from numbers.", False),
        ("", False),
        ("Ans 2:", True),
        ("Overfitting is when training score is too high.", False),
        ("Stop training early to prevent it.", False),
        ("", False),
        ("Ans 3:", True),
        ("CNN is convolution net for camera photos.", False),
        ("RNN is recursive net for text.", False),
        ("", False),
        ("Ans 4:", True),
        ("Gradient descent minimizes loss using slope math steps.", False),
        ("Learning rate is step size.", False),
    ]

    y = 140
    for text, is_header in lines:
        if not text:
            y += 25
            continue
        f = font_header if is_header else font_main
        x_jitter = random.randint(-4, 4)
        y_jitter = random.randint(-2, 3)
        draw.text((155 + x_jitter, y + y_jitter), text, fill=ink_color, font=f)
        
        # Add a simulated crossed out word for realistic messy paper
        if "Machine learning" in text:
            draw.line([(155, y + 14), (320, y + 14)], fill=(120, 20, 20), width=2)

        y += 48

    # Slight rotation to simulate tilted phone photo scan
    img = img.rotate(1.2, resample=Image.Resampling.BICUBIC, expand=False, fillcolor=(250, 248, 245))

    output_path = STUDENTS_DIR / "student_charlie.png"
    img.save(output_path, "PNG")
    print(f"Generated: {output_path}")

if __name__ == "__main__":
    create_alice_assignment()
    create_bob_assignment()
    create_charlie_assignment()
    print("Demo handwritten assignments successfully generated in demo_data/students/")

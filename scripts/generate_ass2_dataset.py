import os
import random
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

BASE_DIR = Path(__file__).resolve().parent.parent
ASS2_DIR = BASE_DIR / "demo_data" / "ass_2"
ASS2_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# 1. Master Solution JSON & Text Data for CS 460: Deep Learning
# ---------------------------------------------------------------------------
MASTER_DATA = {
    "title": "CS 460: Deep Learning & Neural Architectures — Assignment 2: Optimization, Attention Mechanisms & Regularization",
    "subject": "Deep Learning & Artificial Intelligence",
    "total_marks": 50.0,
    "instructions": "Evaluate based on technical accuracy, mathematical rigor, intermediate derivations, and hyperparameter analysis. Award partial credit for sound architectural reasoning even if final expressions contain minor arithmetic slips.",
    "questions": [
        {
            "question_id": "Q1",
            "question_text": "(a) Explain the Adam optimizer update equations. Derive why bias correction terms (1 - beta_1^t) and (1 - beta_2^t) are necessary for the first and second moment estimates m_t and v_t when initialized at zero. (b) Contrast SGD with Nesterov Accelerated Gradient (NAG) vs Adam in non-convex loss landscapes with narrow ravines and saddle points.",
            "max_marks": 12.0,
            "model_answer": "(a) Adam Update Equations & Bias Correction Derivation: Adam computes exponential moving averages of past gradients (first moment m_t = beta_1 * m_{t-1} + (1 - beta_1) * g_t) and squared gradients (second moment v_t = beta_2 * v_{t-1} + (1 - beta_2) * g_t^2). When m_0 = 0, expanding m_t recursively yields m_t = (1 - beta_1) * sum_{i=1}^t beta_1^{t-i} * g_i. Taking expectations on both sides under the assumption that true expectation E[g_i] is stationary (E[g_i] = E[g_t]): E[m_t] = E[(1 - beta_1) * sum_{i=1}^t beta_1^{t-i} * g_i] = E[g_t] * (1 - beta_1) * sum_{i=1}^t beta_1^{t-i} = E[g_t] * (1 - beta_1) * ((1 - beta_1^t) / (1 - beta_1)) = E[g_t] * (1 - beta_1^t). Because (1 - beta_1^t) < 1, the raw estimator m_t is severely biased toward zero during early iterations (small t). Dividing m_t by (1 - beta_1^t) yields the unbiased estimator m_hat_t such that E[m_hat_t] = E[g_t]. Exactly the same derivation applies to the uncentered variance v_t, yielding v_hat_t = v_t / (1 - beta_2^t). (b) SGD+NAG vs Adam: In narrow ravines and ill-conditioned curvatures, standard SGD oscillates violently across steep walls with negligible progress along gentle slopes. NAG computes gradients at a look-ahead position (theta + beta * v), anticipating future slope changes and damping oscillations. However, NAG maintains a single global learning rate. Adam utilizes coordinate-wise adaptive learning rates by dividing by sqrt(v_hat_t) + eps, automatically scaling down steps along steep dimensions (large second moment) and accelerating steps along flat dimensions (small second moment), escaping plateaus and saddle points far more rapidly.",
            "key_concepts": [
                "Adam first and second moment update formulas (m_t, v_t)",
                "Recursive expansion of m_t starting from zero initialization",
                "Expectation proof showing E[m_t] = E[g_t] * (1 - beta_1^t)",
                "Unbiased estimator formulation m_hat_t = m_t / (1 - beta_1^t) and v_hat_t = v_t / (1 - beta_2^t)",
                "Comparison of coordinate-wise adaptive scaling vs Nesterov look-ahead momentum on ravines"
            ],
            "grading_rubric": {
                "full_marks": "Complete recursive expansion and algebraic derivation of (1 - beta_1^t), correct bias-corrected estimators, and sound comparative analysis of coordinate-wise scaling vs NAG momentum.",
                "partial_marks": "States Adam equations accurately but omits expectation proof for bias correction, or gives superficial NAG comparison.",
                "minimal_marks": "Mentions Adam uses momentum without mathematical definitions or bias equations."
            }
        },
        {
            "question_id": "Q2",
            "question_text": "(a) In the Transformer architecture, define the Scaled Dot-Product Attention mechanism. Mathematically prove why the dot product Q*K^T must be scaled by 1/sqrt(d_k), explaining its effect on the softmax gradient. (b) Explain the representational capacity of Multi-Head Attention over Single-Head Attention. Analyze the computational complexity comparison between self-attention O(n^2 * d) and recurrent layers O(n * d^2).",
            "max_marks": 13.0,
            "model_answer": "(a) Scaled Dot-Product Attention is defined as Attention(Q, K, V) = softmax((Q * K^T) / sqrt(d_k)) * V, where Q, K are queries and keys of dimension d_k, and V is values of dimension d_v. Scaling factor derivation: Assume components of q and k are independent random variables with zero mean (E[q_i] = E[k_i] = 0) and unit variance (Var(q_i) = Var(k_i) = 1). The dot product is q . k = sum_{i=1}^{d_k} q_i * k_i. The expected value is E[q . k] = sum E[q_i * k_i] = 0. The variance is Var(q . k) = sum Var(q_i * k_i) = sum (Var(q_i) * Var(k_i)) = d_k * (1 * 1) = d_k. Thus, standard deviation of the dot product grows as sqrt(d_k). For large d_k, dot products grow substantially in magnitude, pushing the softmax function into regions with extremely small gradients (gradient saturation where d(softmax_i)/dz_j -> 0 when z_i >> z_j). Scaling by 1/sqrt(d_k) normalizes the variance back to Var((q . k) / sqrt(d_k)) = Var(q . k) / d_k = d_k / d_k = 1, ensuring stable gradient flow during backpropagation. (b) Multi-Head Attention vs Single-Head: Instead of performing a single attention function with d_model-dimensional keys, Multi-Head Attention linearly projects Q, K, V into h distinct lower-dimensional subspaces of dimension d_k = d_model / h. This allows the model to jointly attend to information from multiple representation subspaces at different positions (e.g., syntactic vs semantic relationships simultaneously). Single-head attention averages across these subspaces, losing fine-grained directional specialization. Complexity: Self-attention processes sequence of length n with dimension d in O(n^2 * d) time per layer with O(1) sequential path length. Recurrent layers (RNN/LSTM) require O(n * d^2) operations with O(n) sequential path length. When sequence length n < representation dimension d, self-attention is computationally faster and natively parallelizable across all tokens.",
            "key_concepts": [
                "Scaled Dot-Product Attention formula Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) V",
                "Variance derivation of dot product proving Var(q . k) = d_k under unit variance assumption",
                "Softmax gradient saturation critique (vanishing gradients for large input magnitudes)",
                "Multi-Head subspace projection rationale (attending to diverse linguistic/relational features)",
                "Complexity analysis O(n^2 * d) vs RNN O(n * d^2) and O(1) sequential execution path"
            ],
            "grading_rubric": {
                "full_marks": "Rigorous variance proof of Var(q.k)=d_k, clear explanation of softmax vanishing gradient prevention, multi-head subspace benefits, and complete complexity tradeoff.",
                "partial_marks": "States variance scaling intuitively without formal summation proof, or omits complexity analysis.",
                "minimal_marks": "Gives basic softmax formula without scaling proof or multi-head explanation."
            }
        },
        {
            "question_id": "Q3",
            "question_text": "(a) Compare Batch Normalization (BatchNorm) and Layer Normalization (LayerNorm) regarding normalization axes, dependencies across batch size, and suitability for sequential models. (b) Explain Inverted Dropout. Derive why activations must be scaled by 1/(1 - p) during training and explain why no scaling is required during inference.",
            "max_marks": 12.0,
            "model_answer": "(a) BatchNorm vs LayerNorm: Batch Normalization computes the mean and variance across the batch dimension (N) for each individual channel/feature (C, H, W). Consequently, BatchNorm depends strictly on mini-batch statistics; its performance degrades severely when batch size is small (e.g., N < 16) or varies dynamically across steps, and it requires maintaining running population statistics (mu_running, sigma^2_running) for inference. Furthermore, in variable-length sequential/RNN/Transformer models, sentence lengths vary, making cross-batch statistics problematic. Layer Normalization normalizes across all feature dimensions (C, H, W) for each individual sample independently (across the channel/hidden axis). Thus, LayerNorm has zero cross-sample dependencies, behaves identically at batch size 1, requires no running statistics across iterations, and is ideal for sequential models (Transformers, RNNs). (b) Inverted Dropout Derivation: In standard dropout with drop probability p, each neuron activation a is multiplied by a Bernoulli random mask r ~ Bernoulli(1 - p). During training, the expected activation is E[r * a] = (1 - p) * a. In naive dropout, test-time activations must be scaled by (1 - p) to match this expectation: a_test = (1 - p) * a. Inverted Dropout applies scaling directly during training by setting a_train = (r * a) / (1 - p). Expected value during training: E[a_train] = E[(r * a) / (1 - p)] = ((1 - p) * a) / (1 - p) = a. Because training expectation is already normalized to match the unmasked activation a, NO mathematical adjustments or scaling operations are needed at test time (a_test = a), dramatically accelerating inference and simplifying model deployment.",
            "key_concepts": [
                "BatchNorm normalizes across batch axis N; LayerNorm normalizes across feature axis per sample",
                "BatchNorm sensitivity to small batch size and requirement of running population statistics",
                "LayerNorm independence from batch size and suitability for variable-length sequence models",
                "Inverted Dropout training scaling factor 1 / (1 - p)",
                "Expectation proof E[a_train] = a showing why test-time requires zero scaling"
            ],
            "grading_rubric": {
                "full_marks": "Clear diagrammatic contrast of normalization axes, impact of mini-batch size, mathematical derivation of inverted dropout expectation invariance, and inference simplicity.",
                "partial_marks": "Contrasts BatchNorm and LayerNorm correctly but lacks mathematical expectation proof for inverted dropout.",
                "minimal_marks": "High-level definitions of dropout and normalization without equations or batch axis distinctions."
            }
        },
        {
            "question_id": "Q4",
            "question_text": "(a) For deep Residual Networks (ResNets), state the identity mapping formulation x_{l+1} = x_l + F(x_l, W_l). Derive the gradient flow equation dE/dx_l and mathematically explain why vanishing gradients are avoided even as network depth exceeds 100 layers. (b) Contrast standard residual blocks with Pre-Activation Residual Blocks.",
            "max_marks": 13.0,
            "model_answer": "(a) ResNet Gradient Flow Derivation: For any two layers l and L where L > l, the recursive identity formulation x_{l+1} = x_l + F(x_l) can be expanded telescopically to: x_L = x_l + sum_{i=l}^{L-1} F(x_i, W_i). Let E be the scalar loss function. Applying the multivariable chain rule to compute the gradient with respect to the earlier layer representation x_l: dE/dx_l = (dE/dx_L) * (dx_L/dx_l) = (dE/dx_L) * (d/dx_l (x_l + sum_{i=l}^{L-1} F(x_i, W_i))) = (dE/dx_L) * (I + d/dx_l sum_{i=l}^{L-1} F(x_i, W_i)), where I is the identity matrix. Why Vanishing Gradients are Avoided: The gradient dE/dx_l decomposes into two additive terms: (dE/dx_L) * I (direct, uninterrupted gradient highway from output layer L straight to input layer l) and (dE/dx_L) * (d/dx_l sum F). In traditional feedforward networks without skip connections, the gradient is a pure product of Jacobian matrices prod_{i=l}^L W_i, which exponentially decays to zero if singular values are < 1. In ResNets, the additive identity term I ensures that even if the weight Jacobian sum d/dx_l sum F decays toward zero, the gradient dE/dx_l does NOT vanish because it retains the non-vanishing component (dE/dx_L) * I. (b) Pre-Activation vs Post-Activation: In standard (post-activation) ResNet blocks, the addition is followed by Batch Normalization and ReLU: x_{l+1} = ReLU(BN(x_l + F(x_l))). This non-linear operation alters the clean identity highway x_l -> x_{l+1}. In Pre-Activation ResNets (He et al., 2016), BN and ReLU are moved inside the residual branch prior to weight multiplication: x_{l+1} = x_l + F(ReLU(BN(x_l))). This preserves a 100% clean identity path across the entire network, leading to easier optimization and lower test error for extremely deep networks (e.g. ResNet-1001).",
            "key_concepts": [
                "Telescopic expansion of residual layers x_L = x_l + sum F(x_i)",
                "Chain rule gradient formulation dE/dx_l = dE/dx_L * (I + d/dx_l sum F)",
                "Additive identity term I acts as an uninterrupted gradient highway",
                "Contrast with multiplicative Jacobian chain prod W_i causing exponential vanishing gradients",
                "Pre-activation architectural restructuring preserving unhampered identity flow"
            ],
            "grading_rubric": {
                "full_marks": "Rigorous telescopic expansion, exact chain rule derivation showing identity term I, clear proof of vanishing gradient prevention, and pre-activation comparison.",
                "partial_marks": "Derives gradient formula but misses telescopic expansion or gives incomplete explanation of why identity term prevents vanishing.",
                "minimal_marks": "States skip connections help training without mathematical equations or gradient derivation."
            }
        }
    ]
}

# ---------------------------------------------------------------------------
# 2. Generate Master Solution PDF using ReportLab
# ---------------------------------------------------------------------------
def generate_master_pdf():
    pdf_path = ASS2_DIR / "master_solution.pdf"
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=19,
        textColor=colors.HexColor("#1e293b"),
        alignment=1
    )
    meta_style = ParagraphStyle(
        "DocMeta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#475569"),
        alignment=1
    )
    q_title_style = ParagraphStyle(
        "QTitle",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=10,
        spaceAfter=4
    )
    model_style = ParagraphStyle(
        "ModelAns",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#0f766e")
    )
    rubric_style = ParagraphStyle(
        "Rubric",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#64748b")
    )

    story = []
    
    story.append(Paragraph("PACIFIC INSTITUTE OF TECHNOLOGY — DEPARTMENT OF ARTIFICIAL INTELLIGENCE", meta_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("CS 460: Deep Learning & Neural Architectures", title_style))
    story.append(Spacer(1, 2))
    story.append(Paragraph("Assignment 2 Master Solution & Grading Rubric | Maximum Marks: 50.0", meta_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#4f46e5"), spaceAfter=12))

    for q in MASTER_DATA["questions"]:
        header_text = f"<b>{q['question_id']} ({q['max_marks']} Marks):</b> {q['question_text']}"
        story.append(Paragraph(header_text, q_title_style))
        story.append(Spacer(1, 3))
        
        ans_text = f"<b>Reference Model Solution:</b><br/>{q['model_answer'].replace(chr(10), '<br/>')}"
        story.append(Paragraph(ans_text, model_style))
        story.append(Spacer(1, 4))

        keys_str = ", ".join(q["key_concepts"])
        rubric_str = f"<b>Required Key Concepts:</b> {keys_str}<br/><b>Rubric:</b> Full: {q['grading_rubric'].get('full_marks','')} | Partial: {q['grading_rubric'].get('partial_marks','')}"
        story.append(Paragraph(rubric_str, rubric_style))
        story.append(Spacer(1, 8))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=8))

    doc.build(story)
    print(f"Generated Master Solution PDF: {pdf_path}")

# ---------------------------------------------------------------------------
# 3. Notebook Sheet Generator (PIL)
# ---------------------------------------------------------------------------
def draw_ruled_page(width=1400, height=1950, page_num=1, total_pages=3, student_name="Student", student_roll="CS-460-000"):
    img = Image.new("RGB", (width, height), (252, 251, 246))
    draw = ImageDraw.Draw(img)

    margin_top = 110
    line_spacing = 34
    rule_color = (212, 224, 240)

    y = margin_top
    while y < height - 50:
        draw.line([(60, y), (width - 60, y)], fill=rule_color, width=1)
        y += line_spacing

    margin_left = 135
    draw.line([(margin_left, 35), (margin_left, height - 35)], fill=(245, 175, 180), width=2)
    draw.line([(margin_left + 4, 35), (margin_left + 4, height - 35)], fill=(245, 175, 180), width=1)
    draw.line([(60, margin_top - 20), (width - 60, margin_top - 20)], fill=(225, 160, 165), width=2)

    font_hdr = get_font(20, "C:/Windows/Fonts/segoeprb.ttf")
    header_text = f"{student_name}  |  Roll: {student_roll}  |  CS 460 Assignment 2"
    draw.text((155, 45), header_text, fill=(70, 80, 100), font=font_hdr)
    draw.text((width - 240, 45), f"Page {page_num} of {total_pages}", fill=(100, 110, 130), font=font_hdr)

    return img

def get_font(size: int, font_path: str = None) -> ImageFont.FreeTypeFont:
    if font_path and os.path.exists(font_path):
        try:
            return ImageFont.truetype(font_path, size)
        except Exception:
            pass
    for p in ["C:/Windows/Fonts/segoepr.ttf", "C:/Windows/Fonts/Inkfree.ttf", "C:/Windows/Fonts/segoesc.ttf", "C:/Windows/Fonts/arial.ttf"]:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()

# ---------------------------------------------------------------------------
# 4. Student 1: Elena Rostova (Score: ~94%, High Accuracy, Fountain Pen)
# ---------------------------------------------------------------------------
def generate_student_elena():
    font_main = get_font(21, "C:/Windows/Fonts/segoepr.ttf")
    font_bold = get_font(22, "C:/Windows/Fonts/segoeprb.ttf")
    ink = (18, 38, 88)

    # Page 1: Q1 (Adam Optimizer & Bias Correction)
    p1 = draw_ruled_page(page_num=1, total_pages=3, student_name="Elena Rostova", student_roll="CS-460-019")
    d1 = ImageDraw.Draw(p1)
    lines_p1 = [
        ("Q1 (a) Adam Optimizer & Bias Correction Derivation:", True),
        ("Adam computes 1st moment m_t = beta1 * m_{t-1} + (1 - beta1) * g_t and 2nd moment v_t = beta2 * v_{t-1} + (1 - beta2) * g_t^2.", False),
        ("Derivation of Bias Correction:", True),
        ("With m_0 = 0, expanding recursively yields: m_t = (1 - beta1) * sum_{i=1}^t beta1^{t-i} * g_i.", False),
        ("Taking expectations, assuming stationary true expectation E[g_i] = E[g_t]:", False),
        ("  E[m_t] = E[g_t] * (1 - beta1) * sum_{i=1}^t beta1^{t-i} = E[g_t] * (1 - beta1) * ((1 - beta1^t)/(1 - beta1)) = E[g_t] * (1 - beta1^t).", False),
        ("Because (1 - beta1^t) < 1, m_t is biased towards 0 during initial steps (especially when beta1 = 0.9).", False),
        ("To obtain an unbiased estimator: m_hat_t = m_t / (1 - beta1^t) such that E[m_hat_t] = E[g_t].", False),
        ("Similarly for second moment: v_hat_t = v_t / (1 - beta2^t) ensures E[v_hat_t] = E[g_t^2].", False),
        ("", False),
        ("Q1 (b) SGD+NAG vs Adam in Non-Convex Curvatures:", True),
        ("Standard SGD oscillates heavily across high-curvature ravine walls with slow progress down the valley.", False),
        ("Nesterov Accelerated Gradient (NAG) calculates gradients at theta + beta*v (look-ahead step),", False),
        ("which dampens oscillations before committing the update, but still relies on a single scalar learning rate.", False),
        ("Adam dynamically scales learning rates per coordinate by dividing by sqrt(v_hat_t) + eps.", False),
        ("This suppresses steep gradients with high second moments and accelerates flat dimensions with low variance,", False),
        ("enabling rapid traversal of ravines and quick escape from saddle points.", False)
    ]
    y = 125
    for text, is_b in lines_p1:
        if not text:
            y += 18
            continue
        d1.text((155 + random.randint(-1, 1), y), text, fill=ink, font=font_bold if is_b else font_main)
        y += 38

    # Page 2: Q2 (Transformer Scaled Dot-Product & Multi-Head)
    p2 = draw_ruled_page(page_num=2, total_pages=3, student_name="Elena Rostova", student_roll="CS-460-019")
    d2 = ImageDraw.Draw(p2)
    lines_p2 = [
        ("Q2 (a) Scaled Dot-Product Attention & Variance Derivation:", True),
        ("Attention formula: Attention(Q, K, V) = softmax( (Q * K^T) / sqrt(d_k) ) * V.", False),
        ("Mathematical Proof of Variance Scaling:", True),
        ("Assume components of q and k are independent with mean E[q_i] = 0 and variance Var(q_i) = 1.", False),
        ("The dot product is: q . k = sum_{i=1}^{d_k} q_i * k_i.", False),
        ("  E[q . k] = sum E[q_i] * E[k_i] = 0.", False),
        ("  Var(q . k) = sum Var(q_i * k_i) = sum (Var(q_i) * Var(k_i)) = d_k * (1 * 1) = d_k.", False),
        ("Standard deviation equals sqrt(d_k). For large d_k, dot products grow huge in magnitude,", False),
        ("pushing softmax into extreme saturating regions where its derivative d(softmax)/dz -> 0 (vanishing gradients).", False),
        ("Dividing by sqrt(d_k) scales variance back: Var((q . k)/sqrt(d_k)) = Var(q . k)/d_k = d_k/d_k = 1, ensuring stable gradient flow.", False),
        ("", False),
        ("Q2 (b) Multi-Head Attention Representation & Complexity:", True),
        ("Multi-Head Attention projects Q, K, V into h distinct lower-dimensional subspaces of dimension d_k = d_model / h.", False),
        ("This allows the network to jointly attend to different representation spaces (e.g. syntactic, positional, coreference).", False),
        ("Single-head attention averages over these diverse subspaces, destroying directional specialization.", False),
        ("Complexity: Self-attention requires O(n^2 * d) operations with O(1) sequential path length.", False),
        ("RNNs require O(n * d^2) operations with O(n) sequential path length, precluding parallelization across tokens.", False)
    ]
    y = 125
    for text, is_b in lines_p2:
        if not text:
            y += 18
            continue
        d2.text((155 + random.randint(-1, 1), y), text, fill=ink, font=font_bold if is_b else font_main)
        y += 38

    # Page 3: Q3 (Normalization & Inverted Dropout) and Q4 (ResNet Gradient Flow)
    p3 = draw_ruled_page(page_num=3, total_pages=3, student_name="Elena Rostova", student_roll="CS-460-019")
    d3 = ImageDraw.Draw(p3)
    lines_p3 = [
        ("Q3 (a) BatchNorm vs LayerNorm:", True),
        ("BatchNorm computes mean/variance across batch dimension N for each feature channel.", False),
        ("It fails when batch size is small (N < 16) and requires running population statistics during inference.", False),
        ("LayerNorm computes mean/variance across all feature channels for each sample independently.", False),
        ("It has zero dependence on batch size and works seamlessly for variable-length sequential Transformer models.", False),
        ("Q3 (b) Inverted Dropout Expectation Derivation:", True),
        ("Inverted Dropout scales activations during training: a_train = (mask * a) / (1 - p), where mask ~ Bernoulli(1 - p).", False),
        ("Expectation during training: E[a_train] = E[(mask * a)/(1 - p)] = ((1 - p)*a)/(1 - p) = a.", False),
        ("Since training expectation equals unmasked activation a, NO scaling is required at test time (a_test = a)!", False),
        ("", False),
        ("Q4 (a) ResNet Gradient Flow Derivation & Vanishing Gradient Prevention:", True),
        ("Residual formulation: x_{l+1} = x_l + F(x_l). Telescoping to layer L: x_L = x_l + sum_{i=l}^{L-1} F(x_i).", False),
        ("Gradient with respect to x_l: dE/dx_l = (dE/dx_L) * (dx_L/dx_l) = (dE/dx_L) * [ I + d/dx_l sum_{i=l}^{L-1} F(x_i) ].", False),
        ("The additive identity term I guarantees that even if the weight Jacobian d/dx_l sum F vanishes to 0,", False),
        ("the gradient dE/dx_l retains the direct signal (dE/dx_L) * I, preventing vanishing gradients in 100+ layer networks.", False),
        ("Q4 (b) Pre-Activation ResNets: Moves BN and ReLU inside residual branch F(x), keeping the skip path", False),
        ("purely linear: x_{l+1} = x_l + F(ReLU(BN(x_l))), which unlocks seamless gradient propagation.", False)
    ]
    y = 125
    for text, is_b in lines_p3:
        if not text:
            y += 18
            continue
        d3.text((155 + random.randint(-1, 1), y), text, fill=ink, font=font_bold if is_b else font_main)
        y += 38

    pdf_out = ASS2_DIR / "student_1_elena_rostova.pdf"
    p1.save(str(pdf_out), "PDF", save_all=True, append_images=[p2, p3], resolution=120.0)
    print(f"Generated Student 1 PDF: {pdf_out}")

# ---------------------------------------------------------------------------
# 5. Student 2: Kavya Patel (Score: ~74%, Authentic College Handwriting, Ballpoint Pen)
# ---------------------------------------------------------------------------
def generate_student_kavya():
    font_main = get_font(20, "C:/Windows/Fonts/Inkfree.ttf")
    font_bold = get_font(21, "C:/Windows/Fonts/Inkfree.ttf")
    ink = (22, 28, 70)

    # Page 1
    p1 = draw_ruled_page(page_num=1, total_pages=3, student_name="Kavya Patel", student_roll="CS-460-044")
    d1 = ImageDraw.Draw(p1)
    lines_p1 = [
        ("Q1 (a) Adam Optimizer and Bias Terms:", True),
        ("Adam keeps running averages of gradients m_t and squared gradients v_t.", False),
        ("Update equations:", False),
        ("  m_t = beta1 * m_{t-1} + (1 - beta1) * g_t", False),
        ("  v_t = beta2 * v_{t-1} + (1 - beta2) * g_t^2", False),
        ("Since m_0 is initialized to 0, m_t starts biased toward 0 in early iterations.", False),
        ("Bias correction divides by (1 - beta1^t) to correct this zero-bias.", False),
        ("Unbiased estimators: m_hat = m_t / (1 - beta1^t) and v_hat = v_t / (1 - beta2^t).", False),
        ("Parameter update: theta_{t+1} = theta_t - alpha * m_hat / (sqrt(v_hat) + eps).", False),
        ("", False),
        ("Q1 (b) Momentum vs Adam in Ravines:", True),
        ("In ravines, loss is steep in one direction and flat along the other.", False),
        ("SGD oscillates back and forth across walls without moving forward.", False),
        ("NAG calculates gradient at look-ahead position to slow down before overshooting.", False),
        ("Adam adjusts the step size for each coordinate using sqrt(v_t), which scales down", False),
        ("updates along steep dimensions and moves faster along gentle slopes.", False)
    ]
    y = 135
    for text, is_b in lines_p1:
        if not text:
            y += 20
            continue
        d1.text((150 + random.randint(-2, 2), y + random.randint(-1, 1)), text, fill=ink, font=font_bold if is_b else font_main)
        y += 44

    # Page 2
    p2 = draw_ruled_page(page_num=2, total_pages=3, student_name="Kavya Patel", student_roll="CS-460-044")
    d2 = ImageDraw.Draw(p2)
    lines_p2 = [
        ("Q2 (a) Transformer Scaled Dot Product Attention:", True),
        ("Attention(Q, K, V) = softmax(Q * K^T / sqrt(d_k)) * V.", False),
        ("Why scale by 1 / sqrt(d_k)?", True),
        ("When dimension d_k is large, the dot product between Q and K becomes very large.", False),
        ("This is because the sum of d_k terms adds up to variance proportional to d_k.", False),
        ("Large dot products push softmax inputs into saturated regions where gradients become tiny.", False),
        ("Dividing by sqrt(d_k) normalizes the variance back to 1, preventing vanishing gradients.", False),
        ("", False),
        ("Q2 (b) Multi-Head Attention and Complexity:", True),
        ("Instead of 1 attention calculation, Multi-Head attention projects Q, K, V into h different heads.", False),
        ("Each head attends to different features or positions in the text.", False),
        ("Complexity: Self-attention is O(n^2 * d) while RNN is O(n * d^2).", False),
        ("Self-attention allows parallel computing because all words are processed at once.", False)
    ]
    y = 135
    for text, is_b in lines_p2:
        if not text:
            y += 20
            continue
        d2.text((150 + random.randint(-2, 2), y + random.randint(-1, 1)), text, fill=ink, font=font_bold if is_b else font_main)
        y += 44

    # Page 3
    p3 = draw_ruled_page(page_num=3, total_pages=3, student_name="Kavya Patel", student_roll="CS-460-044")
    d3 = ImageDraw.Draw(p3)
    lines_p3 = [
        ("Q3 (a) Normalization Techniques:", True),
        ("BatchNorm normalizes across batch items. Requires large batch sizes and running stats.", False),
        ("LayerNorm normalizes across feature dimension per individual sample.", False),
        ("LayerNorm works well for NLP and Transformers because sequence lengths vary.", False),
        ("Q3 (b) Inverted Dropout:", True),
        ("Inverted dropout divides activations by (1 - p) during training: a = a / (1 - p).", False),
        ("This preserves the expected value during training, so at test time no scaling is needed.", False),
        ("", False),
        ("Q4 (a) ResNet Skip Connections & Gradient Flow:", True),
        ("ResNet layer equation: x_{l+1} = x_l + F(x_l).", False),
        ("Gradient: dE/dx_l = dE/dx_L * (I + d/dx_l sum F(x_i)).", False),
        ("The identity matrix I ensures that gradient flows straight back without decaying.", False),
        ("Even if F(x) weights produce small gradients, the I term keeps gradient alive.", False),
        ("Q4 (b) Pre-Activation puts BN and ReLU before the weight layer instead of after addition.", False)
    ]
    y = 135
    for text, is_b in lines_p3:
        if not text:
            y += 20
            continue
        d3.text((150 + random.randint(-2, 2), y + random.randint(-1, 1)), text, fill=ink, font=font_bold if is_b else font_main)
        y += 44

    pdf_out = ASS2_DIR / "student_2_kavya_patel.pdf"
    p1.save(str(pdf_out), "PDF", save_all=True, append_images=[p2, p3], resolution=120.0)
    print(f"Generated Student 2 PDF: {pdf_out}")

# ---------------------------------------------------------------------------
# 6. Student 3: Jordan Hayes (Score: ~44%, Slanted/Messy, Flagged for Manual Review)
# ---------------------------------------------------------------------------
def generate_student_jordan():
    font_main = get_font(19, "C:/Windows/Fonts/segoesc.ttf")
    font_bold = get_font(21, "C:/Windows/Fonts/segoescb.ttf")
    ink = (35, 45, 95)

    # Page 1
    p1 = draw_ruled_page(page_num=1, total_pages=3, student_name="Jordan Hayes", student_roll="CS-460-088")
    d1 = ImageDraw.Draw(p1)
    lines_p1 = [
        ("Q1:", True),
        ("Adam has momentum terms beta1 and beta2.", False),
        ("First moment tracks gradients and second moment tracks variance.", False),
        ("Bias correction divides by beta1 to fix initial zero values.", False),
        ("SGD bounces around in ravines. Nesterov momentum helps prevent bouncing.", False),
        ("Adam changes learning rates automatically based on step size.", False)
    ]
    y = 145
    for text, is_b in lines_p1:
        if not text:
            y += 22
            continue
        d1.text((150 + random.randint(-4, 4), y + random.randint(-2, 2)), text, fill=ink, font=font_bold if is_b else font_main)
        y += 50
    p1 = p1.rotate(0.8, resample=Image.Resampling.BICUBIC, expand=False, fillcolor=(250, 248, 244))

    # Page 2
    p2 = draw_ruled_page(page_num=2, total_pages=3, student_name="Jordan Hayes", student_roll="CS-460-088")
    d2 = ImageDraw.Draw(p2)
    lines_p2 = [
        ("Q2:", True),
        ("Attention = softmax(Q * K / d_k) * V.", False),
        ("Scaling by d_k makes numbers smaller so softmax does not explode.", False),
        ("Multihead attention splits vectors into multiple heads.", False),
        ("Complexity of attention is O(n * d). RNN complexity is O(n^2).", False) # Inverted complexity!
    ]
    y = 145
    for text, is_b in lines_p2:
        if not text:
            y += 22
            continue
        d2.text((150 + random.randint(-4, 4), y + random.randint(-2, 2)), text, fill=ink, font=font_bold if is_b else font_main)
        if "Attention = softmax" in text:
            d2.line([(150, y + 16), (480, y + 16)], fill=(130, 25, 25), width=2)
        y += 50

    # Page 3
    p3 = draw_ruled_page(page_num=3, total_pages=3, student_name="Jordan Hayes", student_roll="CS-460-088")
    d3 = ImageDraw.Draw(p3)
    lines_p3 = [
        ("Q3:", True),
        ("Batch norm normalizes across samples. Layer norm normalizes layers.", False),
        ("Dropout drops nodes with probability p.", False),
        ("Inverted dropout multiplies by (1 - p).", False), # Inverted math!
        ("", False),
        ("Q4:", True),
        ("ResNet has shortcut connections: x + F(x).", False),
        ("Gradients can travel through shortcuts without shrinking.", False),
        ("Preactivation changes block ordering.", False)
    ]
    y = 145
    for text, is_b in lines_p3:
        if not text:
            y += 22
            continue
        d3.text((150 + random.randint(-4, 4), y + random.randint(-2, 2)), text, fill=ink, font=font_bold if is_b else font_main)
        y += 50
    p3 = p3.rotate(-0.7, resample=Image.Resampling.BICUBIC, expand=False, fillcolor=(250, 248, 244))

    pdf_out = ASS2_DIR / "student_3_jordan_hayes.pdf"
    p1.save(str(pdf_out), "PDF", save_all=True, append_images=[p2, p3], resolution=120.0)
    print(f"Generated Student 3 PDF: {pdf_out}")

# ---------------------------------------------------------------------------
# 7. Write Master Solution JSON and TXT in demo_data/ass_2
# ---------------------------------------------------------------------------
def write_master_text_and_json():
    json_path = ASS2_DIR / "master_solution.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(MASTER_DATA, f, indent=2)
    print(f"Generated Master Solution JSON: {json_path}")

    txt_path = ASS2_DIR / "master_solution.txt"
    lines = [
        f"Title: {MASTER_DATA['title']}",
        f"Subject: {MASTER_DATA['subject']}",
        f"Total Marks: {MASTER_DATA['total_marks']}",
        ""
    ]
    for q in MASTER_DATA["questions"]:
        lines.append(f"{q['question_id']}: {q['question_text']}")
        lines.append(f"Marks: {q['max_marks']}")
        lines.append(f"Answer: {q['model_answer']}")
        lines.append(f"Keys: {', '.join(q['key_concepts'])}")
        lines.append("")

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Generated Master Solution TXT: {txt_path}")

if __name__ == "__main__":
    generate_master_pdf()
    write_master_text_and_json()
    generate_student_elena()
    generate_student_kavya()
    generate_student_jordan()
    print("\n[+] demo_data/ass_2 dataset successfully generated with multi-page handwritten PDFs and master solution files!")

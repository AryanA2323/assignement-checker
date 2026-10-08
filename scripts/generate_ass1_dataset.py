import os
import random
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

BASE_DIR = Path(__file__).resolve().parent.parent
ASS1_DIR = BASE_DIR / "ass_1"
ASS1_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# 1. Master Solution JSON & Text Data
# ---------------------------------------------------------------------------
MASTER_DATA = {
    "title": "CS 545: Advanced Distributed Systems — Assignment 1: Consensus, Concurrency & Fault Tolerance",
    "subject": "Computer Science & Distributed Systems",
    "total_marks": 50.0,
    "instructions": "Evaluate based on technical accuracy, mathematical rigor, intermediate steps, and trade-off analysis. Award partial credit for correct reasoning even if final conclusions contain minor omissions.",
    "questions": [
        {
            "question_id": "Q1",
            "question_text": "(a) In the Raft consensus algorithm, state the Log Matching Property and explain how leader election and commit safety rules guarantee that an uncommitted entry from a previous term is never committed directly by counting replicas. (b) Compare steady-state message rounds and leader failure recovery complexity between Multi-Paxos and Raft.",
            "max_marks": 12.0,
            "model_answer": "(a) Raft Log Matching Property: If two logs contain an entry with the same index and term, then they store the same command, and their logs are identical in all entries up through the given index. To prevent committing an entry from an older term, Raft specifies that a leader cannot commit a log entry from an older term simply by counting replicas; it must commit an entry from its CURRENT term by storing it on a majority of servers, which indirectly commits older entries by the Log Matching Property. This rule prevents scenarios where a partitioned former leader overwrites a replicated older entry after network re-convergence. (b) Multi-Paxos vs Raft: In steady state, both Multi-Paxos and Raft require 1 RTT (round-trip time) for log replication once a leader is established. However, during leader failure recovery, Raft simplifies protocol complexity: Raft guarantees that the elected leader already possesses all committed entries (enforced during voting by comparing candidate log term and length), requiring no catch-up phase before accepting writes. In contrast, Multi-Paxos leaders must execute Phase 1 (Prepare/Promise) across all uncommitted slots after election to discover potential values proposed by previous leaders, resulting in significantly higher protocol and recovery complexity.",
            "key_concepts": [
                "Log Matching Property definition (same index and term implies identical history)",
                "Leader cannot commit older term entry merely by replica counting; must commit current term entry",
                "Steady-state replication requires 1 RTT for both Multi-Paxos and Raft",
                "Raft leader election invariant: leader already has all committed entries (no catch-up needed)",
                "Multi-Paxos requires Phase 1 slot discovery across log slots after leader failure"
            ],
            "grading_rubric": {
                "full_marks": "Accurate statement of Log Matching Property, clear explanation of current-term commit rule, and rigorous comparison of leader election recovery complexity.",
                "partial_marks": "Explains Raft leader election but omits the current-term commit safety rule or provides superficial Paxos comparison.",
                "minimal_marks": "High-level summary without state invariants."
            }
        },
        {
            "question_id": "Q2",
            "question_text": "(a) Contrast Strict 2-Phase Locking (Strict 2PL) and Rigorous 2PL. How does Strict 2PL guarantee conflict serializability and avoid cascading aborts? Explain how deadlocks are detected via the Wait-For Graph (WFG). (b) Describe the Write Skew anomaly under Snapshot Isolation (SI) using a formal execution trace (e.g., the On-Call Doctor problem). How does Serializable Snapshot Isolation (SSI) detect and prevent it?",
            "max_marks": 13.0,
            "model_answer": "(a) In Strict 2PL, all exclusive (write) locks acquired by a transaction must be held until the transaction terminates (commit or abort), whereas shared (read) locks may be released before completion. In Rigorous 2PL, ALL locks (both shared and exclusive) are held until transaction completion. Strict 2PL guarantees serializability because transactions reach a lock point before releasing any write lock, preventing conflicting cycles in the precedence graph. It avoids cascading aborts because no other transaction can read uncommitted dirty data written by an uncommitted transaction. Deadlock Detection: The system maintains a directed Wait-For Graph WFG = (V, E) where vertices V are active transactions and a directed edge T_i -> T_j exists if T_i is waiting for a lock held by T_j. A deadlock exists if and only if the WFG contains a directed cycle (detected periodically using Tarjan's or DFS cycle detection algorithms); the deadlock is broken by aborting a victim transaction. (b) Write Skew under Snapshot Isolation (SI): Consider an invariant: Active Doctors >= 1. Initial state: Doctors D_1=Active, D_2=Active. Transaction T_1 checks active doctors (count=2 >= 1) and sets D_1=Inactive. Concurrently, T_2 checks active doctors on its snapshot (count=2 >= 1) and sets D_2=Inactive. Under SI, since T_1 writes to D_1 and T_2 writes to D_2, their write sets are disjoint, so neither transaction violates the first-committer-wins rule. Both commit, leaving Active Doctors = 0, violating the integrity constraint. Serializable Snapshot Isolation (SSI) detects write skew by tracking rw-antidependency conflicts (where a transaction reads a version that is later overwritten by a concurrent transaction, denoted T_read -rw-> T_write). SSI aborts a transaction if it detects two consecutive rw-antidependencies (T_1 -rw-> T_2 -rw-> T_3) forming a dangerous structure.",
            "key_concepts": [
                "Strict 2PL holds write locks until commit; Rigorous 2PL holds all locks until commit",
                "Strict 2PL eliminates dirty reads, preventing cascading aborts",
                "Wait-For Graph (WFG) cycle detection via DFS/Tarjan to resolve deadlocks",
                "Snapshot Isolation write skew: disjoint write sets allow concurrent commits that violate multi-record constraint",
                "Doctor on-call formal trace showing active doctors dropping to 0",
                "Serializable Snapshot Isolation (SSI) tracks rw-antidependency edges and aborts dangerous structures"
            ],
            "grading_rubric": {
                "full_marks": "Clear distinction of lock release rules, WFG cycle detection, complete write-skew trace with disjoint write sets, and SSI rw-antidependency detection.",
                "partial_marks": "Correct 2PL definitions but vague write-skew trace, or missing SSI explanation.",
                "minimal_marks": "Confuses 2PL with 2-Phase Commit (2PC) or gives intuitive description without formal mechanics."
            }
        },
        {
            "question_id": "Q3",
            "question_text": "(a) Explain Consistent Hashing with Virtual Nodes. If a cluster has N physical nodes and each node is assigned V virtual nodes on a 32-bit hash ring, derive the expected key migration fraction when 1 physical node is added. (b) In Dynamo-style leaderless stores, state the Quorum condition (R, W, N) required to guarantee strong consistency. Explain how Vector Clocks resolve concurrent updates and describe the hazard of Last-Write-Wins (LWW).",
            "max_marks": 12.0,
            "model_answer": "(a) Consistent Hashing maps both keys and node identifiers to positions on a circular hash ring (e.g., [0, 2^32 - 1]). A key is assigned to the first node whose position is >= hash(key). In a basic ring with N nodes, non-uniform hash distribution leads to severe partition imbalance. Virtual Nodes solve this by assigning V distinct points on the ring per physical node. The variance of load across nodes is bounded by O(1/V). When 1 new physical node is added to an existing cluster of N nodes, it claims a fraction 1/(N + 1) of the ring from existing nodes. Therefore, the expected fraction of total keys that must be migrated is exactly 1/(N + 1) (or K / (N + 1) keys for a total of K keys), compared to traditional hash mod N where almost all (N / (N + 1)) keys must be re-hashed. (b) In Dynamo-style leaderless replication with replication factor N, strong (read-your-writes) consistency is guaranteed if and only if the read quorum R and write quorum W satisfy: R + W > N. By the Pigeonhole Principle, the set of nodes read from and the set of nodes written to must overlap by at least one node containing the latest write. Vector Clocks track causal dependencies across nodes: a vector clock VC(a) <= VC(b) implies event 'a' causally preceded 'b'. If neither VC(a) <= VC(b) nor VC(b) <= VC(a), concurrent divergent writes are detected, requiring client-side or application-level reconciliation. Last-Write-Wins (LWW) discards vector clocks and uses physical timestamps (e.g. NTP). Due to inevitable clock drift, skew, and leap seconds, LWW can silently overwrite a newer update with an older one, leading to silent data loss.",
            "key_concepts": [
                "Consistent Hashing ring topology and virtual nodes load balancing (O(1/V) variance)",
                "Key migration fraction on node addition is 1 / (N + 1)",
                "Quorum condition R + W > N guarantees overlap by Pigeonhole Principle",
                "Vector Clocks detect concurrent conflicts via partial ordering of node tick vectors",
                "Last-Write-Wins (LWW) hazard: physical clock drift/skew silently drops legitimate writes"
            ],
            "grading_rubric": {
                "full_marks": "Correct key migration derivation (1/(N+1)), quorum condition R+W>N, vector clock causal ordering condition, and LWW clock drift critique.",
                "partial_marks": "States R+W>N but lacks mathematical migration derivation or vector clock conflict explanation.",
                "minimal_marks": "General descriptions lacking formulas and quantitative proofs."
            }
        },
        {
            "question_id": "Q4",
            "question_text": "(a) State the completeness and accuracy properties of Chandra-Toueg Eventually Weak Failure Detectors (<>W). How does <>W circumvent the FLP Impossibility result for asynchronous consensus? (b) In Practical Byzantine Fault Tolerance (PBFT), prove why a system of N nodes can tolerate at most f Byzantine nodes if and only if N >= 3f + 1.",
            "max_marks": 13.0,
            "model_answer": "(a) Chandra-Toueg Failure Detectors: <>W (Eventually Weak) is defined by two properties: (1) Weak Completeness: Eventually every crashed process is permanently suspected by some correct process. (2) Eventual Weak Accuracy: There is a time after which some correct process is never suspected by any correct process. The Fischer-Lynch-Paterson (FLP) impossibility result proves that deterministic consensus is impossible in an asynchronous system with even a single crash failure because it is impossible to distinguish a crashed process from an arbitrarily slow network delay. <>W circumvents FLP by augmenting the asynchronous model with minimal timing/synchrony assumptions: during periods of partial synchrony, the detector achieves accuracy, allowing the rotating coordinator algorithm to reach agreement and terminate safely without violating safety during asynchronous periods. (b) PBFT Node Requirement Proof: In an asynchronous distributed system where up to f nodes can be Byzantine (malicious or arbitrarily faulty): Suppose total nodes is N. If f nodes are Byzantine, they may fail to respond altogether (silent crash). Therefore, an algorithm must make progress after receiving responses from N - f nodes (liveness requirement). However, among those N - f responses, up to f of them might be from Byzantine nodes that sent coordinated malicious lies. Thus, the number of guaranteed non-faulty responses is (N - f) - f = N - 2f. To guarantee that the non-faulty correct responses strictly outnumber the faulty ones (safety/correctness), we require: N - 2f > f, which simplifies directly to N > 3f, meaning N >= 3f + 1. By contrast, crash-stop models only require N >= 2f + 1 because crashed nodes cannot fabricate conflicting votes.",
            "key_concepts": [
                "Weak Completeness (every crashed node eventually suspected by some correct node)",
                "Eventual Weak Accuracy (eventually some correct node is never suspected)",
                "FLP circumvention via partial synchrony and failure detector augmentation",
                "PBFT liveness quorum: must make progress with N - f responses",
                "PBFT safety condition: among N - f responses, at most f can be Byzantine, so N - 2f > f => N >= 3f + 1",
                "Contrast with crash-stop quorum 2f + 1"
            ],
            "grading_rubric": {
                "full_marks": "Formal statement of Weak Completeness and Eventual Weak Accuracy, FLP circumvention mechanism, and rigorous derivation of N >= 3f + 1.",
                "partial_marks": "Explains PBFT 3f+1 intuitively without formal quorum subtraction, or gives vague failure detector properties.",
                "minimal_marks": "States 3f+1 formula without proof or explanation."
            }
        }
    ]
}

# ---------------------------------------------------------------------------
# 2. Generate Master Solution PDF using ReportLab
# ---------------------------------------------------------------------------
def generate_master_pdf():
    pdf_path = ASS1_DIR / "master_solution.pdf"
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
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#334155")
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
    
    # Institution Header
    story.append(Paragraph("PACIFIC INSTITUTE OF TECHNOLOGY — DEPARTMENT OF COMPUTER SCIENCE", meta_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("CS 545: Advanced Distributed Systems & Cloud Infrastructure", title_style))
    story.append(Spacer(1, 2))
    story.append(Paragraph("Assignment 1 Master Solution & Official Grading Rubric | Maximum Marks: 50.0", meta_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#4f46e5"), spaceAfter=12))

    for q in MASTER_DATA["questions"]:
        # Question Header Box
        header_text = f"<b>{q['question_id']} ({q['max_marks']} Marks):</b> {q['question_text']}"
        story.append(Paragraph(header_text, q_title_style))
        story.append(Spacer(1, 3))
        
        # Model Answer
        ans_text = f"<b>Reference Model Solution:</b><br/>{q['model_answer'].replace(chr(10), '<br/>')}"
        story.append(Paragraph(ans_text, model_style))
        story.append(Spacer(1, 4))

        # Key Concepts & Rubrics
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
def draw_ruled_page(width=1400, height=1950, page_num=1, total_pages=3, student_name="Student", student_roll="CS-545-000"):
    """Renders a college ruled notebook page with margin lines and header."""
    img = Image.new("RGB", (width, height), (252, 251, 246))
    draw = ImageDraw.Draw(img)

    margin_top = 110
    line_spacing = 34
    rule_color = (212, 224, 240)

    # Ruled lines
    y = margin_top
    while y < height - 50:
        draw.line([(60, y), (width - 60, y)], fill=rule_color, width=1)
        y += line_spacing

    # Double left red margin
    margin_left = 135
    draw.line([(margin_left, 35), (margin_left, height - 35)], fill=(245, 175, 180), width=2)
    draw.line([(margin_left + 4, 35), (margin_left + 4, height - 35)], fill=(245, 175, 180), width=1)

    # Header separator
    draw.line([(60, margin_top - 20), (width - 60, margin_top - 20)], fill=(225, 160, 165), width=2)

    font_hdr = get_font(20, "C:/Windows/Fonts/segoeprb.ttf")
    # Top running header
    header_text = f"{student_name}  |  Roll: {student_roll}  |  CS 545 Assignment 1"
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
# 4. Generate Student 1: Alex Chen (3-Page PDF, ~92%, Neat Blue Fountain Pen)
# ---------------------------------------------------------------------------
def generate_student_alex():
    font_main = get_font(21, "C:/Windows/Fonts/segoepr.ttf")
    font_bold = get_font(22, "C:/Windows/Fonts/segoeprb.ttf")
    ink = (16, 38, 85)

    # Page 1: Q1 (Raft & Multi-Paxos)
    p1 = draw_ruled_page(page_num=1, total_pages=3, student_name="Alex Chen", student_roll="CS-545-012")
    d1 = ImageDraw.Draw(p1)
    lines_p1 = [
        ("Q1 (a) Raft State Machine Replication & Log Matching:", True),
        ("Log Matching Property: If two logs contain an entry with the identical index and term, then:", False),
        ("  1. They store the same state machine command.", False),
        ("  2. Their logs are completely identical in all preceding entries up to that index.", False),
        ("Commit Safety Rule for Older Terms:", False),
        ("A Raft leader cannot commit an entry from an older term simply by counting replicas.", False),
        ("Instead, the leader must commit an entry from its CURRENT term by replicating it to a majority.", False),
        ("Once an entry from the current term is committed, the Log Matching Property guarantees that all", False),
        ("prior entries from previous terms are committed indirectly. This prevents subtle race conditions", False),
        ("where an old leader rejoins after network partition and overwrites already replicated entries.", False),
        ("", False),
        ("Q1 (b) Multi-Paxos vs Raft Comparison:", True),
        ("Steady-State Message Rounds: Both Multi-Paxos and Raft require exactly 1 RTT once a stable leader", False),
        ("is active (Raft Leader sends AppendEntries RPCs; Multi-Paxos executes Phase 2 Accept/Accepted).", False),
        ("Leader Failure Recovery Complexity: In Raft, leader election ensures that the candidate with the most", False),
        ("up-to-date log (higher last term, longer log) wins the majority vote. Thus, the new leader already", False),
        ("contains all committed entries and needs zero catch-up before serving client write requests.", False),
        ("In Multi-Paxos, any node can become leader, so it must run Phase 1 (Prepare/Promise) across all slots", False),
        ("to discover uncommitted proposals from previous leaders, leading to significantly higher recovery complexity.", False)
    ]
    y = 125
    for text, is_b in lines_p1:
        if not text:
            y += 18
            continue
        d1.text((155 + random.randint(-1, 1), y), text, fill=ink, font=font_bold if is_b else font_main)
        y += 38

    # Page 2: Q2 (Strict 2PL & MVCC Write Skew)
    p2 = draw_ruled_page(page_num=2, total_pages=3, student_name="Alex Chen", student_roll="CS-545-012")
    d2 = ImageDraw.Draw(p2)
    lines_p2 = [
        ("Q2 (a) Strict 2-Phase Locking vs Rigorous 2PL & WFG Deadlock:", True),
        ("Strict 2PL: All exclusive (write) locks held by transaction T must be retained until commit/abort.", False),
        ("Shared (read) locks can be released earlier. In Rigorous 2PL, ALL locks (shared + exclusive) are held to end.", False),
        ("Serializability: Strict 2PL guarantees serializability because transactions do not release write locks", False),
        ("before reaching their lock point, precluding cycles in conflict serialization graphs.", False),
        ("Avoiding Cascading Aborts: Since uncommitted write locks are held until commit, other transactions", False),
        ("cannot read dirty data from T. If T aborts, no other active transaction has read its intermediate writes.", False),
        ("Wait-For Graph (WFG): Directed graph G = (V, E) where vertices are transactions. Edge Ti -> Tj means", False),
        ("Ti is blocked waiting for a lock held by Tj. A cycle in WFG indicates a Deadlock (detected via DFS).", False),
        ("", False),
        ("Q2 (b) Write Skew Anomaly under Snapshot Isolation (SI):", True),
        ("Scenario: Hospital constraint requires Active Doctors >= 1. Initial State: D1 = Active, D2 = Active.", False),
        ("  Time t1: Transaction T1 reads snapshot (D1=Active, D2=Active). Active count = 2.", False),
        ("  Time t2: Transaction T2 reads snapshot (D1=Active, D2=Active). Active count = 2.", False),
        ("  Time t3: T1 sets D1 = Inactive (since count >= 1 is satisfied) and commits.", False),
        ("  Time t4: T2 sets D2 = Inactive (since count >= 1 was satisfied on its snapshot) and commits.", False),
        ("Since T1 writes to D1 and T2 writes to D2, their write sets are disjoint! SI first-committer-wins rule", False),
        ("does not trigger an abort. Both commit, leaving Active Doctors = 0 (Violation of invariant!).", False),
        ("Serializable Snapshot Isolation (SSI) Solution: Tracks rw-antidependencies (T1 read D2 before T2 wrote it).", False),
        ("SSI aborts T2 upon detecting consecutive rw-antidependency edges forming a dangerous structure.", False)
    ]
    y = 125
    for text, is_b in lines_p2:
        if not text:
            y += 18
            continue
        d2.text((155 + random.randint(-1, 1), y), text, fill=ink, font=font_bold if is_b else font_main)
        y += 38

    # Page 3: Q3 (Consistent Hashing & Dynamo) and Q4 (Failure Detectors & PBFT)
    p3 = draw_ruled_page(page_num=3, total_pages=3, student_name="Alex Chen", student_roll="CS-545-012")
    d3 = ImageDraw.Draw(p3)
    lines_p3 = [
        ("Q3 (a) Consistent Hashing with Virtual Nodes & Key Migration:", True),
        ("Keys and nodes are mapped to a 32-bit ring [0, 2^32 - 1]. Each physical node has V virtual nodes.", False),
        ("Virtual nodes bound partition variance to O(1/V). When adding 1 node to an N-node cluster,", False),
        ("the new node takes a fraction 1/(N + 1) of the hash ring from existing nodes. Therefore, exactly", False),
        ("a fraction 1/(N + 1) of total keys migrate (i.e. K / (N + 1) keys), avoiding O(K) rehashing.", False),
        ("Q3 (b) Quorums, Vector Clocks & Last-Write-Wins (LWW):", True),
        ("Quorum Condition: Strong consistency requires R + W > N. By Pigeonhole Principle, read set R and", False),
        ("write set W overlap in at least (R + W - N) nodes, guaranteeing at least one node has latest version.", False),
        ("Vector clocks track causal order: VC(A) <= VC(B). Incomparable vectors indicate concurrent conflict.", False),
        ("LWW Hazard: Relies on physical wall clocks. NTP clock skew/drift silently overwrites newer updates.", False),
        ("", False),
        ("Q4 (a) Failure Detectors & FLP Impossibility:", True),
        ("Chandra-Toueg <>W Failure Detector: 1) Weak Completeness: every crashed node is eventually suspected.", False),
        ("2) Eventual Weak Accuracy: eventually some correct process is never suspected by any correct node.", False),
        ("FLP Impossibility states consensus cannot terminate deterministically in asynchronous systems with", False),
        ("even 1 crash failure. <>W circumvents FLP by adding partial synchrony during which consensus terminates.", False),
        ("Q4 (b) PBFT 3f + 1 Derivation:", True),
        ("In an asynchronous system with f Byzantine nodes: To guarantee liveness, the system must make progress", False),
        ("after N - f responses. Among these N - f responses, up to f could be from Byzantine nodes lying.", False),
        ("Number of guaranteed correct responses is (N - f) - f = N - 2f. To ensure correct nodes outvote Byzantine:", False),
        ("N - 2f > f  ===>  N > 3f  ===>  N >= 3f + 1 nodes required. (Contrasts with crash-only N >= 2f + 1).", False)
    ]
    y = 125
    for text, is_b in lines_p3:
        if not text:
            y += 18
            continue
        d3.text((155 + random.randint(-1, 1), y), text, fill=ink, font=font_bold if is_b else font_main)
        y += 38

    # Save as 3-Page PDF
    pdf_out = ASS1_DIR / "student_1_alex_chen.pdf"
    p1.save(str(pdf_out), "PDF", save_all=True, append_images=[p2, p3], resolution=120.0)
    print(f"Generated Student 1 PDF: {pdf_out}")

# ---------------------------------------------------------------------------
# 5. Generate Student 2: Priya Sharma (3-Page PDF, ~68%, Black Ballpoint, Mistakes in 2PL & Failure Detectors)
# ---------------------------------------------------------------------------
def generate_student_priya():
    font_main = get_font(21, "C:/Windows/Fonts/Inkfree.ttf")
    font_bold = get_font(22, "C:/Windows/Fonts/Inkfree.ttf")
    ink = (20, 20, 25)

    # Page 1
    p1 = draw_ruled_page(page_num=1, total_pages=3, student_name="Priya Sharma", student_roll="CS-545-045")
    d1 = ImageDraw.Draw(p1)
    lines_p1 = [
        ("Answer 1 (Raft & Multi-Paxos):", True),
        ("Log Matching Property means if two logs have an entry with same term and index, they have the same", False),
        ("command and identical previous entries.", False),
        ("In Raft, a leader cannot commit older entries directly by counting server responses.", False),
        ("The leader has to commit an entry from its own current term, which then commits older entries.", False),
        ("This prevents a partitioned leader from overwriting entries after reconnecting.", False),
        ("Comparison: In steady state, both Raft and Multi-Paxos take 1 RTT for log replication.", False),
        ("Leader failure: Raft election chooses a leader that already has all committed logs by checking", False),
        ("log length and term during voting. In Multi-Paxos, any node can become leader and it has to run Phase 1", False),
        ("to discover what past leaders proposed, which is much more complicated.", False)
    ]
    y = 135
    for text, is_b in lines_p1:
        if not text:
            y += 20
            continue
        d1.text((155 + random.randint(-2, 2), y), text, fill=ink, font=font_bold if is_b else font_main)
        y += 44

    # Page 2: Makes mistake on 2PL (confuses with 2PC!)
    p2 = draw_ruled_page(page_num=2, total_pages=3, student_name="Priya Sharma", student_roll="CS-545-045")
    d2 = ImageDraw.Draw(p2)
    lines_p2 = [
        ("Answer 2 (Concurrency & Snapshot Isolation):", True),
        ("Strict 2PL: Transactions have two phases. In Phase 1 prepare message is sent, in Phase 2 commit message.", False),
        ("[Note: Confused 2PL locking with 2-Phase Commit 2PC protocol!]", False),
        ("Rigorous 2PL holds locks until the end of the transaction.", False),
        ("Wait-For Graph is used to find deadlocks by looking for cycles between waiting transactions.", False),
        ("Write Skew in Snapshot Isolation: Suppose we need active doctors >= 1. Two doctors D1 and D2 are active.", False),
        ("Doctor 1 logs in and sees 2 doctors, so D1 goes off duty and commits.", False),
        ("Doctor 2 logs in concurrently, also sees 2 doctors active on snapshot, so D2 goes off duty.", False),
        ("Because D1 updated D1 and D2 updated D2, their write sets are different so both transactions succeed.", False),
        ("This leaves 0 doctors active, which breaks the consistency rule.", False),
        ("SSI prevents write skew by tracking read-write anti-dependencies and aborting one transaction.", False)
    ]
    y = 135
    for text, is_b in lines_p2:
        if not text:
            y += 20
            continue
        d2.text((155 + random.randint(-2, 2), y), text, fill=ink, font=font_bold if is_b else font_main)
        y += 44

    # Page 3: Q3 and Q4 (forgets weak completeness)
    p3 = draw_ruled_page(page_num=3, total_pages=3, student_name="Priya Sharma", student_roll="CS-545-045")
    d3 = ImageDraw.Draw(p3)
    lines_p3 = [
        ("Answer 3 (Consistent Hashing & Dynamo):", True),
        ("Consistent hashing puts keys on a circle. Virtual nodes give each physical server multiple tokens.", False),
        ("This makes key distribution balanced. When 1 node is added to N nodes, only 1/(N + 1) keys need to move.", False),
        ("Quorum condition: R + W > N. This ensures read and write sets overlap on at least 1 server.", False),
        ("Vector clocks track version numbers for each node to detect conflicts. LWW uses timestamps but clock drift", False),
        ("causes data loss when writes are dropped.", False),
        ("", False),
        ("Answer 4 (Failure Detectors & PBFT):", True),
        ("Failure detector <>W has accuracy property where some correct node is not suspected.", False),
        ("FLP impossibility says consensus cannot be solved in asynchronous systems with failures.", False),
        ("<>W helps solve it by adding timing assumptions.", False),
        ("PBFT requires N >= 3f + 1 because Byzantine nodes can send malicious messages and crash.", False),
        ("If f nodes crash, we need N - f to answer. If f nodes lie, we need N - 2f > f, so N >= 3f + 1.", False)
    ]
    y = 135
    for text, is_b in lines_p3:
        if not text:
            y += 20
            continue
        d3.text((155 + random.randint(-2, 2), y), text, fill=ink, font=font_bold if is_b else font_main)
        y += 44

    pdf_out = ASS1_DIR / "student_2_priya_sharma.pdf"
    p1.save(str(pdf_out), "PDF", save_all=True, append_images=[p2, p3], resolution=120.0)
    print(f"Generated Student 2 PDF: {pdf_out}")

# ---------------------------------------------------------------------------
# 6. Generate Student 3: Marcus Vance (3-Page PDF, ~42%, Messy Script, Inverted formulas, Flagged)
# ---------------------------------------------------------------------------
def generate_student_marcus():
    font_main = get_font(19, "C:/Windows/Fonts/segoesc.ttf")
    font_bold = get_font(21, "C:/Windows/Fonts/segoescb.ttf")
    ink = (35, 45, 95)

    # Page 1
    p1 = draw_ruled_page(page_num=1, total_pages=3, student_name="Marcus Vance", student_roll="CS-545-089")
    d1 = ImageDraw.Draw(p1)
    lines_p1 = [
        ("Q1:", True),
        ("Raft log matching says logs have same terms.", False),
        ("Leaders replicate entries to majority nodes.", False),
        ("Older entries cannot be committed easily.", False),
        ("Multi Paxos has phases and takes 2 RTTs. Raft takes 1 RTT.", False),
        ("Raft leader election is simpler because candidate has up to date log.", False)
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
    p2 = draw_ruled_page(page_num=2, total_pages=3, student_name="Marcus Vance", student_roll="CS-545-089")
    d2 = ImageDraw.Draw(p2)
    lines_p2 = [
        ("Q2:", True),
        ("Strict 2PL has locks. Growing phase and shrinking phase.", False),
        ("Rigorous 2PL holds locks.", False),
        ("Wait for graph shows transaction deadlocks.", False),
        ("Write skew happens when two doctors log out at the same time.", False),
        ("Both see 2 doctors active, so both log out, leaving 0 doctors.", False),
        ("Snapshot isolation allows this because write sets don't overlap.", False)
    ]
    y = 145
    for text, is_b in lines_p2:
        if not text:
            y += 22
            continue
        d2.text((150 + random.randint(-4, 4), y + random.randint(-2, 2)), text, fill=ink, font=font_bold if is_b else font_main)
        if "Growing phase and shrinking phase" in text:
            d2.line([(150, y + 16), (480, y + 16)], fill=(130, 25, 25), width=2)
        y += 50

    # Page 3: Inverted formulas, skips PBFT derivation
    p3 = draw_ruled_page(page_num=3, total_pages=3, student_name="Marcus Vance", student_roll="CS-545-089")
    d3 = ImageDraw.Draw(p3)
    lines_p3 = [
        ("Q3:", True),
        ("Consistent hashing maps keys to a circle.", False),
        ("Virtual nodes improve hashing. Keys move when nodes join.", False),
        ("Quorum condition: R + W <= N.", False),  # Inverted!
        ("Vector clocks resolve updates. LWW uses clock timestamps.", False),
        ("", False),
        ("Q4:", True),
        ("Failure detectors check if node is dead.", False),
        ("FLP theorem says consensus is impossible with delays.", False),
        ("PBFT requires 3f + 1 nodes to handle Byzantine faults.", False)
    ]
    y = 145
    for text, is_b in lines_p3:
        if not text:
            y += 22
            continue
        d3.text((150 + random.randint(-4, 4), y + random.randint(-2, 2)), text, fill=ink, font=font_bold if is_b else font_main)
        y += 50
    p3 = p3.rotate(-0.7, resample=Image.Resampling.BICUBIC, expand=False, fillcolor=(250, 248, 244))

    pdf_out = ASS1_DIR / "student_3_marcus_vance.pdf"
    p1.save(str(pdf_out), "PDF", save_all=True, append_images=[p2, p3], resolution=120.0)
    print(f"Generated Student 3 PDF: {pdf_out}")

# ---------------------------------------------------------------------------
# 7. Write Master Solution JSON and TXT in ass_1
# ---------------------------------------------------------------------------
def write_master_text_and_json():
    json_path = ASS1_DIR / "master_solution.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(MASTER_DATA, f, indent=2)
    print(f"Generated Master Solution JSON: {json_path}")

    txt_path = ASS1_DIR / "master_solution.txt"
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
    generate_student_alex()
    generate_student_priya()
    generate_student_marcus()
    print("\n[+] ass_1 college dataset successfully generated with multi-page handwritten PDFs and master solution PDF!")

"""
PowerPoint Presentation Generator for CityFlow Single-Target Multi-Camera Vehicle Tracking.
Generates a clean 16:9 academic presentation for IIT Guwahati (EE5340 - Video Analytics).
"""

import os
import sys
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

ROOT_DIR = Path(__file__).resolve().parent.parent

# Color Palette
NAVY = RGBColor(15, 23, 42)        # #0F172A
SLATE = RGBColor(30, 41, 59)       # #1E293B
BLUE = RGBColor(2, 132, 199)       # #0284C7
EMERALD = RGBColor(16, 185, 129)   # #10B981
EMERALD_DARK = RGBColor(6, 95, 70) # #065F46
AMBER = RGBColor(245, 158, 11)     # #F59E0B
RED = RGBColor(239, 68, 68)        # #EF4444
LIGHT_BG = RGBColor(248, 250, 252) # #F8FAFC
CARD_BG = RGBColor(241, 245, 249)  # #F1F5F9
BORDER = RGBColor(203, 213, 225)   # #CBD5E1
TEXT_DARK = RGBColor(15, 23, 42)
TEXT_MUTED = RGBColor(71, 85, 105)
WHITE = RGBColor(255, 255, 255)


def set_slide_bg(slide, color: RGBColor):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_header(slide, title_text: str, subtitle_text: str, slide_num: int):
    # Top accent bar
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.08))
    bar.fill.solid()
    bar.fill.fore_color.rgb = BLUE
    bar.line.fill.background()

    # Title
    tb = slide.shapes.add_textbox(Inches(0.55), Inches(0.22), Inches(11.5), Inches(0.55))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.text = title_text
    p.font.name = "Calibri"
    p.font.size = Pt(24)
    p.font.bold = True
    p.font.color.rgb = NAVY

    # Subtitle
    if subtitle_text:
        p2 = tf.add_paragraph()
        p2.text = subtitle_text
        p2.font.name = "Calibri"
        p2.font.size = Pt(12)
        p2.font.color.rgb = TEXT_MUTED

    # Divider line
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.55), Inches(0.92), Inches(12.23), Inches(0.02))
    line.fill.solid()
    line.fill.fore_color.rgb = BORDER
    line.line.fill.background()

    # Footer
    ft = slide.shapes.add_textbox(Inches(0.55), Inches(7.12), Inches(12.23), Inches(0.3))
    ft_tf = ft.text_frame
    ft_tf.margin_left = ft_tf.margin_top = ft_tf.margin_right = ft_tf.margin_bottom = 0
    fp = ft_tf.paragraphs[0]
    fp.text = f"EE5340 Video Analytics | IIT Guwahati | Single-Target Multi-Camera Vehicle Tracking                    Slide {slide_num}"
    fp.font.name = "Calibri"
    fp.font.size = Pt(9.5)
    fp.font.color.rgb = TEXT_MUTED


def add_card(slide, left, top, width, height, fill_color=CARD_BG, border_color=BORDER):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
    shape.adjustments[0] = 0.03
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    if border_color:
        shape.line.color.rgb = border_color
        shape.line.width = Pt(1)
    else:
        shape.line.fill.background()
    return shape


def add_bullets(slide, left, top, width, height, title: str, items: list, title_color=BLUE, font_size=13):
    tb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.08)
    tf.margin_top = tf.margin_bottom = Inches(0.05)

    p0 = tf.paragraphs[0]
    p0.text = title
    p0.font.name = "Calibri"
    p0.font.size = Pt(font_size + 2)
    p0.font.bold = True
    p0.font.color.rgb = title_color
    p0.space_after = Pt(6)

    for item in items:
        p = tf.add_paragraph()
        p.text = f"•  {item}"
        p.font.name = "Calibri"
        p.font.size = Pt(font_size)
        p.font.color.rgb = TEXT_DARK
        p.space_after = Pt(5)
    return tb


def style_cell(cell, text: str, font_size=11, bold=False, color=TEXT_DARK, bg_color=None, align=PP_ALIGN.CENTER):
    cell.vertical_anchor = MSO_ANCHOR.MIDDLE
    if bg_color:
        cell.fill.solid()
        cell.fill.fore_color.rgb = bg_color
    tf = cell.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.06)
    tf.margin_top = tf.margin_bottom = Inches(0.04)
    p = tf.paragraphs[0]
    p.text = text
    p.alignment = align
    p.font.name = "Calibri"
    p.font.size = Pt(font_size)
    p.font.bold = bold
    p.font.color.rgb = color


def build_presentation(output_path: str = "outputs/reports/STMCT_Presentation.pptx") -> str:
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]

    # =========================================================================
    # SLIDE 1: TITLE SLIDE
    # =========================================================================
    s1 = prs.slides.add_slide(blank)
    set_slide_bg(s1, NAVY)

    accent = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(0.22), Inches(7.5))
    accent.fill.solid()
    accent.fill.fore_color.rgb = EMERALD
    accent.line.fill.background()

    badge = add_card(s1, 0.8, 0.75, 4.6, 0.42, fill_color=SLATE, border_color=BLUE)
    btf = badge.text_frame
    bp = btf.paragraphs[0]
    bp.text = "EE5340 – VIDEO ANALYTICS  |  IIT GUWAHATI"
    bp.alignment = PP_ALIGN.CENTER
    bp.font.name = "Calibri"
    bp.font.size = Pt(12)
    bp.font.bold = True
    bp.font.color.rgb = RGBColor(56, 189, 248)

    tb1 = s1.shapes.add_textbox(Inches(0.8), Inches(1.45), Inches(11.6), Inches(1.9))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    p = tf1.paragraphs[0]
    p.text = "Single-Target Multi-Camera Vehicle Tracking\nAcross Static Traffic Cameras Using Appearance\nand Spatio-Temporal Association"
    p.font.name = "Calibri"
    p.font.size = Pt(34)
    p.font.bold = True
    p.font.color.rgb = WHITE

    sub = s1.shapes.add_textbox(Inches(0.8), Inches(3.55), Inches(11.4), Inches(0.6))
    stf = sub.text_frame
    stf.word_wrap = True
    sp = stf.paragraphs[0]
    sp.text = "A Reliability-Aware Approach using Deep Re-Identification and Adaptive Spatio-Temporal Fusion"
    sp.font.name = "Calibri"
    sp.font.size = Pt(16)
    sp.font.italic = True
    sp.font.color.rgb = EMERALD

    # Team & Supervisor cards
    add_card(s1, 0.8, 4.55, 5.7, 2.2, fill_color=SLATE, border_color=RGBColor(51, 65, 85))
    tb_team = s1.shapes.add_textbox(Inches(1.0), Inches(4.7), Inches(5.3), Inches(1.9))
    ttf = tb_team.text_frame
    ttf.word_wrap = True
    tp0 = ttf.paragraphs[0]
    tp0.text = "SUBMITTED BY"
    tp0.font.size = Pt(11)
    tp0.font.bold = True
    tp0.font.color.rgb = RGBColor(56, 189, 248)
    tp0.space_after = Pt(6)
    for name, roll in [
        ("Sujit Kumar Munda", "254156015"),
        ("Rohon Alam", "254156013"),
        ("Pranjal Singh Navrang", "264152010"),
    ]:
        tp = ttf.add_paragraph()
        tp.text = f"{name}  (Roll No: {roll})"
        tp.font.size = Pt(14)
        tp.font.color.rgb = WHITE
        tp.space_after = Pt(4)

    add_card(s1, 6.8, 4.55, 5.7, 2.2, fill_color=SLATE, border_color=RGBColor(51, 65, 85))
    tb_sup = s1.shapes.add_textbox(Inches(7.0), Inches(4.7), Inches(5.3), Inches(1.9))
    stf2 = tb_sup.text_frame
    stf2.word_wrap = True
    sp0 = stf2.paragraphs[0]
    sp0.text = "SUPERVISOR & INSTITUTION"
    sp0.font.size = Pt(11)
    sp0.font.bold = True
    sp0.font.color.rgb = RGBColor(56, 189, 248)
    sp0.space_after = Pt(6)
    for line in [
        "Dr. Prithwijit Guha (Associate Professor, Dept. of EEE)",
        "School of Interdisciplinary Studies and Sustainability (SiSAS)",
        "Indian Institute of Technology Guwahati  |  November 2026",
    ]:
        sp_l = stf2.add_paragraph()
        sp_l.text = line
        sp_l.font.size = Pt(13.5)
        sp_l.font.color.rgb = WHITE
        sp_l.space_after = Pt(5)

    # =========================================================================
    # SLIDE 2: PROBLEM STATEMENT & MOTIVATION
    # =========================================================================
    s2 = prs.slides.add_slide(blank)
    set_slide_bg(s2, LIGHT_BG)
    add_header(s2, "1. Problem Statement & Motivation", "Why Single-Target Multi-Camera Tracking (ST-MCT) instead of full MTMCT?", 2)

    add_card(s2, 0.55, 1.15, 5.9, 5.7, fill_color=WHITE)
    add_bullets(
        s2, 0.75, 1.3, 5.5, 5.4,
        "Key Surveillance Challenges",
        [
            "Non-overlapping blind zones: continuity cannot rely on motion alone.",
            "Viewpoint & scale changes: rear vs. front/side views across cameras.",
            "Look-alike distractors: dark SUVs & pickups confuse appearance-only Re-ID.",
            "Template drift: updating local trackers on occluded/edge frames locks onto background.",
            "Compute budget: running detection + deep Re-ID on all vehicles every frame is wasteful.",
            "Goal: Follow ONE selected vehicle (VEHICLE_001) across cameras with zero distractor tracks.",
        ],
        font_size=13.5,
    )

    # Comparison table MTMCT vs ST-MCT
    tbl_shape = s2.shapes.add_table(6, 3, Inches(6.7), Inches(1.15), Inches(6.05), Inches(3.8))
    tbl = tbl_shape.table
    tbl.columns[0].width = Inches(1.35)
    tbl.columns[1].width = Inches(2.25)
    tbl.columns[2].width = Inches(2.45)

    headers = ["Aspect", "MTMCT", "ST-MCT (This Work)"]
    for idx, h in enumerate(headers):
        style_cell(tbl.cell(0, idx), h, font_size=11.5, bold=True, color=WHITE, bg_color=NAVY)

    rows = [
        ("Input", "All detections in all cameras", "One user-selected box (GT / ROI)"),
        ("Output", "Global IDs for every vehicle", "One global ID, or 'not visible'"),
        ("Compute", "Detect + Re-ID every object, every frame", "Local tracker; Re-ID only during search"),
        ("Association", "Global tracklet clustering", "Online search of reachable cameras"),
        ("Failure Mode", "Fragmentation, ID merges", "Wrong reacquisition, missed exit"),
    ]
    for r_idx, row in enumerate(rows, start=1):
        bg = WHITE if r_idx % 2 == 1 else CARD_BG
        style_cell(tbl.cell(r_idx, 0), row[0], font_size=11, bold=True, bg_color=bg, align=PP_ALIGN.LEFT)
        style_cell(tbl.cell(r_idx, 1), row[1], font_size=11, bg_color=bg, align=PP_ALIGN.LEFT)
        style_cell(tbl.cell(r_idx, 2), row[2], font_size=11, bg_color=RGBColor(236, 253, 245), color=EMERALD_DARK, align=PP_ALIGN.LEFT)

    add_card(s2, 6.7, 5.15, 6.05, 1.7, fill_color=RGBColor(239, 246, 255), border_color=BLUE)
    add_bullets(
        s2, 6.85, 5.25, 5.75, 1.5,
        "Core Research Gap Addressed",
        [
            "Fixed fusion weights fail when detection quality or transit delay varies.",
            "Proposed reliability-aware fusion rescales each cue's weight dynamically.",
        ],
        title_color=NAVY, font_size=12.5,
    )

    # =========================================================================
    # SLIDE 3: DATASET & EXPLORATORY ANALYSIS
    # =========================================================================
    s3 = prs.slides.add_slide(blank)
    set_slide_bg(s3, LIGHT_BG)
    add_header(s3, "2. CityFlow Dataset & Exploratory Analysis", "Authentic 1920×1080 @ 30 FPS traffic surveillance footage (Scenario S01)", 3)

    add_card(s3, 0.55, 1.15, 5.5, 5.7, fill_color=WHITE)
    add_bullets(
        s3, 0.72, 1.3, 5.15, 5.4,
        "Dataset & Topology Specifications",
        [
            "Cameras: c001 (intersection entry) & c002 (second view), 121 frames each.",
            "Annotations: 3 identities, 65 MOT boxes; mean size 265 × 221 px.",
            "ID 1 timeline: c001 frames 1–17 -> blind zone (18–34) -> c002 frames 35–50.",
            "Topology priors: c001 -> c002 (p=0.85, μ=15f, σ=4f); reverse (p=0.80, μ=16f).",
            "Calibration: K (f=1600 px), distortion, [R|t], homography H, & binary ROI masks.",
            "Audit finding: Annotated ID 1 is a black SUV in c001 vs. blue pickup in c002.",
        ],
        font_size=12.5,
    )

    # Preview Image c001
    prev_c1 = str(ROOT_DIR / "outputs" / "real_data_preview_c001.jpg")
    if os.path.exists(prev_c1):
        s3.shapes.add_picture(prev_c1, Inches(6.3), Inches(1.15), width=Inches(6.45))
    cap3 = s3.shapes.add_textbox(Inches(6.3), Inches(4.82), Inches(6.45), Inches(0.3))
    cp3 = cap3.text_frame.paragraphs[0]
    cp3.text = "Camera c001 (Frame 1): Initial target VEHICLE_001 selected at [605, 448, 459, 258]"
    cp3.alignment = PP_ALIGN.CENTER
    cp3.font.size = Pt(10.5)
    cp3.font.italic = True
    cp3.font.color.rgb = TEXT_MUTED

    # Re-ID crops
    crop_paths = [
        (ROOT_DIR / "outputs" / "crops" / "c003_v1_f0.jpg", "c001: Target SUV"),
        (ROOT_DIR / "outputs" / "crops" / "c003_v2_f0.jpg", "c001: Distractor ID 2"),
        (ROOT_DIR / "outputs" / "crops" / "c004_v1_f0.jpg", "c002: SUV (Frame 0)"),
    ]
    cx = 6.3
    for cp, label in crop_paths:
        if cp.exists():
            s3.shapes.add_picture(str(cp), Inches(cx), Inches(5.25), width=Inches(2.0), height=Inches(1.25))
            ctb = s3.shapes.add_textbox(Inches(cx), Inches(6.52), Inches(2.0), Inches(0.3))
            cp_p = ctb.text_frame.paragraphs[0]
            cp_p.text = label
            cp_p.alignment = PP_ALIGN.CENTER
            cp_p.font.size = Pt(10)
            cp_p.font.color.rgb = TEXT_DARK
        cx += 2.22

    # =========================================================================
    # SLIDE 4: SYSTEM ARCHITECTURE
    # =========================================================================
    s4 = prs.slides.add_slide(blank)
    set_slide_bg(s4, LIGHT_BG)
    add_header(s4, "3. System Architecture & Pipeline", "Modular end-to-end ST-MCT pipeline from synchronized video input to web dashboards", 4)

    # Custom flow boxes
    boxes = [
        (0.55, 1.35, 3.6, 1.15, NAVY, WHITE, "1. Data Layer (data/)", "CityFlowLoader & AnnotationParser\n1080p @ 30 FPS, ROI masks, calibration"),
        (4.85, 1.35, 3.6, 1.15, BLUE, WHITE, "2. Target Selection", "Benchmark GT ID or Interactive\ncv2.selectROI bounding box"),
        (9.15, 1.35, 3.6, 1.15, EMERALD_DARK, WHITE, "3. Local Tracker (CSRT/MIL)", "Detection-guided centering, NCC/PSR\nconfidence, update gating (>= 0.65)"),
        (9.15, 3.15, 3.6, 1.15, AMBER, NAVY, "4. Exit / Failure Monitor", "Boundary x <= 20 or x+w >= W-20\nor confidence < 0.35 -> SEARCHING"),
        (4.85, 3.15, 3.6, 1.15, SLATE, WHITE, "5. Detector + Re-ID", "SSDLite-MobileNetV3 in ROI\nResNet-50 (2048-d) + 3-stripe HSV"),
        (0.55, 3.15, 3.6, 1.15, EMERALD, NAVY, "6. Cross-Camera Association", "Adaptive Reliability Fusion\nS_app, S_temp, S_topo, S_motion"),
        (0.55, 5.05, 5.8, 1.25, NAVY, WHITE, "7. Global Target State Manager", "ACTIVE <-> LOST -> SEARCHING -> REACQUIRED\nPersistent ID: VEHICLE_001 | Re-init tracker on match >= 0.55"),
        (6.95, 5.05, 5.8, 1.25, BLUE, WHITE, "8. Evaluation & Visualization", "IoU, IDF1, Recovery Latency | H.264 avc1 MP4s\nHTTP 206 Dashboard (:8090) & Streamlit App (:8501)"),
    ]
    for x, y, w, h, bg, fg, title_b, body_b in boxes:
        shp = add_card(s4, x, y, w, h, fill_color=bg, border_color=None)
        tf = shp.text_frame
        tf.word_wrap = True
        p0 = tf.paragraphs[0]
        p0.text = title_b
        p0.alignment = PP_ALIGN.CENTER
        p0.font.size = Pt(13)
        p0.font.bold = True
        p0.font.color.rgb = fg
        p1 = tf.add_paragraph()
        p1.text = body_b
        p1.alignment = PP_ALIGN.CENTER
        p1.font.size = Pt(10.5)
        p1.font.color.rgb = fg

    # Connectors
    arrows = [
        (4.2, 1.8, 0.6, 0.22, MSO_SHAPE.RIGHT_ARROW),
        (8.5, 1.8, 0.6, 0.22, MSO_SHAPE.RIGHT_ARROW),
        (10.85, 2.55, 0.22, 0.55, MSO_SHAPE.DOWN_ARROW),
        (8.5, 3.6, 0.6, 0.22, MSO_SHAPE.LEFT_ARROW),
        (4.2, 3.6, 0.6, 0.22, MSO_SHAPE.LEFT_ARROW),
        (2.25, 4.35, 0.22, 0.65, MSO_SHAPE.DOWN_ARROW),
        (6.4, 5.55, 0.5, 0.22, MSO_SHAPE.RIGHT_ARROW),
    ]
    for ax, ay, aw, ah, atype in arrows:
        arr = s4.shapes.add_shape(atype, Inches(ax), Inches(ay), Inches(aw), Inches(ah))
        arr.fill.solid()
        arr.fill.fore_color.rgb = TEXT_MUTED
        arr.line.fill.background()

    # =========================================================================
    # SLIDE 5: LOCAL TRACKER & STATE MACHINE
    # =========================================================================
    s5 = prs.slides.add_slide(blank)
    set_slide_bg(s5, LIGHT_BG)
    add_header(s5, "4. Local Single-Object Tracker & State Machine", "Confidence-gated CSRT/MIL tracking with drift prevention and FOV exit monitoring", 5)

    add_card(s5, 0.55, 1.15, 6.0, 5.7, fill_color=WHITE)
    add_bullets(
        s5, 0.75, 1.3, 5.6, 5.4,
        "Local Tracking & Drift Prevention",
        [
            "Detection-Guided Centering (within 120 px): b_t <- 0.4 * b_trk + 0.6 * b_det (fixes slow CSRT scale adaptation).",
            "Confidence Estimation: C_t = 0.60 * NCC_t + 0.25 * C_ar + 0.15 * E_t (or NCC_t if NCC_t < 0.25).",
            "Update Gating: Clean template is refreshed ONLY when C_t >= 0.65.",
            "Boundary Exit Rule: Triggers departure when x <= 20, x+w >= W-20, y <= 20, or y+h >= H-20.",
            "Failure Threshold: Declared LOST when C_t < 0.35; reported tracked while C_t >= 0.45.",
        ],
        font_size=13,
    )

    add_card(s5, 6.8, 1.15, 5.95, 5.7, fill_color=WHITE)
    add_bullets(
        s5, 7.0, 1.3, 5.55, 2.2,
        "Global Target State Machine",
        [
            "ACTIVE: Tracking target locally inside current camera FOV.",
            "LOST: Triggered on boundary exit or confidence collapse.",
            "SEARCHING: Scans reachable cameras (patience <= 90 frames).",
            "REACQUIRED: Candidate score S >= 0.55 -> re-initializes local tracker with same VEHICLE_001 ID.",
        ],
        font_size=12.5,
    )

    # Mini State Diagram inside right card
    states = [
        (7.1, 4.3, EMERALD_DARK, "ACTIVE"),
        (8.5, 4.3, RED, "LOST"),
        (9.9, 4.3, AMBER, "SEARCHING"),
        (11.3, 4.3, BLUE, "REACQUIRED"),
    ]
    for sx, sy, scol, stxt in states:
        sb = add_card(s5, sx, sy, 1.25, 0.65, fill_color=scol, border_color=None)
        stf = sb.text_frame
        sp = stf.paragraphs[0]
        sp.text = stxt
        sp.alignment = PP_ALIGN.CENTER
        sp.font.size = Pt(11)
        sp.font.bold = True
        sp.font.color.rgb = WHITE if scol != AMBER else NAVY

    cap5 = s5.shapes.add_textbox(Inches(7.0), Inches(5.25), Inches(5.55), Inches(1.2))
    c5tf = cap5.text_frame
    c5tf.word_wrap = True
    c5p = c5tf.paragraphs[0]
    c5p.text = "Loop: REACQUIRED returns to ACTIVE on the next tracked frame.\nIf delta_t > 90 frames without match >= 0.55, search is abandoned."
    c5p.font.size = Pt(11.5)
    c5p.font.color.rgb = TEXT_MUTED

    # =========================================================================
    # SLIDE 6: VEHICLE DETECTION & RE-ID
    # =========================================================================
    s6 = prs.slides.add_slide(blank)
    set_slide_bg(s6, LIGHT_BG)
    add_header(s6, "5. Vehicle Detection & Deep Appearance Re-ID", "Fusing ImageNet ResNet-50 features with spatial-part HSV color histograms", 6)

    add_card(s6, 0.55, 1.15, 5.9, 5.7, fill_color=WHITE)
    add_bullets(
        s6, 0.75, 1.3, 5.5, 5.4,
        "Candidate Detection (vehicle_detector.py)",
        [
            "Primary Backend: Pretrained SSDLite320-MobileNetV3 (COCO).",
            "Classes Retained: car, bus, truck, motorcycle (confidence >= 0.40).",
            "ROI Filtering: Suppresses off-road false positives using per-camera binary mask (roi.jpg).",
            "Fallbacks: Faster R-CNN, YOLO, and OpenCV MOG2 background subtraction.",
        ],
        font_size=13,
    )

    add_card(s6, 6.7, 1.15, 6.05, 5.7, fill_color=WHITE)
    add_bullets(
        s6, 6.9, 1.3, 5.65, 5.4,
        "Appearance Re-Identification (vehicle_reid.py)",
        [
            "Deep Backbone: 2048-d L2-normalized ResNet-50 global-average-pooled vector (f_cnn).",
            "Spatial Color: 3 horizontal stripes (roof, body, wheels) x (16H + 8S + 8V) = 96-d f_col.",
            "Fused Descriptor: f = L2_norm([0.8 * f_cnn ; 0.2 * f_col]) in R^2144.",
            "Dynamic Gallery: Stores up to K = 10 diverse embeddings (added if max similarity < 0.95).",
            "EMA Running Reference: m <- 0.90 * m + 0.10 * f.",
            "Appearance Score: S_app = clip(0.7 * max_k(f_c^T g_k) + 0.3 * f_c^T m).",
        ],
        font_size=12.5,
    )

    # =========================================================================
    # SLIDE 7: PROPOSED RELIABILITY-AWARE ADAPTIVE ASSOCIATION
    # =========================================================================
    s7 = prs.slides.add_slide(blank)
    set_slide_bg(s7, LIGHT_BG)
    add_header(s7, "6. Proposed Reliability-Aware Adaptive Association", "Dynamically weighting appearance, temporal, topology, and motion cues", 7)

    add_card(s7, 0.55, 1.15, 5.95, 5.7, fill_color=WHITE)
    add_bullets(
        s7, 0.75, 1.3, 5.55, 5.4,
        "Four Cross-Camera Association Cues",
        [
            "1. Appearance (S_app): Cosine similarity against target gallery & EMA reference.",
            "2. Temporal Consistency (S_temp): Gaussian travel-delay kernel exp(-(dt - mu)^2 / (2*sigma^2)); 0.05 floor if dt < 5.",
            "3. Topology Prior (S_topo): Directed transition probability p_ij from topology.json (0.85 for c001->c002).",
            "4. Motion & Scale (S_motion): 0.6 * min(A-,A+)/max(A-,A+) + 0.4 * aspect consistency.",
            "Static Baseline (B3): Fixed weights w = (0.40, 0.25, 0.20, 0.15) — vulnerable to strong priors overriding weak appearance.",
        ],
        font_size=12.5,
    )

    add_card(s7, 6.75, 1.15, 6.0, 5.7, fill_color=RGBColor(236, 253, 245), border_color=EMERALD)
    add_bullets(
        s7, 6.95, 1.3, 5.6, 5.4,
        "Proposed Adaptive Formulation",
        [
            "Reliability Factors gamma_k in [0, 1]:",
            "  gamma_app = max(0.2, S_app^1.5) * min(1, D) * d  (penalizes uncertain detections & middling matches).",
            "  gamma_temp = exp(-0.02 * max(0, dt - 45))  (decays stale temporal priors).",
            "  gamma_topo = S_topo,   gamma_motion = S_motion  (amplifies confident cues).",
            "Normalized Adaptive Weights:  alpha_k = (w_k * gamma_k) / sum_j(w_j * gamma_j).",
            "Final Score: S_proposed = sum_k(alpha_k * S_k). Reacquires if S_proposed >= 0.55.",
            "Result: Prevents Baseline 3's distractor lock onto vehicle 3 in c002.",
        ],
        title_color=EMERALD_DARK, font_size=12.5,
    )

    # =========================================================================
    # SLIDE 8: QUANTITATIVE BENCHMARK RESULTS
    # =========================================================================
    s8 = prs.slides.add_slide(blank)
    set_slide_bg(s8, LIGHT_BG)
    add_header(s8, "7. Quantitative Benchmark Evaluation", "Controlled comparison across 4 methods on CityFlow S01 (|GT| = 33 frames)", 8)

    bm_tbl_shape = s8.shapes.add_table(5, 8, Inches(0.55), Inches(1.12), Inches(12.23), Inches(2.2))
    bm = bm_tbl_shape.table
    col_w = [2.63, 1.25, 1.45, 1.5, 1.45, 1.45, 1.25, 1.25]
    for i, w in enumerate(col_w):
        bm.columns[i].width = Inches(w)

    bm_headers = ["Method", "Mean IoU", "Center Error", "Success Rate", "Reacq Rate", "Recovery Delay", "IDF1", "FPS"]
    for i, h in enumerate(bm_headers):
        style_cell(bm.cell(0, i), h, font_size=11, bold=True, color=WHITE, bg_color=NAVY)

    bm_rows = [
        ("Baseline 1: Local Only", "0.9071", "17.46 px", "12.12%", "0.00%", "N/A", "0.2162", "118.7"),
        ("Baseline 2: Appearance Only", "0.7983", "21.05 px", "48.48%", "100.00%", "15.0 frames", "0.2500", "7.1"),
        ("Baseline 3: Static Fusion", "0.2247", "304.20 px", "15.15%", "100.00%", "8.0 frames", "0.1111", "7.5"),
        ("Proposed: Adaptive Fusion", "0.8504", "14.16 px", "69.70%", "100.00%", "15.0 frames", "0.5476", "7.0"),
    ]
    for r_idx, r in enumerate(bm_rows, start=1):
        is_prop = (r_idx == 4)
        bg = RGBColor(220, 252, 231) if is_prop else (WHITE if r_idx % 2 == 1 else CARD_BG)
        fg = EMERALD_DARK if is_prop else TEXT_DARK
        for c_idx, val in enumerate(r):
            style_cell(
                bm.cell(r_idx, c_idx), val, font_size=11, bold=is_prop, color=fg, bg_color=bg,
                align=PP_ALIGN.LEFT if c_idx == 0 else PP_ALIGN.CENTER
            )

    comp_plot = str(ROOT_DIR / "outputs" / "plots" / "baseline_comparison.png")
    if os.path.exists(comp_plot):
        s8.shapes.add_picture(comp_plot, Inches(2.15), Inches(3.48), width=Inches(5.0))

    add_card(s8, 7.45, 3.48, 5.33, 3.5, fill_color=WHITE)
    add_bullets(
        s8, 7.62, 3.6, 5.0, 3.25,
        "Key Performance Takeaways",
        [
            "Best Overall Tracking: Proposed Adaptive achieves highest Success Rate (69.70%), highest IDF1 (0.5476), and lowest Center Error (14.16 px).",
            "Local-Only Failure (B1): High IoU on 4 frames only; permanent loss after exit.",
            "Static Fusion Trap (B3): Locks onto distractor vehicle 3 in c002 (304.20 px error).",
            "Adaptive Advantage: Down-weights uncertain appearance cues and avoids distractor lock.",
        ],
        font_size=11.5,
    )

    # =========================================================================
    # SLIDE 9: TRAJECTORY & TRANSITION ANALYSIS
    # =========================================================================
    s9 = prs.slides.add_slide(blank)
    set_slide_bg(s9, LIGHT_BG)
    add_header(s9, "8. Trajectory & Cross-Camera Transition Analysis", "Spatial path reconstruction and handoff event breakdown", 9)

    traj_plot = str(ROOT_DIR / "outputs" / "plots" / "target_trajectory_proposed_adaptive.png")
    if os.path.exists(traj_plot):
        s9.shapes.add_picture(traj_plot, Inches(0.55), Inches(1.12), width=Inches(12.23))

    add_card(s9, 0.55, 4.95, 12.23, 2.0, fill_color=WHITE)
    add_bullets(
        s9, 0.75, 5.05, 11.8, 1.8,
        "Transition Log Findings (transitions_proposed_adaptive.csv)",
        [
            "Designated Hand-off (Event 5): c001 (Frame 18) -> c002 (Frame 32), delay dt = 14 frames (near mu = 15), highest score S = 0.833.",
            "Early False Hand-off (Events 1–3): Anti-teleportation floor (0.05 for dt < 5) is soft, allowing frames 6–8 false lock before returning to c001.",
            "Post-Annotation Reacquisitions (Frames 57–113): Without a terminal EXITED state, search continues after target exits c002 at frame 48.",
        ],
        font_size=12,
    )

    # =========================================================================
    # SLIDE 10: IMPLEMENTATION & VALIDITY AUDIT
    # =========================================================================
    s10 = prs.slides.add_slide(blank)
    set_slide_bg(s10, LIGHT_BG)
    add_header(s10, "9. Implementation Deliverables & Evaluation Audit", "Web dashboards, H.264 video outputs, unit tests, and critical validity findings", 10)

    add_card(s10, 0.55, 1.15, 5.9, 5.7, fill_color=WHITE)
    add_bullets(
        s10, 0.75, 1.3, 5.5, 5.4,
        "Deliverables & Engineering Stack",
        [
            "Annotated H.264 (avc1) Videos: c001, c002, and synchronized dashboard stream.",
            "Custom Web Dashboard (app/dashboard.py, :8090): HTTP 206 byte-range video streaming + run API.",
            "Streamlit App (app/streamlit_app.py, :8501): Interactive KPIs, Plotly charts, video tabs, and PDF download.",
            "Automated Tests (tests/test_pipeline.py): 7/7 unit & integration tests passing.",
            "Open-Source Repository: github.com/msujit908/cityflow-single-target-tracking.",
        ],
        font_size=12.5,
    )

    add_card(s10, 6.7, 1.15, 6.08, 5.7, fill_color=RGBColor(254, 242, 242), border_color=RED)
    add_bullets(
        s10, 6.9, 1.3, 5.68, 5.4,
        "Honest Validity Audit (Report Section 6.10)",
        [
            "Annotation Mismatch: ID 1 in sample gt.txt is a black SUV in c001 but a blue pickup in c002 (SUV is visible in c002 only at frames 1–10). Metrics measure annotation agreement, not same-vehicle Re-ID.",
            "IDSW Counter: metrics.py initializes idsw = 0 and never increments it; distractor overlap (Table 6.3) serves as the true proxy.",
            "Small Sample Size: Single annotated transition (33 GT frames); hand-set prior mu = 15 on the same clip.",
            "Hard-Coded Dashboard Text: Streamlit transition timeline uses static text rather than dynamic CSV parsing.",
        ],
        title_color=RGBColor(153, 27, 27), font_size=12,
    )

    # =========================================================================
    # SLIDE 11: CONCLUSION & FUTURE SCOPE
    # =========================================================================
    s11 = prs.slides.add_slide(blank)
    set_slide_bg(s11, NAVY)

    accent11 = s11.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(0.22), Inches(7.5))
    accent11.fill.solid()
    accent11.fill.fore_color.rgb = EMERALD
    accent11.line.fill.background()

    tb11 = s11.shapes.add_textbox(Inches(0.75), Inches(0.45), Inches(11.8), Inches(0.7))
    p11 = tb11.text_frame.paragraphs[0]
    p11.text = "10. Conclusion & Future Scope"
    p11.font.name = "Calibri"
    p11.font.size = Pt(28)
    p11.font.bold = True
    p11.font.color.rgb = WHITE

    add_card(s11, 0.75, 1.35, 5.75, 4.65, fill_color=SLATE, border_color=BLUE)
    tb_c = s11.shapes.add_textbox(Inches(0.95), Inches(1.5), Inches(5.35), Inches(4.35))
    ctf = tb_c.text_frame
    ctf.word_wrap = True
    cp0 = ctf.paragraphs[0]
    cp0.text = "Summary of Contributions"
    cp0.font.size = Pt(16)
    cp0.font.bold = True
    cp0.font.color.rgb = EMERALD
    cp0.space_after = Pt(8)
    for item in [
        "Built complete modular ST-MCT pipeline for static traffic cameras.",
        "Proposed reliability-aware adaptive fusion outperforming static fusion (0.8504 IoU, 69.70% success, 0.5476 IDF1) and avoiding distractor lock.",
        "Delivered interactive OpenCV ROI selector, H.264 video rendering, HTTP 206 dashboard, Streamlit app, and 43-page technical report.",
        "Conducted transparent validity audit identifying exact fixes.",
    ]:
        cp = ctf.add_paragraph()
        cp.text = f"•  {item}"
        cp.font.size = Pt(13)
        cp.font.color.rgb = WHITE
        cp.space_after = Pt(8)

    add_card(s11, 6.8, 1.35, 5.75, 4.65, fill_color=SLATE, border_color=EMERALD)
    tb_f = s11.shapes.add_textbox(Inches(7.0), Inches(1.5), Inches(5.35), Inches(4.35))
    ftf = tb_f.text_frame
    ftf.word_wrap = True
    fp0 = ftf.paragraphs[0]
    fp0.text = "Immediate Fixes & Future Work"
    fp0.font.size = Pt(16)
    fp0.font.bold = True
    fp0.font.color.rgb = RGBColor(56, 189, 248)
    fp0.space_after = Pt(8)
    for item in [
        "Evaluate on official CityFlow MTMC S01/S02 ground truth with consistent cross-camera IDs.",
        "Add hard temporal gate (dt < dt_min) and terminal EXITED state after mu + 3*sigma.",
        "Implement ID-switch counter & calibrate acceptance threshold (~0.65) on held-out clips.",
        "Fine-tune Re-ID on VeRi-776 / CityFlow-ReID; project boxes via homography H for 3D speed.",
        "Export SSDLite + ResNet-50 to TensorRT FP16/INT8 for 45+ FPS real-time deployment.",
    ]:
        fp_i = ftf.add_paragraph()
        fp_i.text = f"•  {item}"
        fp_i.font.size = Pt(13)
        fp_i.font.color.rgb = WHITE
        fp_i.space_after = Pt(7)

    thanks = s11.shapes.add_textbox(Inches(0.75), Inches(6.35), Inches(11.8), Inches(0.7))
    t_p = thanks.text_frame.paragraphs[0]
    t_p.text = "Thank You!  Questions & Discussion   |   github.com/msujit908/cityflow-single-target-tracking"
    t_p.alignment = PP_ALIGN.CENTER
    t_p.font.size = Pt(15)
    t_p.font.bold = True
    t_p.font.color.rgb = EMERALD

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    prs.save(output_path)
    print(f"[+] Presentation saved successfully to: {output_path}")
    return output_path


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "outputs/reports/STMCT_Presentation.pptx"
    build_presentation(out)

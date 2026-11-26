"""
PowerPoint Presentation Generator for CityFlow Single-Target Multi-Camera Vehicle Tracking.
Generates a clean, well-aligned 16:9 presentation with conceptual clarity (minimal equations)
for IIT Guwahati (EE5340 - Video Analytics).
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
NAVY = RGBColor(15, 23, 42)          # #0F172A
SLATE = RGBColor(30, 41, 59)         # #1E293B
BLUE = RGBColor(2, 132, 199)         # #0284C7
EMERALD = RGBColor(16, 185, 129)     # #10B981
EMERALD_DARK = RGBColor(6, 95, 70)   # #065F46
AMBER = RGBColor(245, 158, 11)       # #F59E0B
RED = RGBColor(239, 68, 68)          # #EF4444
LIGHT_BG = RGBColor(248, 250, 252)   # #F8FAFC
CARD_BG = RGBColor(241, 245, 249)    # #F1F5F9
BORDER = RGBColor(203, 213, 225)     # #CBD5E1
TEXT_DARK = RGBColor(15, 23, 42)
TEXT_MUTED = RGBColor(71, 85, 105)
WHITE = RGBColor(255, 255, 255)

MARGIN_X = 0.55
CONTENT_W = 12.23  # 13.333 - 2 * 0.55


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

    # Title + Subtitle
    tb = slide.shapes.add_textbox(Inches(MARGIN_X), Inches(0.20), Inches(CONTENT_W), Inches(0.68))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.text = title_text
    p.font.name = "Calibri"
    p.font.size = Pt(24)
    p.font.bold = True
    p.font.color.rgb = NAVY

    if subtitle_text:
        p2 = tf.add_paragraph()
        p2.text = subtitle_text
        p2.font.name = "Calibri"
        p2.font.size = Pt(12)
        p2.font.color.rgb = TEXT_MUTED

    # Divider line
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(MARGIN_X), Inches(0.94), Inches(CONTENT_W), Inches(0.02))
    line.fill.solid()
    line.fill.fore_color.rgb = BORDER
    line.line.fill.background()

    # Footer Left
    ft_l = slide.shapes.add_textbox(Inches(MARGIN_X), Inches(7.12), Inches(9.5), Inches(0.28))
    tf_l = ft_l.text_frame
    tf_l.margin_left = tf_l.margin_top = tf_l.margin_right = tf_l.margin_bottom = 0
    pl = tf_l.paragraphs[0]
    pl.text = "EE5340 – Video Analytics  |  IIT Guwahati  |  Single-Target Multi-Camera Vehicle Tracking"
    pl.font.name = "Calibri"
    pl.font.size = Pt(9.5)
    pl.font.color.rgb = TEXT_MUTED

    # Footer Right (Slide Number)
    ft_r = slide.shapes.add_textbox(Inches(10.5), Inches(7.12), Inches(2.28), Inches(0.28))
    tf_r = ft_r.text_frame
    tf_r.margin_left = tf_r.margin_top = tf_r.margin_right = tf_r.margin_bottom = 0
    pr = tf_r.paragraphs[0]
    pr.text = f"Slide {slide_num} / 11"
    pr.alignment = PP_ALIGN.RIGHT
    pr.font.name = "Calibri"
    pr.font.size = Pt(9.5)
    pr.font.bold = True
    pr.font.color.rgb = TEXT_MUTED


def add_card(slide, left, top, width, height, fill_color=CARD_BG, border_color=BORDER, radius=0.03):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
    shape.adjustments[0] = radius
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    if border_color:
        shape.line.color.rgb = border_color
        shape.line.width = Pt(1)
    else:
        shape.line.fill.background()
    return shape


def add_bullets(slide, left, top, width, height, title: str, items: list, title_color=BLUE, font_size=13, text_color=TEXT_DARK):
    tb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.08)
    tf.margin_top = tf.margin_bottom = Inches(0.05)

    p0 = tf.paragraphs[0]
    p0.text = title
    p0.font.name = "Calibri"
    p0.font.size = Pt(font_size + 2.5)
    p0.font.bold = True
    p0.font.color.rgb = title_color
    p0.space_after = Pt(8)

    for item in items:
        p = tf.add_paragraph()
        p.text = f"•  {item}"
        p.font.name = "Calibri"
        p.font.size = Pt(font_size)
        p.font.color.rgb = text_color
        p.space_after = Pt(6)
    return tb


def style_cell(cell, text: str, font_size=11, bold=False, color=TEXT_DARK, bg_color=None, align=PP_ALIGN.CENTER):
    cell.vertical_anchor = MSO_ANCHOR.MIDDLE
    if bg_color:
        cell.fill.solid()
        cell.fill.fore_color.rgb = bg_color
    tf = cell.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.08)
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

    badge = add_card(s1, 0.8, 0.70, 4.8, 0.44, fill_color=SLATE, border_color=BLUE, radius=0.15)
    badge.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    bp = badge.text_frame.paragraphs[0]
    bp.text = "EE5340 – VIDEO ANALYTICS  |  IIT GUWAHATI"
    bp.alignment = PP_ALIGN.CENTER
    bp.font.name = "Calibri"
    bp.font.size = Pt(12)
    bp.font.bold = True
    bp.font.color.rgb = RGBColor(56, 189, 248)

    tb1 = s1.shapes.add_textbox(Inches(0.8), Inches(1.40), Inches(11.73), Inches(1.95))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    p = tf1.paragraphs[0]
    p.text = "Single-Target Multi-Camera Vehicle Tracking\nAcross Static Traffic Cameras Using Appearance\nand Spatio-Temporal Association"
    p.font.name = "Calibri"
    p.font.size = Pt(34)
    p.font.bold = True
    p.font.color.rgb = WHITE

    sub = s1.shapes.add_textbox(Inches(0.8), Inches(3.52), Inches(11.73), Inches(0.55))
    stf = sub.text_frame
    stf.word_wrap = True
    sp = stf.paragraphs[0]
    sp.text = "A Reliability-Aware Approach using Deep Re-Identification and Adaptive Spatio-Temporal Fusion"
    sp.font.name = "Calibri"
    sp.font.size = Pt(16)
    sp.font.italic = True
    sp.font.color.rgb = EMERALD

    # Team & Supervisor cards (aligned symmetrically: 5.7" each, gap 0.33")
    add_card(s1, 0.8, 4.50, 5.7, 2.25, fill_color=SLATE, border_color=RGBColor(51, 65, 85))
    tb_team = s1.shapes.add_textbox(Inches(1.05), Inches(4.70), Inches(5.2), Inches(1.85))
    ttf = tb_team.text_frame
    ttf.word_wrap = True
    tp0 = ttf.paragraphs[0]
    tp0.text = "SUBMITTED BY"
    tp0.font.name = "Calibri"
    tp0.font.size = Pt(11)
    tp0.font.bold = True
    tp0.font.color.rgb = RGBColor(56, 189, 248)
    tp0.space_after = Pt(8)
    for name, roll in [
        ("Sujit Kumar Munda", "254156015"),
        ("Rohon Alam", "254156013"),
        ("Pranjal Singh Navrang", "264152010"),
    ]:
        tp = ttf.add_paragraph()
        tp.text = f"{name}  (Roll No: {roll})"
        tp.font.name = "Calibri"
        tp.font.size = Pt(14)
        tp.font.color.rgb = WHITE
        tp.space_after = Pt(5)

    add_card(s1, 6.83, 4.50, 5.7, 2.25, fill_color=SLATE, border_color=RGBColor(51, 65, 85))
    tb_sup = s1.shapes.add_textbox(Inches(7.08), Inches(4.70), Inches(5.2), Inches(1.85))
    stf2 = tb_sup.text_frame
    stf2.word_wrap = True
    sp0 = stf2.paragraphs[0]
    sp0.text = "SUPERVISOR & INSTITUTION"
    sp0.font.name = "Calibri"
    sp0.font.size = Pt(11)
    sp0.font.bold = True
    sp0.font.color.rgb = RGBColor(56, 189, 248)
    sp0.space_after = Pt(8)
    for line in [
        "Dr. Prithwijit Guha (Associate Professor, Dept. of EEE)",
        "School of Interdisciplinary Studies and Sustainability (SiSAS)",
        "Indian Institute of Technology Guwahati  |  November 2026",
    ]:
        sp_l = stf2.add_paragraph()
        sp_l.text = line
        sp_l.font.name = "Calibri"
        sp_l.font.size = Pt(13.5)
        sp_l.font.color.rgb = WHITE
        sp_l.space_after = Pt(6)

    # =========================================================================
    # SLIDE 2: PROBLEM STATEMENT & MOTIVATION
    # =========================================================================
    s2 = prs.slides.add_slide(blank)
    set_slide_bg(s2, LIGHT_BG)
    add_header(s2, "1. Problem Statement & Motivation", "Why Single-Target Multi-Camera Tracking (ST-MCT) instead of full MTMCT?", 2)

    add_card(s2, MARGIN_X, 1.15, 5.95, 5.75, fill_color=WHITE)
    add_bullets(
        s2, MARGIN_X + 0.18, 1.32, 5.59, 5.4,
        "Key Surveillance Challenges",
        [
            "Non-overlapping blind zones: continuity cannot rely on motion alone.",
            "Viewpoint & scale changes: rear vs. front/side views across cameras.",
            "Look-alike distractors: dark SUVs & pickups confuse appearance-only Re-ID.",
            "Template drift: updating local trackers on occluded or edge frames locks onto background.",
            "Compute waste: running detection + deep Re-ID on all vehicles every frame is unnecessary for a single query.",
            "Goal: Follow ONE selected vehicle (VEHICLE_001) across cameras without spawning distractor tracks.",
        ],
        font_size=13.5,
    )

    tbl_shape = s2.shapes.add_table(6, 3, Inches(6.80), Inches(1.15), Inches(5.98), Inches(3.85))
    tbl = tbl_shape.table
    tbl.columns[0].width = Inches(1.30)
    tbl.columns[1].width = Inches(2.25)
    tbl.columns[2].width = Inches(2.43)

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

    add_card(s2, 6.80, 5.20, 5.98, 1.70, fill_color=RGBColor(239, 246, 255), border_color=BLUE)
    add_bullets(
        s2, 6.98, 5.32, 5.62, 1.48,
        "Core Research Gap Addressed",
        [
            "Fixed-weight fusion fails when detection quality or travel delay varies.",
            "Our reliability-aware fusion adapts each cue's influence dynamically per candidate.",
        ],
        title_color=NAVY, font_size=12.5,
    )

    # =========================================================================
    # SLIDE 3: DATASET & EXPLORATORY ANALYSIS
    # =========================================================================
    s3 = prs.slides.add_slide(blank)
    set_slide_bg(s3, LIGHT_BG)
    add_header(s3, "2. CityFlow Dataset & Exploratory Analysis", "Authentic 1920×1080 @ 30 FPS traffic surveillance footage (Scenario S01)", 3)

    add_card(s3, MARGIN_X, 1.15, 5.55, 5.75, fill_color=WHITE)
    add_bullets(
        s3, MARGIN_X + 0.18, 1.32, 5.19, 5.4,
        "Dataset & Topology Specifications",
        [
            "Cameras: c001 (intersection entry) & c002 (second view), 121 frames each at 30 FPS.",
            "Annotations: 3 vehicle identities, 65 MOT boxes; average size 265 × 221 px.",
            "ID 1 timeline: c001 frames 1–17 -> blind zone (18–34) -> c002 frames 35–50.",
            "Topology priors: c001 -> c002 (85% prob., ~15 frames delay); reverse (80% prob., ~16 frames).",
            "Auxiliary files: camera calibration matrices, binary road ROI masks, and time offsets.",
            "Audit finding: Annotated ID 1 is a black SUV in c001 vs. a blue pickup in c002.",
        ],
        font_size=12.5,
    )

    # Preview Image c001 (width 6.40", height 3.60" -> bottom 4.75")
    prev_c1 = str(ROOT_DIR / "outputs" / "real_data_preview_c001.jpg")
    if os.path.exists(prev_c1):
        s3.shapes.add_picture(prev_c1, Inches(6.38), Inches(1.15), width=Inches(6.40), height=Inches(3.60))

    cap3 = s3.shapes.add_textbox(Inches(6.38), Inches(4.80), Inches(6.40), Inches(0.28))
    cp3 = cap3.text_frame.paragraphs[0]
    cp3.text = "Camera c001 (Frame 1): Initial target VEHICLE_001 selected at [605, 448, 459, 258]"
    cp3.alignment = PP_ALIGN.CENTER
    cp3.font.name = "Calibri"
    cp3.font.size = Pt(10.5)
    cp3.font.italic = True
    cp3.font.color.rgb = TEXT_MUTED

    # Re-ID crops aligned evenly across 6.40" width (3 x 2.00" + 2 x 0.20" gap = 6.40")
    crop_paths = [
        (ROOT_DIR / "outputs" / "crops" / "c003_v1_f0.jpg", "c001: Target SUV"),
        (ROOT_DIR / "outputs" / "crops" / "c003_v2_f0.jpg", "c001: Distractor ID 2"),
        (ROOT_DIR / "outputs" / "crops" / "c004_v1_f0.jpg", "c002: SUV (Frame 0)"),
    ]
    cx = 6.38
    for cp, label in crop_paths:
        if cp.exists():
            s3.shapes.add_picture(str(cp), Inches(cx), Inches(5.22), width=Inches(2.00), height=Inches(1.30))
            ctb = s3.shapes.add_textbox(Inches(cx), Inches(6.58), Inches(2.00), Inches(0.28))
            cp_p = ctb.text_frame.paragraphs[0]
            cp_p.text = label
            cp_p.alignment = PP_ALIGN.CENTER
            cp_p.font.name = "Calibri"
            cp_p.font.size = Pt(10.5)
            cp_p.font.bold = True
            cp_p.font.color.rgb = TEXT_DARK
        cx += 2.20

    # =========================================================================
    # SLIDE 4: SYSTEM ARCHITECTURE
    # =========================================================================
    s4 = prs.slides.add_slide(blank)
    set_slide_bg(s4, LIGHT_BG)
    add_header(s4, "3. System Architecture & Pipeline", "Modular end-to-end ST-MCT pipeline from synchronized video input to web dashboards", 4)

    # 3 columns: x = 0.55, 4.84, 9.13 (width 3.65, gap 0.64 -> ends at 12.78)
    boxes = [
        (0.55, 1.30, 3.65, 1.25, NAVY, WHITE, "1. Data Layer (data/)", "CityFlowLoader & AnnotationParser\n1080p @ 30 FPS, ROI masks, calibration"),
        (4.84, 1.30, 3.65, 1.25, BLUE, WHITE, "2. Target Selection", "Benchmark Ground-Truth ID or\nInteractive OpenCV ROI Selection"),
        (9.13, 1.30, 3.65, 1.25, EMERALD_DARK, WHITE, "3. Local Tracker (CSRT/MIL)", "Detection-guided centering,\nconfidence gating & drift control"),
        (9.13, 3.15, 3.65, 1.25, AMBER, NAVY, "4. Exit / Failure Monitor", "Detects FOV boundary departure\nor confidence drop -> SEARCHING"),
        (4.84, 3.15, 3.65, 1.25, SLATE, WHITE, "5. Detector + Re-ID", "SSDLite-MobileNetV3 inside ROI\nResNet-50 + 3-stripe HSV features"),
        (0.55, 3.15, 3.65, 1.25, EMERALD, NAVY, "6. Cross-Camera Association", "Reliability-Aware Adaptive Fusion\n(Appearance, Time, Topology, Scale)"),
        (0.55, 5.05, 5.90, 1.35, NAVY, WHITE, "7. Global Target State Manager", "ACTIVE  <->  LOST  ->  SEARCHING  ->  REACQUIRED\nMaintains persistent VEHICLE_001 ID & re-initializes tracker"),
        (6.88, 5.05, 5.90, 1.35, BLUE, WHITE, "8. Evaluation & Visualization", "IoU, IDF1, Recovery Delay  |  H.264 avc1 MP4s\nHTTP 206 Dashboard (:8090) & Streamlit App (:8501)"),
    ]
    for x, y, w, h, bg, fg, title_b, body_b in boxes:
        shp = add_card(s4, x, y, w, h, fill_color=bg, border_color=None)
        tf = shp.text_frame
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf.word_wrap = True
        p0 = tf.paragraphs[0]
        p0.text = title_b
        p0.alignment = PP_ALIGN.CENTER
        p0.font.name = "Calibri"
        p0.font.size = Pt(13.5)
        p0.font.bold = True
        p0.font.color.rgb = fg
        p0.space_after = Pt(4)
        p1 = tf.add_paragraph()
        p1.text = body_b
        p1.alignment = PP_ALIGN.CENTER
        p1.font.name = "Calibri"
        p1.font.size = Pt(11)
        p1.font.color.rgb = fg

    arrows = [
        (4.27, 1.81, 0.50, 0.22, MSO_SHAPE.RIGHT_ARROW),
        (8.56, 1.81, 0.50, 0.22, MSO_SHAPE.RIGHT_ARROW),
        (10.84, 2.60, 0.22, 0.50, MSO_SHAPE.DOWN_ARROW),
        (8.56, 3.66, 0.50, 0.22, MSO_SHAPE.LEFT_ARROW),
        (4.27, 3.66, 0.50, 0.22, MSO_SHAPE.LEFT_ARROW),
        (2.26, 4.45, 0.22, 0.55, MSO_SHAPE.DOWN_ARROW),
        (6.50, 5.61, 0.33, 0.22, MSO_SHAPE.RIGHT_ARROW),
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

    add_card(s5, MARGIN_X, 1.15, 5.95, 5.75, fill_color=WHITE)
    add_bullets(
        s5, MARGIN_X + 0.18, 1.32, 5.59, 5.4,
        "Local Tracking & Drift Prevention",
        [
            "Detection-Guided Centering: Pulls the tracker box toward any nearby vehicle detection (within 120 px) to correct slow scale adaptation.",
            "Multi-Cue Confidence: Combines template similarity (NCC against initial crop), box aspect-ratio consistency, and frame-edge proximity.",
            "Template Update Gating: Refreshes the appearance template only on high-confidence frames (>= 0.65) to prevent background drift.",
            "Boundary Exit Monitor: Flags departure automatically when the vehicle reaches within 20 px of any frame border.",
            "Failure Detection: Transitions to LOST if tracking confidence drops below 0.35.",
        ],
        font_size=13,
    )

    add_card(s5, 6.83, 1.15, 5.95, 5.75, fill_color=WHITE)
    add_bullets(
        s5, 7.01, 1.32, 5.59, 2.75,
        "Global Target State Machine",
        [
            "ACTIVE: Local tracker follows the selected vehicle inside the current camera FOV.",
            "LOST: Triggered on FOV boundary exit or confidence collapse.",
            "SEARCHING: Scans reachable downstream cameras for up to 90 frames.",
            "REACQUIRED: Best candidate passes match threshold (0.55) -> re-initializes local tracker with the same VEHICLE_001 ID.",
        ],
        font_size=12.5,
    )

    # 4 state boxes centered horizontally inside right card [6.83 .. 12.78] (width 5.95")
    # 4 * 1.15" + 3 * 0.25" = 5.35" -> start at 6.83 + 0.30 = 7.13"
    states = [
        (7.13, 4.45, EMERALD_DARK, "ACTIVE"),
        (8.53, 4.45, RED, "LOST"),
        (9.93, 4.45, AMBER, "SEARCHING"),
        (11.33, 4.45, BLUE, "REACQUIRED"),
    ]
    for i, (sx, sy, scol, stxt) in enumerate(states):
        sb = add_card(s5, sx, sy, 1.15, 0.65, fill_color=scol, border_color=None, radius=0.12)
        sb.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
        sp = sb.text_frame.paragraphs[0]
        sp.text = stxt
        sp.alignment = PP_ALIGN.CENTER
        sp.font.name = "Calibri"
        sp.font.size = Pt(11)
        sp.font.bold = True
        sp.font.color.rgb = WHITE if scol != AMBER else NAVY
        if i < 3:
            arr = s5.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(sx + 1.18), Inches(sy + 0.22), Inches(0.19), Inches(0.20))
            arr.fill.solid()
            arr.fill.fore_color.rgb = TEXT_MUTED
            arr.line.fill.background()

    cap5 = s5.shapes.add_textbox(Inches(7.01), Inches(5.40), Inches(5.59), Inches(1.15))
    c5tf = cap5.text_frame
    c5tf.word_wrap = True
    c5p = c5tf.paragraphs[0]
    c5p.text = "Once REACQUIRED, tracking seamlessly returns to ACTIVE on the next frame under the identical global target ID. Search stops if no match exceeds 0.55 within 90 frames."
    c5p.font.name = "Calibri"
    c5p.font.size = Pt(12)
    c5p.font.color.rgb = TEXT_MUTED

    # =========================================================================
    # SLIDE 6: VEHICLE DETECTION & RE-ID
    # =========================================================================
    s6 = prs.slides.add_slide(blank)
    set_slide_bg(s6, LIGHT_BG)
    add_header(s6, "5. Vehicle Detection & Deep Appearance Re-ID", "Fusing pretrained ResNet-50 features with spatial-part HSV color histograms", 6)

    add_card(s6, MARGIN_X, 1.15, 5.95, 5.75, fill_color=WHITE)
    add_bullets(
        s6, MARGIN_X + 0.18, 1.32, 5.59, 5.4,
        "Candidate Detection (vehicle_detector.py)",
        [
            "Primary Detector: Pretrained SSDLite320-MobileNetV3 (fast mobile/edge COCO model).",
            "Vehicle Classes: Retains car, bus, truck, and motorcycle detections (confidence >= 0.40).",
            "ROI Mask Filtering: Discards background detections outside the active roadway mask (roi.jpg).",
            "Modular Fallbacks: Supports Faster R-CNN, YOLO, and OpenCV MOG2 background subtraction.",
        ],
        font_size=13.5,
    )

    add_card(s6, 6.83, 1.15, 5.95, 5.75, fill_color=WHITE)
    add_bullets(
        s6, 7.01, 1.32, 5.59, 5.4,
        "Appearance Re-Identification (vehicle_reid.py)",
        [
            "Deep Visual Features: Pretrained ResNet-50 backbone extracts a 2048-d embedding capturing vehicle shape and texture.",
            "Spatial Color Cues: Splits crop into 3 horizontal stripes (roof, body, wheels) to compute HSV color histograms.",
            "Fused Descriptor: Combines 80% deep CNN features + 20% color histograms (L2-normalized).",
            "Diverse Target Gallery: Keeps up to 10 distinct appearance snapshots across viewpoints and lighting.",
            "EMA Running Reference: Smoothly updates a running target vector and matches candidates via cosine similarity.",
        ],
        font_size=13,
    )

    # =========================================================================
    # SLIDE 7: PROPOSED RELIABILITY-AWARE ADAPTIVE ASSOCIATION
    # =========================================================================
    s7 = prs.slides.add_slide(blank)
    set_slide_bg(s7, LIGHT_BG)
    add_header(s7, "6. Proposed Reliability-Aware Adaptive Association", "Dynamically weighting appearance, temporal, topology, and motion cues", 7)

    add_card(s7, MARGIN_X, 1.15, 5.95, 5.75, fill_color=WHITE)
    add_bullets(
        s7, MARGIN_X + 0.18, 1.32, 5.59, 5.4,
        "Four Cross-Camera Association Cues",
        [
            "1. Appearance Similarity: Cosine similarity against the target gallery and EMA reference.",
            "2. Travel-Delay Consistency: Gaussian prior centered on expected transit time (15 frames); penalizes impossible instant jumps (< 5 frames).",
            "3. Camera Topology Prior: Directed link probability from topology.json (0.85 for c001 -> c002).",
            "4. Motion & Scale Consistency: Penalizes large jumps in bounding-box area or aspect ratio.",
            "Limitation of Static Fusion (B3): Fixed weights (40% / 25% / 20% / 15%) let strong priors override weak appearance matches.",
        ],
        font_size=13,
    )

    add_card(s7, 6.83, 1.15, 5.95, 5.75, fill_color=RGBColor(236, 253, 245), border_color=EMERALD)
    add_bullets(
        s7, 7.01, 1.32, 5.59, 5.4,
        "Proposed Adaptive Reliability Weighting",
        [
            "Core Idea: Rescale each cue's weight on the fly by how trustworthy it is for the current candidate.",
            "Appearance Reliability: Down-weights appearance when detector confidence is low or visual match is ambiguous.",
            "Temporal Decay: Gradually reduces travel-time weight if the vehicle has been missing longer than 45 frames.",
            "Self-Reinforcing Agreement: Rewards candidates where multiple cues agree strongly, rather than letting one prior dominate.",
            "Reacquisition Rule: Accepts best downstream candidate with score >= 0.55.",
            "Key Benefit: Avoided Baseline 3's distractor lock onto vehicle 3 in c002.",
        ],
        title_color=EMERALD_DARK, font_size=13,
    )

    # =========================================================================
    # SLIDE 8: QUANTITATIVE BENCHMARK RESULTS
    # =========================================================================
    s8 = prs.slides.add_slide(blank)
    set_slide_bg(s8, LIGHT_BG)
    add_header(s8, "7. Quantitative Benchmark Evaluation", "Controlled comparison across 4 methods on CityFlow S01 (33 annotated target frames)", 8)

    bm_tbl_shape = s8.shapes.add_table(5, 8, Inches(MARGIN_X), Inches(1.12), Inches(CONTENT_W), Inches(2.15))
    bm = bm_tbl_shape.table
    col_w = [2.63, 1.25, 1.45, 1.50, 1.45, 1.45, 1.25, 1.25]
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

    # Align chart on left (width 4.90", height 3.50" -> top 3.42", bottom 6.92") & takeaways card on right (x=5.70, width=7.08, height=3.50)
    comp_plot = str(ROOT_DIR / "outputs" / "plots" / "baseline_comparison.png")
    if os.path.exists(comp_plot):
        s8.shapes.add_picture(comp_plot, Inches(MARGIN_X), Inches(3.42), width=Inches(4.90), height=Inches(3.50))

    add_card(s8, 5.70, 3.42, 7.08, 3.50, fill_color=WHITE)
    add_bullets(
        s8, 5.88, 3.54, 6.72, 3.25,
        "Key Performance Takeaways",
        [
            "Best Overall Tracking: Proposed Adaptive achieves highest Success Rate (69.70%), highest IDF1 (0.5476), and lowest Center Error (14.16 px).",
            "Local-Only Failure (B1): High IoU on 4 frames only; permanent loss after c001 exit (12.12% success).",
            "Appearance-Only (B2): Reacquires well on c002, but keeps predicting 71 frames after GT ends (low precision 0.167).",
            "Static Fusion Trap (B3): Fixed priors pull tracker onto distractor vehicle 3 in c002 (304.20 px error).",
            "Adaptive Advantage: Down-weights uncertain cues and eliminates annotated distractor locks.",
        ],
        font_size=12,
    )

    # =========================================================================
    # SLIDE 9: TRAJECTORY & TRANSITION ANALYSIS
    # =========================================================================
    s9 = prs.slides.add_slide(blank)
    set_slide_bg(s9, LIGHT_BG)
    add_header(s9, "8. Trajectory & Cross-Camera Transition Analysis", "Spatial path reconstruction and handoff event breakdown", 9)

    # 2800x1200 (aspect 2.333:1) -> width 8.40", height 3.60" centered at x = (13.333 - 8.40)/2 = 2.466"
    traj_plot = str(ROOT_DIR / "outputs" / "plots" / "target_trajectory_proposed_adaptive.png")
    if os.path.exists(traj_plot):
        s9.shapes.add_picture(traj_plot, Inches(2.47), Inches(1.10), width=Inches(8.40), height=Inches(3.60))

    add_card(s9, MARGIN_X, 4.88, CONTENT_W, 2.02, fill_color=WHITE)
    add_bullets(
        s9, MARGIN_X + 0.18, 4.98, CONTENT_W - 0.36, 1.82,
        "Transition Log Findings (transitions_proposed_adaptive.csv)",
        [
            "Designated Hand-off (Event 5): c001 (Frame 18) -> c002 (Frame 32), delay 14 frames (near expected 15), highest score 0.833.",
            "Early False Hand-off (Events 1–3): Soft penalty for < 5 frames allowed a brief false jump at frames 6–8 before returning to c001.",
            "Post-Annotation Reacquisitions (Frames 57–113): Without a terminal EXITED state, search resumes after the target leaves c002 at frame 48.",
        ],
        font_size=12,
    )

    # =========================================================================
    # SLIDE 10: IMPLEMENTATION & VALIDITY AUDIT
    # =========================================================================
    s10 = prs.slides.add_slide(blank)
    set_slide_bg(s10, LIGHT_BG)
    add_header(s10, "9. Implementation Deliverables & Evaluation Audit", "Web dashboards, H.264 video outputs, unit tests, and critical validity findings", 10)

    add_card(s10, MARGIN_X, 1.15, 5.95, 5.75, fill_color=WHITE)
    add_bullets(
        s10, MARGIN_X + 0.18, 1.32, 5.59, 5.4,
        "Deliverables & Engineering Stack",
        [
            "Annotated H.264 (avc1) Videos: Per-camera c001/c002 streams and side-by-side synchronized dashboard MP4.",
            "Custom Web Dashboard (:8090): Dependency-free HTTP server with byte-range video streaming and live run API.",
            "Streamlit App (:8501): Interactive KPIs, Plotly charts, video tabs, and one-click PDF/PPTX downloads.",
            "Automated Tests (tests/test_pipeline.py): 7/7 unit & integration tests passing.",
            "Open-Source Repository: github.com/msujit908/cityflow-single-target-tracking.",
        ],
        font_size=12.5,
    )

    add_card(s10, 6.83, 1.15, 5.95, 5.75, fill_color=RGBColor(254, 242, 242), border_color=RED)
    add_bullets(
        s10, 7.01, 1.32, 5.59, 5.4,
        "Honest Validity Audit (Report Section 6.10)",
        [
            "Annotation Mismatch: ID 1 in sample gt.txt is a black SUV in c001 but a blue pickup in c002 (SUV is visible in c002 only at frames 1–10). Metrics measure annotation agreement, not same-vehicle Re-ID.",
            "IDSW Counter: metrics.py initializes ID switches to 0 and never updates it; distractor overlap serves as the true proxy.",
            "Small Sample Size: Single annotated transition (33 GT frames); transit prior was hand-set on the same clip.",
            "Dashboard Alignment: Streamlit timeline panel still displays static summary text instead of parsing transitions CSV dynamically.",
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

    tb11 = s11.shapes.add_textbox(Inches(0.75), Inches(0.42), Inches(11.83), Inches(0.65))
    p11 = tb11.text_frame.paragraphs[0]
    p11.text = "10. Conclusion & Future Scope"
    p11.font.name = "Calibri"
    p11.font.size = Pt(28)
    p11.font.bold = True
    p11.font.color.rgb = WHITE

    add_card(s11, 0.75, 1.30, 5.75, 4.75, fill_color=SLATE, border_color=BLUE)
    tb_c = s11.shapes.add_textbox(Inches(0.95), Inches(1.48), Inches(5.35), Inches(4.40))
    ctf = tb_c.text_frame
    ctf.word_wrap = True
    cp0 = ctf.paragraphs[0]
    cp0.text = "Summary of Contributions"
    cp0.font.name = "Calibri"
    cp0.font.size = Pt(16)
    cp0.font.bold = True
    cp0.font.color.rgb = EMERALD
    cp0.space_after = Pt(10)
    for item in [
        "Built a complete modular ST-MCT pipeline for static traffic cameras.",
        "Proposed reliability-aware adaptive fusion outperforming static fusion (0.8504 IoU, 69.70% success, 0.5476 IDF1) and avoiding distractor lock.",
        "Delivered interactive OpenCV ROI selector, H.264 video rendering, HTTP 206 dashboard, Streamlit app, and 43-page technical report.",
        "Conducted transparent validity audit identifying concrete engineering fixes.",
    ]:
        cp = ctf.add_paragraph()
        cp.text = f"•  {item}"
        cp.font.name = "Calibri"
        cp.font.size = Pt(13)
        cp.font.color.rgb = WHITE
        cp.space_after = Pt(9)

    add_card(s11, 6.83, 1.30, 5.75, 4.75, fill_color=SLATE, border_color=EMERALD)
    tb_f = s11.shapes.add_textbox(Inches(7.03), Inches(1.48), Inches(5.35), Inches(4.40))
    ftf = tb_f.text_frame
    ftf.word_wrap = True
    fp0 = ftf.paragraphs[0]
    fp0.text = "Immediate Fixes & Future Work"
    fp0.font.name = "Calibri"
    fp0.font.size = Pt(16)
    fp0.font.bold = True
    fp0.font.color.rgb = RGBColor(56, 189, 248)
    fp0.space_after = Pt(10)
    for item in [
        "Evaluate on official CityFlow MTMC S01/S02 ground truth with consistent cross-camera IDs.",
        "Enforce a hard minimum-delay gate and add a terminal EXITED state after expected transit window.",
        "Implement true ID-switch counting & calibrate acceptance threshold (~0.65) on held-out clips.",
        "Fine-tune Re-ID on VeRi-776 / CityFlow-ReID; use camera homography for 3D speed estimation.",
        "Export detector & Re-ID to TensorRT FP16/INT8 for real-time 45+ FPS deployment.",
    ]:
        fp_i = ftf.add_paragraph()
        fp_i.text = f"•  {item}"
        fp_i.font.name = "Calibri"
        fp_i.font.size = Pt(13)
        fp_i.font.color.rgb = WHITE
        fp_i.space_after = Pt(8)

    thanks = s11.shapes.add_textbox(Inches(0.75), Inches(6.40), Inches(11.83), Inches(0.6))
    t_p = thanks.text_frame.paragraphs[0]
    t_p.text = "Thank You!  Questions & Discussion   |   github.com/msujit908/cityflow-single-target-tracking"
    t_p.alignment = PP_ALIGN.CENTER
    t_p.font.name = "Calibri"
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

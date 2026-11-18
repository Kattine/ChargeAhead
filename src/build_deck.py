"""
ChargeAhead: build the mid-semester review deck.

- 10 slides, 10 minute hard stop, solo presenter
- Palette and typography match the Idea Pitch deck
- Covers all mandatory topics from the guidelines (marked * below):
    Project Overview*          slide 2
    Progress Overview*         slide 3
    Customer Discovery         slide 7 note
    Data Collection*           slide 4
    Model Development*         slide 5 + 6
    Evaluation Metrics*        slide 7
    Next Steps*                slide 10
    Challenges & Risks*        slide 9
"""

from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "outputs" / "figures"
OUT = ROOT / "outputs" / "deck"
OUT.mkdir(parents=True, exist_ok=True)

# palette (match Idea Pitch)
BG = RGBColor(0xF5, 0xF8, 0xF6)
NAVY = RGBColor(0x10, 0x20, 0x2E)
LIME = RGBColor(0xC9, 0xF0, 0x3F)
TEAL = RGBColor(0x14, 0xA8, 0x8C)
TEAL_DARK = RGBColor(0x0A, 0x76, 0x63)
ORANGE = RGBColor(0xD4, 0x64, 0x3C)
AMBER = RGBColor(0xF0, 0xA9, 0x3B)
GREY = RGBColor(0x5E, 0x6E, 0x7E)
GREY_LIGHT = RGBColor(0x93, 0xA3, 0xB3)
CARD = RGBColor(0xDD, 0xE3, 0xE7)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

SLIDE_W = Inches(10)
SLIDE_H = Inches(5.625)
FOOTER_H = Inches(0.35)

TITLE_FONT = "Georgia"
BODY_FONT = "Calibri"


def _bg(slide, color=BG):
    """set a solid background on the slide via a full-slide rectangle at the back."""
    rect = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_W, SLIDE_H)
    rect.fill.solid(); rect.fill.fore_color.rgb = color
    rect.line.fill.background()
    rect.shadow.inherit = False
    # move to back by reordering xml
    sp = rect._element
    sp.getparent().remove(sp)
    slide.shapes._spTree.insert(2, sp)
    return rect


def _shape(slide, kind, l, t, w, h, fill=None, line_rgb=None):
    s = slide.shapes.add_shape(kind, l, t, w, h)
    if fill is not None:
        s.fill.solid(); s.fill.fore_color.rgb = fill
    else:
        s.fill.background()
    if line_rgb is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line_rgb
        s.line.width = Pt(0.75)
    s.shadow.inherit = False
    return s


def _tb(slide, l, t, w, h, text, size=12, bold=False, color=NAVY, font=BODY_FONT,
        align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(l, t, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Emu(0)
    tf.margin_top = tf.margin_bottom = Emu(0)
    tf.vertical_anchor = anchor
    lines = text.split("\n") if isinstance(text, str) else [text]
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        r = p.add_run()
        r.text = line
        r.font.name = font
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.color.rgb = color
    return tb


def _footer(slide, page_num):
    # thin lime line + small text
    _shape(slide, MSO_SHAPE.RECTANGLE, Inches(0), SLIDE_H - Inches(0.08), SLIDE_W, Inches(0.08), fill=LIME)
    _tb(slide, Inches(0.4), SLIDE_H - Inches(0.33), Inches(8), Inches(0.25),
        "ChargeAhead  |  AIPI 590 Mid-Semester Review  |  Keming Zhou",
        size=9, color=GREY_LIGHT, font=BODY_FONT)
    _tb(slide, SLIDE_W - Inches(0.6), SLIDE_H - Inches(0.33), Inches(0.35), Inches(0.25),
        str(page_num), size=9, color=GREY_LIGHT, font=BODY_FONT, align=PP_ALIGN.RIGHT)


def _page_header(slide, eyebrow, title, subtitle=None):
    """Standard page header used by content slides."""
    _tb(slide, Inches(0.4), Inches(0.2), Inches(9.2), Inches(0.3),
        eyebrow.upper(), size=10, bold=True, color=TEAL_DARK, font=BODY_FONT)
    # lime underline below eyebrow
    _shape(slide, MSO_SHAPE.RECTANGLE, Inches(0.4), Inches(0.47), Inches(0.5), Inches(0.06), fill=LIME)
    # title: fixed size 20pt, fits in one line within 9.2 inches
    _tb(slide, Inches(0.4), Inches(0.57), Inches(9.2), Inches(0.5), title,
        size=20, bold=True, color=NAVY, font=TITLE_FONT)
    if subtitle:
        _tb(slide, Inches(0.4), Inches(1.05), Inches(9.2), Inches(0.3), subtitle,
            size=10.5, color=GREY, font=BODY_FONT)


# ------------------------------------------------------------------
# slides
# ------------------------------------------------------------------
def slide_1_cover(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])  # blank
    _bg(s, NAVY)
    # LIME accent corner
    _shape(s, MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(0.5), SLIDE_H, fill=LIME)
    _tb(s, Inches(0.9), Inches(1.1), Inches(8), Inches(0.4), "AIPI 590  |  TERM PROJECT  |  MID-SEMESTER REVIEW",
        size=11, bold=True, color=LIME, font=BODY_FONT)
    _tb(s, Inches(0.9), Inches(1.5), Inches(8), Inches(1.1), "ChargeAhead",
        size=56, bold=True, color=WHITE, font=TITLE_FONT)
    _tb(s, Inches(0.9), Inches(2.65), Inches(8.5), Inches(0.6),
        "Where China's car market is moving, and what the shift means for individual models.",
        size=18, color=LIME, font=BODY_FONT)
    _tb(s, Inches(0.9), Inches(3.4), Inches(8.5), Inches(0.5),
        "An alternative-data index tracking China's powertrain transition, tested against model-level market performance.",
        size=13, color=GREY_LIGHT, font=BODY_FONT)
    _tb(s, Inches(0.9), Inches(4.6), Inches(8.5), Inches(0.4),
        "Keming Zhou  |  Mid-Semester Review  |  October 14, 2026",
        size=11, color=GREY_LIGHT, font=BODY_FONT)


def slide_2_overview(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _bg(s)
    _page_header(s, "Project Overview", "The project in one slide",
                 "Recap from the Sept 16 Idea Pitch, same scope and same framing.")

    # single top banner card
    _shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.4), Inches(1.5), Inches(9.2), Inches(0.8), fill=WHITE)
    _shape(s, MSO_SHAPE.RECTANGLE, Inches(0.4), Inches(1.5), Inches(0.08), Inches(0.8), fill=LIME)
    _tb(s, Inches(0.6), Inches(1.55), Inches(9), Inches(0.3), "The idea",
        size=10, bold=True, color=TEAL_DARK, font=BODY_FONT)
    _tb(s, Inches(0.6), Inches(1.8), Inches(9), Inches(0.5),
        "Market statistics tell us what already happened. ChargeAhead combines monthly CPCA data with alternative signals, tests whether they detect the powertrain shift earlier, and ships a simple decision dashboard.",
        size=11, color=NAVY, font=BODY_FONT)

    # four columns underneath
    col_w = Inches(2.2); col_h = Inches(2.6); gap = Inches(0.14)
    base_l = Inches(0.4); base_t = Inches(2.55)
    tiles = [
        ("Problem", "Where a segment is heading is much less visible than where it has been.", TEAL),
        ("Alternative data", "Consumer search attention plus channel inventory and pricing conditions.", TEAL),
        ("Primary user", "The car buyer. Used-car dealers and auto analysts are extensions.", TEAL),
        ("Approach", "Build a Transition Index, test it against model-level outcomes, ship a dashboard.", TEAL),
    ]
    for i, (title, body, color) in enumerate(tiles):
        l = base_l + (col_w + gap) * i
        _shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, l, base_t, col_w, col_h, fill=WHITE)
        _shape(s, MSO_SHAPE.RECTANGLE, l, base_t, col_w, Inches(0.08), fill=color)
        _tb(s, l + Inches(0.2), base_t + Inches(0.25), col_w - Inches(0.4), Inches(0.4),
            title, size=14, bold=True, color=NAVY, font=TITLE_FONT)
        _tb(s, l + Inches(0.2), base_t + Inches(0.75), col_w - Inches(0.4), col_h - Inches(0.9),
            body, size=10, color=GREY, font=BODY_FONT)

    _footer(s, 2)


def slide_3_progress(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _bg(s)
    _page_header(s, "Progress Overview", "Four weeks since the Idea Pitch",
                 "What is done, what is new since September 16, and where the data stands.")

    # left column: milestone timeline
    tl_l = Inches(0.4); tl_t = Inches(1.5); tl_w = Inches(4.3)
    _shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, tl_l, tl_t, tl_w, Inches(3.85), fill=WHITE)
    _tb(s, tl_l + Inches(0.25), tl_t + Inches(0.12), tl_w - Inches(0.5), Inches(0.4),
        "Milestones hit since Sept 16", size=12, bold=True, color=NAVY, font=TITLE_FONT)

    milestones = [
        ("Sept 20", "Scoped the four index components and sketched the data map", TEAL),
        ("Sept 25", "Collected CPCA 2023-2026 monthly aggregates, cleaned 44 months", TEAL),
        ("Sept 30", "Built the national monthly panel, 36 columns, Jan 23 to Aug 26", TEAL),
        ("Oct 03", "Transition Index v1 running end-to-end, four components", TEAL),
        ("Oct 06", "Channel inventory signal aligned, lead-lag correlations computed", TEAL),
        ("Oct 10", "Brand-level 2026 Mar-Aug validation preview", AMBER),
        ("Oct 12", "Persistence baseline, MAE and direction accuracy on dIndex", TEAL),
        ("Oct 13", "Baidu Search Index collected, 42 keywords, 199 weeks, Baidu-as-feature baseline", TEAL),
    ]
    for i, (date, text, color) in enumerate(milestones):
        y = tl_t + Inches(0.6) + Inches(0.38) * i
        _shape(s, MSO_SHAPE.OVAL, tl_l + Inches(0.3), y + Inches(0.08),
               Inches(0.12), Inches(0.12), fill=color)
        _tb(s, tl_l + Inches(0.55), y, Inches(0.9), Inches(0.3), date,
            size=9, bold=True, color=TEAL_DARK, font=BODY_FONT)
        _tb(s, tl_l + Inches(1.5), y, tl_w - Inches(1.7), Inches(0.32), text,
            size=9, color=NAVY, font=BODY_FONT)

    # right column: data coverage image
    _shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, Inches(4.95), Inches(1.5), Inches(4.7), Inches(3.8), fill=WHITE)
    _tb(s, Inches(5.1), Inches(1.6), Inches(4.4), Inches(0.4),
        "Data coverage snapshot", size=12, bold=True, color=NAVY, font=TITLE_FONT)
    s.shapes.add_picture(str(FIG / "06_data_coverage.png"),
                         Inches(5.0), Inches(2.05), width=Inches(4.6))

    _footer(s, 3)


def slide_4_data(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _bg(s)
    _page_header(s, "Data Collection and Preparation", "What is in the panel, and what the gaps are",
                 "All sources are public. Status is reported honestly.")

    # left column: source list
    l0 = Inches(0.4); t0 = Inches(1.5); w0 = Inches(5.0); h0 = Inches(3.75)
    _shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, l0, t0, w0, h0, fill=WHITE)
    _tb(s, l0 + Inches(0.25), t0 + Inches(0.12), w0 - Inches(0.5), Inches(0.3),
        "Sources and status", size=11, bold=True, color=NAVY, font=TITLE_FONT)

    sources = [
        ("CPCA monthly reports", "Jan 2023 to Aug 2026, 44 months in one panel.", TEAL),
        ("Channel inventory signal", "Derived from CPCA wholesale minus retail. 44 months.", TEAL),
        ("ICE YoY retail decline", "Derived from total retail minus NEV retail. 2024 to 2026.", TEAL),
        ("Baidu Search Index", "42 keywords, 199 weeks, Jan 2023 to Oct 2026, rolled to month.", TEAL),
        ("Brand-level retail 2026", "Hand-collected. 14 brands, Mar to Aug 2026.", AMBER),
        ("Brand wholesale, CPCA table 五", "Parseable from raw files. 2025 full year + 2026 Jan-Aug.", AMBER),
        ("Residual values (CADA)", "Downstream validation. Stretch for Final.", ORANGE),
    ]
    row_h = Inches(0.44)
    for i, (src, txt, color) in enumerate(sources):
        y = t0 + Inches(0.55) + row_h * i
        _shape(s, MSO_SHAPE.RECTANGLE, l0 + Inches(0.3), y + Inches(0.06),
               Inches(0.08), Inches(0.3), fill=color)
        _tb(s, l0 + Inches(0.5), y, w0 - Inches(0.7), Inches(0.2),
            src, size=9.5, bold=True, color=NAVY, font=BODY_FONT)
        _tb(s, l0 + Inches(0.5), y + Inches(0.2), w0 - Inches(0.7), Inches(0.22),
            txt, size=8, color=GREY, font=BODY_FONT)

    # right column: how it was prepared
    l1 = Inches(5.6); w1 = Inches(4.0)
    _shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, l1, t0, w1, h0, fill=WHITE)
    _tb(s, l1 + Inches(0.25), t0 + Inches(0.12), w1 - Inches(0.5), Inches(0.3),
        "Preparation and issues", size=11, bold=True, color=NAVY, font=TITLE_FONT)

    notes = [
        ("Entity alignment", "Monthly alignment across all series. Text-form percentages parsed to decimals, 万辆 normalized."),
        ("The 2023 split", "2023 CPCA reports do not cleanly separate PHEV and EREV, so BEV share of NEV is only available from 2024 onward."),
        ("Weekly to monthly", "Baidu rolled by week_start month attribution. Mean intensity used so months with different week counts stay comparable."),
        ("Keyword volume gap", "Category terms (纯电车, 燃油车) hit much lower volume than brand terms. Signal strength tracked per keyword."),
        ("No private data", "Aggregated indicators only. No individual search, identity, or behavioural data at any point."),
    ]
    note_h = Inches(0.62)
    for i, (title, text) in enumerate(notes):
        y = t0 + Inches(0.55) + note_h * i
        _tb(s, l1 + Inches(0.3), y, w1 - Inches(0.6), Inches(0.2),
            title, size=9.5, bold=True, color=TEAL_DARK, font=BODY_FONT)
        _tb(s, l1 + Inches(0.3), y + Inches(0.2), w1 - Inches(0.6), Inches(0.42),
            text, size=8.5, color=GREY, font=BODY_FONT)

    _footer(s, 4)


def slide_5_index(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _bg(s)
    _page_header(s, "Model Development  —  Transition Index",
                 "Baseline composite, four transparent components",
                 "Each component min-max normalized to [0, 1], equal-weighted. Composite = mean of what is available.")

    # formula strip (left)
    l0 = Inches(0.4); t0 = Inches(1.5); w0 = Inches(3.6); h0 = Inches(3.85)
    _shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, l0, t0, w0, h0, fill=WHITE)
    _tb(s, l0 + Inches(0.25), t0 + Inches(0.12), w0 - Inches(0.5), Inches(0.3),
        "Four components", size=11, bold=True, color=NAVY, font=TITLE_FONT)

    rows = [
        ("C1", "NEV penetration", "NEV retail / total retail", TEAL),
        ("C2", "ICE YoY decline", "Negated YoY of ICE retail", ORANGE),
        ("C3", "BEV share of NEV", "BEV / (BEV + PHEV + EREV) wholesale", TEAL_DARK),
        ("C4", "BEV mainstream", "A0 + A level share within BEV", AMBER),
    ]
    for i, (tag, name, desc, color) in enumerate(rows):
        y = t0 + Inches(0.55) + Inches(0.62) * i
        _shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, l0 + Inches(0.25), y, Inches(0.5), Inches(0.5),
               fill=color)
        _tb(s, l0 + Inches(0.25), y + Inches(0.1), Inches(0.5), Inches(0.3),
            tag, size=12, bold=True, color=WHITE, font=TITLE_FONT, align=PP_ALIGN.CENTER)
        _tb(s, l0 + Inches(0.85), y + Inches(0.03), w0 - Inches(1.0), Inches(0.25),
            name, size=10, bold=True, color=NAVY, font=BODY_FONT)
        _tb(s, l0 + Inches(0.85), y + Inches(0.26), w0 - Inches(1.0), Inches(0.3),
            desc, size=8.5, color=GREY, font=BODY_FONT)

    # formula at bottom (inside its own strip)
    _shape(s, MSO_SHAPE.RECTANGLE, l0 + Inches(0.25), t0 + Inches(3.25),
           w0 - Inches(0.5), Inches(0.4), fill=CARD)
    _tb(s, l0 + Inches(0.25), t0 + Inches(3.3), w0 - Inches(0.5), Inches(0.3),
        "Index_t = mean( norm(C1..C4) )",
        size=9.5, bold=True, color=NAVY, font="Consolas", align=PP_ALIGN.CENTER)

    # right: chart 01
    _shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, Inches(4.2), Inches(1.5), Inches(5.45), h0, fill=WHITE)
    s.shapes.add_picture(str(FIG / "01_transition_index.png"),
                         Inches(4.3), Inches(1.65), width=Inches(5.25))

    _footer(s, 5)


def slide_6_channel(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _bg(s)
    _page_header(s, "Preliminary Result  —  Channel Signal", "Channel inventory moves with the Transition Index",
                 "Both the channel gap and the inventory ratio co-move with the index. Lead time is small so far.")

    # left chart
    _shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.4), Inches(1.5), Inches(5.6), Inches(3.8), fill=WHITE)
    s.shapes.add_picture(str(FIG / "02_channel_vs_index.png"),
                         Inches(0.5), Inches(1.6), width=Inches(5.4))

    # right summary
    l1 = Inches(6.2); w1 = Inches(3.4)
    _shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, l1, Inches(1.5), w1, Inches(3.8), fill=WHITE)
    _tb(s, l1 + Inches(0.2), Inches(1.6), w1 - Inches(0.4), Inches(0.35),
        "Lead-lag of channel signal", size=12, bold=True, color=NAVY, font=TITLE_FONT)
    s.shapes.add_picture(str(FIG / "03_leadlag.png"),
                         l1 + Inches(0.08), Inches(1.95), width=Inches(3.3))
    _tb(s, l1 + Inches(0.25), Inches(3.9), w1 - Inches(0.5), Inches(1.1),
        "Both signals correlate strongly with the index level. The inventory ratio peaks at +1 month lead, r = 0.82. The channel gap peaks contemporaneously, r = 0.85.\n"
        "This is a co-movement finding, not yet a forecast.",
        size=9.5, color=GREY, font=BODY_FONT)

    _footer(s, 6)


def slide_7_baidu(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _bg(s)
    _page_header(s, "Preliminary Result  —  Baidu Attention",
                 "The core alt signal is in, 42 keywords across 199 weeks",
                 "Category terms are low-volume, brand and model terms carry the signal.")

    # left: chart 07
    _shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.4), Inches(1.5), Inches(6.0), Inches(3.8), fill=WHITE)
    s.shapes.add_picture(str(FIG / "07_baidu_vs_index.png"),
                         Inches(0.5), Inches(1.6), width=Inches(5.8))

    # right summary
    l1 = Inches(6.55); w1 = Inches(3.05); h1 = Inches(3.8)
    _shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, l1, Inches(1.5), w1, h1, fill=WHITE)
    _tb(s, l1 + Inches(0.2), Inches(1.6), w1 - Inches(0.4), Inches(0.35),
        "What the data says", size=12, bold=True, color=NAVY, font=TITLE_FONT)
    bullets = [
        "Category terms 纯电车 174, 燃油车 150 are too low-volume to carry signal alone. Powertrain-level attention has to be built from brand aggregates.",
        "Brand attention is strong. 特斯拉 17k, 比亚迪 14k, 极氪 7k. Clean month-to-month movement.",
        "Raw-level correlations with the index are negative because brand attention has launch-spike dynamics while the index trends up. Differencing is required before use.",
        "The real test is predictive, next slide.",
    ]
    for i, b in enumerate(bullets):
        _tb(s, l1 + Inches(0.3), Inches(1.95) + Inches(0.75) * i,
            w1 - Inches(0.5), Inches(0.7),
            "• " + b, size=8.5, color=GREY, font=BODY_FONT)

    _footer(s, 7)


def slide_8_eval(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _bg(s)
    _page_header(s, "Evaluation Metrics", "Baidu attention beats persistence on MAE",
                 "NEV-category and top-model attention cut forecast error 14% at the same direction accuracy.")

    # chart on top (full width)
    _shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.4), Inches(1.5), Inches(9.2), Inches(2.5), fill=WHITE)
    s.shapes.add_picture(str(FIG / "08_baidu_baseline.png"),
                         Inches(0.5), Inches(1.6), width=Inches(9.0))

    # bottom row: two cards side by side
    l0 = Inches(0.4); l1 = Inches(5.1); card_w = Inches(4.5); card_h = Inches(1.2)
    _shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, l0, Inches(4.1), card_w, card_h, fill=WHITE)
    _tb(s, l0 + Inches(0.2), Inches(4.17), card_w - Inches(0.4), Inches(0.3),
        "The headline finding", size=10, bold=True, color=TEAL_DARK, font=BODY_FONT)
    _tb(s, l0 + Inches(0.2), Inches(4.42), card_w - Inches(0.4), Inches(0.75),
        "NEV category attention and Top-model attention both drop MAE from 0.080 to 0.069, "
        "about 14% improvement, while matching persistence at 85% direction accuracy. "
        "This is incremental value from a true alt signal, not a repackaging of CPCA.",
        size=9, color=NAVY, font=BODY_FONT)

    _shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, l1, Inches(4.1), card_w, card_h, fill=WHITE)
    _tb(s, l1 + Inches(0.2), Inches(4.17), card_w - Inches(0.4), Inches(0.3),
        "Customer discovery to date", size=10, bold=True, color=TEAL_DARK, font=BODY_FONT)
    _tb(s, l1 + Inches(0.2), Inches(4.42), card_w - Inches(0.4), Inches(0.75),
        "Four informal conversations with Duke MEng peers weighing an EV purchase. "
        "Shared pain is too many rankings, no view of segment direction. "
        "Formal dealer and analyst interviews planned Oct 20 to Nov 7.",
        size=9, color=NAVY, font=BODY_FONT)

    _footer(s, 8)


def slide_9_models(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _bg(s)
    _page_header(s, "Preliminary Result  —  Brand-level Validation",
                 "BEV-leaning brands outgrew the market, Mar to Aug 2026",
                 "Index moved from 0.64 to 1.00 in the same window. 14 brands in the first sample.")

    # chart left
    _shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.4), Inches(1.5), Inches(6.0), Inches(3.8), fill=WHITE)
    s.shapes.add_picture(str(FIG / "04_brand_growth.png"),
                         Inches(0.5), Inches(1.6), width=Inches(5.8))

    # right summary
    l1 = Inches(6.55); w1 = Inches(3.05); h1 = Inches(3.8)
    _shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, l1, Inches(1.5), w1, h1, fill=WHITE)
    _tb(s, l1 + Inches(0.2), Inches(1.6), w1 - Inches(0.4), Inches(0.35),
        "What stands out", size=12, bold=True, color=NAVY, font=TITLE_FONT)
    stats = [
        ("BEV-only brands", "mean +34%", "7 brands including XPeng, Xiaomi, ARCFOX, IM Motors"),
        ("BEV + EREV mix", "mean +20%", "4 brands including Leapmotor (+154% outlier), Deepal (-38%)"),
        ("BEV + PHEV mix", "mean +3%", "3 brands including BYD (+12%), Voyah, Lynk & Co"),
    ]
    for i, (lbl, val, note) in enumerate(stats):
        y = Inches(2.0) + Inches(0.8) * i
        _tb(s, l1 + Inches(0.3), y, w1 - Inches(0.5), Inches(0.25),
            lbl, size=10, bold=True, color=TEAL_DARK, font=BODY_FONT)
        _tb(s, l1 + Inches(0.3), y + Inches(0.25), w1 - Inches(0.5), Inches(0.3),
            val, size=16, bold=True, color=NAVY, font=TITLE_FONT)
        _tb(s, l1 + Inches(0.3), y + Inches(0.55), w1 - Inches(0.5), Inches(0.25),
            note, size=8, color=GREY, font=BODY_FONT)
    _tb(s, l1 + Inches(0.3), Inches(4.6), w1 - Inches(0.5), Inches(0.6),
        "Directionally consistent with the Transition Index, but noisy and sample-small. "
        "Brand monthly wholesale 2024 to 2026 parseable from CPCA table 五, scheduled for Oct 20.",
        size=8.5, color=GREY, font=BODY_FONT)

    _footer(s, 9)


def slide_10_risks(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _bg(s)
    _page_header(s, "Challenges and Risks", "What is hard, and the fallback for each",
                 "Each risk is paired with a mitigation that can be executed by Nov 18.")

    items = [
        ("Keyword signal strength",
         "Category terms 纯电车, 燃油车, 混动车 are an order of magnitude lower in volume than brand terms. Powertrain-level attention is thin.",
         "Build powertrain-level attention from brand aggregates. 比亚迪 for PHEV, 理想 and 问界 for EREV, pure BEV brand basket for BEV.",
         AMBER),
        ("Raw-level negative correlation",
         "Brand attention has launch-spike dynamics that trend differently from the slowly rising Transition Index.",
         "Differencing or de-trending required before use. Current baseline uses first-differenced attention as the feature.",
         AMBER),
        ("Lead-lag versus forecasting",
         "Co-movement is not a predictive claim. Only one feature so far beats persistence on test MAE.",
         "Report leading-indicator correlations separately. Build a rolling-window out-of-sample ARIMAX for the Final Demo.",
         ORANGE),
        ("Brand-level sample is thin",
         "Model-level validation only covers Mar - Aug 2026, 6 months x 14 brands.",
         "Parse CPCA table 五 to pull brand monthly wholesale 2025 full year + 2026 Jan-Aug. Scripting task, half a day.",
         AMBER),
        ("Signal decay",
         "The 2023 regime looks different from 2026. BEV brand attention peaked Mar 2024 then faded.",
         "Rolling-window ablation and a dated regime-shift note in the Final Demo postmortem.",
         AMBER),
        ("Residual value data",
         "CADA / Chezhen is a scraping and licensing question, not just technical.",
         "Treat as a Final Demo stretch chapter. Core evaluation does not depend on it.",
         ORANGE),
    ]

    base_t = Inches(1.5)
    for i, (title, risk, mit, color) in enumerate(items):
        y = base_t + Inches(0.6) * i
        _shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.4), y, Inches(9.2), Inches(0.55), fill=WHITE)
        _shape(s, MSO_SHAPE.RECTANGLE, Inches(0.4), y, Inches(0.1), Inches(0.55), fill=color)
        _tb(s, Inches(0.6), y + Inches(0.05), Inches(2.6), Inches(0.22),
            title, size=9.5, bold=True, color=NAVY, font=TITLE_FONT)
        _tb(s, Inches(0.6), y + Inches(0.27), Inches(2.6), Inches(0.28),
            risk, size=7.5, color=GREY, font=BODY_FONT)
        _tb(s, Inches(3.3), y + Inches(0.05), Inches(0.6), Inches(0.22),
            "Mitigation", size=7.5, bold=True, color=TEAL_DARK, font=BODY_FONT)
        _tb(s, Inches(3.3), y + Inches(0.26), Inches(6.2), Inches(0.3),
            mit, size=8.5, color=NAVY, font=BODY_FONT)

    _footer(s, 10)


def slide_11_next(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _bg(s)
    _page_header(s, "Next Steps  —  Toward November 18", "From co-movement to a decision tool",
                 "Four workstreams, each with a visible deliverable by the Final Demo.")

    steps = [
        ("1", "ARIMAX with Baidu attention",
         "Replace linear regression with rolling-window ARIMAX. Baidu NEV attention and top-model attention as exogenous inputs.",
         "Target: Oct 25"),
        ("2", "Parse CPCA table 五",
         "Brand monthly wholesale 2025 full year + 2026 Jan-Aug. Scripting task, extends brand validation from 6 months to 20.",
         "Target: Oct 22"),
        ("3", "Build the three-page dashboard",
         "Page 1 index and components. Page 2 segment heatmap with attention overlay. Page 3 model-level verdict for a selected car.",
         "Target: Nov 10"),
        ("4", "Ablation, decay, out-of-sample",
         "Component drop-one ablation, rolling-window retrain, regime-shift note. Residual values as stretch chapter if licensing permits.",
         "Target: Nov 15"),
    ]

    col_w = Inches(2.25); gap = Inches(0.13); base_l = Inches(0.4); base_t = Inches(1.5)
    for i, (num, title, body, target) in enumerate(steps):
        l = base_l + (col_w + gap) * i
        _shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, l, base_t, col_w, Inches(3.3), fill=WHITE)
        _shape(s, MSO_SHAPE.OVAL, l + Inches(0.2), base_t + Inches(0.2),
               Inches(0.6), Inches(0.6), fill=TEAL)
        _tb(s, l + Inches(0.2), base_t + Inches(0.3), Inches(0.6), Inches(0.4),
            num, size=18, bold=True, color=WHITE, font=TITLE_FONT, align=PP_ALIGN.CENTER)
        _tb(s, l + Inches(0.9), base_t + Inches(0.32), col_w - Inches(1.0), Inches(0.4),
            title, size=11, bold=True, color=NAVY, font=TITLE_FONT)
        _tb(s, l + Inches(0.2), base_t + Inches(1.0), col_w - Inches(0.4), Inches(1.9),
            body, size=9, color=GREY, font=BODY_FONT)
        _tb(s, l + Inches(0.2), base_t + Inches(2.85), col_w - Inches(0.4), Inches(0.3),
            target, size=9, bold=True, color=TEAL_DARK, font=BODY_FONT)

    # closing line (nudged up slightly to clear the footer)
    _shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.4), Inches(4.9), Inches(9.2), Inches(0.32), fill=NAVY)
    _tb(s, Inches(0.6), Inches(4.95), Inches(9), Inches(0.24),
        "The dashboard is the product. The index is what makes it defensible.",
        size=10, bold=True, color=LIME, font=BODY_FONT)

    _footer(s, 11)


# ------------------------------------------------------------------
# main
# ------------------------------------------------------------------
def main():
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H

    slide_1_cover(prs)
    slide_2_overview(prs)
    slide_3_progress(prs)
    slide_4_data(prs)
    slide_5_index(prs)
    slide_6_channel(prs)
    slide_7_baidu(prs)
    slide_8_eval(prs)
    slide_9_models(prs)
    slide_10_risks(prs)
    slide_11_next(prs)

    out = OUT / "ChargeAhead_Mid_Semester.pptx"
    prs.save(out)
    print(f"wrote {out}  slides={len(prs.slides)}")


if __name__ == "__main__":
    main()

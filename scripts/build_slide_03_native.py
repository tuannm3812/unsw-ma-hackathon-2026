#!/usr/bin/env python3
"""Build Slide 3 (Project Blueprint / Table of Contents) as native Google Slides elements.

Uses strictly Google Sans and Courier New, following docs/presentation/DESIGN.md.
"""
import json
import subprocess
from pathlib import Path

PRES_ID = "17rHwKFXiqN4GBo8TT5xnBWk33bN7niIodw9K9APNwDk"
SLIDE_ID = "SLIDES_API349037430_0"
OLD_IMG_ID = "SLIDES_API2144309192_0"

EMU_PER_INCH = 914400
EMU_PER_PT = 12700

def to_emu_in(inches):
    return int(inches * EMU_PER_INCH)

def to_emu_pt(pts):
    return int(pts * EMU_PER_PT)

def rgb(r, g, b):
    return {"red": r / 255.0, "green": g / 255.0, "blue": b / 255.0}

C_YELLOW = rgb(0xFF, 0xDD, 0x04)
C_INK = rgb(0x1C, 0x23, 0x33)
C_BLUE = rgb(0x31, 0x68, 0x8E)
C_MUTED = rgb(0x6E, 0x72, 0x78)
C_WHITE = rgb(0xFF, 0xFF, 0xFF)
C_CARD_BG = rgb(0xFF, 0xFF, 0xFF)
C_CARD_BORDER = rgb(0xE2, 0xE0, 0xD6)
C_PANEL_BG = rgb(0xF3, 0xF2, 0xED)

requests = []

# 1. Delete old raster image if present
requests.append({
    "deleteObject": {
        "objectId": OLD_IMG_ID
    }
})

# 2. Eyebrow Textbox
id_eyebrow = "slide3_eyebrow"
requests.append({
    "createShape": {
        "objectId": id_eyebrow,
        "shapeType": "TEXT_BOX",
        "elementProperties": {
            "pageObjectId": SLIDE_ID,
            "size": {"width": {"magnitude": to_emu_in(8.0), "unit": "EMU"},
                     "height": {"magnitude": to_emu_in(0.35), "unit": "EMU"}},
            "transform": {"scaleX": 1, "scaleY": 1,
                          "translateX": to_emu_in(0.75), "translateY": to_emu_in(0.48), "unit": "EMU"}
        }
    }
})
requests.append({
    "insertText": {
        "objectId": id_eyebrow,
        "text": "TABLE OF CONTENTS · PROJECT BLUEPRINT\n"
    }
})
requests.append({
    "updateTextStyle": {
        "objectId": id_eyebrow,
        "style": {
            "fontFamily": "Courier New",
            "fontSize": {"magnitude": 11, "unit": "PT"},
            "bold": True,
            "foregroundColor": {"opaqueColor": {"rgbColor": C_BLUE}}
        },
        "fields": "fontFamily,fontSize,bold,foregroundColor"
    }
})

# 3. Active chip in top right
id_chip = "slide3_chip"
requests.append({
    "createShape": {
        "objectId": id_chip,
        "shapeType": "ROUNDED_RECTANGLE",
        "elementProperties": {
            "pageObjectId": SLIDE_ID,
            "size": {"width": {"magnitude": to_emu_in(1.3), "unit": "EMU"},
                     "height": {"magnitude": to_emu_in(0.36), "unit": "EMU"}},
            "transform": {"scaleX": 1, "scaleY": 1,
                          "translateX": to_emu_in(11.28), "translateY": to_emu_in(0.48), "unit": "EMU"}
        }
    }
})
requests.append({
    "updateShapeProperties": {
        "objectId": id_chip,
        "shapeProperties": {
            "shapeBackgroundFill": {"solidFill": {"color": {"rgbColor": C_YELLOW}}},
            "outline": {"propertyState": "NOT_RENDERED"},
            "contentAlignment": "MIDDLE"
        },
        "fields": "shapeBackgroundFill,outline,contentAlignment"
    }
})
requests.append({
    "insertText": {
        "objectId": id_chip,
        "text": "OVERVIEW\n"
    }
})
requests.append({
    "updateTextStyle": {
        "objectId": id_chip,
        "style": {
            "fontFamily": "Courier New",
            "fontSize": {"magnitude": 10.5, "unit": "PT"},
            "bold": True,
            "foregroundColor": {"opaqueColor": {"rgbColor": C_INK}}
        },
        "fields": "fontFamily,fontSize,bold,foregroundColor"
    }
})
requests.append({
    "updateParagraphStyle": {
        "objectId": id_chip,
        "style": {"alignment": "CENTER"},
        "fields": "alignment"
    }
})

# 4. Slide Title
id_title = "slide3_title"
requests.append({
    "createShape": {
        "objectId": id_title,
        "shapeType": "TEXT_BOX",
        "elementProperties": {
            "pageObjectId": SLIDE_ID,
            "size": {"width": {"magnitude": to_emu_in(10.5), "unit": "EMU"},
                     "height": {"magnitude": to_emu_in(0.65), "unit": "EMU"}},
            "transform": {"scaleX": 1, "scaleY": 1,
                          "translateX": to_emu_in(0.75), "translateY": to_emu_in(0.88), "unit": "EMU"}
        }
    }
})
requests.append({
    "insertText": {
        "objectId": id_title,
        "text": "How the 1.45M loan investigation is structured\n"
    }
})
requests.append({
    "updateTextStyle": {
        "objectId": id_title,
        "style": {
            "fontFamily": "Google Sans",
            "fontSize": {"magnitude": 30, "unit": "PT"},
            "bold": True,
            "foregroundColor": {"opaqueColor": {"rgbColor": C_INK}}
        },
        "fields": "fontFamily,fontSize,bold,foregroundColor"
    }
})

# 5. Title accent bar
id_bar = "slide3_accent_bar"
requests.append({
    "createShape": {
        "objectId": id_bar,
        "shapeType": "RECTANGLE",
        "elementProperties": {
            "pageObjectId": SLIDE_ID,
            "size": {"width": {"magnitude": to_emu_in(0.85), "unit": "EMU"},
                     "height": {"magnitude": to_emu_in(0.06), "unit": "EMU"}},
            "transform": {"scaleX": 1, "scaleY": 1,
                          "translateX": to_emu_in(0.75), "translateY": to_emu_in(1.68), "unit": "EMU"}
        }
    }
})
requests.append({
    "updateShapeProperties": {
        "objectId": id_bar,
        "shapeProperties": {
            "shapeBackgroundFill": {"solidFill": {"color": {"rgbColor": C_YELLOW}}},
            "outline": {"propertyState": "NOT_RENDERED"}
        },
        "fields": "shapeBackgroundFill,outline"
    }
})

# 6. Four Column Cards
sections = [
    {
        "tag": "ACT I · CONTEXT",
        "slides": "SLIDES 4–5",
        "title": "The Operating Reality",
        "sub": "Why narrative advice is pitched, and what really happens on the ground.",
        "points": [
            ("The Platform Dilemma", "Text is the only unsealed lever at listing; platforms want to coach it."),
            ("Market Slowdown", "Same-day funding collapsed from 46% to 30% post-pandemic."),
            ("Capital Reality", "96.4% pre-disbursed; partner working capital waits, not borrowers.")
        ]
    },
    {
        "tag": "ACT II · INFERENCE",
        "slides": "SLIDES 6–9",
        "title": "Empirical Stress-Test",
        "sub": "Testing narrative claims against 1.45M loans with econometric rigor.",
        "points": [
            ("Methodological Screen", "64 of 120 coefficients collapse under country-clustering."),
            ("Structural Dominance", "Amount, terms, and sector beat storytelling by ~10×."),
            ("Narrative Scrutiny", "Urgency dissolves (p ≈ 0.49); family rests on 2-country screen."),
            ("Topic Modeling", "Topics track loan purpose (water vs farming; 9× swing).")
        ]
    },
    {
        "tag": "ACT III · STRATEGY",
        "slides": "SLIDES 10–12",
        "title": "The Strategic Playbook",
        "sub": "High-ROI platform decisions, borrower realism, and epistemic bounds.",
        "points": [
            ("4-Quadrant Playbook", "Kill generic tips, A/B test family framing, fix structural lag."),
            ("Borrower Realism", "Set cash-flow expectations; do NOT game gender or story."),
            ("Scientific Bounds", "Observational associations, completed-loans survival truncation.")
        ]
    },
    {
        "tag": "APPENDIX · AUDITS",
        "slides": "SLIDES 14–17",
        "title": "Methodological Audits",
        "sub": "Full numerical proofs and statistical architecture for defense.",
        "points": [
            ("Two-Country Problem", "The conservative t(1) = 12.7 heuristic screen in full."),
            ("Predictive vs Causal", "Why SHAP importance cannot certify policy rules."),
            ("The ~10× Comparison", "Decile monotonicities and correlation breakdown."),
            ("24h Early Warning", "LightGBM classifier architecture (ROC AUC 0.8997).")
        ]
    }
]

left_margin = 0.75
col_w = 2.80
col_gap = 0.21
top_cards = 1.95
card_h = 3.95

for idx, sec in enumerate(sections):
    card_x = left_margin + idx * (col_w + col_gap)
    card_id = f"slide3_card_{idx+1}"

    # Create Rounded Rectangle Card
    requests.append({
        "createShape": {
            "objectId": card_id,
            "shapeType": "ROUNDED_RECTANGLE",
            "elementProperties": {
                "pageObjectId": SLIDE_ID,
                "size": {"width": {"magnitude": to_emu_in(col_w), "unit": "EMU"},
                         "height": {"magnitude": to_emu_in(card_h), "unit": "EMU"}},
                "transform": {"scaleX": 1, "scaleY": 1,
                              "translateX": to_emu_in(card_x), "translateY": to_emu_in(top_cards), "unit": "EMU"}
            }
        }
    })
    requests.append({
        "updateShapeProperties": {
            "objectId": card_id,
            "shapeProperties": {
                "shapeBackgroundFill": {"solidFill": {"color": {"rgbColor": C_CARD_BG}}},
                "outline": {
                    "solidFill": {"color": {"rgbColor": C_CARD_BORDER}},
                    "weight": {"magnitude": to_emu_pt(1.0), "unit": "EMU"},
                    "dashStyle": "SOLID"
                },
                "contentAlignment": "TOP"
            },
            "fields": "shapeBackgroundFill,outline,contentAlignment"
        }
    })

    # Prepare text blocks
    text_content = ""
    # 0: Tag
    p_tag = sec["tag"] + "\n"
    # 1: Slide range
    p_sl = sec["slides"] + "\n"
    # 2: Title
    p_t = sec["title"] + "\n"
    # 3: Subtitle
    p_sub = sec["sub"] + "\n\n"

    text_content = p_tag + p_sl + p_t + p_sub

    # Add points
    point_spans = []
    for head, desc in sec["points"]:
        start_pt = len(text_content)
        bullet_str = "▪ "
        head_str = f"{head}: "
        desc_str = f"{desc}\n\n"
        full_pt = bullet_str + head_str + desc_str
        text_content += full_pt
        point_spans.append((start_pt, len(bullet_str), len(head_str), len(desc_str)))

    requests.append({
        "insertText": {
            "objectId": card_id,
            "text": text_content
        }
    })

    # Style Tag
    requests.append({
        "updateTextStyle": {
            "objectId": card_id,
            "textRange": {"startIndex": 0, "endIndex": len(p_tag)},
            "style": {
                "fontFamily": "Courier New",
                "fontSize": {"magnitude": 9.5, "unit": "PT"},
                "bold": True,
                "foregroundColor": {"opaqueColor": {"rgbColor": C_BLUE}}
            },
            "fields": "fontFamily,fontSize,bold,foregroundColor"
        }
    })

    # Style Slide Range
    idx1 = len(p_tag)
    idx2 = idx1 + len(p_sl)
    requests.append({
        "updateTextStyle": {
            "objectId": card_id,
            "textRange": {"startIndex": idx1, "endIndex": idx2},
            "style": {
                "fontFamily": "Courier New",
                "fontSize": {"magnitude": 8.5, "unit": "PT"},
                "bold": True,
                "foregroundColor": {"opaqueColor": {"rgbColor": C_MUTED}}
            },
            "fields": "fontFamily,fontSize,bold,foregroundColor"
        }
    })

    # Style Title
    idx3 = idx2 + len(p_t)
    requests.append({
        "updateTextStyle": {
            "objectId": card_id,
            "textRange": {"startIndex": idx2, "endIndex": idx3},
            "style": {
                "fontFamily": "Google Sans",
                "fontSize": {"magnitude": 13.5, "unit": "PT"},
                "bold": True,
                "foregroundColor": {"opaqueColor": {"rgbColor": C_INK}}
            },
            "fields": "fontFamily,fontSize,bold,foregroundColor"
        }
    })

    # Style Subtitle
    idx4 = idx3 + len(p_sub)
    requests.append({
        "updateTextStyle": {
            "objectId": card_id,
            "textRange": {"startIndex": idx3, "endIndex": idx4},
            "style": {
                "fontFamily": "Google Sans",
                "fontSize": {"magnitude": 9.5, "unit": "PT"},
                "italic": True,
                "foregroundColor": {"opaqueColor": {"rgbColor": C_MUTED}}
            },
            "fields": "fontFamily,fontSize,italic,foregroundColor"
        }
    })

    # Style points
    for s_pt, l_b, l_h, l_d in point_spans:
        # Bullet ▪
        requests.append({
            "updateTextStyle": {
                "objectId": card_id,
                "textRange": {"startIndex": s_pt, "endIndex": s_pt + l_b},
                "style": {
                    "fontFamily": "Google Sans",
                    "fontSize": {"magnitude": 10, "unit": "PT"},
                    "bold": True,
                    "foregroundColor": {"opaqueColor": {"rgbColor": C_YELLOW}}
                },
                "fields": "fontFamily,fontSize,bold,foregroundColor"
            }
        })
        # Lead-in
        requests.append({
            "updateTextStyle": {
                "objectId": card_id,
                "textRange": {"startIndex": s_pt + l_b, "endIndex": s_pt + l_b + l_h},
                "style": {
                    "fontFamily": "Google Sans",
                    "fontSize": {"magnitude": 9.5, "unit": "PT"},
                    "bold": True,
                    "foregroundColor": {"opaqueColor": {"rgbColor": C_INK}}
                },
                "fields": "fontFamily,fontSize,bold,foregroundColor"
            }
        })
        # Description
        requests.append({
            "updateTextStyle": {
                "objectId": card_id,
                "textRange": {"startIndex": s_pt + l_b + l_h, "endIndex": s_pt + l_b + l_h + l_d},
                "style": {
                    "fontFamily": "Google Sans",
                    "fontSize": {"magnitude": 9.5, "unit": "PT"},
                    "bold": False,
                    "foregroundColor": {"opaqueColor": {"rgbColor": C_INK}}
                },
                "fields": "fontFamily,fontSize,bold,foregroundColor"
            }
        })

# 7. Bottom Methodology Stack Banner
id_banner = "slide3_banner"
requests.append({
    "createShape": {
        "objectId": id_banner,
        "shapeType": "ROUNDED_RECTANGLE",
        "elementProperties": {
            "pageObjectId": SLIDE_ID,
            "size": {"width": {"magnitude": to_emu_in(11.833), "unit": "EMU"},
                     "height": {"magnitude": to_emu_in(0.92), "unit": "EMU"}},
            "transform": {"scaleX": 1, "scaleY": 1,
                          "translateX": to_emu_in(0.75), "translateY": to_emu_in(6.05), "unit": "EMU"}
        }
    }
})
requests.append({
    "updateShapeProperties": {
        "objectId": id_banner,
        "shapeProperties": {
            "shapeBackgroundFill": {"solidFill": {"color": {"rgbColor": C_PANEL_BG}}},
            "outline": {
                "solidFill": {"color": {"rgbColor": C_YELLOW}},
                "weight": {"magnitude": to_emu_pt(1.5), "unit": "EMU"},
                "dashStyle": "SOLID"
            },
            "contentAlignment": "MIDDLE"
        },
        "fields": "shapeBackgroundFill,outline,contentAlignment"
    }
})

b_h = "PORTFOLIO METHODOLOGY & REPRODUCIBILITY STACK · 1,453,846 REAL LOANS (2016–2025)\n"
b_t = "Econometric OLS Duration Modeling · Binomial GLM · Country-Clustered Standard Errors · Conservative Few-Cluster t(1)=12.7 Screen · NMF Topic Extraction (8 Components) · LightGBM Predictive Benchmark (Strict Chronological Split, Zero Future Leakage)\n"

requests.append({
    "insertText": {
        "objectId": id_banner,
        "text": b_h + b_t
    }
})
requests.append({
    "updateTextStyle": {
        "objectId": id_banner,
        "textRange": {"startIndex": 0, "endIndex": len(b_h)},
        "style": {
            "fontFamily": "Courier New",
            "fontSize": {"magnitude": 9.5, "unit": "PT"},
            "bold": True,
            "foregroundColor": {"opaqueColor": {"rgbColor": C_INK}}
        },
        "fields": "fontFamily,fontSize,bold,foregroundColor"
    }
})
requests.append({
    "updateTextStyle": {
        "objectId": id_banner,
        "textRange": {"startIndex": len(b_h), "endIndex": len(b_h) + len(b_t)},
        "style": {
            "fontFamily": "Google Sans",
            "fontSize": {"magnitude": 9.5, "unit": "PT"},
            "bold": False,
            "foregroundColor": {"opaqueColor": {"rgbColor": C_INK}}
        },
        "fields": "fontFamily,fontSize,bold,foregroundColor"
    }
})

# 8. Bottom Full-width Yellow Footer Bar
id_foot = "slide3_footer"
requests.append({
    "createShape": {
        "objectId": id_foot,
        "shapeType": "RECTANGLE",
        "elementProperties": {
            "pageObjectId": SLIDE_ID,
            "size": {"width": {"magnitude": to_emu_in(13.333), "unit": "EMU"},
                     "height": {"magnitude": to_emu_in(0.35), "unit": "EMU"}},
            "transform": {"scaleX": 1, "scaleY": 1,
                          "translateX": 0, "translateY": to_emu_in(7.15), "unit": "EMU"}
        }
    }
})
requests.append({
    "updateShapeProperties": {
        "objectId": id_foot,
        "shapeProperties": {
            "shapeBackgroundFill": {"solidFill": {"color": {"rgbColor": C_YELLOW}}},
            "outline": {"propertyState": "NOT_RENDERED"}
        },
        "fields": "shapeBackgroundFill,outline"
    }
})

id_foot_txt = "slide3_foot_txt"
requests.append({
    "createShape": {
        "objectId": id_foot_txt,
        "shapeType": "TEXT_BOX",
        "elementProperties": {
            "pageObjectId": SLIDE_ID,
            "size": {"width": {"magnitude": to_emu_in(10.0), "unit": "EMU"},
                     "height": {"magnitude": to_emu_in(0.35), "unit": "EMU"}},
            "transform": {"scaleX": 1, "scaleY": 1,
                          "translateX": to_emu_in(0.75), "translateY": to_emu_in(7.15), "unit": "EMU"}
        }
    }
})
requests.append({
    "insertText": {
        "objectId": id_foot_txt,
        "text": "UNSW Marketing Analytics Hackathon 2026\n"
    }
})
requests.append({
    "updateTextStyle": {
        "objectId": id_foot_txt,
        "style": {
            "fontFamily": "Courier New",
            "fontSize": {"magnitude": 10, "unit": "PT"},
            "bold": True,
            "foregroundColor": {"opaqueColor": {"rgbColor": C_INK}}
        },
        "fields": "fontFamily,fontSize,bold,foregroundColor"
    }
})

batch_file = Path("/tmp/slide3_batch.json")
with open(batch_file, "w") as f:
    json.dump({"requests": requests}, f, indent=2)

print(f"Generated {len(requests)} operations in {batch_file}")

#!/usr/bin/env python3
"""Render a selected research timeline using titles and dates from the README."""
from html import escape
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
CATEGORIES = {
    'F': ('Foundations', '#a5b4fc'),
    'P': ('Primitives', '#67e8f9'),
    'S': ('Search', '#fbbf24'),
    'O': ('Online evolution', '#6ee7b7'),
    'R': ('Recursive evolution', '#c4b5fd'),
    'T': ('Training / co-evolution', '#f9a8d4'),
    'E': ('Evaluation / critique', '#fda4af'),
}
# (arXiv ID or source URL, short display title, direction). Dates come from README.
COLUMNS = [
    ('2022–2023', 'Loops & programs', [
        ('2210.03629', 'ReAct', 'F'),
        ('2307.16789', 'ToolLLM', 'P'),
        ('2310.02304', 'STOP', 'R'),
        ('2310.03714', 'DSPy', 'S'),
    ]),
    ('2024', 'Searchable scaffolds', [
        ('2402.16823', 'GPTSwarm', 'F'),
        ('2405.15793', 'SWE-agent', 'P'),
        ('2406.07496', 'TextGrad', 'S'),
        ('2408.08435', 'ADAS', 'S'),
        ('2408.09559', 'HiAgent', 'P'),
        ('2410.04444', 'Gödel Agent', 'R'),
        ('2410.10762', 'AFlow', 'S'),
    ]),
    ('2025', 'Self-modifying agents', [
        ('2504.07079', 'SkillWeaver', 'P'),
        ('2504.19413', 'Mem0', 'P'),
        ('2505.22954', 'Darwin Gödel Machine', 'R'),
        ('2507.03616', 'EvoAgentX', 'S'),
        ('2510.10232', 'Statistical Gödel Machine', 'R'),
        ('2511.13646', 'Live-SWE-agent', 'O'),
        ('2512.18746', 'MemEvolve', 'R'),
    ]),
    ('2026 · JAN–JUN', 'The harness as an object', [
        ('2603.03329', 'AutoHarness', 'S'),
        ('2603.28052', 'Meta-Harness', 'S'),
        ('2604.21003', 'The Last Harness', 'R'),
        ('2605.09998', 'Continual Harness', 'O'),
        ('2605.27922', 'Harness-Bench', 'E'),
        ('2606.09498', 'Self-Harness', 'O'),
        ('https://ornith.ai/ornith_1_0.html', 'Ornith-1.0', 'T'),
    ]),
    ('2026 · JUL', 'Evolution under scrutiny', [
        ('2607.05297', 'MetaSkill-Evolve', 'R'),
        ('2607.08124', 'TTHE', 'O'),
        ('2607.12227', 'Rethinking Evaluation', 'E'),
        ('2607.13683', 'HarnessBank', 'S'),
        ('2607.14004', 'Do Optimizers Compound?', 'E'),
        ('2607.15524', 'Recursive Harness SI', 'T'),
    ]),
    ('2026 · AUG–SEP', 'Learning to evolve', [
        ('2608.02276', 'Harness-R1', 'T'),
        ('2608.06301', 'HarnessOpt-Bench', 'E'),
        ('2608.13951', 'HELIX', 'T'),
        ('2608.25593', 'JIT-Agent', 'S'),
        ('2609.00196', 'WHALE', 'T'),
        ('2609.01437', 'HarnessDev', 'E'),
        ('2609.06396', 'MetaRSI / RSI2', 'R'),
    ]),
]


def main():
    entries = {}
    for title, url, date in re.findall(
        r'^1\. (.+?) \[\[(?:Paper|Blog)\]\]\((https?://[^)]+)\) '
        r'`(?:arXiv|Preprint|Blog) (\d{4}-\d{2})`$',
        (ROOT / 'README.md').read_text(), re.M,
    ):
        entries[url.rsplit('/', 1)[-1] if 'arxiv.org/abs/' in url else url] = (title, url, date)

    svg = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1440" height="930" viewBox="0 0 1440 930" role="img" aria-labelledby="title desc">',
        '<title id="title">Harness Evolution: Selected Research Timeline</title>',
        '<desc id="desc">Selected works from 2022 to September 2026, grouped by first-submission period and research direction. Unequal time intervals; no performance ranking.</desc>',
        '<rect width="1440" height="930" rx="20" fill="#0b1220"/>',
        '<style>text{font-family:Arial,Helvetica,sans-serif} .card{fill:#132033;stroke:#27364b} .paper{font-size:14px;font-weight:600;fill:#f1f5f9} .muted{fill:#9baec6;font-size:13px}</style>',
        '<text x="32" y="42" fill="#67e8f9" font-size="12" letter-spacing="3">AWESOME HARNESS EVOLUTION</text>',
        '<text x="32" y="85" fill="#f8fafc" font-size="32" font-weight="700">From agent loops to recursive self-improvement</text>',
        '<text x="32" y="116" class="muted">Selected research · first-submission dates · full bibliography and reading notes below</text>',
        '<path d="M32 180 H1400 l-10 -5 m10 5 l-10 5" fill="none" stroke="#526b87" stroke-width="2"/>',
    ]
    for col, (period, subtitle, papers) in enumerate(COLUMNS):
        x = 32 + col * 230
        svg.extend([
            f'<circle cx="{x+8}" cy="180" r="5" fill="#67e8f9"/>',
            f'<text x="{x}" y="156" fill="#e2e8f0" font-size="17" font-weight="700">{escape(period)}</text>',
            f'<text x="{x}" y="210" class="muted">{escape(subtitle)}</text>',
        ])
        ordered = sorted(papers, key=lambda paper: entries[paper[0]][2])
        for row, (key, short, category) in enumerate(ordered):
            title, url, date = entries[key]
            valid_period = (date[:4] in ('2022', '2023') if col == 0 else
                            date[:4] == '2024' if col == 1 else
                            date[:4] == '2025' if col == 2 else
                            '2026-01' <= date <= '2026-06' if col == 3 else
                            date == '2026-07' if col == 4 else
                            '2026-08' <= date <= '2026-09')
            assert valid_period, (short, date, period)
            label, color = CATEGORIES[category]
            y = 238 + row * 72
            svg.extend([
                f'<a href="{escape(url, quote=True)}"><title>{escape(title)} — {escape(label)}, {date}</title>',
                f'<rect x="{x}" y="{y}" width="216" height="62" rx="7" class="card"/>',
                f'<rect x="{x}" y="{y+10}" width="3" height="42" rx="1.5" fill="{color}"/>',
                f'<text x="{x+12}" y="{y+25}" class="paper">{escape(short)}</text>',
                f'<text x="{x+12}" y="{y+47}" class="muted">{date}</text>',
                f'<rect x="{x+181}" y="{y+32}" width="23" height="19" rx="4" fill="{color}"/>',
                f'<text x="{x+192.5}" y="{y+46}" text-anchor="middle" fill="#0b1220" font-size="12" font-weight="700">{category}</text></a>',
            ])
    svg.append('<path d="M32 770 H1408" stroke="#27364b"/>')
    for i, (key, (label, color)) in enumerate(CATEGORIES.items()):
        x, y = 32 + (i % 4) * 346, 809 + (i // 4) * 37
        svg.extend([
            f'<rect x="{x}" y="{y-16}" width="23" height="22" rx="4" fill="{color}"/>',
            f'<text x="{x+11.5}" y="{y}" text-anchor="middle" font-size="13" font-weight="700" fill="#0b1220">{key}</text>',
            f'<text x="{x+34}" y="{y}" font-size="15" fill="#d7e2f0">{escape(label)}</text>',
        ])
    svg.extend([
        '<text x="32" y="900" class="muted">Reading map, not a leaderboard. Time bins have unequal duration; chronology does not establish capability gains.</text>',
        '</svg>',
    ])
    (ROOT / 'assets/research-timeline.svg').write_text('\n'.join(svg) + '\n')
    print(f'Timeline: {sum(len(items) for _, _, items in COLUMNS)} works, all resolved from README.')


if __name__ == '__main__':
    main()

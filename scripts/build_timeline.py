#!/usr/bin/env python3
"""Build the README's curved, categorized paper timeline from its bibliography."""
from html import escape
from pathlib import Path
import base64
import json
import math
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
# Label, icon color, card background. The two groups share the same chronology.
CATEGORIES = {
    'F': ('Foundations', '#dc3545', '#fff1f2'),
    'P': ('Harness primitives', '#16994c', '#effdf4'),
    'T': ('Harness engineering training', '#089bb8', '#ecfcff'),
    'E': ('Evaluation & critique', '#5368c9', '#f1f3ff'),
    'S': ('Search & optimization', '#ef6515', '#fff8ef'),
    'O': ('Online evolution', '#149953', '#effdf4'),
    'R': ('Recursive evolution', '#923bea', '#faf1ff'),
    'C': ('Model–harness co-evolution', '#d63e80', '#fff0f7'),
}
# Each row: source ID, display label, category. Labels are abbreviations;
# full titles, links and first-submission dates are resolved from README.
PERIODS = [
    ('≤ 2024', '0000-01', '2024-12', {
        'top': [
            ('2210.03629', 'ReAct', 'F'),
            ('2307.16789', 'ToolLLM', 'P'),
            ('2310.03714', 'DSPy', 'F'),
            ('2402.16823', 'GPTSwarm', 'F'),
            ('2405.15793', 'SWE-agent', 'P'),
            ('2406.07496', 'TextGrad', 'F'),
            ('2407.19056', 'OfficeBench', 'E'),
            ('2408.09559', 'HiAgent', 'P'),
        ],
        'bottom': [
            ('2310.02304', 'STOP', 'R'),
            ('2406.14228', 'EvoAgent', 'S'),
            ('2408.08435', 'ADAS', 'S'),
            ('2410.04444', 'Gödel Agent', 'R'),
            ('2410.06153', 'AgentSquare', 'S'),
            ('2410.10762', 'AFlow', 'S'),
        ],
    }),
    ('2025', '2025-01', '2025-12', {
        'top': [
            ('2503.09572', 'Plan-and-Act', 'P'),
            ('2504.07079', 'SkillWeaver', 'P'),
            ('2504.13958', 'ToolRL', 'T'),
            ('2504.19413', 'Mem0', 'P'),
            ('2507.02652', 'HiRA', 'P'),
            ('2508.09124', 'OdysseyBench', 'E'),
            ('2509.13313', 'ReSum', 'P'),
            ('2510.11977', 'HAL', 'E'),
            ('2510.24699', 'AgentFold', 'P'),
            ('2512.24615', 'Youtu-Agent', 'T'),
        ],
        'bottom': [
            ('2502.00757', 'AgentBreeder', 'S'),
            ('2502.04180', 'Agentic Supernet', 'S'),
            ('2505.22954', 'Darwin Gödel Machine', 'R'),
            ('2506.06017', 'AgentSwift', 'S'),
            ('2507.03616', 'EvoAgentX', 'S'),
            ('2510.10232', 'Statistical Gödel Machine', 'R'),
            ('2511.13646', 'Live-SWE-agent', 'O'),
            ('2512.18746', 'MemEvolve', 'R'),
        ],
    }),
    ('2026 · Q1', '2026-01', '2026-03', {
        'top': [
            ('2601.02163', 'EverMemOS', 'P'),
            ('2601.08079', 'MemoBrain', 'P'),
            ('2601.11868', 'Terminal-Bench', 'E'),
            ('2601.20975', 'DeepSearchQA', 'E'),
            ('2602.01848', 'ROMA', 'P'),
            ('2602.03786', 'AOrchestra', 'P'),
            ('2602.07883', 'ToolSelf', 'T'),
            ('2602.17100', 'AgentConductor', 'T'),
        ],
        'bottom': [
            ('2602.07839', 'TodoEvolve', 'S'),
            ('2602.23413', 'EvoX', 'R'),
            ('2603.03329', 'AutoHarness', 'S'),
            ('2603.28052', 'Meta-Harness', 'S'),
            ('2603.28342', 'Kernel-Smith', 'S'),
        ],
    }),
    ('2026 · Q2', '2026-04', '2026-06', {
        'top': [
            ('2604.08224', 'Externalization', 'F'),
            ('2605.08693', 'SkillMaster', 'T'),
            ('2605.18747', 'Code as Agent Harness', 'F'),
            ('2605.27922', 'Harness-Bench', 'E'),
            ('2606.10106', 'What Makes a Harness?', 'F'),
            ('2606.17546', 'SEAGym', 'E'),
        ],
        'bottom': [
            ('2604.20938', 'HARBOR', 'S'),
            ('2604.21003', 'The Last Harness', 'R'),
            ('2604.25850', 'Agentic Harness Eng.', 'S'),
            ('2605.09998', 'Continual Harness', 'O'),
            ('2605.22794', 'MOSS', 'R'),
            ('2605.24539', 'DemoEvolve', 'O'),
            ('2605.27276', 'SIA', 'C'),
            ('2606.01314', 'SkillSmith', 'O'),
            ('2606.01770', 'Adaptive Auto-Harness', 'O'),
            ('2606.01779', 'HarnessForge', 'C'),
            ('2606.09498', 'Self-Harness', 'O'),
            ('2606.14249', 'HarnessX', 'S'),
            ('2606.26294', 'Red Queen Gödel Machine', 'R'),
            ('https://ornith.ai/ornith_1_0.html', 'Ornith-1.0', 'C'),
        ],
    }),
    ('2026 · JUL', '2026-07', '2026-07', {
        'top': [
            ('2607.05378', 'CompactionRL', 'T'),
            ('2607.12227', 'Rethinking Evaluation', 'E'),
            ('2607.14004', 'Do Optimizers Compound?', 'E'),
            ('2607.21419', 'PATS', 'T'),
            ('2607.21557', 'OpenForgeRL', 'T'),
        ],
        'bottom': [
            ('2607.03935', 'Harness-Aware SE', 'C'),
            ('2607.05297', 'MetaSkill-Evolve', 'R'),
            ('2607.05458', 'Offline RL Control', 'O'),
            ('2607.08124', 'TTHE', 'O'),
            ('2607.08938', 'Better Harnesses', 'S'),
            ('2607.13285', 'Harness Handbook', 'R'),
            ('2607.13683', 'HarnessBank', 'S'),
            ('2607.14159', 'MemoHarness', 'O'),
            ('2607.15524', 'Recursive Harness SI', 'C'),
            ('2607.26598', 'Living-Harness', 'O'),
            ('2607.26722', 'DREvo', 'O'),
            ('2607.27994', 'SKIMIX', 'R'),
        ],
    }),
    ('2026 · AUG–SEP', '2026-08', '2026-09', {
        'top': [
            ('2608.02276', 'Harness-R1', 'T'),
            ('2608.05446', 'EvoHarness-RL', 'T'),
            ('2608.06301', 'HarnessOpt-Bench', 'E'),
            ('2609.01437', 'HarnessDev', 'E'),
        ],
        'bottom': [
            ('2608.01918', 'HarnessCompass', 'S'),
            ('2608.04968', 'EvolveNet', 'O'),
            ('2608.07545', 'DarwinX', 'S'),
            ('2608.07645', 'Mendel Gödel Machine', 'R'),
            ('2608.13560', 'AutoDesign', 'R'),
            ('2608.13951', 'HELIX', 'C'),
            ('2608.19013', 'Harness Continual Learning', 'O'),
            ('2608.23041', 'AutoSaddler', 'S'),
            ('2608.24804', 'StarHarness', 'S'),
            ('2608.25593', 'JIT-Agent', 'S'),
            ('2608.26530', 'PILOT in the Loop', 'O'),
            ('2608.28363', 'EvoUndo', 'O'),
            ('https://ornith.ai/ornith_1_5.html', 'Ornith-1.5', 'C'),
            ('2609.00196', 'WHALE', 'C'),
            ('2609.00829', 'HarnessEvolve', 'O'),
            ('2609.02786', 'SafeEvolve', 'C'),
            ('2609.06396', 'MetaRSI / RSI2', 'R'),
            ('2609.11677', 'Ecdysis', 'S'),
        ],
    }),
]


def curve(x):
    return 690 - 490 * (x / 1560) ** 0.55


def icon(kind, x, y, color):
    shapes = {
        'F': '<rect x="3" y="1" width="15" height="20" rx="1"/><path d="M7 6h7M7 10h7M7 14h7"/>',
        'P': '<rect x="1" y="3" width="20" height="6" rx="1"/><rect x="1" y="13" width="20" height="6" rx="1"/>',
        'T': '<circle cx="11" cy="11" r="10"/><circle cx="11" cy="11" r="6"/><circle cx="11" cy="11" r="2"/>',
        'E': '<path d="M2 20V2M2 20h19M6 16v-4M12 16V8M18 16V3"/>',
        'S': '<path d="M3 11h16"/><rect x="1" y="8" width="5" height="6" fill="currentColor" stroke="none"/><rect x="9" y="8" width="5" height="6" fill="currentColor" stroke="none"/><rect x="17" y="8" width="5" height="6" fill="currentColor" stroke="none"/>',
        'O': '<path d="M19 7A9 9 0 1 0 20 14M19 1v7h-7"/>',
        'R': '<path d="M11 7C-3 -5 -3 27 11 15C25 3 25 25 11 15C-3 3 -3 25 11 15C25 3 25 -5 11 7"/>',
        'C': '<path d="M5 2v18M17 2v18M5 6h12M5 16h12M8 3L5 0L2 3M14 19l3 3l3-3"/>',
    }
    return f'<g transform="translate({x},{y})" color="{color}" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none">{shapes[kind]}</g>'


def main():
    affiliations = json.loads((ROOT / 'assets/timeline-affiliations.json').read_text())
    institutions = json.loads((ROOT / 'assets/institutions.json').read_text())
    entries = {}
    for title, url, date in re.findall(
        r'^1\. (.+?) \[\[(?:Paper|Blog)\]\]\((https?://[^)]+)\) '
        r'`(?:arXiv|Preprint|Blog) (\d{4}-\d{2})`$',
        (ROOT / 'README.md').read_text(), re.M,
    ):
        entries[url.rsplit('/', 1)[-1] if 'arxiv.org/abs/' in url else url] = (title, url, date)
    svg = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1090" viewBox="0 0 1600 1090" role="img" aria-labelledby="title desc">',
        '<title id="title">Timeline of Harness Evolution Research</title>',
        '<desc id="desc">Selected papers arranged around a curved timeline. Above: foundations, primitives, training and evaluation. Below: search, online evolution, recursive evolution and model–harness co-evolution. First-submission periods, not a quantitative capability axis.</desc>',
        '<rect width="1600" height="1090" fill="#0d1117"/>',
        '<style>text{font-family:Georgia,"Times New Roman",serif}.paper{font-weight:700;fill:#182033}.date{font:11px Arial,sans-serif;fill:#697386}.small{font:13px Arial,sans-serif;fill:#adb7c5}</style>',
    ]
    seen = set()
    for col, (label, start, end, groups) in enumerate(PERIODS):
        x = 22 + col * 262
        if col:
            svg.append(f'<path d="M{x-9} 20V920" stroke="#8b949e" stroke-dasharray="6 5"/>')
        for side, papers in groups.items():
            ordered = sorted(papers, key=lambda item: (entries[item[0]][2], item[0]))
            first_y = 22 if side == 'top' else math.ceil((curve(x) + 42) / 36) * 36
            for row, (key, short, category) in enumerate(ordered):
                assert key not in seen, f'Duplicate timeline paper: {key}'
                seen.add(key)
                title, url, date = entries[key]
                assert start <= date <= end, (short, date, label)
                y = first_y + row * 36
                assert y + 31 <= (curve(x+244)-32 if side == 'top' else 936), (short, 'card exceeds available space', y)
                direction, color, bg = CATEGORIES[category]
                # Long names use two lines, preserving every word of the display label.
                words = short.split()
                if len(short) > 19:
                    split = min(range(1, len(words)), key=lambda k: abs(len(' '.join(words[:k]))-len(' '.join(words[k:]))))
                    labels = [' '.join(words[:split]), ' '.join(words[split:])]
                else:
                    labels = [short]
                svg.extend([
                    f'<a href="{escape(url, quote=True)}"><title>{escape(title)} — {escape(direction)} — {date}</title>',
                    f'<rect x="{x}" y="{y}" width="244" height="31" rx="5" fill="{bg}" stroke="#c7c9cd" stroke-width="0.6"/>',
                    icon(category, x+7, y+5, color),
                ])
                for j, text in enumerate(labels):
                    baseline = y+21 if len(labels)==1 else y+13+j*13
                    size = 16 if len(labels)==1 else 13
                    svg.append(f'<text x="{x+37}" y="{baseline}" class="paper" font-size="{size}">{escape(text)}</text>')
                affiliation = affiliations[key]
                org = institutions.get(affiliation['institution'])
                if org and org.get('logo'):
                    logo = ROOT / 'assets' / org['logo']
                    encoded = base64.b64encode(logo.read_bytes()).decode()
                    logo_width = 47 if org['aspect_ratio'] > 1.8 else 27
                    if org.get('viewbox'):
                        # Display the university mark within an official co-branded asset.
                        box = ' '.join(map(str, org['viewbox']))
                        w, h = org['source_size']
                        svg.append(f'<svg x="{x+213}" y="{y+3}" width="27" height="25" viewBox="{box}" overflow="hidden"><title>{escape(org["name"])}</title><image width="{w}" height="{h}" href="data:image/png;base64,{encoded}"/></svg>')
                    else:
                        svg.append(f'<image x="{x+240-logo_width}" y="{y+3}" width="{logo_width}" height="25" preserveAspectRatio="xMidYMid meet" href="data:image/png;base64,{encoded}"><title>{escape(org["name"])}</title></image>')
                else:
                    badge = affiliation.get('badge', affiliation['institution'])
                    svg.append(f'<text x="{x+239}" y="{y+20}" text-anchor="end" font-size="9" fill="#546176">{escape(badge)}</text>')
                svg.append('</a>')
        cx = x + 122
        cy = curve(cx)
        svg.extend([
            f'<circle cx="{cx}" cy="{cy:.1f}" r="8" fill="#f8fafc" stroke="#bfc3c8" stroke-width="3"/>',
            f'<rect x="{cx-98}" y="{cy+18:.1f}" width="196" height="26" rx="3" fill="#f5f6f8"/>',
            f'<text x="{cx}" y="{cy+37:.1f}" text-anchor="middle" font-size="18" font-weight="700" fill="#182033">{escape(label)}</text>',
        ])
    # Draw the curve behind the cards and milestone circles.
    path = ' '.join(f'{"M" if x==12 else "L"}{x},{curve(x):.2f}' for x in range(12,1581,8))
    svg.insert(5, f'<path d="{path}" fill="none" stroke="#bfc3c8" stroke-width="3"/>')
    svg.insert(6, f'<path d="M1587 {curve(1580):.1f}l-12 -4l1 10z" fill="#bfc3c8"/>')
    svg.append('<path d="M22 940H1578" stroke="#a5acb6" stroke-width="1.5"/>')
    for box_x, title, keys in [(22, 'Evolving the Harness', 'SORC'), (866, 'Foundations, Training & Evaluation', 'FPTE')]:
        width = 770 if box_x==22 else 712
        svg.extend([
            f'<rect x="{box_x}" y="960" width="{width}" height="92" rx="7" fill="#e7e9ef"/>',
            f'<text x="{box_x+width/2}" y="984" text-anchor="middle" font-weight="700" font-size="20" fill="#182033">{escape(title)}</text>',
        ])
        for i,key in enumerate(keys):
            gx = box_x+15+(i%2)*(width/2)
            gy = 999+(i//2)*27
            label,color,_ = CATEGORIES[key]
            svg.append(icon(key,gx,gy-4,color))
            svg.append(f'<text x="{gx+31}" y="{gy+13}" font-size="16" fill="#182033">{escape(label)}</text>')
    svg.extend([
        '<path d="M811 999h35l-7 -7m7 7l-7 7M846 1022h-35l7 -7m-7 7l7 7" fill="none" stroke="#aab7c7" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>',
        f'<text x="800" y="1076" text-anchor="middle" class="small">{len(seen)} selected works · logos: representative author affiliations · first-submission periods, not to scale · full bibliography below</text>',
        '</svg>',
    ])
    (ROOT / 'assets/research-timeline.svg').write_text('\n'.join(svg)+'\n')
    if '--png' in sys.argv:
        import cairosvg
        cairosvg.svg2png(url=str(ROOT / 'assets/research-timeline.svg'),
                        write_to=str(ROOT / 'assets/research-timeline.png'), scale=2)
    print(f'Timeline: {len(seen)} unique works, dates and layout bounds checked.')


if __name__ == '__main__':
    main()

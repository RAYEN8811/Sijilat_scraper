#!/usr/bin/env python3
"""
Generate publication-quality, self-contained charts for LaTeX reports.
Ensures clean, cohesive organization without requiring any external screenshots.
"""

import os
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

os.makedirs("figures", exist_ok=True)

# Set clean aesthetic style
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'Helvetica, Arial, DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#d0d7de'
plt.rcParams['axes.linewidth'] = 0.8

# -------------------------------------------------------------------------
# 1. Executive Dashboard (Unified 2-Panel Business Graphic)
# -------------------------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.4), dpi=300)

# Panel A: Operational Latency & Throughput Comparison
cats = ['Manual Portal Search\n(Analyst Browser)', 'Automated Sijilat Ingestion\n(Direct API Prototype)']
times = [480, 1.43]
colors = ['#c93b2b', '#1e7b4e']

bars1 = ax1.bar(cats, times, color=colors, width=0.48, edgecolor='#333333', linewidth=0.8)
ax1.set_ylabel('Inquiry Latency per Entity (Seconds - Log Scale)', fontsize=10, fontweight='bold', color='#24292f')
ax1.set_title('A. Ingestion Speed: 99.7% Latency Reduction', fontsize=11, fontweight='bold', pad=10, color='#1f2328')
ax1.set_yscale('log')
ax1.set_ylim(0.5, 1500)
ax1.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: f'{int(y)}s' if y >= 1 else f'{y:.1f}s'))

for bar in bars1:
    h = bar.get_height()
    label = f"{h:.2f}s" if h < 10 else f"{int(h)}s (~8 min)"
    ax1.annotate(label,
                 xy=(bar.get_x() + bar.get_width() / 2, h),
                 xytext=(0, 5),
                 textcoords="offset points",
                 ha='center', va='bottom',
                 fontsize=9.5, fontweight='bold', color='#1f2328')

ax1.axhline(60, color='#8c959f', linestyle='--', linewidth=0.8, alpha=0.7)
ax1.text(0.5, 68, '1-Minute Threshold', color='#57606a', fontsize=8.5, ha='center', style='italic')

# Panel B: Due Diligence Responsibility Matrix
labels = [
    'Automated: Registry Status\n& License Dates (25%)',
    'Automated: Physical Address\n& Activities (20%)',
    'Automated: Branch Cataloging\n& Change Logs (20%)',
    'Human Analyst: Mortgage &\nLegal Lien Forensic (15%)',
    'Human Analyst: Offshore UBO\n& Sanctions Synthesis (20%)'
]
sizes = [25, 20, 20, 15, 20]
colors_pie = ['#1e7b4e', '#2da44e', '#56d364', '#d29922', '#cf222e']
explode = (0.02, 0.02, 0.02, 0.06, 0.06)

wedges, texts, autotexts = ax2.pie(
    sizes,
    explode=explode,
    labels=labels,
    colors=colors_pie,
    autopct='%1.0f%%',
    pctdistance=0.72,
    startangle=140,
    textprops=dict(color="#1f2328", fontsize=8.5),
    wedgeprops=dict(width=0.58, edgecolor='white', linewidth=2)
)

for autotext in autotexts:
    autotext.set_color('white')
    autotext.set_fontweight('bold')
    autotext.set_fontsize(9.5)

ax2.set_title("B. Due Diligence Allocation:\n65% Automated vs. 35% Human Analysis",
              fontsize=11, fontweight='bold', pad=10, color='#1f2328')

plt.tight_layout()
fig.savefig("figures/executive_dashboard.png", dpi=300)
fig.savefig("figures/executive_dashboard.pdf")
plt.close(fig)

# -------------------------------------------------------------------------
# 2. Technical Latency Breakdown Graphic
# -------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9, 4.0), dpi=300)

components = [
    '1. Client Auth & HMAC Signature (/token)',
    '2. HTTPS Network Handshake (api.sijilat.bh)',
    '3. CompleteCRDetails Ingestion',
    '4. Branch Catalog Resolution (13 Branches)',
    '5. Field Normalization & Provenance Tagging',
    '6. Full 13-Branch Deep Crawl (--all-branches)'
]
latency_ms = [420, 180, 810, 15, 2, 10800]
colors_tech = ['#0969da', '#218bff', '#54aeff', '#8250df', '#1a7f37', '#cf222e']

bars = ax.barh(components, latency_ms, color=colors_tech, height=0.52, edgecolor='#333333', linewidth=0.6)
ax.set_xscale('log')
ax.set_xlabel('Execution Latency in Milliseconds (Logarithmic Scale)', fontsize=10, fontweight='bold', color='#24292f')
ax.set_title('Sijilat Scraper Component Latency Profile', fontsize=11, fontweight='bold', pad=12, color='#1f2328')
ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{int(x):,}ms' if x >= 1000 else f'{int(x)}ms'))

for bar in bars:
    w = bar.get_width()
    val_str = f"{w/1000:.2f}s" if w >= 1000 else f"{int(w)}ms"
    ax.annotate(f" {val_str}",
                xy=(w, bar.get_y() + bar.get_height() / 2),
                xytext=(5, 0),
                textcoords="offset points",
                ha='left', va='center',
                fontsize=8.5, fontweight='bold', color='#1f2328')

ax.set_xlim(0.8, 35000)
plt.tight_layout()
fig.savefig("figures/technical_latency_breakdown.png", dpi=300)
fig.savefig("figures/technical_latency_breakdown.pdf")
plt.close(fig)

print("[OK] Re-generated figures/executive_dashboard.png and figures/technical_latency_breakdown.png")

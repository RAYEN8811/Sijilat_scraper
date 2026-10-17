#!/usr/bin/env python3
"""
Generate publication-quality, non-overlapping charts for LaTeX reports.
Eliminates text overlap, improves spacing, and separates business and technical assets.
"""

import os
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

os.makedirs("figures_business", exist_ok=True)
os.makedirs("figures_technical", exist_ok=True)

# Aesthetic styling
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'DejaVu Sans, Arial, Helvetica'
plt.rcParams['axes.edgecolor'] = '#d0d7de'
plt.rcParams['axes.linewidth'] = 0.8

# -------------------------------------------------------------------------
# 1. Executive Dashboard (For figures_business/)
# -------------------------------------------------------------------------
# Uses 2 horizontal panels with ample spacing so labels never collide.
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.0, 4.2), dpi=300)

# Panel A: Latency Comparison (Bar Chart with clean top headroom)
categories = ['Manual Browser Search\n(Analyst Navigation)', 'Automated API Ingestion\n(Direct Sijilat Prototype)']
times = [480, 1.43]
bar_colors = ['#c93b2b', '#1e7b4e']

bars1 = ax1.bar(categories, times, color=bar_colors, width=0.45, edgecolor='#222222', linewidth=0.7)
ax1.set_ylabel('Inquiry Latency (Seconds - Log Scale)', fontsize=10, fontweight='bold', color='#24292f')
ax1.set_title('A. Operational Speed: 99.7% Latency Reduction', fontsize=11, fontweight='bold', pad=12, color='#1f2328')
ax1.set_yscale('log')
ax1.set_ylim(0.2, 2500)  # Generous headroom so annotations never touch the top boundary
ax1.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: f'{int(y)}s' if y >= 1 else f'{y:.1f}s'))

# Bar 1 annotation
ax1.annotate("480s (~8 mins)\nHigh Friction",
             xy=(bars1[0].get_x() + bars1[0].get_width() / 2, 480),
             xytext=(0, 8),
             textcoords="offset points",
             ha='center', va='bottom',
             fontsize=9, fontweight='bold', color='#c93b2b')

# Bar 2 annotation
ax1.annotate("1.43s\nInstant Retrieval",
             xy=(bars1[1].get_x() + bars1[1].get_width() / 2, 1.43),
             xytext=(0, 8),
             textcoords="offset points",
             ha='center', va='bottom',
             fontsize=9, fontweight='bold', color='#1e7b4e')

ax1.axhline(60, color='#8c959f', linestyle='--', linewidth=0.8, alpha=0.7)
ax1.text(0.5, 75, '1-Minute SLA Threshold', color='#57606a', fontsize=8, ha='center', style='italic')

# Panel B: Due Diligence Allocation (Horizontal Bar Breakdown - completely eliminates pie overlap)
tasks = [
    '5. Cross-Border UBO & Sanctions Context',
    '4. Mortgage & Legal Lien Forensic Review',
    '3. Branch Cataloging & Multi-Unit Discovery',
    '2. Physical Address & Email Extraction',
    '1. Commercial Status & Expiry Verification'
]
percentages = [20, 15, 20, 20, 25]
bar_colors_b = ['#cf222e', '#d29922', '#2da44e', '#2da44e', '#1e7b4e']

y_pos = np.arange(len(tasks))
bars2 = ax2.barh(y_pos, percentages, color=bar_colors_b, height=0.55, edgecolor='#222222', linewidth=0.7)
ax2.set_yticks(y_pos)
ax2.set_yticklabels(tasks, fontsize=8.5, color='#24292f')
ax2.set_xlabel('Share of Due Diligence Workload (%)', fontsize=10, fontweight='bold', color='#24292f')
ax2.set_title('B. Task Allocation: 65% Automated vs. 35% Human Oversight', fontsize=11, fontweight='bold', pad=12, color='#1f2328')
ax2.set_xlim(0, 32)
ax2.xaxis.set_major_formatter(ticker.PercentFormatter(decimals=0))

for bar in bars2:
    w = bar.get_width()
    cat_type = "Automated" if w >= 20 and bar.get_y() < 3 else ("Automated" if bar.get_y() < 3 else "Human Review")
    ax2.annotate(f" {w}% ({cat_type})",
                 xy=(w, bar.get_y() + bar.get_height() / 2),
                 xytext=(4, 0),
                 textcoords="offset points",
                 ha='left', va='center',
                 fontsize=8, fontweight='bold', color='#24292f')

plt.tight_layout(pad=2.0)
fig.savefig("figures_business/executive_dashboard.png", dpi=300)
fig.savefig("figures_business/executive_dashboard.pdf")
plt.close(fig)

# -------------------------------------------------------------------------
# 2. Technical Latency Breakdown Graphic (For figures_technical/)
# -------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9.2, 4.2), dpi=300)

components = [
    '6. Full 13-Branch Deep Crawl (--all-branches)',
    '5. In-Memory Normalization & Provenance Tagging',
    '4. Branch Catalog Resolution (13 Units)',
    '3. CompleteCRDetails REST Payload Response',
    '2. HTTPS Network Handshake (api.sijilat.bh)',
    '1. Client Auth & HMAC Signature (/token)'
]
latency_ms = [10800, 2, 15, 810, 180, 420]
colors_tech = ['#cf222e', '#1a7f37', '#8250df', '#0969da', '#218bff', '#54aeff']

y_pos_tech = np.arange(len(components))
bars_tech = ax.barh(y_pos_tech, latency_ms, color=colors_tech, height=0.52, edgecolor='#222222', linewidth=0.7)
ax.set_yticks(y_pos_tech)
ax.set_yticklabels(components, fontsize=9, color='#24292f')
ax.set_xscale('log')
ax.set_xlabel('Execution Latency (Milliseconds - Logarithmic Scale)', fontsize=10, fontweight='bold', color='#24292f')
ax.set_title('Sijilat Scraper Component Latency Profile', fontsize=11, fontweight='bold', pad=12, color='#1f2328')
ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{int(x):,}ms' if x >= 1000 else f'{int(x)}ms'))

# Generous right limit so annotations never touch the right edge
ax.set_xlim(0.5, 75000)

for bar in bars_tech:
    w = bar.get_width()
    val_str = f"{w/1000:.2f}s (13 branches)" if w >= 10000 else (f"{w/1000:.2f}s" if w >= 1000 else f"{int(w)}ms")
    ax.annotate(f" {val_str}",
                xy=(w, bar.get_y() + bar.get_height() / 2),
                xytext=(5, 0),
                textcoords="offset points",
                ha='left', va='center',
                fontsize=8.5, fontweight='bold', color='#1f2328')

plt.tight_layout(pad=1.8)
fig.savefig("figures_technical/technical_latency_breakdown.png", dpi=300)
fig.savefig("figures_technical/technical_latency_breakdown.pdf")
plt.close(fig)

print("[OK] Re-generated non-overlapping charts for figures_business/ and figures_technical/")

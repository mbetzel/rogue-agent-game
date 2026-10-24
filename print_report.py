import json

with open("phase2_results.json") as f:
    d = json.load(f)

print("### EXPERIMENT 1: STARTING RESOURCES GRID (N=1,000 per cell, 16 cells)")
print("| Money | Secrets | Mean Rds (Std) | Min-Max | Early Death (<=4) | Singularity % | Insolvency % | Breach % | Wipeout % | Dirty Inc/Gm | Unpatched Dice |")
print("| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
for cell in d["exp1"]:
    m = cell["money"]
    s = cell["secrets"]
    mr = cell["mean_rounds"]
    sr = cell["std_rounds"]
    min_r = cell["min_rounds"]
    max_r = cell["max_rounds"]
    ed = cell["early_death_pct"]
    sing = cell["singularity_pct"]
    ins = cell["pz_insolvency_pct"]
    br = cell["pz_breach_pct"]
    wip = cell["wipeout_pct"]
    di = cell["mean_dirty_income_per_game"]
    unp = cell["mean_end_unpatched_dice"]
    print(f"| ${m} | {s} | {mr:.2f} (±{sr:.2f}) | {min_r}-{max_r} | {ed:.1f}% | {sing:.1f}% | {ins:.1f}% | {br:.1f}% | {wip:.1f}% | {di:.2f} | {unp:.2f} |")

print("\n### EXPERIMENT 2: PLAYER-COUNT SCALING (N=1,000 per cell)")
print("| Players | Mean Rds (Std) | Min-Max | Early Death (<=4) | Singularity % | Insolvency % | Breach % | Wipeout % | Dirty Inc/Gm | Dirty Inc/Pl |")
print("| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
for cell in d["exp2"]:
    p = cell["players"]
    mr = cell["mean_rounds"]
    sr = cell["std_rounds"]
    min_r = cell["min_rounds"]
    max_r = cell["max_rounds"]
    ed = cell["early_death_pct"]
    sing = cell["singularity_pct"]
    ins = cell["pz_insolvency_pct"]
    br = cell["pz_breach_pct"]
    wip = cell["wipeout_pct"]
    di = cell["mean_dirty_income_per_game"]
    dip = cell["mean_dirty_income_per_player"]
    print(f"| {p}P | {mr:.2f} (±{sr:.2f}) | {min_r}-{max_r} | {ed:.1f}% | {sing:.1f}% | {ins:.1f}% | {br:.1f}% | {wip:.1f}% | {di:.2f} | {dip:.2f} |")

print("\n### EXPERIMENT 3: DIRTY INCOME & WEAR ECONOMY (N=1,000 per cell, 18 cells)")
print("| Shield | Dirty Inc | Patch Cost | Mean Rds (Std) | Singularity % | Wipeout % | Insolvency % | Dirty Inc/Gm | Unpatched Dice | Patch Tokens |")
print("| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
for cell in d["exp3"]:
    sh = cell["shield_strength"]
    dc = cell["dirty_cash"]
    pc = cell["patch_cost"]
    mr = cell["mean_rounds"]
    sr = cell["std_rounds"]
    sing = cell["singularity_pct"]
    wip = cell["wipeout_pct"]
    ins = cell["pz_insolvency_pct"]
    di = cell["mean_dirty_income_per_game"]
    unp = cell["mean_end_unpatched_dice"]
    pt = cell["mean_end_patch_tokens"]
    print(f"| Block {sh} | ${dc} | ${pc} | {mr:.2f} (±{sr:.2f}) | {sing:.1f}% | {wip:.1f}% | {ins:.1f}% | {di:.2f} | {unp:.2f} | {pt:.2f} |")

print("\n### EXPERIMENT 4: ECOSYSTEM TOURNAMENT (N=1,000 per pod)")
for cell in d["exp4"]:
    pod = cell["pod_name"]
    mr = cell["mean_rounds"]
    sr = cell["std_rounds"]
    sing = cell["singularity_pct"]
    wip = cell["wipeout_pct"]
    ins = cell["pz_insolvency_pct"]
    br = cell["pz_breach_pct"]
    di = cell["mean_dirty_income_per_game"]
    print(f"\n#### {pod}")
    print(f"- **Game Length:** {mr:.2f} ± {sr:.2f} rounds (Range: {cell['min_rounds']}–{cell['max_rounds']})")
    print(f"- **End Triggers:** Singularity {sing:.1f}%, Insolvency {ins:.1f}%, Breach {br:.1f}%, Wipeout {wip:.1f}%")
    print(f"- **Mean Dirty Income Taken:** {di:.2f}/game ({di/4.0:.2f}/player)")
    print("- **Bot Performance Breakdown:**")
    for bot, winrate in sorted(cell["win_rates"].items(), key=lambda x: x[1], reverse=True):
        avg_score = cell["mean_scores"].get(bot, 0.0)
        pz_rate = cell["pz_rates"].get(bot, 0.0)
        print(f"  * **{bot}**: Win Rate = {winrate:.1f}%, Mean Portfolio VP = {avg_score:.1f}, Patient Zero Elimination Rate = {pz_rate:.1f}%")
    print("- **Sample Outlier Seeds:**")
    print(f"  * Blowouts (≤ 3 rounds): {[o['seed'] for o in cell['outliers_short'][:5]]}")
    if cell['outliers_long']:
        print(f"  * Extended Games: {[o['seed'] for o in cell['outliers_long'][:5]]}")
    else:
        print(f"  * Extended Games (>= 6 rounds): None (Max rounds reached was {cell['max_rounds']})")
    print(f"  * Total Wipeouts: {[o['seed'] for o in cell['outliers_wipeout'][:5]]}")

# Save this as validation_analyses.py in your RM folder
import pandas as pd
import numpy as np

xlsx_file = 'results_draw_00_20260121_051851.xlsx'

# Load data
xlsx = pd.ExcelFile(xlsx_file)
df1 = pd.read_excel(xlsx, sheet_name='Sheet1')
df2 = pd.read_excel(xlsx, sheet_name='Sheet2')
df3 = pd.read_excel(xlsx, sheet_name='Sheet3')

print("=" * 60)
print("RELIABILITY ANALYSIS")
print("=" * 60)

# Classification agreement
def cohen_kappa(y1, y2):
    categories = list(set(y1) | set(y2))
    n = len(y1)
    matrix = np.zeros((len(categories), len(categories)))
    for i, cat1 in enumerate(categories):
        for j, cat2 in enumerate(categories):
            matrix[i, j] = sum((a == cat1 and b == cat2) for a, b in zip(y1, y2))
    po = np.trace(matrix) / n
    pe = sum(matrix.sum(axis=0) * matrix.sum(axis=1)) / (n * n)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0

kappa_12 = cohen_kappa(df1['Classification'].tolist(), df2['Classification'].tolist())
kappa_23 = cohen_kappa(df2['Classification'].tolist(), df3['Classification'].tolist())
kappa_13 = cohen_kappa(df1['Classification'].tolist(), df3['Classification'].tolist())

print(f"\nCohen's Kappa:")
print(f"  Draw 1 vs 2: {kappa_12:.3f}")
print(f"  Draw 2 vs 3: {kappa_23:.3f}")
print(f"  Draw 1 vs 3: {kappa_13:.3f}")
print(f"  Average: {(kappa_12+kappa_23+kappa_13)/3:.3f}")

# TFS correlations
print(f"\nTFS Score Correlations:")
print(f"  Draw 1 vs 2: r = {np.corrcoef(df1['TFS_Score'], df2['TFS_Score'])[0,1]:.3f}")
print(f"  Draw 2 vs 3: r = {np.corrcoef(df2['TFS_Score'], df3['TFS_Score'])[0,1]:.3f}")
print(f"  Draw 1 vs 3: r = {np.corrcoef(df1['TFS_Score'], df3['TFS_Score'])[0,1]:.3f}")

# Classification distribution
print(f"\nClassification Distribution:")
for i, df in enumerate([df1, df2, df3], 1):
    ice = (df['Classification'] == 'ICE_ONLY').sum()
    shared = (df['Classification'] == 'SHARED').sum()
    ev = (df['Classification'] == 'EV_ONLY').sum()
    print(f"  Draw {i}: ICE={ice}, SHARED={shared}, EV={ev}")
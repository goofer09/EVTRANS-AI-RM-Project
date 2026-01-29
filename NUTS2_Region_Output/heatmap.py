import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt

# Load NUTS-2 shapefile
nuts_url = "https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/NUTS_RG_20M_2021_4326_LEVL_2.geojson"
nuts = gpd.read_file(nuts_url)
germany = nuts[nuts['CNTR_CODE'] == 'DE'].copy()

# Your RAVI data
ravi_df = pd.DataFrame({
    'nuts2_code': ['DE11', 'DE21', 'DE22', 'DEC0'],
    'ravi_score': [29.7, 38.1, 100.0, 78.5]
})

germany = germany.merge(ravi_df, left_on='NUTS_ID', right_on='nuts2_code', how='left')

# Plot - FIXED: removed 'label' from legend_kwds
fig, ax = plt.subplots(1, 1, figsize=(10, 12))
germany.plot(
    column='ravi_score',
    cmap='RdYlGn_r',
    legend=True,
    legend_kwds={'shrink': 0.6},  # ← REMOVED 'label' - that was the bug
    edgecolor='white',
    linewidth=0.5,
    ax=ax,
    missing_kwds={'color': 'lightgrey'}
)

# Add colorbar label separately
cbar = ax.get_figure().get_axes()[1]
cbar.set_ylabel('RAVI Score', fontsize=10)

ax.set_title('RAVI - German NUTS-2 Regions', fontsize=14)
ax.axis('off')
plt.savefig('germany_ravi_heatmap.png', dpi=300, bbox_inches='tight')
plt.show()
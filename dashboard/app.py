"""Lunar Analog Explorer: interactive presentation of reproducible pipeline outputs."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from dashboard.data import (
    OUTPUTS, METRICS, TARGETS, EARTH_COORDINATES,
    read_ranking, read_sensitivity, read_summary, weighted_ranking,
    winners, validate_baseline, terrain_figure_path,
)

st.set_page_config(page_title='Lunar Analog Explorer', page_icon='🌕', layout='wide', initial_sidebar_state='expanded')
st.markdown('''<style>
.block-container {padding-top: 1.8rem; max-width: 1480px;}
[data-testid="stMetricValue"] {font-size: 1.65rem;}
.small-print {color:#8892a0; font-size:0.85rem;}
</style>''', unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def load(target: str, excluded: bool):
    return read_ranking(target, excluded), read_sensitivity(target, excluded)


@st.cache_data(show_spinner=False)
def summary():
    return read_summary()


st.title('🌕 Lunar Analog Explorer')
st.caption('Terrestrial terrain analogues for lunar south-polar exploration  ·  Novo Oeste HT NASA')

for key, default in [('slope_weight', 33), ('roughness_weight', 33), ('relief_weight', 33)]:
    if key not in st.session_state:
        st.session_state[key] = default


def reset_weights():
    st.session_state['slope_weight'] = 33
    st.session_state['roughness_weight'] = 33
    st.session_state['relief_weight'] = 33


with st.sidebar:
    st.header('Explore the analysis')
    target = st.radio('Lunar target', TARGETS)
    exclude_haughton = st.checkbox('Exclude Haughton Crater', value=False,
        help='Run the robustness subset using exported without-Haughton normalization.')
    st.divider()
    st.subheader('Similarity weights')
    st.caption('Move sliders to recompute the ranking instantly using exported normalized distances.')
    weight_slope = st.slider('Slope distribution', 0, 100, key='slope_weight')
    weight_rough = st.slider('Multi-scale roughness', 0, 100, key='roughness_weight')
    weight_relief = st.slider('Robust relief', 0, 100, key='relief_weight')
    weights = {'slope': weight_slope, 'roughness': weight_rough, 'relief': weight_relief}
    total = sum(weights.values())
    if total == 0:
        st.warning('At least one weight must be greater than zero.')
        st.stop()
    st.caption('Effective weights: ' + ' · '.join(f'{m}: {weights[m]/total:.1%}' for m in METRICS))
    st.button('Reset to default weights', use_container_width=True, on_click=reset_weights)
    st.divider()
    st.caption('All displayed composite scores are relative, candidate-set-dependent distances—not similarity percentages.')

try:
    raw, sensitivity = load(target, exclude_haughton)
except (FileNotFoundError, ValueError) as exc:
    st.error(f'Cannot load the exported pipeline results: {exc}')
    st.info('Run `python -m scripts.run_pipeline` first, or copy the exported CSV files into `outputs/`.')
    st.stop()

ranked = weighted_ranking(raw, weights)
champion = ranked.iloc[0]
runner_up = ranked.iloc[1] if len(ranked) > 1 else None
winner_counts = winners(sensitivity)['earth_site'].value_counts()
quality = {item['name']: item for item in summary().get('quality', [])}

left, middle, right, last = st.columns(4)
left.metric('Leading candidate', str(champion['earth_site']))
middle.metric('Composite distance', f"{champion['composite_distance']:.4f}")
right.metric('Runner-up', str(runner_up['earth_site']) if runner_up is not None else '—')
last.metric('Wins in seven preset scenarios', f"{winner_counts.get(champion['earth_site'], 0)}/7")

ranking_tab, maps_tab, sensitivity_tab, geography_tab, method_tab = st.tabs([
    '🏆 Interactive ranking', '🗺️ Terrain comparison', '🧪 Weight sensitivity',
    '🌍 Candidate locations', 'ℹ️ Methods & quality',
])

with ranking_tab:
    st.subheader(f'Topographic similarity to {target}')
    st.caption('Shorter bar = smaller composite distance = better match under the selected weights.')
    fig = px.bar(ranked.sort_values('composite_distance', ascending=False),
                 x='composite_distance', y='earth_site', orientation='h',
                 text='composite_distance', color='earth_site',
                 color_discrete_sequence=px.colors.qualitative.Safe)
    fig.update_traces(texttemplate='%{text:.4f}', textposition='outside', cliponaxis=False,
                      hovertemplate='%{y}<br>Distance: %{x:.6f}<extra></extra>')
    fig.update_layout(showlegend=False, xaxis_title='Composite normalized distance (lower is better)',
                      yaxis_title='', height=420, margin=dict(l=5,r=70,t=10,b=40))
    st.plotly_chart(fig, use_container_width=True)

    st.subheader('What drives each score?')
    cdata = ranked.melt(id_vars=['earth_site'], value_vars=[f'{m}_contribution' for m in METRICS],
                        var_name='Metric', value_name='Weighted contribution')
    cdata['Metric'] = cdata['Metric'].str.replace('_contribution','', regex=False).str.capitalize()
    fig_c = px.bar(cdata, y='earth_site', x='Weighted contribution', color='Metric', orientation='h',
                   category_orders={'earth_site': ranked['earth_site'].iloc[::-1].tolist()},
                   color_discrete_map={'Slope':'#4f91c7','Roughness':'#e6a157','Relief':'#9f80d0'})
    fig_c.update_layout(barmode='stack', height=390, yaxis_title='',
                        xaxis_title='Weighted contribution to composite distance', margin=dict(l=5,r=10,t=10,b=30))
    st.plotly_chart(fig_c, use_container_width=True)
    display_columns = ['rank', 'earth_site', 'composite_distance'] + [f'{m}_distance_normalized' for m in METRICS]
    st.dataframe(ranked[display_columns], hide_index=True, use_container_width=True,
                 column_config={'composite_distance': st.column_config.NumberColumn(format='%.5f')})
    st.download_button('Download current weighted ranking (CSV)',
                       data=ranked.to_csv(index=False).encode('utf-8-sig'),
                       file_name=f'{target.lower()}_interactive_ranking.csv', mime='text/csv')

with maps_tab:
    st.subheader('Explore the terrain maps')
    st.caption('These are the original, pipeline-generated elevation, slope, roughness and (lunar-only) solar-visibility panels.')
    options = ranked['earth_site'].tolist()
    default_index = options.index('Tolbachik') if 'Tolbachik' in options else 0
    selected_earth = st.selectbox('Compare lunar target with terrestrial site', options, index=default_index)
    moon_path, earth_path = terrain_figure_path(target), terrain_figure_path(selected_earth)
    left_img, right_img = st.columns(2)
    with left_img:
        st.markdown(f'**Moon · {target}**')
        if moon_path.exists():
            st.image(str(moon_path), use_container_width=True)
        else:
            st.warning(f'Figure missing: {moon_path.name}')
    with right_img:
        st.markdown(f'**Earth · {selected_earth}**')
        if earth_path.exists():
            st.image(str(earth_path), use_container_width=True)
        else:
            st.warning(f'Figure missing: {earth_path.name}')
    comp = ranked.set_index('earth_site').loc[selected_earth]
    a,b,c = st.columns(3)
    a.metric('Slope distance', f"{comp['slope_distance']:.3f}°")
    b.metric('Roughness distance', f"{comp['roughness_distance']:.3f}")
    c.metric('Relief distance', f"{comp['relief_distance']:.3f}")
    st.info('Color bars have different ranges across locations. Visual color matching is not the similarity algorithm. Solar visibility is shown only as lunar context and is excluded from the score.')

with sensitivity_tab:
    st.subheader('Seven predefined weighting scenarios')
    heat = sensitivity.pivot(index='earth_site', columns='scenario', values='rank')
    order = sensitivity['scenario'].drop_duplicates().tolist()
    heat = heat.reindex(index=ranked['earth_site'], columns=order)
    fig_h = px.imshow(heat, labels=dict(x='Weight scenario', y='Earth candidate', color='Rank'),
                      color_continuous_scale='Viridis_r', zmin=1, zmax=len(heat),
                      text_auto=True, aspect='auto')
    fig_h.update_layout(height=390, margin=dict(l=5,r=10,t=10,b=90),
                        xaxis_tickangle=-25)
    st.plotly_chart(fig_h, use_container_width=True)
    winner_table = winners(sensitivity).rename(columns={'scenario':'Scenario','earth_site':'Winner'})
    st.dataframe(winner_table, hide_index=True, use_container_width=True)
    original = read_ranking(target, False)
    reduced = read_ranking(target, True)
    st.caption(f"Haughton exclusion robustness: balanced winner is {original.sort_values('rank').iloc[0]['earth_site']} with all sites and {reduced.sort_values('rank').iloc[0]['earth_site']} without Haughton. Re-normalization is performed per candidate set.")
    st.caption('The heatmap uses the seven archived weight scenarios, while the sliders above provide an additional interactive scenario.')

with geography_tab:
    st.subheader('Where are the terrestrial candidates?')
    locations = []
    for name,(lat,lon) in EARTH_COORDINATES.items():
        candidate = ranked.loc[ranked['earth_site'].eq(name)]
        if candidate.empty: continue
        row = candidate.iloc[0]
        locations.append({'Name': name, 'Latitude': lat, 'Longitude':lon,
                          'Rank': int(row['rank']), 'Distance': float(row['composite_distance'])})
    geo = pd.DataFrame(locations)
    fig_geo = px.scatter_geo(geo, lat='Latitude', lon='Longitude', hover_name='Name',
                             color='Rank', size_max=18, size=[1] * len(geo),
                             custom_data=['Distance'], projection='natural earth',
                             color_continuous_scale='Viridis_r',
                             range_color=(1, len(geo)))
    fig_geo.update_traces(marker=dict(size=13, line=dict(width=1, color='white')),
                          hovertemplate='<b>%{hovertext}</b><br>Rank: %{marker.color}<br>Distance: %{customdata[0]:.4f}<extra></extra>')
    fig_geo.update_geos(showland=True, landcolor='#e6e8ec', showocean=True, oceancolor='#c6d8e6',
                        showcountries=True, countrycolor='white')
    fig_geo.update_layout(height=480, margin=dict(l=0,r=0,t=0,b=0))
    st.plotly_chart(fig_geo, use_container_width=True)
    st.caption('Locations represent the centres of the ~40 km analysis windows, not the full extent of each geographical region.')

with method_tab:
    st.subheader('Methods, interpretation and data-quality checks')
    st.markdown('''**Composite distance:** three candidate-set-normalized components are combined using the selected weights.

- **Slope:** 1D Wasserstein distance between clipped (0–45°) slope histograms, raw distance in degrees.
- **Roughness:** mean absolute logarithmic ratio of RMS values at shared baselines (120–1920 m).
- **Relief:** absolute logarithmic ratio of elevation P99–P01 ranges.

**Important:** a score of zero is not a perfect match. It means that the candidate attains the minimum normalized distance on each weighted component in the considered candidate set. These are **terrain-only comparisons**, not verified analogues of gravity, illumination, regolith, thermal conditions or landing safety.''')
    quality_items = summary().get('quality', [])
    if quality_items:
        q = pd.DataFrame(quality_items)
        q = q[['name','pixel_size_m','missing_fraction','zero_fraction','near_median_fraction','flags']].copy()
        for col in ('missing_fraction','zero_fraction','near_median_fraction'):
            q[col] = q[col].map(lambda x: f'{100*x:.2f}%')
        q['flags'] = q['flags'].map(lambda x: ', '.join(x) if x else '—')
        st.dataframe(q, hide_index=True, use_container_width=True)
    st.warning('Haughton has a connected zero-elevation region requiring source-level water/no-data validation. Atacama has a large nearly-flat region that may be real or influenced by resampling. The exclusion test does not prove data quality.')
    err = validate_baseline(raw)
    st.caption(f'Balanced score consistency check against archived ranking: maximum absolute difference = {err:.2e}.')
    st.caption('Data source: CSV, JSON and PNG output files generated by the Novo Oeste HT NASA pipeline.')

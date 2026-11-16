"""Lunar Analog Explorer: interactive presentation of reproducible pipeline outputs."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from urllib.parse import quote
import streamlit as st

from dashboard.data import (
    OUTPUTS, METRICS, TARGETS, EARTH_COORDINATES,
    read_ranking, read_sensitivity, read_summary, weighted_ranking,
    winners, validate_baseline, terrain_figure_path,
)
from dashboard.insights import (
    LABELS, PAIR, pairwise_comparison, slope_threshold_with_equal_other_weights,
    weight_simplex_winners,
)

st.set_page_config(
    page_title='Lunar Analog Explorer | Novo Oeste',
    page_icon=':material/public:', layout='wide', initial_sidebar_state='expanded',
)

# Visual system based on NASA Style Guide v2.1. This independent
# hackathon project does not use NASA's official insignia or claim endorsement.
NASA_BLUE = '#0B3D91'
NASA_RED = '#FC3D21'
INK = '#101820'
PAPER = '#FFFFFF'
SOFT_GREY = '#F3F5F8'
BORDER = '#DCE3ED'
NAVY = '#091A35'
METRIC_PALETTE = {'Slope': NASA_BLUE, 'Roughness': NASA_RED, 'Relief': '#7C8797'}
CANDIDATE_PALETTE = {
    'Tolbachik': NASA_BLUE,
    'Death Valley': NASA_RED,
    'Haughton Crater': '#6C7890',
    'Pinacate': '#829AB5',
    'Meteor Crater': '#A4AEC0',
    'Atacama': '#CCD3DE',
}

st.markdown('''<style>
/* NASA-inspired communication design — not an official NASA product. */
:root {--nasa-blue:#0B3D91;--nasa-red:#FC3D21;--ink:#101820;--line:#DCE3ED;}
html,body,[class*="css"],.stApp {font-family:Arial,Helvetica,sans-serif;}
.stApp {background:#FFFFFF;color:#101820;}
.block-container {max-width:1480px;padding-top:1.1rem;padding-bottom:3.5rem;}
[data-testid="stSidebar"] {background:#F3F5F8;border-right:1px solid #DCE3ED;}
[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3 {color:#0B3D91;}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] {font-weight:650;}
[data-testid="stHeader"] {background:rgba(255,255,255,.95);}
h1,h2,h3,h4 {font-family:Arial,Helvetica,sans-serif;letter-spacing:-.035em;color:#0B3D91;}
h1 {font-size:clamp(2.2rem,4.0vw,4.3rem)!important;font-weight:800!important;}
h2,h3 {font-weight:750!important;}
p,li {line-height:1.58;}
/* Bright, restrained editorial identity. */
.mission-kicker {font-size:.70rem;letter-spacing:.22em;font-weight:800;color:#FC3D21;margin:0 0 .5rem;}
.mission-masthead {position:relative;border-top:7px solid #FC3D21;border-bottom:1px solid #DCE3ED;padding:1.6rem 0 1.35rem;margin-bottom:1.45rem;}
.mission-masthead:after {content:"";position:absolute;right:0;top:0;width:90px;height:7px;background:#0B3D91;}
.mission-title {color:#0B3D91!important;margin:0!important;font-size:clamp(2.15rem,3.7vw,3.6rem);font-weight:850;letter-spacing:-.055em;line-height:1.08;}
.mission-subtitle {font-size:1rem;color:#526175;margin-top:.65rem;max-width:800px;}
.mission-meta {font-size:.72rem;color:#64748B;letter-spacing:.11em;text-transform:uppercase;margin-top:1rem;font-weight:700;}
.section-intro {padding:0 0 .8rem 0;border-bottom:1px solid #DCE3ED;margin-bottom:1rem;}
.small-print {color:#64748B;font-size:.82rem;}
[data-testid="stMetric"] {background:#F8FAFC;border:1px solid #DCE3ED;border-top:3px solid #0B3D91;border-radius:2px;padding:1rem 1.1rem;min-height:112px;}
[data-testid="stMetricLabel"] {color:#53657B;font-weight:650;font-size:.82rem;}
[data-testid="stMetricValue"] {font-size:1.55rem;color:#0B3D91;font-weight:800;letter-spacing:-.035em;}
.stTabs [data-baseweb="tab-list"] {border-bottom:2px solid #DCE3ED;gap:.1rem;flex-wrap:wrap;}
.stTabs [data-baseweb="tab"] {border-radius:0!important;padding:.75rem .85rem;font-weight:700;color:#526175;}
.stTabs [aria-selected="true"] {color:#0B3D91!important;border-bottom:3px solid #FC3D21!important;}
.stButton>button[kind="primary"],.stDownloadButton>button {border-radius:3px;background:#0B3D91;color:white;border-color:#0B3D91;font-weight:700;}
.stButton>button {border-radius:3px;font-weight:700;}
.stButton>button:hover,.stDownloadButton>button:hover {border-color:#FC3D21;color:#FC3D21;}
[data-testid="stAlert"] {border-radius:2px;}
[data-testid="stDataFrame"], [data-testid="stPlotlyChart"] {border:1px solid #EBEFF5;border-radius:3px;}
hr {border-color:#DCE3ED;}
/* Keep plots and notebook-like data controls accessible on narrow screens. */
@media (max-width:750px){.block-container{padding-left:1rem;padding-right:1rem}.mission-masthead{padding:1.1rem 0}.mission-title{font-size:2rem}}
</style>''', unsafe_allow_html=True)


# Monochrome vector icons for the six navigation tabs, matching the NASA-inspired palette.
# The icons are locally defined SVG paths; no external icon fonts or CDN are required.
TAB_ICONS = [
    '<path d="M3 3v18h18"/><path d="M7 16v-5"/><path d="M12 16V7"/><path d="M17 16v-8"/>',
    '<path d="M12 3v18"/><path d="M5 6h14"/><path d="M7 6 3 14h8L7 6Z"/><path d="m17 6-4 8h8l-4-8Z"/>',
    '<path d="m3 6 6-3 6 3 6-3v15l-6 3-6-3-6 3V6Z"/><path d="M9 3v15"/><path d="M15 6v15"/>',
    '<path d="M9 3h6"/><path d="M10 3v7l-5.5 8.3A2 2 0 0 0 6.2 21h11.6a2 2 0 0 0 1.7-2.7L14 10V3"/><path d="M8 15h8"/>',
    '<circle cx="12" cy="12" r="9"/><path d="M3 12h18"/><path d="M12 3a15 15 0 0 1 0 18"/><path d="M12 3a15 15 0 0 0 0 18"/>',
    '<circle cx="12" cy="12" r="9"/><path d="M12 11v5"/><path d="M12 8h.01"/>',
]


def tab_icon_css() -> str:
    """Create self-contained icon masks without adding glyphs to tab labels."""
    rules = [
        '.stTabs [data-baseweb="tab-list"] [data-baseweb="tab"] {'
        'display:inline-flex; align-items:center; gap:.45rem;}',
        '.stTabs [data-baseweb="tab-list"] [data-baseweb="tab"]::before {'
        'content:""; display:inline-block; width:17px; height:17px; flex:0 0 17px;'
        'background-color:currentColor; mask-size:contain; mask-position:center;'
        'mask-repeat:no-repeat; -webkit-mask-size:contain; -webkit-mask-position:center;'
        '-webkit-mask-repeat:no-repeat;}',
    ]
    for index, paths in enumerate(TAB_ICONS, 1):
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
            'fill="none" stroke="black" stroke-width="1.8" '
            'stroke-linecap="round" stroke-linejoin="round">'
            f'{paths}</svg>'
        )
        url = 'data:image/svg+xml,' + quote(svg, safe='')
        rules.append(
            f'.stTabs [data-baseweb="tab-list"] [data-baseweb="tab"]:nth-child({index})::before'
            f' {{ mask-image:url("{url}"); -webkit-mask-image:url("{url}"); }}'
        )
    return '<style>' + '\n'.join(rules) + '</style>'


st.markdown(tab_icon_css(), unsafe_allow_html=True)


def nasa_chart(fig, *, height=None):
    """Apply a consistent, legible visual language to every Plotly figure."""
    fig.update_layout(
        template='plotly_white',
        font=dict(family='Arial, Helvetica, sans-serif', color=INK, size=12),
        paper_bgcolor=PAPER, plot_bgcolor=PAPER,
        colorway=[NASA_BLUE, NASA_RED, '#72839A', '#A3B4C8', '#34445C'],
        title_font=dict(color=NASA_BLUE),
        legend=dict(font=dict(color=INK), bgcolor='rgba(255,255,255,0)'),
        hoverlabel=dict(bgcolor=NAVY, font=dict(color='white',family='Arial')),
    )
    if height is not None:
        fig.update_layout(height=height)
    fig.update_xaxes(showgrid=True, gridcolor='#EBEFF5', zerolinecolor='#B8C4D4', linecolor=BORDER)
    fig.update_yaxes(showgrid=False, linecolor=BORDER)
    return fig


@st.cache_data(show_spinner=False)
def load(target: str, excluded: bool):
    return read_ranking(target, excluded), read_sensitivity(target, excluded)


@st.cache_data(show_spinner=False)
def summary():
    return read_summary()


st.markdown('''<div class="mission-masthead">
  <div class="mission-kicker">NOVO OESTE / TERRAIN INTELLIGENCE</div>
  <div class="mission-title">LUNAR ANALOG<br>EXPLORER<span style="color:#FC3D21">.</span></div>
  <div class="mission-subtitle">Explore terrestrial terrain analogues for lunar south-polar exploration through reproducible topographic comparisons.</div>
  <div class="mission-meta">Independent hackathon research project · Using open planetary datasets</div>
</div>''', unsafe_allow_html=True)

for key, default in [('slope_weight', 33), ('roughness_weight', 33), ('relief_weight', 33)]:
    if key not in st.session_state:
        st.session_state[key] = default


def reset_weights():
    st.session_state['slope_weight'] = 33
    st.session_state['roughness_weight'] = 33
    st.session_state['relief_weight'] = 33


with st.sidebar:
    st.markdown('**MISSION CONTROL**')
    st.header('Analysis controls')
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
    st.caption('Method note: lower normalized distance means better match within the selected candidate set. Not a similarity percentage.')
    st.caption('Design inspired by NASA Style Guide v2.1. Independent project; not affiliated with or endorsed by NASA.')

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

ranking_tab, duel_tab, maps_tab, sensitivity_tab, geography_tab, method_tab = st.tabs([
    'Interactive ranking', 'Why the winner changes',
    'Terrain comparison', 'Weight sensitivity',
    'Candidate locations', 'Methods & quality',
])

with ranking_tab:
    st.subheader(f'Topographic similarity to {target}')
    st.caption('Shorter bar = smaller composite distance = better match under the selected weights.')
    fig = px.bar(ranked.sort_values('composite_distance', ascending=False),
                 x='composite_distance', y='earth_site', orientation='h',
                 text='composite_distance', color='earth_site',
                 color_discrete_map=CANDIDATE_PALETTE)
    fig.update_traces(texttemplate='%{text:.4f}', textposition='outside', cliponaxis=False,
                      hovertemplate='%{y}<br>Distance: %{x:.6f}<extra></extra>')
    fig.update_layout(showlegend=False, xaxis_title='Composite normalized distance (lower is better)',
                      yaxis_title='', height=420, margin=dict(l=5,r=70,t=10,b=40))
    st.plotly_chart(nasa_chart(fig), use_container_width=True)

    st.subheader('What drives each score?')
    cdata = ranked.melt(id_vars=['earth_site'], value_vars=[f'{m}_contribution' for m in METRICS],
                        var_name='Metric', value_name='Weighted contribution')
    cdata['Metric'] = cdata['Metric'].str.replace('_contribution','', regex=False).str.capitalize()
    fig_c = px.bar(cdata, y='earth_site', x='Weighted contribution', color='Metric', orientation='h',
                   category_orders={'earth_site': ranked['earth_site'].iloc[::-1].tolist()},
                   color_discrete_map=METRIC_PALETTE)
    fig_c.update_layout(barmode='stack', height=390, yaxis_title='',
                        xaxis_title='Weighted contribution to composite distance', margin=dict(l=5,r=10,t=10,b=30))
    st.plotly_chart(nasa_chart(fig_c), use_container_width=True)
    display_columns = ['rank', 'earth_site', 'composite_distance'] + [f'{m}_distance_normalized' for m in METRICS]
    st.dataframe(ranked[display_columns], hide_index=True, use_container_width=True,
                 column_config={'composite_distance': st.column_config.NumberColumn(format='%.5f')})
    st.download_button('Download current weighted ranking (CSV)',
                       data=ranked.to_csv(index=False).encode('utf-8-sig'),
                       file_name=f'{target.lower()}_interactive_ranking.csv', mime='text/csv')

with duel_tab:
    st.subheader('Tolbachik vs Death Valley — why does the winner change?')
    st.caption('Direct comparison using the archived normalized distances. Lower is better; green indicates an advantage for Tolbachik, and orange indicates an advantage for Death Valley.')
    pair = pairwise_comparison(raw, weights)
    first, second = PAIR
    arow = raw.set_index('earth_site').loc[first]
    brow = raw.set_index('earth_site').loc[second]
    left_duel, right_duel = st.columns(2)
    with left_duel:
        st.metric(first, f"{pair['first_score']:.5f}", help='Composite distance at the currently selected weights')
    with right_duel:
        st.metric(second, f"{pair['second_score']:.5f}", help='Composite distance at the currently selected weights')

    if pair['winner'] == 'Tie':
        st.info('The candidates are tied for the current weights (within numerical tolerance).')
    else:
        st.success(f"**{pair['winner']} wins this head-to-head comparison** by {abs(pair['difference']):.5f} composite-distance units at the current weights.")
    if str(champion['earth_site']) not in PAIR:
        st.warning(f"The overall top-ranked candidate is {champion['earth_site']}, not one of the two in this comparison.")

    st.markdown('#### 1. Which candidate matches each metric more closely?')
    components = []
    for metric in METRICS:
        for name, row in ((first, arow), (second, brow)):
            components.append({
                'Metric': LABELS[metric],
                'Candidate': name,
                'Normalized distance': float(row[f'{metric}_distance_normalized']),
            })
    cfig = px.bar(pd.DataFrame(components), x='Metric', y='Normalized distance', color='Candidate',
                  barmode='group', text='Normalized distance',
                  color_discrete_map={first:NASA_BLUE, second:NASA_RED})
    cfig.update_traces(texttemplate='%{text:.3f}', textposition='outside', cliponaxis=False)
    cfig.update_layout(height=345, legend_title='', yaxis_title='Normalized component distance (lower is better)',
                       margin=dict(l=8,r=8,t=8,b=15))
    st.plotly_chart(nasa_chart(cfig), use_container_width=True)

    st.markdown('#### 2. How do your selected weights decide the result?')
    st.caption('Each bar is the weighted contribution difference: Tolbachik minus Death Valley. Positive values favor Death Valley; negative values favor Tolbachik. The sum equals the total score difference.')
    deltas = pair['metric_differences']
    delta_frame = pd.DataFrame({
        'Metric': [LABELS[m] for m in METRICS],
        'Difference': [deltas[m] for m in METRICS],
        'Favours': [second if deltas[m] > 1e-12 else first if deltas[m] < -1e-12 else 'Tie' for m in METRICS],
    })
    dfig = px.bar(delta_frame, y='Metric', x='Difference', orientation='h', color='Favours',
                  text='Difference', color_discrete_map={first:NASA_BLUE,second:NASA_RED,'Tie':'#7C8797'})
    dfig.update_traces(texttemplate='%{text:+.4f}', textposition='outside', cliponaxis=False)
    dfig.add_vline(x=0, line_color='gray', line_width=1)
    dfig.update_layout(height=260, showlegend=True, legend_title='', yaxis_title='',
                       xaxis_title='Contribution difference (Tolbachik − Death Valley)',
                       margin=dict(l=8,r=45,t=5,b=30))
    st.plotly_chart(nasa_chart(dfig), use_container_width=True)
    st.caption(f"Total difference: {pair['difference']:+.6f}. A negative total means Tolbachik wins; a positive total means Death Valley wins.")

    threshold = slope_threshold_with_equal_other_weights(raw)
    if threshold is not None:
        st.markdown('#### 3. A simple decision boundary')
        st.markdown(f'If roughness and relief share the remaining weight **equally**, these two candidates tie when slope receives **{threshold:.1%}** of the total weight. This threshold describes only the Tolbachik–Death Valley comparison, not an absolute lunar-similarity cutoff.')
        examples = []
        for sweight in np.linspace(0,1,101):
            w = {'slope':float(sweight), 'roughness':float((1-sweight)/2), 'relief':float((1-sweight)/2)}
            duel = pairwise_comparison(raw, w)
            examples.append({'Slope weight (%)':sweight*100, 'Score difference':duel['difference']})
        boundary = px.line(pd.DataFrame(examples), x='Slope weight (%)', y='Score difference',
                           color_discrete_sequence=[NASA_BLUE])
        boundary.add_hline(y=0, line_dash='dash', line_color='gray')
        boundary.add_vline(x=threshold*100, line_dash='dot', line_color=NASA_RED)
        boundary.update_layout(height=280, margin=dict(l=8,r=8,t=5,b=25),
                               yaxis_title='Tolbachik − Death Valley score')
        st.plotly_chart(nasa_chart(boundary), use_container_width=True)

    st.markdown('#### 4. Explore *all* possible weight combinations')
    st.caption('Each point represents one non-negative combination of slope, roughness and relief weights summing to 100%. Its color shows the overall winner among all candidates, not just the two compared above. The diamond marks your current weights.')
    simplex = weight_simplex_winners(raw, steps=31)
    palette = CANDIDATE_PALETTE
    ternary = px.scatter_ternary(simplex, a='slope', b='roughness', c='relief',
                                 color='winner', color_discrete_map=palette,
                                 hover_data={'slope':':.1f','roughness':':.1f','relief':':.1f',
                                             'winning_distance':':.5f','gap_to_runner_up':':.5f'},
                                 category_orders={'winner':raw['earth_site'].tolist()})
    ternary.update_traces(marker=dict(size=7, opacity=0.8))
    total_weight = sum(weights.values())
    ternary.add_trace(go.Scatterternary(
        a=[100*weights['slope']/total_weight],
        b=[100*weights['roughness']/total_weight],
        c=[100*weights['relief']/total_weight],
        mode='markers', name='Current weights',
        marker=dict(size=17, symbol='diamond', color=NAVY, line=dict(color='white',width=2)),
        hovertemplate='Your weights: slope %{a:.1f}%, roughness %{b:.1f}%, relief %{c:.1f}%<extra></extra>',
    ))
    ternary.update_layout(
        height=560, legend_title='Overall winner',
        ternary=dict(sum=100, aaxis_title='Slope (%)', baxis_title='Roughness (%)', caxis_title='Relief (%)'),
        margin=dict(l=25,r=25,t=10,b=10),
    )
    st.plotly_chart(nasa_chart(ternary), use_container_width=True)
    st.caption('This decision map is sampled on a regular 31-level weight grid. It is a deterministic sensitivity visualization, not a statistical confidence map. Candidate-set Min–Max normalization stays fixed for the selected target and Haughton setting.')

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
                      color_continuous_scale=[[0,'#0B3D91'],[0.5,'#7DA7D9'],[1,'#FC3D21']], zmin=1, zmax=len(heat),
                      text_auto=True, aspect='auto')
    fig_h.update_layout(height=390, margin=dict(l=5,r=10,t=10,b=90),
                        xaxis_tickangle=-25)
    st.plotly_chart(nasa_chart(fig_h), use_container_width=True)
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
                             color_continuous_scale=[[0,'#0B3D91'],[0.5,'#7DA7D9'],[1,'#FC3D21']],
                             range_color=(1, len(geo)))
    fig_geo.update_traces(marker=dict(size=13, line=dict(width=1, color='white')),
                          hovertemplate='<b>%{hovertext}</b><br>Rank: %{marker.color}<br>Distance: %{customdata[0]:.4f}<extra></extra>')
    fig_geo.update_geos(showland=True, landcolor='#EDF0F5', showocean=True, oceancolor='#DCE8F7',
                        showcountries=True, countrycolor='white')
    fig_geo.update_layout(height=480, margin=dict(l=0,r=0,t=0,b=0))
    st.plotly_chart(nasa_chart(fig_geo), use_container_width=True)
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

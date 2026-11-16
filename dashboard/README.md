# Lunar Analog Explorer

Interactive visualization of the **already generated** Novo Oeste HT NASA results. No external service, dataset download or terrain reprocessing is required.

## Run

From the project root:

```powershell
python -m pip install -r requirements-dashboard.txt
python -m streamlit run dashboard/app.py
```

The application loads `outputs/{shackleton,haworth}_ranking.csv`, matching sensitivity files, their `_without_haughton` equivalents, `outputs/pipeline_summary.json`, and `outputs/figures/*.png`.

If an output file is missing, run `python -m scripts.run_pipeline` first. The full demo ZIP already includes the outputs, so it can run without downloading NASA datasets.

## Features

- Select Shackleton or Haworth.
- Reweight slope, multi-scale roughness and relief using sliders.
- Re-rank candidates live, with a component contribution breakdown and CSV export.
- View the original lunar and terrestrial terrain figures side by side.
- Examine a 7-scenario rank heatmap and compare the Haughton-excluded ranking.
- See the geographic positions of Earth candidate windows and quality flags.

## Scientific scope

Composite distances are relative to the candidate pool and Min-Max scaling. The sensitivity heatmap is built from the fixed seven scenarios saved by the pipeline, not from the current slider weights. AVGVISIB is lunar context only; no terrestrial illumination equivalence is claimed. Terrain images use their original, non-identical color-bar ranges.

## Presentation highlight: Why the winner changes

The **⚖️ Why the winner changes** tab compares Tolbachik and Death Valley using the
three *archived normalized components*. It shows the original component distances,
the weighted differences that decide the head-to-head outcome, and a sampled ternary
map indicating which candidate wins for different non-negative metric weight mixes.
A diamond marks the weights currently chosen in the sidebar.

For **Shackleton**, Tolbachik and Death Valley tie at approximately **44.26% slope
weight** if the two remaining metrics share their weight equally. Higher slope
weight then favors Death Valley in this *head-to-head* comparison. For **Haworth**,
Tolbachik dominates most weight settings; when all the weight is assigned to
roughness alone, Haughton can win if it is included in the candidate set.

This is a **deterministic**, candidate-pool-dependent sensitivity graphic, not a
probability, terrain safety map, or environmental-equivalence model. Switching the
Haughton checkbox reuses the corresponding archived normalization and recomputes
the visualization consistently.

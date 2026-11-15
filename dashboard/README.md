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

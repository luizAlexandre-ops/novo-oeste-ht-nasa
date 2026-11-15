"""Run the complete lunar-to-Earth analogue comparison with one command."""
import argparse

from src.terrain.pipeline.runner import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-download", action="store_true", help="Require existing local lunar datasets")
    parser.add_argument("--include-diviner", action="store_true", help="Enable optional Diviner temperature layers")
    parser.add_argument("--no-plots", action="store_true", help="Skip PNG output")
    parser.add_argument("--skip-failed-sites", action="store_true", help="Continue if an Earth site fails to load")
    args = parser.parse_args()
    run_pipeline(
        skip_download=args.skip_download,
        include_diviner=args.include_diviner,
        generate_plots=not args.no_plots,
        strict=not args.skip_failed_sites,
    )


if __name__ == "__main__":
    main()

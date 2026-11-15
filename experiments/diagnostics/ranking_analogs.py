
from src.terrain.analysis.signature import build_signature
from src.terrain.comparison.comparison import (
    rank_analogs,
    sensitivity_analysis,
    export_ranking_csv,
)
from src.terrain.site import build_lunar_site, build_earth_site
from src.terrain.locations import (
    SHACKLETON_CRATER,
    HAWORTH_CRATER,
    EARTH_ANALOG_SITES,
)
from src.terrain.config import OUTPUT_DIRECTORY


def print_ranking(title, ranking):
    print(f"\n=== {title} ===")

    for result in ranking:
        print(
            f"{result['rank']}º - {result['earth_site']}: "
            f"{result['composite_distance']:.4f}"
        )


def print_sensitivity_results(title, results):
    print(f"\n=== {title} ===")

    current_scenario = None

    for result in results:
        if result["scenario"] != current_scenario:
            current_scenario = result["scenario"]

            print(f"\nCenário: {current_scenario}")
            print(
                f"Pesos: "
                f"Declividade={result['weight_slope']:.2f}, "
                f"Rugosidade={result['weight_roughness']:.2f}, "
                f"Relevo={result['weight_relief']:.2f}"
            )

        print(
            f"{result['rank']}º - {result['earth_site']}: "
            f"{result['composite_distance']:.4f}"
        )


def run_analysis(lunar_signature, earth_signatures, suffix=""):
    """
    Executa o ranking e a análise de sensibilidade
    para um alvo lunar.
    """
    ranking = rank_analogs(
        lunar_signature,
        earth_signatures,
    )

    sensitivity = sensitivity_analysis(
        lunar_signature,
        earth_signatures,
    )

    # File-safe output name
    lunar_name = lunar_signature.name.lower().replace(" ", "_")

    # Exporta ranking
    export_ranking_csv(
        ranking,
        OUTPUT_DIRECTORY / f"{lunar_name}_ranking{suffix}.csv",
    )

    # Export sensitivity analysis
    export_ranking_csv(
        sensitivity,
        OUTPUT_DIRECTORY / f"{lunar_name}_sensitivity{suffix}.csv",
    )

    print_ranking(
        f"RANKING {lunar_signature.name} {suffix}",
        ranking,
    )

    print_sensitivity_results(
        f"SENSIBILIDADE {lunar_signature.name} {suffix}",
        sensitivity,
    )

    return ranking, sensitivity


if __name__ == "__main__":
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)

    # 1. Build lunar signatures
    shackleton = build_signature(
        build_lunar_site(SHACKLETON_CRATER)
    )

    haworth = build_signature(
        build_lunar_site(HAWORTH_CRATER)
    )

    lunar_signatures = [
        shackleton,
        haworth,
    ]

    # 2. Build Earth signatures
    earth_signatures = [
        build_signature(build_earth_site(location))
        for location in EARTH_ANALOG_SITES
    ]

    # 3. Build a second candidate list without Haughton
    earth_without_haughton = [
        signature
        for signature in earth_signatures
        if signature.name != "Haughton Crater"
    ]

    # 4. Run both analyses
    for lunar in lunar_signatures:

        # Original analysis: all candidates
        original_ranking, original_sensitivity = run_analysis(
            lunar,
            earth_signatures,
        )

        # Alternative analysis: exclude Haughton
        filtered_ranking, filtered_sensitivity = run_analysis(
            lunar,
            earth_without_haughton,
            suffix="_without_haughton",
        )

        # 5. Compara os vencedores
        original_winner = original_ranking[0]["earth_site"]
        filtered_winner = filtered_ranking[0]["earth_site"]

        print(f"\n=== COMPARAÇÃO FINAL: {lunar.name} ===")
        print(f"Vencedor original: {original_winner}")
        print(f"Vencedor sem Haughton: {filtered_winner}")

        if original_winner == filtered_winner:
            print("OK: o primeiro colocado permaneceu igual.")
        else:
            print("ATENÇÃO: o primeiro colocado mudou.")

        # Compare the winner in each sensitivity scenario
        original_winners = {
            result["scenario"]: result["earth_site"]
            for result in original_sensitivity
            if result["rank"] == 1
        }

        filtered_winners = {
            result["scenario"]: result["earth_site"]
            for result in filtered_sensitivity
            if result["rank"] == 1
        }

        print("\nComparação dos cenários de sensibilidade:")

        for scenario, winner in original_winners.items():
            filtered_winner = filtered_winners[scenario]

            status = (
                "IGUAL"
                if winner == filtered_winner
                else "ALTERADO"
            )

            print(
                f"{scenario}: "
                f"{winner} -> {filtered_winner} [{status}]"
            )

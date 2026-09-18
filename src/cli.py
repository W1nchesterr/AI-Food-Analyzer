import argparse
import asyncio
import sys
from pathlib import Path

from src.config import get_settings
from src.core.analyzer import analyze_meal
from src.storage.repository import AnalysisRecord, AnalysisRepository


def print_totals_table(ingredients: list[dict], totals: dict) -> None:
    print(f"\n{'ingredient':<25} {'g':<6} {'kcal':<8} {'protein':<8} {'carbs':<8} {'fat':<8}")
    print("-" * 65)

    for item in ingredients:
        grams = item.get("estimated_grams", item.get("grams", 0))
        print(
            f"{item['name']:<25} "
            f"{grams:<6.0f} "
            f"{item['kcal']:<8.1f} "
            f"{item['protein']:<8.1f} "
            f"{item['carbs']:<8.1f} "
            f"{item['fat']:<8.1f}"
        )

    print("-" * 65)
    print(
        f"{'TOTAL':<25} "
        f"{'':<6} "
        f"{totals['kcal']:<8.1f} "
        f"{totals['protein']:<8.1f} "
        f"{totals['carbs']:<8.1f} "
        f"{totals['fat']:<8.1f}\n"
    )


async def run_cli(image_path_str: str, offline: bool = False) -> None:
    image_path = Path(image_path_str)

    if not image_path.exists():
        print(f"Xəta: Şəkil tapılmadı -> {image_path_str}")
        sys.exit(1)

    print(f"Analiz edilir: {image_path.name} (mode={'offline' if offline else 'online'})...\n")

    try:
        result = await analyze_meal(str(image_path), offline=offline)
    except Exception as e:
        print(f"Analiz zamanı xəta baş verdi: {e}")
        sys.exit(1)

    if not result or not result.get("ingredients"):
        print("Yemək müəyyən edilmədi (Meal not recognized).")
        return

    print_totals_table(result["ingredients"], result["totals"])

    try:
        settings = get_settings()
        repo = await AnalysisRepository.create(dsn=settings.DATABASE_URL)

        record = AnalysisRecord(
            image_path=str(image_path),
            ingredients=result["ingredients"],
            total_kcal=result["totals"]["kcal"],
            total_protein=result["totals"]["protein"],
            total_carbs=result["totals"]["carbs"],
            total_fat=result["totals"]["fat"],
        )
        record_id = await repo.save_analysis(record)
        print(f"Analiz uğurla bazaya yazıldı! Record ID: {record_id}")
        await repo.close()
    except Exception as e:
        print(f"Xəbərdarlıq: Nəticə bazaya yazıla bilmədi: {e}")


def main():
    parser = argparse.ArgumentParser(description="AI Food Analyzer CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze_parser = subparsers.add_parser("analyze", help="Analyze a meal image")
    analyze_parser.add_argument("image_path", type=str, help="Path to the image file")
    analyze_parser.add_argument("--offline", action="store_true", help="Run in offline mode using fakes")

    args = parser.parse_args()

    if args.command == "analyze":
        asyncio.run(run_cli(args.image_path, offline=args.offline))


if __name__ == "__main__":
    main()
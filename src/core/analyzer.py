import asyncio

from src.services.ai_service import AIService
from src.services.nutrition_cache import NutritionCache
from src.concurrency.pipeline import fetch_all_nutrition
from ai import compute_totals


class Analyzer:
    def __init__(self, ai_service: AIService, nutrition_provider, cache: NutritionCache):
        self.ai_service = ai_service
        self.nutrition_provider = nutrition_provider
        self.cache = cache

    async def analyze(self, image_path: str):
        loop = asyncio.get_running_loop()

        ingredients = await loop.run_in_executor(
            None, self.ai_service.identify_ingredients, image_path
        )

        if not ingredients:
            return {"ingredients": [], "totals": None, "failed": []}

        facts_by_name, failed = await fetch_all_nutrition(
            ingredients, self.nutrition_provider, self.cache
        )

        totals = compute_totals(ingredients, facts_by_name)

        return {
            "ingredients": ingredients,
            "facts_by_name": facts_by_name,
            "totals": totals,
            "failed": failed,
        }




if __name__ == "__main__":
    from ai import get_nutrition_provider

    async def main():
        ai_service = AIService(max_size_bytes=5 * 1024 * 1024)  # 5MB limit
        provider = get_nutrition_provider()
        cache = NutritionCache(ttl_seconds=86400)

        analyzer = Analyzer(ai_service, provider, cache)

        result = await analyzer.analyze("data/bread_cheese.png")
        print("İnqrediyentlər:", result["ingredients"])
        print("Cəmi:", result["totals"])
        print("Uğursuz:", result["failed"])

    asyncio.run(main())
    #commit problem
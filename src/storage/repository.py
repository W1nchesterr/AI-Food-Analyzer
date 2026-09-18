from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

import asyncpg

logger = logging.getLogger(__name__)


@dataclass
class AnalysisRecord:
    """One row of analysis history."""

    image_path: str
    ingredients: list[dict[str, Any]]
    total_kcal: float
    total_protein: float
    total_carbs: float
    total_fat: float
    id: Optional[int] = None
    timestamp: Optional[datetime] = None


class AnalysisRepository:
    """Async PostgreSQL repository for analysis history."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    @classmethod
    async def create(cls, dsn: str, *, min_size: int = 1, max_size: int = 10) -> "AnalysisRepository":
        """Open a connection pool and return a repository wrapping it."""
        pool = await asyncpg.create_pool(dsn=dsn, min_size=min_size, max_size=max_size)
        return cls(pool)

    async def close(self) -> None:
        await self._pool.close()

    async def save_analysis(self, record: AnalysisRecord) -> int:
        """Insert a new analysis row."""
        query = """
            INSERT INTO analyses
                (image_path, ingredients, total_kcal, total_protein, total_carbs, total_fat)
            VALUES ($1, $2::jsonb, $3, $4, $5, $6)
            RETURNING id, timestamp;
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    record.image_path,
                    json.dumps(record.ingredients),
                    record.total_kcal,
                    record.total_protein,
                    record.total_carbs,
                    record.total_fat,
                )
        except Exception:
            logger.exception("Failed to save analysis for %s", record.image_path)
            raise

        record.id = row["id"]
        record.timestamp = row["timestamp"]
        logger.info("Saved analysis id=%s image=%s", record.id, record.image_path)
        return record.id

    async def get_by_id(self, analysis_id: int) -> Optional[AnalysisRecord]:
        query = "SELECT * FROM analyses WHERE id = $1;"
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, analysis_id)
        if row is None:
            return None
        return self._row_to_record(row)

    async def list_recent(self, limit: int = 20) -> list[AnalysisRecord]:
        query = "SELECT * FROM analyses ORDER BY timestamp DESC LIMIT $1;"
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, limit)
        return [self._row_to_record(r) for r in rows]

    @staticmethod
    def _row_to_record(row: Any) -> AnalysisRecord:
        ingredients = row["ingredients"]
        if isinstance(ingredients, str):
            ingredients = json.loads(ingredients)
        return AnalysisRecord(
            id=row["id"],
            timestamp=row["timestamp"],
            image_path=row["image_path"],
            ingredients=ingredients,
            total_kcal=float(row["total_kcal"]),
            total_protein=float(row["total_protein"]),
            total_carbs=float(row["total_carbs"]),
            total_fat=float(row["total_fat"]),
        )
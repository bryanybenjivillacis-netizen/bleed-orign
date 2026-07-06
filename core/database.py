import asyncpg

from core.config import DATABASE_URL
from core.schema import SCHEMA

pool: asyncpg.Pool | None = None


async def init_db():
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL, ssl="require")
    async with pool.acquire() as conn:
        await conn.execute(SCHEMA)


async def close_pool():
    if pool is not None:
        await pool.close()

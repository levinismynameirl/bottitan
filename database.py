import asyncpg
import os

async def create_pool():
    """Create and return a connection pool for the PostgreSQL database."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set.")
    return await asyncpg.create_pool(database_url)

async def initialize_database(pool):
    """Initialize the PostgreSQL database."""
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS points (
                user_id BIGINT PRIMARY KEY,
                points INT DEFAULT 0
            );
        """)
    print("✅ Database initialized successfully.")
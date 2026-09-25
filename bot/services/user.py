import aiosqlite
from datetime import datetime, timedelta
from typing import Optional

from loader import settings


class UserService:
    def __init__(self, db_path: str = settings.db_path):
        self.db_path = db_path

    async def init_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    full_name TEXT,
                    created_at TEXT NOT NULL,
                    is_banned INTEGER DEFAULT 0
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    plan TEXT NOT NULL,
                    starts_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    payment_id TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    subscription_id INTEGER NOT NULL,
                    key_value TEXT NOT NULL,
                    config_link TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id)
                )
            """)
            await db.commit()

    async def ensure_user(self, user_id: int, username: Optional[str], full_name: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO users (user_id, username, full_name, created_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    username = excluded.username,
                    full_name = excluded.full_name
                """,
                (user_id, username, full_name, datetime.utcnow().isoformat()),
            )
            await db.commit()

    async def is_banned(self, user_id: int) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT is_banned FROM users WHERE user_id = ?", (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return bool(row and row[0])

    async def set_ban(self, user_id: int, banned: bool = True):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET is_banned = ? WHERE user_id = ?",
                (1 if banned else 0, user_id),
            )
            await db.commit()

    async def get_active_subscription(self, user_id: int) -> Optional[dict]:
        now = datetime.utcnow().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT * FROM subscriptions
                WHERE user_id = ? AND is_active = 1 AND expires_at > ?
                ORDER BY expires_at DESC LIMIT 1
                """,
                (user_id, now),
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def create_subscription(
        self,
        user_id: int,
        plan: str,
        days: int,
        payment_id: Optional[str] = None,
    ) -> int:
        now = datetime.utcnow()
        starts_at = now
        expires_at = now + timedelta(days=days)

        # Если уже есть активная подписка — продлеваем от её конца
        current = await self.get_active_subscription(user_id)
        if current:
            current_expires = datetime.fromisoformat(current["expires_at"])
            if current_expires > now:
                starts_at = current_expires
                expires_at = current_expires + timedelta(days=days)

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO subscriptions (user_id, plan, starts_at, expires_at, is_active, payment_id)
                VALUES (?, ?, ?, ?, 1, ?)
                """,
                (
                    user_id,
                    plan,
                    starts_at.isoformat(),
                    expires_at.isoformat(),
                    payment_id,
                ),
            )
            await db.commit()
            return cursor.lastrowid

    async def get_user_key(self, user_id: int) -> Optional[dict]:
        sub = await self.get_active_subscription(user_id)
        if not sub:
            return None

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT * FROM keys
                WHERE user_id = ? AND subscription_id = ?
                ORDER BY created_at DESC LIMIT 1
                """,
                (user_id, sub["id"]),
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def save_key(
        self,
        user_id: int,
        subscription_id: int,
        key_value: str,
        config_link: Optional[str] = None,
    ):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO keys (user_id, subscription_id, key_value, config_link, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    subscription_id,
                    key_value,
                    config_link,
                    datetime.utcnow().isoformat(),
                ),
            )
            await db.commit()

    async def count_users(self) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM users") as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def count_active_subs(self) -> int:
        now = datetime.utcnow().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT COUNT(*) FROM subscriptions WHERE is_active = 1 AND expires_at > ?",
                (now,),
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0


user_service = UserService()

from neo4j import AsyncGraphDatabase
from src.core.config import settings

class Neo4jConnection:
    def __init__(self):
        self.driver = None

    async def connect(self):
        self.driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )

    async def close(self):
        if self.driver:
            await self.driver.close()

db = Neo4jConnection()

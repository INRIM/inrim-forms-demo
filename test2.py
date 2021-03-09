from motor.motor_asyncio import AsyncIOMotorClient

from odmantic import AIOEngine, Model


class Forms(Model):
    name: str


client = AsyncIOMotorClient(
    "mongodb://root:cAoMhDYU6+^eYIO@docker.ininrim.it:27018/test_forms",
    # username="root",
    # password='cAoMhDYU6+^eYIO',
    replicaset="rs",
    serverSelectionTimeoutMS=10, connectTimeoutMS=20000)

engine = AIOEngine(motor_client=client)
motor_collection = engine.get_collection(Forms)
print(motor_collection)
# print(await engine.database.list_collection_names())

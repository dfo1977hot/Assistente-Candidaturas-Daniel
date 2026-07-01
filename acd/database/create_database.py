from acd.database.database import engine
from acd.models.base import Base
# importa os models
import acd.models.company
def create_database():
    Base.metadata.create_all(engine)
if __name__ == "__main__":
    create_database()
    print("Banco criado com sucesso.")
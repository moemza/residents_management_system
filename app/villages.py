from .models import Village
from .database import SessionLocal

def get_all_villages():
    return [{"id": i + 1, "name": name} for i, name in enumerate(VILLAGES)]

VILLAGES = [
    "Village A",
    "Village B",
    "Village C",
    "Village D"
]
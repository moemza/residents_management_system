from .models import Village
from .database import SessionLocal

def get_all_villages():
    return VILLAGES

VILLAGES = [
    "Village A",
    "Village B",
    "Village C",
    "Village D"
]
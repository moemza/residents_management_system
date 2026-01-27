from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .home_routes import router as home_router
from .search_routes import router as search_router
from .resident_routes import router as resident_router

app = FastAPI()

# Include all routers
app.include_router(home_router)
app.include_router(search_router)
app.include_router(resident_router)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
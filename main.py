import os 
from typing import Any, List, Optional, Dict
from config.config import settings

from fastapi_users import fastapi_users, FastAPIUsers

from fastapi import FastAPI, Request, Depends, HTTPException, Request, Cookie, status
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from database.session import create_db, drop_db

from api.routers import router as api_router
from api.auth import router as auth_router

from config.config import settings


async def on_startup():
    drop_database = False
    if drop_database == True:
        await drop_db()
    await create_db()
    print("Database created")

app = FastAPI(title="Epocha Admin Panel", on_startup=[on_startup])
templates = Jinja2Templates(directory="web/templates")
app.mount("/static", StaticFiles(directory=rf"{settings.STATIC_FOLDER}"), name="static")




app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "DELETE", "PATCH", "PUT"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(auth_router)

# 
# Default endpoints
# 
@app.get("/")
async def root(request: Request, auth_token: Optional[str] = Cookie(None)):
    if auth_token is None:
        return templates.TemplateResponse("index.html", {"request": request})
    else:
        return templates.TemplateResponse("admin.html", {"request": request})


@app.get("/admin")
async def admin_panel(request: Request, auth_token: Optional[str] = Cookie(None)):
    if auth_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )
    else:
        return templates.TemplateResponse("admin.html", {"request": request})


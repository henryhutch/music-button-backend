from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import songs, oauth, buttons, playlist
from app.db import create_db_and_tables

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://music-button.henryhutchison.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()


app.include_router(oauth.router)
app.include_router(songs.router)
app.include_router(buttons.router)
app.include_router(playlist.router)


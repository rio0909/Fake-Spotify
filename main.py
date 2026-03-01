import os
import urllib.parse
from typing import Optional
from fastapi import FastAPI, Request, Form, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Template
from sqlmodel import Field, Session, SQLModel, create_engine, select
from passlib.context import CryptContext
import yt_dlp

# Absolute Paths for your Server
BASE_DIR = "/home/server1/my_streamer"
MUSIC_DIR = os.path.join(BASE_DIR, "music")
DB_PATH = os.path.join(BASE_DIR, "users.db")
HTML_PATH = os.path.join(BASE_DIR, "index.html")

# Database & Security
sqlite_url = f"sqlite:///{DB_PATH}"
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True)
    password: str

class PlaylistEntry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    song_file: str

SQLModel.metadata.create_all(engine)
app = FastAPI()

if os.path.exists(MUSIC_DIR):
    app.mount("/music", StaticFiles(directory=MUSIC_DIR), name="music")

def get_session():
    with Session(engine) as session:
        yield session

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, session: Session = Depends(get_session), show_liked: bool = False):
    username = request.cookies.get("user")
    
    if not username:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    user_playlist = session.exec(select(PlaylistEntry).where(PlaylistEntry.username == username)).all()
    liked_files = [p.song_file for p in user_playlist]

    songs = []
    if os.path.exists(MUSIC_DIR):
        for filename in os.listdir(MUSIC_DIR):
            if filename.endswith(".mp3"):
                encoded = urllib.parse.quote(filename)
                is_liked = encoded in liked_files
                if show_liked and not is_liked: continue
                songs.append({
                    "file_name": encoded,
                    "display_name": filename.rsplit(".", 1)[0].replace("'", "\\'"),
                    "raw_name": filename.rsplit(".", 1)[0],
                    "is_liked": is_liked
                })
    
    songs.sort(key=lambda x: x["raw_name"].lower())
    
    with open(HTML_PATH, "r", encoding="utf-8") as f:
        template = Template(f.read())
        return HTMLResponse(template.render(songs=songs, username=username, show_liked=show_liked))

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    return """
    <html><body style="background:#000;color:white;font-family:sans-serif;display:flex;flex-direction:column;align-items:center;padding-top:100px;">
        <h2 style="color:#1DB954; font-size: 32px;">Rio Music</h2>
        <form action="/login" method="post" style="display:flex;flex-direction:column;gap:15px;width:320px;background:#181818;padding:40px;border-radius:8px;">
            <input name="username" placeholder="Username" required style="padding:14px;background:#282828;border:none;color:white;border-radius:4px;">
            <input name="password" type="password" placeholder="Password" required style="padding:14px;background:#282828;border:none;color:white;border-radius:4px;">
            <button type="submit" style="padding:14px;background:#1DB954;color:black;border:none;border-radius:30px;cursor:pointer;font-weight:bold;">LOG IN</button>
        </form>
    </body></html>
    """

@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...), session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == username)).first()
    safe_pw = password[:72]
    if not user:
        user = User(username=username, password=pwd_context.hash(safe_pw))
        session.add(user)
        session.commit()
    elif not pwd_context.verify(safe_pw, user.password):
        return HTMLResponse("<h2>Invalid Login</h2><a href='/login'>Try again</a>")
    
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="user", value=username, max_age=2592000, path="/")
    return response

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login")
    response.delete_cookie("user")
    return response

@app.post("/toggle-like")
async def toggle_like(request: Request, song: str = Form(...), session: Session = Depends(get_session)):
    username = request.cookies.get("user")
    if not username: return RedirectResponse(url="/login")
    existing = session.exec(select(PlaylistEntry).where(PlaylistEntry.username == username, PlaylistEntry.song_file == song)).first()
    if existing: session.delete(existing)
    else: session.add(PlaylistEntry(username=username, song_file=song))
    session.commit()
    return RedirectResponse(url=request.headers.get("referer", "/"), status_code=status.HTTP_303_SEE_OTHER)

# --- NEW: Live SoundCloud Integration ---
@app.get("/api/soundcloud/search")
def search_soundcloud(q: str):
    """Searches SoundCloud without downloading anything."""
    ydl_opts = {'extract_flat': True, 'quiet': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            # Fetches the top 15 results from SoundCloud
            info = ydl.extract_info(f"scsearch15:{q}", download=False)
            return info.get('entries', [])
        except Exception as e:
            return {"error": str(e)}

@app.get("/api/soundcloud/stream")
def stream_soundcloud(url: str):
    """Resolves the direct audio stream URL and redirects the player to it."""
    ydl_opts = {'format': 'bestaudio/best', 'quiet': True, 'noplaylist': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            # Redirect the frontend to the live audio stream
            return RedirectResponse(url=info.get('url'))
        except Exception as e:
            return {"error": str(e)}
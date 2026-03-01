# Fake-Spotify
Rio Music is a full-stack Spotify-inspired web application built with FastAPI, SQLModel, and JavaScript. It allows users to stream music from a local server, manage liked songs, and live-stream audio directly from SoundCloud via dynamic backend integration.

🚀 Features
🔐 User Authentication

Secure login system

Password hashing using bcrypt

Session management with cookies

Automatic user creation on first login

🎶 Local Music Streaming

Streams .mp3 files from a server directory

Dynamic music listing

Search functionality

Previous / Next controls

Playback slider and volume control

❤️ Liked Songs System

Users can like/unlike tracks

Stored in SQLite database

Personalized playlists

Filter view for liked songs only

☁️ Live SoundCloud Streaming

Real-time SoundCloud search

Streams audio without downloading

Backend resolves direct audio streams using yt_dlp

No file storage required

🎧 Advanced Audio Controls

Play / Pause

Next / Previous

Seek bar

Volume control

Keyboard spacebar support

Auto-play next track

🛠 Tech Stack
Backend

FastAPI

SQLModel

SQLite

Passlib (bcrypt hashing)

yt_dlp (SoundCloud streaming)

Jinja2 templating

Frontend

HTML5

CSS3 (Spotify-inspired UI)

JavaScript (Vanilla JS)

FontAwesome Icons

HTML5 Audio API

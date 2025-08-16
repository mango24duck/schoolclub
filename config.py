import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(os.path.dirname(__file__), 'instance', 'clubhub.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8MB
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

os.makedirs(os.path.join(os.path.dirname(__file__), 'instance'), exist_ok=True)
os.makedirs(os.path.join(os.path.dirname(__file__), 'uploads'), exist_ok=True)
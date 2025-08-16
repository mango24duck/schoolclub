from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


db = SQLAlchemy()

# 태그(예: 과학, 토론, 문학 등)
class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

# 동아리-태그 다대다 연결 테이블
club_tags = db.Table(
    'club_tags',
    db.Column('club_id', db.Integer, db.ForeignKey('club.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id')),
)

class Club(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    one_liner = db.Column(db.String(200))
    description = db.Column(db.Text)
    logo_filename = db.Column(db.String(255))

    # 모집 정보
    recruit_start = db.Column(db.Date)
    recruit_end = db.Column(db.Date)
    interview_datetime = db.Column(db.String(120))  # 장소/일시 자유기재
    capacity = db.Column(db.Integer)
    form_link = db.Column(db.String(255))
    last_year_competition = db.Column(db.String(50))  # 미기재 허용 -> 문자열
    contact = db.Column(db.String(120))
    closed = db.Column(db.Boolean, default=False)

    tags = db.relationship('Tag', secondary=club_tags, backref='clubs')
    images = db.relationship('ClubImage', backref='club', cascade='all, delete')

class ClubImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'))

# 회장 계정(사전 승인된 아이디)
class President(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=True)  # 자신의 동아리
    club = db.relationship('Club', backref='president', uselist=False)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

# 공지(관심 동아리 알림용)
class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    club = db.relationship('Club', backref='announcements')
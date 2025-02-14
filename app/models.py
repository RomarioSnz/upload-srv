# Работа с db, нужна доработка
from datetime import datetime
from . import db

class Upload(db.Model):
    __tablename__ = 'uploads'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    archive_name = db.Column(db.String(255), nullable=False)
    file_count = db.Column(db.Integer)
    filesize = db.Column(db.BigInteger)
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Upload {self.archive_name}>'

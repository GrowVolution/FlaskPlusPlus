from app.extensions import db


class YourModel(db.Model):
    __tablename__ = 'your_table'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(32), nullable=False)
    email = db.Column(db.String(64), nullable=False, unique=True)
    message = db.Column(db.String, nullable=False)
    received_at = db.Column(db.DateTime, nullable=False,
                           default=db.func.now())

    def __init__(self, name: str, email: str, message: str):
        self.name = name
        self.email = email
        self.message = message

    def __repr__(self):
        return '<YourModel %r>' % self.name

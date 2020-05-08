"""
models.py
- Data classes for the quantumapi application
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'

    student_id = db.Column(db.Integer, primary_key=True)
    is_admin = db.Column(db.Integer)
    first_name = db.Column(db.String(191), nullable=False)
    last_name = db.Column(db.String(191), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    confirm_admin = db.Column(db.String(255), nullable=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    updated_date = db.Column(db.DateTime, default=datetime.utcnow)

    circuits = relationship("Circuit")

    def __init__(self, student_id, is_admin, first_name, last_name, email, password, confirm_admin):
        self.student_id = student_id
        self.is_admin = is_admin
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password = generate_password_hash(password, method='sha256')
        self.confirm_admin = generate_password_hash(confirm_admin, method='sha256')
    
    @classmethod
    def authenticate(cls, **kwargs):
        email = kwargs.get('email')
        password = kwargs.get('password')
        
        if not email or not password:
            return None

        user = cls.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password, password):
            return None

        return user

    def to_dict(self):
        return dict(id=self.student_id, email=self.email)


class Circuit(db.Model):
    __tablename__ = 'circuits'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.student_id'), nullable=False)
    circuit_name = db.Column(db.String(191), unique=True, nullable=False)
    circuit_input = db.Column(db.Text(4294000000), nullable=False)
    circuit_output_json = db.Column(db.Text(4294000000), nullable=False)
    algorithm_grade = db.Column(db.Integer)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    updated_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, student_id, circuit_name, circuit_input, circuit_output_json, grade):
        self.student_id = student_id
        self.circuit_name = circuit_name
        self.circuit_input = circuit_input
        self.circuit_output_json = circuit_output_json
        self.algorithm_grade = grade
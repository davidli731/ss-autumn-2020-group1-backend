"""
models.py
- Data classes for the quantumapi application
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'

    student_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(191), nullable=False)
    last_name = db.Column(db.String(191), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    updated_date = db.Column(db.DateTime, default=datetime.utcnow)


    def __init__(self, student_id, first_name, last_name, email, password):
        self.student_id = student_id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password = generate_password_hash(password, method='sha256')

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
        return dict(id=self.id, email=self.email)


class Circuit(db.Model):
    __tablename__ = 'circuits'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.student_id'), nullable=False)
    circuit_name = db.Column(db.String(191), unique=True, nullable=False)
    circuit_input = db.Column(db.Text(4294000000), nullable=False)
    circuit_output_json = db.Column(db.Text(4294000000), nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    updated_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, student_id, circuit_name, circuit_input, circuit_output_json):
        self.student_id = student_id
        self.circuit_name = circuit_name
        self.circuit_input = circuit_input
        self.circuit_output_json = circuit_output_json

    # Search function for circuit given student_id and circuit_name
    @classmethod
    def search_circuit(cls, **kwargs):
        student_id = kwargs.get('student_id')
        circuit_name = kwargs.get('circuit_name')

        if not student_id or not circuit_name:
            return None

        user = cls.query.filter_by(student_id=student_id).first()
        if user is not None:
            circuit = user.query.filter_by(circuit_name=circuit_name).first()
            if circuit is not None:
                return circuit

        return None
"""
api.py
- provides the API endpoints for consuming and producing
  REST requests and responses
"""

from flask import Blueprint, jsonify, request, make_response, current_app
from flask_cors import CORS, cross_origin
from datetime import datetime, timedelta
from sqlalchemy import exc
from functools import wraps
from .models import db, User, Circuit
from .services.calculate_circuit import calculate_circuit
import jwt

api = Blueprint('api', __name__)

@api.route('/')
@cross_origin()
def index():
    response = { 'Status': "API is up and running!" }
    return make_response(jsonify(response),200)


@api.route('/register', methods=('POST',))
@cross_origin()
def register():
    data = request.get_json()
    user = User(**data)
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201


@api.route('/login', methods=('POST',))
@cross_origin()
def login():
    data = request.get_json()
    user = User.authenticate(**data)

    if not user:
        return jsonify({ 'message': 'Invalid credentials', 'authenticated': False }), 401

    token = jwt.encode({
        'sub': user.email,
        'iat':str(datetime.utcnow()),
        'exp': str(datetime.utcnow() + timedelta(minutes=30))},
        current_app.config['SECRET_KEY'])
    return jsonify({ 'token': token.decode('UTF-8') })


# This is a decorator function which will be used to protect authentication-sensitive API endpoints
def token_required(f):
    @wraps(f)
    def _verify(*args, **kwargs):
        auth_headers = request.headers.get('Authorization', '').split()

        invalid_msg = {
            'message': 'Invalid token. Registeration and / or authentication required',
            'authenticated': False
        }
        expired_msg = {
            'message': 'Expired token. Reauthentication required.',
            'authenticated': False
        }

        if len(auth_headers) != 2:
            return jsonify(invalid_msg), 401

        try:
            token = auth_headers[1]
            data = jwt.decode(token, current_app.config['SECRET_KEY'])
            user = User.query.filter_by(email=data['sub']).first()
            if not user:
                raise RuntimeError('User not found')
            return f(user, *args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify(expired_msg), 401 # 401 is Unauthorized HTTP status code
        except (jwt.InvalidTokenError, Exception) as e:
            print(e)
            return jsonify(invalid_msg), 401

    return _verify


# Take in an input json of circuit components, return circuit output JSON
@api.route('/calculate', methods=('POST',))
@cross_origin()
def calculate():
    try:
        data = request.json
        engine = calculate_circuit(data)
        circuit_output = engine.calculate()
        return jsonify(circuit_output)
    except Exception as e:
        return jsonify({ 'message': e.args })


# Fetch student_id, circuit name and circuit JSON from payload and save to DB
@api.route('/save-circuit', methods=('POST',))
@cross_origin()
def save_circuit():
    try:
        data = request.get_json()
        circuit = Circuit(**data)
        db.session.add(circuit)
        db.session.commit()
        db.session.close()

        return jsonify({ 'message': "circuit saved successfully" })
    except exc.SQLAlchemyError as e:
        db.session.rollback()

        return jsonify({ 'message': e.args })
        
# Delete circuit based on student_id and circuit name found in payload
@api.route('/delete-circuit', methods=('POST',))
@cross_origin()
def delete_circuit():
    try:
        data = request.get_json()
        to_delete_algorithm = Circuit.query.filter_by(circuit_name=data['circuit_name']).filter_by(student_id=data['student_id']).first()

        if to_delete_algorithm:
            db.session.delete(to_delete_algorithm)
            db.session.commit()
            return jsonify({ 'message': "Circuit found and deleted"}), 200
        else:
            return jsonify({ 'message': "Circuit not found"}), 400
        
    except exc.SQLAlchemyError as e:
        db.session.rollback()

        return jsonify({ 'message': e.args })

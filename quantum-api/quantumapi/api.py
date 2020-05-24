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
def index():
    response = { 'Status': "API is up and running!" }
    return make_response(jsonify(response), 200)


@api.route('/register', methods=('POST',))
def register():
    data = request.get_json()
    user = User(**data)
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201


@api.route('/login', methods=('POST',))
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
    student_id = User.query.filter_by(email=data['email']).first().student_id
    is_admin = User.query.filter_by(email=data['email']).first().is_admin
    return jsonify({ 'student_id': student_id , 'is_admin': is_admin, 'token': token.decode('UTF-8') }), 200


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
def calculate():
    try:
        data = request.json
        engine = calculate_circuit(data)
        circuit_output = engine.calculate()
        return jsonify(circuit_output), 200
    except Exception as e:
        return jsonify({ 'message': e.args }), 400


# Fetch student_id, circuit name and circuit JSON from payload and save to DB
@api.route('/save-circuit', methods=('POST',))
def save_circuit():
    try:
        data = request.get_json()
        circuit = Circuit(**data)
        db.session.add(circuit)
        db.session.commit()
        db.session.close()

        return jsonify({ 'message': "Circuit saved successfully" }), 201
    except exc.SQLAlchemyError as e:
        db.session.rollback()

        return jsonify({ 'message': e.args }), 500
        
# Delete circuit based on student_id and circuit name found in payload
@api.route('/delete-circuit', methods=('POST',))
def delete_circuit():
    try:
        data = request.get_json()
        to_delete_circuit = Circuit.query.filter_by(circuit_name=data['circuit_name']).filter_by(student_id=data['student_id']).first()

        if to_delete_circuit:
            #db.session.delete(to_delete_circuit)
            to_delete_circuit.is_deleted = True
            db.session.commit()
            return jsonify({ 'message': "Circuit found and deleted"}), 200
        else:
            return jsonify({ 'message': "Circuit not found"}), 400
        
    except exc.SQLAlchemyError as e:
        db.session.rollback()

        return jsonify({ 'message': e.args }), 500

# Update circuit grade and flag is_graded = True based on student_id, circuit name and grade found in payload
@api.route('/grade-circuit', methods=('POST',))
@cross_origin()
def grade_circuit():
    try:
        data = request.get_json()
        to_grade_circuit = Circuit.query.filter_by(circuit_name=data['circuit_name']).filter_by(student_id=data['student_id']).first()

        if to_grade_circuit:
            to_grade_circuit.algorithm_grade = data['grade']
            to_grade_circuit.is_graded = True
            db.session.commit()
            return jsonify({ 'message': "Circuit grade updated successfully"}), 200
        else:
            return jsonify({ 'message': "Circuit not found"}), 400
        
    except exc.SQLAlchemyError as e:
        db.session.rollback()

        return jsonify({ 'message': e.args }), 500
        
# Update circuit flag is_submitted = True based on student_id and circuit name found in payload
@api.route('/submit-circuit', methods=('POST',))
@cross_origin()
def submit_circuit():
    try:
        data = request.get_json()
        to_submit_circuit = Circuit.query.filter_by(circuit_name=data['circuit_name']).filter_by(student_id=data['student_id']).first()

        if to_submit_circuit:
            to_submit_circuit.is_submitted = True
            db.session.commit()
            return jsonify({ 'message': "Circuit submitted successfully"}), 200
        else:
            return jsonify({ 'message': "Circuit not found"}), 400
        
    except exc.SQLAlchemyError as e:
        db.session.rollback()

        return jsonify({ 'message': e.args }), 500

# Retrieve all circuits or based on studentid found in payload
@api.route('/retrieve-circuits', methods=('POST',))
@cross_origin()
def retrieve_circuits():
    try:
        data = request.get_json()
    
        #Check for valid keys, return 400 bad request if invlaid key is found
        for key in data:
            if hasattr(Circuit, key):
                valid_attributes = 1
            else:
                valid_attributes = 0
                break
            
    
        #Continue only if valid attributes exist, thorw 400 bad request if not
        if valid_attributes:
            query = ['SELECT * FROM circuits where ']
            counter = 1
            for key in data:
                query.append(key + " = '"  + str(data[key]) + "'")
                if counter < len(data):
                    query.append(' AND ') 
                    counter += 1
                query_final = ''.join(query)
                    
            #check if student_id attr is included in payload. 
            if data.get("student_id"):
                
                #If student id is set to "all", return all circuits in the db
                if data['student_id'] == 'all':
                    all_circuits = db.session.execute('SELECT * FROM circuits')
                    return jsonify({ 'circuits': to_dict(all_circuits)}), 200
                    
                    #For all other cases, use the dynamically build query    
                else:
                    all_circuits = db.session.execute(query_final)                    
                    return jsonify({ 'circuits': to_dict(all_circuits)}), 200
            
            #Catches payloads missing student_id           
            else:
                all_circuits = db.session.execute(query_final)
                return jsonify({ 'circuits': to_dict(all_circuits)}), 200

        else:
            return jsonify({'message': 'Invalid atrributes.'}), 400
    
    except exc.SQLAlchemyError as e:
        db.session.rollback()
        
        return jsonify({ 'message': e.args }), 500

#converts a resultproxy object type to dict
def to_dict(resultproxy):
    d, a = {}, []
    for rowproxy in resultproxy:
        # rowproxy.items() returns an array like [(key0, value0), (key1, value1)]
        for column, value in rowproxy.items():
            # build up the dictionary
            d = {**d, **{column: value}}
        a.append(d)
    return a
    
        
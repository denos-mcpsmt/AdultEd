# app.py

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity
)
from flask_cors import CORS
import os

app = Flask(__name__)

# Configuration settings
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Replace with your secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key_here'  # Replace with your JWT secret key
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)
CORS(app)  # Enable CORS for all routes

# User model with role
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'student' or 'teacher'

# Class model with instructor relationship
class Class(db.Model):
    __tablename__ = 'classes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    instructor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    instructor = db.relationship('User', backref='classes_taught')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'instructor': self.instructor.username if self.instructor else None
        }

# Enrollment association table
enrollments = db.Table('enrollments',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('class_id', db.Integer, db.ForeignKey('classes.id'))
)

# Add relationships to User model
User.classes_enrolled = db.relationship('Class', secondary=enrollments, backref='students')



# Signup route
@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')  # Expecting 'student' or 'teacher'

    # Validate input
    if not username or not password or not role:
        return jsonify({'message': 'Missing username, password, or role'}), 400

    if role not in ['student', 'teacher']:
        return jsonify({'message': 'Invalid role'}), 400

    # Check if user already exists
    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'User already exists'}), 409

    # Hash the password and create a new user
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(username=username, password=hashed_password, role=role)

    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User created successfully'}), 201

# Login route
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    # Validate input
    if not username or not password:
        return jsonify({'message': 'Missing username or password'}), 400

    user = User.query.filter_by(username=username).first()

    if user and bcrypt.check_password_hash(user.password, password):
        # Generate access token including role
        access_token = create_access_token(identity={'username': user.username, 'role': user.role})
        return jsonify({'token': access_token}), 200
    else:
        return jsonify({'message': 'Invalid credentials'}), 401

# Route to get available classes for students
@app.route('/api/student/classes', methods=['GET'])
@jwt_required()
def get_available_classes():
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user['username']).first()
    if user.role != 'student':
        return jsonify({'message': 'Access forbidden'}), 403
    # Return all classes the student is not enrolled in
    enrolled_class_ids = [c.id for c in user.classes_enrolled]
    classes = Class.query.filter(~Class.id.in_(enrolled_class_ids)).all()
    return jsonify([c.to_dict() for c in classes]), 200

# Route for students to enroll in a class
@app.route('/api/student/enroll', methods=['POST'])
@jwt_required()
def enroll_in_class():
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user['username']).first()
    if user.role != 'student':
        return jsonify({'message': 'Access forbidden'}), 403

    data = request.get_json()
    class_id = data.get('class_id')

    if not class_id:
        return jsonify({'message': 'Missing class_id'}), 400

    class_to_enroll = Class.query.get(class_id)

    if not class_to_enroll:
        return jsonify({'message': 'Class not found'}), 404

    if class_to_enroll in user.classes_enrolled:
        return jsonify({'message': 'Already enrolled in this class'}), 400

    user.classes_enrolled.append(class_to_enroll)
    db.session.commit()

    return jsonify({'message': 'Enrolled in class successfully'}), 200

# Route to get classes a student is enrolled in
@app.route('/api/student/my-classes', methods=['GET'])
@jwt_required()
def get_student_classes():
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user['username']).first()
    if user.role != 'student':
        return jsonify({'message': 'Access forbidden'}), 403
    classes = user.classes_enrolled
    return jsonify([c.to_dict() for c in classes]), 200

# Route for teachers to get their classes
@app.route('/api/teacher/classes', methods=['GET'])
@jwt_required()
def get_teacher_classes():
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user['username']).first()
    if user.role != 'teacher':
        return jsonify({'message': 'Access forbidden'}), 403
    classes = Class.query.filter_by(instructor_id=user.id).all()
    return jsonify([c.to_dict() for c in classes]), 200

# Route for teachers to create a new class
@app.route('/api/teacher/classes', methods=['POST'])
@jwt_required()
def create_class():
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user['username']).first()
    if user.role != 'teacher':
        return jsonify({'message': 'Access forbidden'}), 403

    data = request.get_json()
    class_name = data.get('name')

    if not class_name:
        return jsonify({'message': 'Missing class name'}), 400

    new_class = Class(name=class_name, instructor=user)
    db.session.add(new_class)
    db.session.commit()

    return jsonify({'message': 'Class created successfully'}), 201

# Error handlers for JWT errors
@jwt.unauthorized_loader
def unauthorized_response(callback):
    return jsonify({'message': 'Missing Authorization Header'}), 401

@jwt.invalid_token_loader
def invalid_token_response(callback):
    return jsonify({'message': 'Invalid token'}), 401

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)

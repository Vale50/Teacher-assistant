"""
Student Enrollment Routes
Handles course enrollment requests from public-facing enrollment pages
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
import hashlib
import uuid
import logging
import mysql.connector
from mysql.connector import Error

# Initialize logging
logger = logging.getLogger(__name__)

# Create blueprint
enrollment_bp = Blueprint('enrollment', __name__, url_prefix='/api/enrollment')

# Global database connection pool
db_config = {}


def get_db_connection():
    """Create database connection from config"""
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except Error as e:
        logger.error(f"Database connection error: {e}")
        raise


def execute_query(query, params=None, fetch_one=False, fetch_all=False, commit=False):
    """Execute a database query with proper error handling"""
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(query, params or ())

        if commit:
            connection.commit()
            return cursor.lastrowid

        if fetch_one:
            return cursor.fetchone()

        if fetch_all:
            return cursor.fetchall()

        return None

    except Error as e:
        if connection:
            connection.rollback()
        logger.error(f"Database query error: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# =========================================
# START-COURSE PAGE ENROLLMENT ENDPOINTS
# =========================================

@enrollment_bp.route('/start-course/enroll', methods=['POST', 'OPTIONS'])
def start_course_enroll():
    """
    Handle comprehensive enrollment from start-course.html page
    Captures: name, email, phone, grade level, country, course selection, schedule, and notes
    """
    if request.method == 'OPTIONS':
        return jsonify({'success': True}), 200

    try:
        data = request.json

        # Extract form data
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        email = data.get('email', '').strip().lower()
        phone = data.get('phone', '').strip()
        grade_level = data.get('grade_level', '').strip()
        country = data.get('country', '').strip()
        selected_courses = data.get('courses', [])  # Array of course names
        selected_schedules = data.get('schedules', [])  # Array of schedule objects
        notes = data.get('notes', '').strip()

        # Validation
        if not email:
            return jsonify({'success': False, 'error': 'Email is required'}), 400

        if not first_name or not last_name:
            return jsonify({'success': False, 'error': 'First and last name are required'}), 400

        # Validate email format
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return jsonify({'success': False, 'error': 'Invalid email address'}), 400

        full_name = f"{first_name} {last_name}"

        # Check if student already exists (by email or phone number)
        student = execute_query("""
            SELECT id, name, email, phone_number, grade_level
            FROM students
            WHERE email = %s OR phone_number = %s
        """, (email, phone), fetch_one=True)

        if student:
            student_id = student['id']
            logger.info(f"Existing student found: {student_id} - Email: {email}, Phone: {phone}")
        else:
            # Create new student record
            # Generate temporary password
            temp_password = str(uuid.uuid4())[:8]
            password_hash = hashlib.sha256(temp_password.encode()).hexdigest()

            student_id = execute_query("""
                INSERT INTO students (
                    name, email, phone_number, grade_level,
                    password_hash, is_active, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                full_name, email, phone, grade_level,
                password_hash, True, datetime.utcnow()
            ), commit=True)

            logger.info(f"New student created: {student_id} - {email}")

        # Store enrollment request with comprehensive data
        # Convert arrays to JSON strings for storage
        import json
        courses_json = json.dumps(selected_courses) if selected_courses else None
        schedules_json = json.dumps(selected_schedules) if selected_schedules else None

        # Create enrollment request record
        enrollment_id = execute_query("""
            INSERT INTO start_course_enrollments (
                student_id, first_name, last_name, email, phone,
                grade_level, country, selected_courses, selected_schedules,
                notes, enrollment_status, created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            student_id, first_name, last_name, email, phone,
            grade_level, country, courses_json, schedules_json,
            notes, 'pending', datetime.utcnow()
        ), commit=True)

        logger.info(f"Start-course enrollment created: ID={enrollment_id}, Email={email}")

        return jsonify({
            'success': True,
            'message': f'Thank you {first_name}! Your enrollment request has been submitted successfully.',
            'enrollment_id': enrollment_id,
            'student_id': student_id,
            'data': {
                'name': full_name,
                'email': email,
                'phone': phone,
                'grade_level': grade_level,
                'country': country,
                'courses': selected_courses,
                'schedules': selected_schedules
            }
        })

    except Exception as e:
        logger.error(f"Start-course enrollment error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'An error occurred. Please try again.'}), 500


@enrollment_bp.route('/start-course/enrollment/<email>', methods=['GET', 'OPTIONS'])
def get_start_course_enrollment(email):
    """
    Get enrollment data for a student by email
    Returns all enrollment requests and their status
    """
    if request.method == 'OPTIONS':
        return jsonify({'success': True}), 200

    try:
        email = email.strip().lower()

        # Get all enrollment requests for this email
        enrollments = execute_query("""
            SELECT
                id, student_id, first_name, last_name, email, phone,
                grade_level, country, selected_courses, selected_schedules,
                notes, enrollment_status, created_at, updated_at
            FROM start_course_enrollments
            WHERE email = %s
            ORDER BY created_at DESC
        """, (email,), fetch_all=True)

        if not enrollments:
            return jsonify({
                'success': False,
                'error': 'No enrollment found for this email'
            }), 404

        # Parse JSON fields
        import json
        for enrollment in enrollments:
            if enrollment.get('selected_courses'):
                try:
                    enrollment['selected_courses'] = json.loads(enrollment['selected_courses'])
                except:
                    enrollment['selected_courses'] = []

            if enrollment.get('selected_schedules'):
                try:
                    enrollment['selected_schedules'] = json.loads(enrollment['selected_schedules'])
                except:
                    enrollment['selected_schedules'] = []

        return jsonify({
            'success': True,
            'enrollments': enrollments,
            'total': len(enrollments)
        })

    except Exception as e:
        logger.error(f"Get enrollment error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@enrollment_bp.route('/start-course/enrollment/status/<email>', methods=['GET', 'OPTIONS'])
def check_enrollment_status(email):
    """
    Check enrollment status for a student by email
    Returns simple status: pending, approved, or not_found
    """
    if request.method == 'OPTIONS':
        return jsonify({'success': True}), 200

    try:
        email = email.strip().lower()

        # Get most recent enrollment
        enrollment = execute_query("""
            SELECT
                id, enrollment_status, first_name, created_at
            FROM start_course_enrollments
            WHERE email = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (email,), fetch_one=True)

        if not enrollment:
            return jsonify({
                'success': True,
                'status': 'not_found',
                'message': 'No enrollment found for this email'
            })

        return jsonify({
            'success': True,
            'status': enrollment['enrollment_status'],
            'enrollment_id': enrollment['id'],
            'student_name': enrollment['first_name'],
            'enrolled_at': enrollment['created_at'].isoformat() if enrollment['created_at'] else None
        })

    except Exception as e:
        logger.error(f"Check enrollment status error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@enrollment_bp.route('/start-course/enrollments/all', methods=['GET', 'OPTIONS'])
def get_all_start_course_enrollments():
    """
    Get all start-course enrollment requests (admin/coach view)
    Supports filtering by status
    """
    if request.method == 'OPTIONS':
        return jsonify({'success': True}), 200

    try:
        status_filter = request.args.get('status')  # pending, approved, rejected

        query = """
            SELECT
                sce.id, sce.student_id, sce.first_name, sce.last_name,
                sce.email, sce.phone, sce.grade_level, sce.country,
                sce.selected_courses, sce.selected_schedules, sce.notes,
                sce.enrollment_status, sce.created_at, sce.updated_at,
                s.name as student_name, s.last_login
            FROM start_course_enrollments sce
            LEFT JOIN students s ON sce.student_id = s.id
        """

        params = []
        if status_filter:
            query += " WHERE sce.enrollment_status = %s"
            params.append(status_filter)

        query += " ORDER BY sce.created_at DESC"

        enrollments = execute_query(query, tuple(params) if params else None, fetch_all=True)

        # Parse JSON fields
        import json
        for enrollment in enrollments:
            if enrollment.get('selected_courses'):
                try:
                    enrollment['selected_courses'] = json.loads(enrollment['selected_courses'])
                except:
                    enrollment['selected_courses'] = []

            if enrollment.get('selected_schedules'):
                try:
                    enrollment['selected_schedules'] = json.loads(enrollment['selected_schedules'])
                except:
                    enrollment['selected_schedules'] = []

        return jsonify({
            'success': True,
            'enrollments': enrollments or [],
            'total': len(enrollments) if enrollments else 0
        })

    except Exception as e:
        logger.error(f"Get all enrollments error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


def register_blueprint(app, mysql_config):
    """Register this blueprint with the main app"""
    global db_config
    db_config = mysql_config

    app.register_blueprint(enrollment_bp)
    logger.info("✅ Enrollment blueprint registered successfully at /api/enrollment")

    return enrollment_bp
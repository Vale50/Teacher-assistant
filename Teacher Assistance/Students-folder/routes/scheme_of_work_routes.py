"""
Scheme of Work API Routes
Handles scheme of work uploads and management for students
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from auth.models import db, Student, SchemeOfWork
from services.s3_upload_service import s3_service
from datetime import datetime
from sqlalchemy import desc

scheme_of_work_bp = Blueprint('scheme_of_work', __name__, url_prefix='/api/student/scheme-of-work')


# ============================================
# Scheme of Work Management Routes
# ============================================

@scheme_of_work_bp.route('/', methods=['GET'])
@jwt_required()
def get_all_schemes():
    """Get all scheme of works for the current student"""
    try:
        student_id = get_jwt_identity()

        # Get pagination params
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        schemes = SchemeOfWork.query.filter_by(
            student_id=student_id,
            is_active=True
        ).order_by(desc(SchemeOfWork.created_at)).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        return jsonify({
            'success': True,
            'schemes': [scheme.to_dict() for scheme in schemes.items],
            'total': schemes.total,
            'pages': schemes.pages,
            'current_page': schemes.page
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@scheme_of_work_bp.route('/<int:scheme_id>', methods=['GET'])
@jwt_required()
def get_scheme(scheme_id):
    """Get a specific scheme of work"""
    try:
        student_id = get_jwt_identity()
        scheme = SchemeOfWork.query.get(scheme_id)

        if not scheme or not scheme.is_active:
            return jsonify({'error': 'Scheme of work not found'}), 404

        if scheme.student_id != student_id:
            return jsonify({'error': 'Unauthorized'}), 403

        return jsonify({
            'success': True,
            'scheme': scheme.to_dict()
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@scheme_of_work_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_scheme():
    """Upload a new scheme of work (file, image, or text)"""
    try:
        student_id = get_jwt_identity()
        student = Student.query.get(student_id)

        if not student:
            return jsonify({'error': 'Student not found'}), 404

        # Get form data
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        upload_type = request.form.get('type', '').strip()  # 'file', 'image', or 'text'
        text_content = request.form.get('text_content', '').strip()

        if not title:
            return jsonify({'error': 'Title is required'}), 400

        if not upload_type or upload_type not in ['file', 'image', 'text']:
            return jsonify({'error': 'Invalid upload type. Must be file, image, or text'}), 400

        # Create scheme of work record
        scheme = SchemeOfWork(
            student_id=student_id,
            title=title,
            description=description,
            file_type=upload_type
        )

        # Handle text-based scheme of work
        if upload_type == 'text':
            if not text_content:
                return jsonify({'error': 'Text content is required for text-based scheme of work'}), 400

            scheme.text_content = text_content
            db.session.add(scheme)
            db.session.commit()

            return jsonify({
                'success': True,
                'message': 'Text-based scheme of work created successfully',
                'scheme': scheme.to_dict()
            }), 201

        # Handle file/image upload
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Determine S3 file type based on upload type
        if upload_type == 'image':
            s3_file_type = 'image'
        else:  # file (document)
            s3_file_type = 'document'

        # Upload to S3
        upload_result = s3_service.upload_file(
            file,
            file.filename,
            student_id,
            s3_file_type
        )

        if not upload_result['success']:
            return jsonify({'error': upload_result['error']}), 400

        # Update scheme record with file info
        scheme.file_url = upload_result['s3_url']
        scheme.s3_key = upload_result['s3_key']
        scheme.file_name = upload_result['file_name']
        scheme.file_size_mb = upload_result['file_size_mb']

        db.session.add(scheme)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Scheme of work uploaded successfully',
            'scheme': scheme.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@scheme_of_work_bp.route('/<int:scheme_id>', methods=['PUT'])
@jwt_required()
def update_scheme(scheme_id):
    """Update a scheme of work"""
    try:
        student_id = get_jwt_identity()
        scheme = SchemeOfWork.query.get(scheme_id)

        if not scheme or not scheme.is_active:
            return jsonify({'error': 'Scheme of work not found'}), 404

        if scheme.student_id != student_id:
            return jsonify({'error': 'Unauthorized'}), 403

        # Get form data
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        text_content = request.form.get('text_content', '').strip()

        # Update basic fields
        if title:
            scheme.title = title
        if description:
            scheme.description = description

        # Update text content if scheme is text-based
        if scheme.file_type == 'text' and text_content:
            scheme.text_content = text_content

        # Handle file replacement if new file is provided
        if 'file' in request.files:
            file = request.files['file']

            if file.filename != '':
                # Determine S3 file type
                s3_file_type = 'image' if scheme.file_type == 'image' else 'document'

                # Upload new file to S3
                upload_result = s3_service.upload_file(
                    file,
                    file.filename,
                    student_id,
                    s3_file_type
                )

                if not upload_result['success']:
                    return jsonify({'error': upload_result['error']}), 400

                # Delete old file from S3 if exists
                if scheme.s3_key:
                    s3_service.delete_file(scheme.s3_key)

                # Update scheme with new file info
                scheme.file_url = upload_result['s3_url']
                scheme.s3_key = upload_result['s3_key']
                scheme.file_name = upload_result['file_name']
                scheme.file_size_mb = upload_result['file_size_mb']

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Scheme of work updated successfully',
            'scheme': scheme.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@scheme_of_work_bp.route('/<int:scheme_id>', methods=['DELETE'])
@jwt_required()
def delete_scheme(scheme_id):
    """Delete a scheme of work (soft delete)"""
    try:
        student_id = get_jwt_identity()
        scheme = SchemeOfWork.query.get(scheme_id)

        if not scheme:
            return jsonify({'error': 'Scheme of work not found'}), 404

        if scheme.student_id != student_id:
            return jsonify({'error': 'Unauthorized'}), 403

        # Soft delete
        scheme.is_active = False
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Scheme of work deleted successfully'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
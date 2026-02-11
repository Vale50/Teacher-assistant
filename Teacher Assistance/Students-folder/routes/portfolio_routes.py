"""
Student Portfolio API Routes
Handles portfolio items, projects, reviews, and shareable links
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from auth.models import db, Student, PortfolioItem, PortfolioProject, PortfolioMedia, PortfolioReview, StudentTask
from services.s3_upload_service import s3_service
from datetime import datetime
from sqlalchemy import desc
import uuid
import json

portfolio_bp = Blueprint('portfolio', __name__, url_prefix='/api/student/portfolio')


# ============================================
# Portfolio Link Generation
# ============================================

@portfolio_bp.route('/generate-link', methods=['POST'])
@jwt_required()
def generate_portfolio_link():
    """Generate a unique shareable portfolio link"""
    try:
        student_id = get_jwt_identity()
        student = Student.query.get(student_id)

        if not student:
            return jsonify({'error': 'Student not found'}), 404

        # Generate unique link if not exists
        if not student.portfolio_link:
            # Create a unique slug from username or UUID
            base_slug = student.username if student.username else f"student-{student_id}"
            slug = base_slug.lower().replace(' ', '-')

            # Check if slug exists, if so add UUID
            existing = Student.query.filter_by(portfolio_link=slug).first()
            if existing:
                slug = f"{slug}-{str(uuid.uuid4())[:8]}"

            student.portfolio_link = slug
            db.session.commit()

        portfolio_url = f"{request.host_url}portfolio/{student.portfolio_link}"

        return jsonify({
            'success': True,
            'portfolio_link': student.portfolio_link,
            'portfolio_url': portfolio_url
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@portfolio_bp.route('/view/<portfolio_link>', methods=['GET'])
def view_portfolio(portfolio_link):
    """View a student's portfolio by shareable link (public access)"""
    try:
        student = Student.query.filter_by(portfolio_link=portfolio_link).first()

        if not student:
            return jsonify({'error': 'Portfolio not found'}), 404

        # Get all portfolio data
        portfolio_items = PortfolioItem.query.filter_by(
            student_id=student.id,
            is_active=True
        ).order_by(desc(PortfolioItem.created_at)).all()

        projects = PortfolioProject.query.filter_by(
            student_id=student.id,
            is_active=True
        ).order_by(desc(PortfolioProject.is_featured), PortfolioProject.display_order).all()

        reviews = PortfolioReview.query.filter_by(
            student_id=student.id,
            is_active=True
        ).order_by(desc(PortfolioReview.created_at)).all()

        # Get completed tasks
        completed_tasks = StudentTask.query.filter_by(
            student_id=student.id,
            status='completed'
        ).order_by(desc(StudentTask.completed_at)).limit(10).all()

        # Organize portfolio items by type
        items_by_type = {
            'certificates': [item.to_dict() for item in portfolio_items if item.item_type == 'certificate'],
            'awards': [item.to_dict() for item in portfolio_items if item.item_type == 'award'],
            'achievements': [item.to_dict() for item in portfolio_items if item.item_type == 'achievement'],
            'files': [item.to_dict() for item in portfolio_items if item.item_type == 'file']
        }

        # Organize projects by type
        projects_by_type = {
            'top_projects': [p.to_dict() for p in projects if p.project_type == 'top_project'],
            'in_class_projects': [p.to_dict() for p in projects if p.project_type == 'in_class_project'],
            'personal_projects': [p.to_dict() for p in projects if p.project_type == 'personal_project']
        }

        return jsonify({
            'success': True,
            'student': {
                'name': student.name,
                'username': student.username,
                'bio': student.bio,
                'profile_picture_url': student.profile_picture_url,
                'workshop': student.workshop,
                'total_points': student.total_points,
                'current_level': student.current_level,
                'achievements': student.achievements_list
            },
            'portfolio_items': items_by_type,
            'projects': projects_by_type,
            'reviews': [r.to_dict() for r in reviews],
            'completed_tasks_count': student.completed_tasks_count
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@portfolio_bp.route('/my-portfolio', methods=['GET'])
@jwt_required()
def get_my_portfolio():
    """Get current student's complete portfolio data"""
    try:
        student_id = get_jwt_identity()
        student = Student.query.get(student_id)

        if not student:
            return jsonify({'error': 'Student not found'}), 404

        # Get all portfolio data
        portfolio_items = PortfolioItem.query.filter_by(
            student_id=student_id,
            is_active=True
        ).order_by(desc(PortfolioItem.created_at)).all()

        projects = PortfolioProject.query.filter_by(
            student_id=student_id,
            is_active=True
        ).order_by(desc(PortfolioProject.is_featured), PortfolioProject.display_order).all()

        reviews = PortfolioReview.query.filter_by(
            student_id=student_id,
            is_active=True
        ).order_by(desc(PortfolioReview.created_at)).all()

        # Get completed tasks
        completed_tasks = StudentTask.query.filter_by(
            student_id=student_id,
            status='completed'
        ).order_by(desc(StudentTask.completed_at)).all()

        # Organize by type
        items_by_type = {
            'certificates': [item.to_dict() for item in portfolio_items if item.item_type == 'certificate'],
            'awards': [item.to_dict() for item in portfolio_items if item.item_type == 'award'],
            'achievements': [item.to_dict() for item in portfolio_items if item.item_type == 'achievement'],
            'files': [item.to_dict() for item in portfolio_items if item.item_type == 'file']
        }

        projects_by_type = {
            'top_projects': [p.to_dict() for p in projects if p.project_type == 'top_project'],
            'in_class_projects': [p.to_dict() for p in projects if p.project_type == 'in_class_project'],
            'personal_projects': [p.to_dict() for p in projects if p.project_type == 'personal_project']
        }

        return jsonify({
            'success': True,
            'portfolio_items': items_by_type,
            'projects': projects_by_type,
            'reviews': [r.to_dict() for r in reviews],
            'completed_tasks': [
                {
                    'id': task.id,
                    'title': task.task_title,
                    'type': task.task_type,
                    'completed_at': task.completed_at.isoformat() if task.completed_at else None,
                    'points_reward': task.points_reward
                }
                for task in completed_tasks
            ],
            'portfolio_link': student.portfolio_link,
            'has_portfolio_link': bool(student.portfolio_link)
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# Portfolio Items (Certificates, Awards, Achievements, Files)
# ============================================

@portfolio_bp.route('/items', methods=['POST'])
@jwt_required()
def create_portfolio_item():
    """Create a new portfolio item (certificate, award, achievement, file)"""
    try:
        student_id = get_jwt_identity()
        student = Student.query.get(student_id)

        if not student:
            return jsonify({'error': 'Student not found'}), 404

        # Get form data
        item_type = request.form.get('item_type')  # certificate, award, achievement, file
        title = request.form.get('title')
        description = request.form.get('description')
        issuer = request.form.get('issuer')
        issue_date_str = request.form.get('issue_date')

        if not item_type or not title:
            return jsonify({'error': 'Item type and title are required'}), 400

        if item_type not in ['certificate', 'award', 'achievement', 'file']:
            return jsonify({'error': 'Invalid item type'}), 400

        # Parse issue date
        issue_date = None
        if issue_date_str:
            try:
                issue_date = datetime.fromisoformat(issue_date_str.replace('Z', '+00:00')).date()
            except ValueError:
                return jsonify({'error': 'Invalid issue date format'}), 400

        # Create portfolio item
        item = PortfolioItem(
            student_id=student_id,
            item_type=item_type,
            title=title,
            description=description,
            issuer=issuer,
            issue_date=issue_date
        )

        # Handle file upload if present
        if 'file' in request.files:
            file = request.files['file']
            if file.filename:
                # Upload to S3
                upload_result = s3_service.upload_file(
                    file,
                    file.filename,
                    student_id,
                    'document'
                )

                if upload_result['success']:
                    item.file_url = upload_result['s3_url']
                    item.s3_key = upload_result['s3_key']
                    item.file_name = upload_result['file_name']
                    item.file_size_mb = upload_result['file_size_mb']
                else:
                    return jsonify({'error': upload_result['error']}), 400

        db.session.add(item)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Portfolio item created successfully',
            'item': item.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@portfolio_bp.route('/items/<int:item_id>', methods=['PUT'])
@jwt_required()
def update_portfolio_item(item_id):
    """Update a portfolio item"""
    try:
        student_id = get_jwt_identity()
        item = PortfolioItem.query.get(item_id)

        if not item:
            return jsonify({'error': 'Item not found'}), 404

        if item.student_id != student_id:
            return jsonify({'error': 'Unauthorized'}), 403

        data = request.get_json()

        if 'title' in data:
            item.title = data['title']
        if 'description' in data:
            item.description = data['description']
        if 'issuer' in data:
            item.issuer = data['issuer']
        if 'issue_date' in data:
            try:
                item.issue_date = datetime.fromisoformat(data['issue_date'].replace('Z', '+00:00')).date()
            except ValueError:
                return jsonify({'error': 'Invalid issue date format'}), 400

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Portfolio item updated successfully',
            'item': item.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@portfolio_bp.route('/items/<int:item_id>', methods=['DELETE'])
@jwt_required()
def delete_portfolio_item(item_id):
    """Delete a portfolio item (soft delete)"""
    try:
        student_id = get_jwt_identity()
        item = PortfolioItem.query.get(item_id)

        if not item:
            return jsonify({'error': 'Item not found'}), 404

        if item.student_id != student_id:
            return jsonify({'error': 'Unauthorized'}), 403

        # Soft delete
        item.is_active = False

        # Delete file from S3 if exists
        if item.s3_key:
            s3_service.delete_file(item.s3_key)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Portfolio item deleted successfully'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ============================================
# Projects
# ============================================

@portfolio_bp.route('/projects', methods=['POST'])
@jwt_required()
def create_project():
    """Create a new portfolio project"""
    try:
        student_id = get_jwt_identity()
        student = Student.query.get(student_id)

        if not student:
            return jsonify({'error': 'Student not found'}), 404

        # Get form data
        project_type = request.form.get('project_type')  # top_project, in_class_project, personal_project
        title = request.form.get('title')
        description = request.form.get('description')
        technologies_str = request.form.get('technologies')  # JSON array string
        project_url = request.form.get('project_url')
        github_url = request.form.get('github_url')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        is_featured = request.form.get('is_featured', 'false').lower() == 'true'

        if not project_type or not title:
            return jsonify({'error': 'Project type and title are required'}), 400

        if project_type not in ['top_project', 'in_class_project', 'personal_project']:
            return jsonify({'error': 'Invalid project type'}), 400

        # Parse dates
        start_date = None
        end_date = None
        if start_date_str:
            try:
                start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00')).date()
            except ValueError:
                return jsonify({'error': 'Invalid start date format'}), 400
        if end_date_str:
            try:
                end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00')).date()
            except ValueError:
                return jsonify({'error': 'Invalid end date format'}), 400

        # Create project
        project = PortfolioProject(
            student_id=student_id,
            project_type=project_type,
            title=title,
            description=description,
            technologies=technologies_str,
            project_url=project_url,
            github_url=github_url,
            start_date=start_date,
            end_date=end_date,
            is_featured=is_featured
        )
        db.session.add(project)
        db.session.flush()  # Get project ID

        # Handle file uploads (media)
        if 'files' in request.files:
            files = request.files.getlist('files')

            for idx, file in enumerate(files):
                if file.filename == '':
                    continue

                # Determine file type
                file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''

                if file_ext in s3_service.ALLOWED_VIDEO_EXTENSIONS:
                    file_type = 'video'
                elif file_ext in s3_service.ALLOWED_IMAGE_EXTENSIONS:
                    file_type = 'image'
                else:
                    continue

                # Upload to S3
                upload_result = s3_service.upload_file(
                    file,
                    file.filename,
                    student_id,
                    file_type
                )

                if upload_result['success']:
                    media = PortfolioMedia(
                        project_id=project.id,
                        media_type=file_type,
                        media_url=upload_result['s3_url'],
                        s3_key=upload_result['s3_key'],
                        file_name=upload_result['file_name'],
                        file_size_mb=upload_result['file_size_mb'],
                        display_order=idx
                    )
                    db.session.add(media)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Project created successfully',
            'project': project.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@portfolio_bp.route('/projects/<int:project_id>', methods=['PUT'])
@jwt_required()
def update_project(project_id):
    """Update a portfolio project"""
    try:
        student_id = get_jwt_identity()
        project = PortfolioProject.query.get(project_id)

        if not project:
            return jsonify({'error': 'Project not found'}), 404

        if project.student_id != student_id:
            return jsonify({'error': 'Unauthorized'}), 403

        data = request.get_json()

        if 'title' in data:
            project.title = data['title']
        if 'description' in data:
            project.description = data['description']
        if 'technologies' in data:
            # Expect list, convert to JSON string
            if isinstance(data['technologies'], list):
                project.technologies = json.dumps(data['technologies'])
            else:
                project.technologies = data['technologies']
        if 'project_url' in data:
            project.project_url = data['project_url']
        if 'github_url' in data:
            project.github_url = data['github_url']
        if 'start_date' in data:
            try:
                project.start_date = datetime.fromisoformat(data['start_date'].replace('Z', '+00:00')).date()
            except ValueError:
                pass
        if 'end_date' in data:
            try:
                project.end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00')).date()
            except ValueError:
                pass
        if 'is_featured' in data:
            project.is_featured = data['is_featured']
        if 'display_order' in data:
            project.display_order = data['display_order']

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Project updated successfully',
            'project': project.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@portfolio_bp.route('/projects/<int:project_id>', methods=['DELETE'])
@jwt_required()
def delete_project(project_id):
    """Delete a project (soft delete)"""
    try:
        student_id = get_jwt_identity()
        project = PortfolioProject.query.get(project_id)

        if not project:
            return jsonify({'error': 'Project not found'}), 404

        if project.student_id != student_id:
            return jsonify({'error': 'Unauthorized'}), 403

        # Soft delete
        project.is_active = False

        # Delete media files from S3
        for media in project.media:
            if media.s3_key:
                s3_service.delete_file(media.s3_key)
            media.is_active = False

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Project deleted successfully'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ============================================
# Reviews
# ============================================

@portfolio_bp.route('/reviews', methods=['POST'])
@jwt_required()
def create_review():
    """Create a new review/testimonial"""
    try:
        student_id = get_jwt_identity()
        student = Student.query.get(student_id)

        if not student:
            return jsonify({'error': 'Student not found'}), 404

        data = request.get_json()

        reviewer_name = data.get('reviewer_name')
        review_text = data.get('review_text')

        if not reviewer_name or not review_text:
            return jsonify({'error': 'Reviewer name and review text are required'}), 400

        review = PortfolioReview(
            student_id=student_id,
            reviewer_name=reviewer_name,
            reviewer_title=data.get('reviewer_title'),
            reviewer_organization=data.get('reviewer_organization'),
            review_text=review_text,
            rating=data.get('rating'),
            project_id=data.get('project_id')
        )
        db.session.add(review)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Review created successfully',
            'review': review.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@portfolio_bp.route('/reviews/<int:review_id>', methods=['PUT'])
@jwt_required()
def update_review(review_id):
    """Update a review"""
    try:
        student_id = get_jwt_identity()
        review = PortfolioReview.query.get(review_id)

        if not review:
            return jsonify({'error': 'Review not found'}), 404

        if review.student_id != student_id:
            return jsonify({'error': 'Unauthorized'}), 403

        data = request.get_json()

        if 'reviewer_name' in data:
            review.reviewer_name = data['reviewer_name']
        if 'reviewer_title' in data:
            review.reviewer_title = data['reviewer_title']
        if 'reviewer_organization' in data:
            review.reviewer_organization = data['reviewer_organization']
        if 'review_text' in data:
            review.review_text = data['review_text']
        if 'rating' in data:
            review.rating = data['rating']

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Review updated successfully',
            'review': review.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@portfolio_bp.route('/reviews/<int:review_id>', methods=['DELETE'])
@jwt_required()
def delete_review(review_id):
    """Delete a review (soft delete)"""
    try:
        student_id = get_jwt_identity()
        review = PortfolioReview.query.get(review_id)

        if not review:
            return jsonify({'error': 'Review not found'}), 404

        if review.student_id != student_id:
            return jsonify({'error': 'Unauthorized'}), 403

        review.is_active = False
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Review deleted successfully'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
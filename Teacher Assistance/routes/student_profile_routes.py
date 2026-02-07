"""
Student Profile and Timeline API Routes
Handles profile management, posts, likes, and comments
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from auth.models import db, Student, StudentPost, PostMedia, PostLike, PostComment
from services.s3_upload_service import s3_service
from datetime import datetime
from sqlalchemy import desc

student_profile_bp = Blueprint('student_profile', __name__, url_prefix='/api/student/profile')


# ============================================
# Profile Management Routes
# ============================================

@student_profile_bp.route('/', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current student's profile with enhanced data"""
    try:
        from auth.models import StudentTask, ACardTransaction
        from datetime import datetime

        student_id = get_jwt_identity()
        student = Student.query.get(student_id)

        if not student:
            return jsonify({'error': 'Student not found'}), 404

        # Get pending tasks count
        pending_tasks_count = StudentTask.query.filter_by(
            student_id=student_id,
            status='pending'
        ).count()

        # Get recent transactions for A-Card history
        recent_transactions = ACardTransaction.query.filter_by(
            student_id=student_id
        ).order_by(ACardTransaction.created_at.desc()).limit(5).all()

        transactions_data = []
        for transaction in recent_transactions:
            transactions_data.append({
                'amount': float(transaction.amount),
                'description': transaction.description,
                'created_at': transaction.created_at.isoformat(),
                'balance_after': float(transaction.balance_after)
            })

        # Prepare enhanced student data matching frontend expectations
        student_data = {
            'id': student.id,
            'name': student.name,
            'email': student.email,
            'age': getattr(student, 'age', 0),
            'grade_level': getattr(student, 'grade_level', 'N/A'),
            'school_name': getattr(student, 'school_name', 'N/A'),
            'total_points': getattr(student, 'total_points', 0),
            'current_level': getattr(student, 'current_level', 1),
            'acard_balance': float(getattr(student, 'acard_balance', 0) or 0),
            'pending_tasks_count': pending_tasks_count,
            'is_active': getattr(student, 'is_active', True),
            'created_at': student.created_at.isoformat() if hasattr(student, 'created_at') and student.created_at else None,
            'last_login': student.last_login.isoformat() if hasattr(student, 'last_login') and student.last_login else None,
            'recent_transactions': transactions_data
        }

        # Return in format expected by frontend (data.user)
        return jsonify({
            'user': student_data,
            'fresh_data': True,
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@student_profile_bp.route('/<int:student_id>', methods=['GET'])
@jwt_required()
def get_student_profile(student_id):
    """Get another student's profile"""
    try:
        student = Student.query.get(student_id)

        if not student:
            return jsonify({'error': 'Student not found'}), 404

        return jsonify({
            'success': True,
            'profile': student.to_dict()
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@student_profile_bp.route('/update', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update student profile information"""
    try:
        student_id = get_jwt_identity()
        student = Student.query.get(student_id)

        if not student:
            return jsonify({'error': 'Student not found'}), 404

        data = request.get_json()

        # Update allowed fields
        if 'name' in data:
            student.name = data['name']
        if 'username' in data:
            # Check if username is already taken
            existing = Student.query.filter_by(username=data['username']).first()
            if existing and existing.id != student_id:
                return jsonify({'error': 'Username already taken'}), 400
            student.username = data['username']
        if 'phone_number' in data:
            student.phone_number = data['phone_number']
        if 'age' in data:
            student.age = data['age']
        if 'grade_level' in data:
            student.grade_level = data['grade_level']
        if 'school_name' in data:
            student.school_name = data['school_name']
        if 'workshop' in data:
            if data['workshop'] in ['coding', 'graphics', 'video_editor', None]:
                student.workshop = data['workshop']
            else:
                return jsonify({'error': 'Invalid workshop type'}), 400
        if 'birthday' in data:
            try:
                student.birthday = datetime.fromisoformat(data['birthday'].replace('Z', '+00:00')).date()
            except ValueError:
                return jsonify({'error': 'Invalid birthday format'}), 400
        if 'favourite_game' in data:
            student.favourite_game = data['favourite_game']
        if 'bio' in data:
            student.bio = data['bio']

        student.update_profile_complete_status()
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'profile': student.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@student_profile_bp.route('/upload-profile-picture', methods=['POST'])
@jwt_required()
def upload_profile_picture():
    """Upload profile picture"""
    try:
        student_id = get_jwt_identity()
        student = Student.query.get(student_id)

        if not student:
            return jsonify({'error': 'Student not found'}), 404

        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Upload to S3
        upload_result = s3_service.upload_file(
            file,
            file.filename,
            student_id,
            'profile_picture'
        )

        if not upload_result['success']:
            return jsonify({'error': upload_result['error']}), 400

        # Delete old profile picture from S3 if exists
        if student.profile_picture_url:
            # Extract S3 key from URL (simplified - might need adjustment based on URL format)
            old_key = student.profile_picture_url.split('/')[-4:]
            old_key = '/'.join(old_key)
            s3_service.delete_file(old_key)

        # Update student profile
        student.profile_picture_url = upload_result['s3_url']
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Profile picture uploaded successfully',
            'profile_picture_url': upload_result['s3_url']
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ============================================
# Post Management Routes
# ============================================

@student_profile_bp.route('/posts', methods=['POST'])
@jwt_required()
def create_post():
    """Create a new post"""
    try:
        student_id = get_jwt_identity()
        student = Student.query.get(student_id)

        if not student:
            return jsonify({'error': 'Student not found'}), 404

        # Get content from form data
        content = request.form.get('content', '')

        # Create post
        post = StudentPost(
            student_id=student_id,
            content=content,
            post_type='text'  # Will be updated based on media
        )
        db.session.add(post)
        db.session.flush()  # Get post ID

        # Handle file uploads
        media_files = []
        if 'files' in request.files:
            files = request.files.getlist('files')

            for file in files:
                if file.filename == '':
                    continue

                # Determine file type
                file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''

                if file_ext in s3_service.ALLOWED_VIDEO_EXTENSIONS:
                    file_type = 'video'
                elif file_ext in s3_service.ALLOWED_IMAGE_EXTENSIONS:
                    file_type = 'image'
                else:
                    file_type = 'avatar'

                # Upload to S3
                upload_result = s3_service.upload_file(
                    file,
                    file.filename,
                    student_id,
                    file_type
                )

                if upload_result['success']:
                    # Create media record
                    media = PostMedia(
                        post_id=post.id,
                        media_type=file_type,
                        media_url=upload_result['s3_url'],
                        s3_key=upload_result['s3_key'],
                        file_name=upload_result['file_name'],
                        file_size_mb=upload_result['file_size_mb']
                    )
                    db.session.add(media)
                    media_files.append(file_type)

        # Update post type based on media
        if media_files:
            if len(set(media_files)) > 1 or content:
                post.post_type = 'mixed'
            elif 'video' in media_files:
                post.post_type = 'video'
            elif 'image' in media_files:
                post.post_type = 'image'

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Post created successfully',
            'post': post.to_dict(current_student_id=student_id)
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@student_profile_bp.route('/posts/<int:post_id>', methods=['GET'])
@jwt_required()
def get_post(post_id):
    """Get a specific post"""
    try:
        current_student_id = get_jwt_identity()
        post = StudentPost.query.get(post_id)

        if not post or not post.is_active:
            return jsonify({'error': 'Post not found'}), 404

        return jsonify({
            'success': True,
            'post': post.to_dict(current_student_id=current_student_id)
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@student_profile_bp.route('/posts/<int:post_id>', methods=['DELETE'])
@jwt_required()
def delete_post(post_id):
    """Delete a post (soft delete)"""
    try:
        student_id = get_jwt_identity()
        post = StudentPost.query.get(post_id)

        if not post:
            return jsonify({'error': 'Post not found'}), 404

        if post.student_id != student_id:
            return jsonify({'error': 'Unauthorized'}), 403

        # Soft delete
        post.is_active = False

        # Also soft delete all media
        for media in post.media:
            media.is_active = False

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Post deleted successfully'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@student_profile_bp.route('/posts/my-posts', methods=['GET'])
@jwt_required()
def get_my_posts():
    """Get current student's posts"""
    try:
        student_id = get_jwt_identity()

        # Get pagination params
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        posts = StudentPost.query.filter_by(
            student_id=student_id,
            is_active=True
        ).order_by(desc(StudentPost.created_at)).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        return jsonify({
            'success': True,
            'posts': [post.to_dict(current_student_id=student_id) for post in posts.items],
            'total': posts.total,
            'pages': posts.pages,
            'current_page': posts.page
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@student_profile_bp.route('/posts/student/<int:student_id>', methods=['GET'])
@jwt_required()
def get_student_posts(student_id):
    """Get another student's posts"""
    try:
        current_student_id = get_jwt_identity()

        # Get pagination params
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        posts = StudentPost.query.filter_by(
            student_id=student_id,
            is_active=True
        ).order_by(desc(StudentPost.created_at)).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        return jsonify({
            'success': True,
            'posts': [post.to_dict(current_student_id=current_student_id) for post in posts.items],
            'total': posts.total,
            'pages': posts.pages,
            'current_page': posts.page
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# Timeline Routes
# ============================================

@student_profile_bp.route('/timeline', methods=['GET'])
@jwt_required()
def get_timeline():
    """Get timeline feed (all students' posts)"""
    try:
        current_student_id = get_jwt_identity()

        # Get pagination params
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        posts = StudentPost.query.filter_by(
            is_active=True
        ).order_by(desc(StudentPost.created_at)).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        return jsonify({
            'success': True,
            'posts': [post.to_dict(current_student_id=current_student_id) for post in posts.items],
            'total': posts.total,
            'pages': posts.pages,
            'current_page': posts.page
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# Like Routes
# ============================================

@student_profile_bp.route('/posts/<int:post_id>/like', methods=['POST'])
@jwt_required()
def like_post(post_id):
    """Like a post"""
    try:
        student_id = get_jwt_identity()
        post = StudentPost.query.get(post_id)

        if not post or not post.is_active:
            return jsonify({'error': 'Post not found'}), 404

        # Check if already liked
        existing_like = PostLike.query.filter_by(
            post_id=post_id,
            student_id=student_id
        ).first()

        if existing_like:
            if existing_like.is_active:
                return jsonify({'error': 'Post already liked'}), 400
            else:
                # Reactivate the like
                existing_like.is_active = True
        else:
            # Create new like
            like = PostLike(
                post_id=post_id,
                student_id=student_id
            )
            db.session.add(like)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Post liked successfully',
            'likes_count': len([l for l in post.likes if l.is_active])
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@student_profile_bp.route('/posts/<int:post_id>/unlike', methods=['POST'])
@jwt_required()
def unlike_post(post_id):
    """Unlike a post"""
    try:
        student_id = get_jwt_identity()

        like = PostLike.query.filter_by(
            post_id=post_id,
            student_id=student_id,
            is_active=True
        ).first()

        if not like:
            return jsonify({'error': 'Like not found'}), 404

        # Soft delete
        like.is_active = False
        db.session.commit()

        post = StudentPost.query.get(post_id)

        return jsonify({
            'success': True,
            'message': 'Post unliked successfully',
            'likes_count': len([l for l in post.likes if l.is_active])
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@student_profile_bp.route('/posts/<int:post_id>/likes', methods=['GET'])
@jwt_required()
def get_post_likes(post_id):
    """Get all likes for a post"""
    try:
        post = StudentPost.query.get(post_id)

        if not post or not post.is_active:
            return jsonify({'error': 'Post not found'}), 404

        likes = PostLike.query.filter_by(
            post_id=post_id,
            is_active=True
        ).all()

        return jsonify({
            'success': True,
            'likes': [like.to_dict() for like in likes],
            'total': len(likes)
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# Comment Routes
# ============================================

@student_profile_bp.route('/posts/<int:post_id>/comments', methods=['POST'])
@jwt_required()
def create_comment(post_id):
    """Create a comment on a post"""
    try:
        student_id = get_jwt_identity()
        post = StudentPost.query.get(post_id)

        if not post or not post.is_active:
            return jsonify({'error': 'Post not found'}), 404

        data = request.get_json()
        content = data.get('content', '').strip()

        if not content:
            return jsonify({'error': 'Comment content is required'}), 400

        comment = PostComment(
            post_id=post_id,
            student_id=student_id,
            content=content
        )
        db.session.add(comment)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Comment created successfully',
            'comment': comment.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@student_profile_bp.route('/posts/<int:post_id>/comments', methods=['GET'])
@jwt_required()
def get_post_comments(post_id):
    """Get all comments for a post"""
    try:
        post = StudentPost.query.get(post_id)

        if not post or not post.is_active:
            return jsonify({'error': 'Post not found'}), 404

        # Get pagination params
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        comments = PostComment.query.filter_by(
            post_id=post_id,
            is_active=True
        ).order_by(PostComment.created_at.asc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        return jsonify({
            'success': True,
            'comments': [comment.to_dict() for comment in comments.items],
            'total': comments.total,
            'pages': comments.pages,
            'current_page': comments.page
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@student_profile_bp.route('/comments/<int:comment_id>', methods=['DELETE'])
@jwt_required()
def delete_comment(comment_id):
    """Delete a comment (soft delete)"""
    try:
        student_id = get_jwt_identity()
        comment = PostComment.query.get(comment_id)

        if not comment:
            return jsonify({'error': 'Comment not found'}), 404

        if comment.student_id != student_id:
            return jsonify({'error': 'Unauthorized'}), 403

        # Soft delete
        comment.is_active = False
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Comment deleted successfully'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@student_profile_bp.route('/comments/<int:comment_id>', methods=['PUT'])
@jwt_required()
def update_comment(comment_id):
    """Update a comment"""
    try:
        student_id = get_jwt_identity()
        comment = PostComment.query.get(comment_id)

        if not comment:
            return jsonify({'error': 'Comment not found'}), 404

        if comment.student_id != student_id:
            return jsonify({'error': 'Unauthorized'}), 403

        data = request.get_json()
        content = data.get('content', '').strip()

        if not content:
            return jsonify({'error': 'Comment content is required'}), 400

        comment.content = content
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Comment updated successfully',
            'comment': comment.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
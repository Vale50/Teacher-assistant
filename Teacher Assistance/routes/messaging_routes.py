"""
Messaging API Routes
Handles super-admin <-> student messaging system.
Super-admin can send messages to any student.
Students can view inbox, reply to messages, and compose new messages to super-admin.
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from auth.models import db, Student, Admin, Message
from datetime import datetime
from sqlalchemy import or_, and_, desc
import jwt as pyjwt
import logging
from functools import wraps

logger = logging.getLogger(__name__)

messaging_bp = Blueprint('messaging', __name__, url_prefix='/api/messages')


# ============================================
# Auth helpers
# ============================================

def admin_auth_required(f):
    """Decorator to require admin/super-admin authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'No token provided'}), 401
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            payload = pyjwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            admin_id = payload.get('admin_id')
            if not admin_id:
                return jsonify({'error': 'Invalid token'}), 401
            admin = Admin.query.get(admin_id)
            if not admin or not admin.is_active:
                return jsonify({'error': 'Admin not found or inactive'}), 401
            request.current_admin = admin
            return f(*args, **kwargs)
        except pyjwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except pyjwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
    return decorated


def super_admin_auth_required(f):
    """Decorator to require super-admin authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'No token provided'}), 401
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            payload = pyjwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            admin_id = payload.get('admin_id')
            if not admin_id:
                return jsonify({'error': 'Invalid token'}), 401
            admin = Admin.query.get(admin_id)
            if not admin or not admin.is_active:
                return jsonify({'error': 'Admin not found or inactive'}), 401
            if admin.role != 'super_admin':
                return jsonify({'error': 'Super admin access required'}), 403
            request.current_admin = admin
            return f(*args, **kwargs)
        except pyjwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except pyjwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
    return decorated


# ============================================
# Super-Admin Messaging Routes
# ============================================

@messaging_bp.route('/admin/send', methods=['POST'])
@super_admin_auth_required
def admin_send_message():
    """Super-admin sends a message to a student or broadcasts to all students"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        subject = data.get('subject', '').strip()
        message_body = data.get('message_body', '').strip()
        message_type = data.get('message_type', 'general')
        priority = data.get('priority', 'normal')
        recipient_id = data.get('recipient_id')
        is_broadcast = data.get('is_broadcast', False)

        if not subject or not message_body:
            return jsonify({'error': 'Subject and message body are required'}), 400

        admin = request.current_admin
        messages_created = []

        if is_broadcast:
            # Send to all active students
            students = Student.query.filter_by(is_active=True).all()
            if not students:
                return jsonify({'error': 'No active students found'}), 404

            import uuid
            broadcast_group_id = str(uuid.uuid4())

            for student in students:
                msg = Message(
                    sender_id=admin.id,
                    sender_type='super_admin',
                    recipient_id=student.id,
                    recipient_type='student',
                    subject=subject,
                    message_body=message_body,
                    message_type=message_type,
                    priority=priority,
                    is_broadcast=True,
                    broadcast_group_id=broadcast_group_id
                )
                db.session.add(msg)
                messages_created.append(msg)

            db.session.commit()
            return jsonify({
                'success': True,
                'message': f'Broadcast sent to {len(students)} students',
                'broadcast_group_id': broadcast_group_id,
                'recipients_count': len(students)
            }), 201

        else:
            # Send to a specific student
            if not recipient_id:
                return jsonify({'error': 'recipient_id is required for non-broadcast messages'}), 400

            student = Student.query.get(recipient_id)
            if not student:
                return jsonify({'error': 'Student not found'}), 404

            msg = Message(
                sender_id=admin.id,
                sender_type='super_admin',
                recipient_id=student.id,
                recipient_type='student',
                subject=subject,
                message_body=message_body,
                message_type=message_type,
                priority=priority,
                is_broadcast=False
            )
            db.session.add(msg)
            db.session.commit()

            return jsonify({
                'success': True,
                'message': 'Message sent successfully',
                'data': msg.to_dict()
            }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error sending admin message: {str(e)}")
        return jsonify({'error': 'Failed to send message'}), 500


@messaging_bp.route('/admin/inbox', methods=['GET'])
@super_admin_auth_required
def admin_inbox():
    """Get all messages received by super-admin (from students)"""
    try:
        admin = request.current_admin
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        filter_read = request.args.get('filter_read')

        query = Message.query.filter_by(
            recipient_id=admin.id,
            recipient_type='super_admin'
        )

        if filter_read == 'unread':
            query = query.filter_by(is_read=False)
        elif filter_read == 'read':
            query = query.filter_by(is_read=True)

        query = query.order_by(desc(Message.created_at))
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)

        unread_count = Message.query.filter_by(
            recipient_id=admin.id,
            recipient_type='super_admin',
            is_read=False
        ).count()

        return jsonify({
            'success': True,
            'messages': [msg.to_dict() for msg in paginated.items],
            'unread_count': unread_count,
            'pagination': {
                'page': paginated.page,
                'per_page': paginated.per_page,
                'total': paginated.total,
                'pages': paginated.pages,
                'has_next': paginated.has_next,
                'has_prev': paginated.has_prev
            }
        }), 200

    except Exception as e:
        logger.error(f"Error fetching admin inbox: {str(e)}")
        return jsonify({'error': 'Failed to fetch inbox'}), 500


@messaging_bp.route('/admin/sent', methods=['GET'])
@super_admin_auth_required
def admin_sent_messages():
    """Get all messages sent by super-admin"""
    try:
        admin = request.current_admin
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        query = Message.query.filter_by(
            sender_id=admin.id,
            sender_type='super_admin'
        ).order_by(desc(Message.created_at))

        paginated = query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'success': True,
            'messages': [msg.to_dict() for msg in paginated.items],
            'pagination': {
                'page': paginated.page,
                'per_page': paginated.per_page,
                'total': paginated.total,
                'pages': paginated.pages,
                'has_next': paginated.has_next,
                'has_prev': paginated.has_prev
            }
        }), 200

    except Exception as e:
        logger.error(f"Error fetching admin sent messages: {str(e)}")
        return jsonify({'error': 'Failed to fetch sent messages'}), 500


@messaging_bp.route('/admin/conversation/<int:student_id>', methods=['GET'])
@super_admin_auth_required
def admin_conversation_with_student(student_id):
    """Get the full conversation thread between super-admin and a specific student"""
    try:
        admin = request.current_admin
        student = Student.query.get(student_id)
        if not student:
            return jsonify({'error': 'Student not found'}), 404

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)

        query = Message.query.filter(
            or_(
                and_(
                    Message.sender_id == admin.id,
                    Message.sender_type == 'super_admin',
                    Message.recipient_id == student_id,
                    Message.recipient_type == 'student'
                ),
                and_(
                    Message.sender_id == student_id,
                    Message.sender_type == 'student',
                    Message.recipient_id == admin.id,
                    Message.recipient_type == 'super_admin'
                )
            )
        ).order_by(Message.created_at.asc())

        paginated = query.paginate(page=page, per_page=per_page, error_out=False)

        # Mark unread messages from student as read
        unread_msgs = Message.query.filter(
            Message.sender_id == student_id,
            Message.sender_type == 'student',
            Message.recipient_id == admin.id,
            Message.recipient_type == 'super_admin',
            Message.is_read == False
        ).all()
        for msg in unread_msgs:
            msg.is_read = True
            msg.read_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'success': True,
            'student': {
                'id': student.id,
                'name': student.name,
                'email': student.email,
                'username': student.username,
                'grade_level': student.grade_level
            },
            'messages': [msg.to_dict() for msg in paginated.items],
            'pagination': {
                'page': paginated.page,
                'per_page': paginated.per_page,
                'total': paginated.total,
                'pages': paginated.pages,
                'has_next': paginated.has_next,
                'has_prev': paginated.has_prev
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error fetching admin conversation: {str(e)}")
        return jsonify({'error': 'Failed to fetch conversation'}), 500


@messaging_bp.route('/admin/students', methods=['GET'])
@super_admin_auth_required
def admin_list_students():
    """List all students for the super-admin to select as message recipients"""
    try:
        search = request.args.get('search', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)

        query = Student.query.filter_by(is_active=True)

        if search:
            query = query.filter(
                or_(
                    Student.name.ilike(f'%{search}%'),
                    Student.email.ilike(f'%{search}%'),
                    Student.username.ilike(f'%{search}%')
                )
            )

        query = query.order_by(Student.name.asc())
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)

        students = []
        for s in paginated.items:
            # Get unread count from this student
            unread = Message.query.filter_by(
                sender_id=s.id,
                sender_type='student',
                recipient_type='super_admin',
                is_read=False
            ).count()

            # Get last message time
            last_msg = Message.query.filter(
                or_(
                    and_(Message.sender_id == s.id, Message.sender_type == 'student'),
                    and_(Message.recipient_id == s.id, Message.recipient_type == 'student')
                )
            ).order_by(desc(Message.created_at)).first()

            students.append({
                'id': s.id,
                'name': s.name,
                'email': s.email,
                'username': s.username,
                'grade_level': s.grade_level,
                'unread_count': unread,
                'last_message_at': last_msg.created_at.isoformat() if last_msg else None
            })

        return jsonify({
            'success': True,
            'students': students,
            'pagination': {
                'page': paginated.page,
                'per_page': paginated.per_page,
                'total': paginated.total,
                'pages': paginated.pages
            }
        }), 200

    except Exception as e:
        logger.error(f"Error listing students: {str(e)}")
        return jsonify({'error': 'Failed to list students'}), 500


# ============================================
# Student Messaging Routes
# ============================================

@messaging_bp.route('/student/inbox', methods=['GET'])
@jwt_required()
def student_inbox():
    """Get student's inbox - all messages received"""
    try:
        student_id = get_jwt_identity()
        student = Student.query.get(student_id)
        if not student:
            return jsonify({'error': 'Student not found'}), 404

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        filter_read = request.args.get('filter_read')

        query = Message.query.filter_by(
            recipient_id=student_id,
            recipient_type='student'
        )

        if filter_read == 'unread':
            query = query.filter_by(is_read=False)
        elif filter_read == 'read':
            query = query.filter_by(is_read=True)

        query = query.order_by(desc(Message.created_at))
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)

        unread_count = Message.query.filter_by(
            recipient_id=student_id,
            recipient_type='student',
            is_read=False
        ).count()

        return jsonify({
            'success': True,
            'messages': [msg.to_dict() for msg in paginated.items],
            'unread_count': unread_count,
            'pagination': {
                'page': paginated.page,
                'per_page': paginated.per_page,
                'total': paginated.total,
                'pages': paginated.pages,
                'has_next': paginated.has_next,
                'has_prev': paginated.has_prev
            }
        }), 200

    except Exception as e:
        logger.error(f"Error fetching student inbox: {str(e)}")
        return jsonify({'error': 'Failed to fetch inbox'}), 500


@messaging_bp.route('/student/sent', methods=['GET'])
@jwt_required()
def student_sent_messages():
    """Get messages sent by the student"""
    try:
        student_id = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        query = Message.query.filter_by(
            sender_id=student_id,
            sender_type='student'
        ).order_by(desc(Message.created_at))

        paginated = query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'success': True,
            'messages': [msg.to_dict() for msg in paginated.items],
            'pagination': {
                'page': paginated.page,
                'per_page': paginated.per_page,
                'total': paginated.total,
                'pages': paginated.pages,
                'has_next': paginated.has_next,
                'has_prev': paginated.has_prev
            }
        }), 200

    except Exception as e:
        logger.error(f"Error fetching student sent messages: {str(e)}")
        return jsonify({'error': 'Failed to fetch sent messages'}), 500


@messaging_bp.route('/student/send', methods=['POST'])
@jwt_required()
def student_send_message():
    """Student sends a message to super-admin"""
    try:
        student_id = get_jwt_identity()
        student = Student.query.get(student_id)
        if not student:
            return jsonify({'error': 'Student not found'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        subject = data.get('subject', '').strip()
        message_body = data.get('message_body', '').strip()

        if not subject or not message_body:
            return jsonify({'error': 'Subject and message body are required'}), 400

        # Find the super-admin to send to
        # If a specific admin_id is provided, use that; otherwise send to the first active super-admin
        admin_id = data.get('admin_id')
        if admin_id:
            admin = Admin.query.filter_by(id=admin_id, role='super_admin', is_active=True).first()
        else:
            admin = Admin.query.filter_by(role='super_admin', is_active=True).first()

        if not admin:
            return jsonify({'error': 'No super-admin available to receive messages'}), 404

        msg = Message(
            sender_id=student.id,
            sender_type='student',
            recipient_id=admin.id,
            recipient_type='super_admin',
            subject=subject,
            message_body=message_body,
            message_type='general',
            priority='normal',
            is_broadcast=False
        )
        db.session.add(msg)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Message sent to admin successfully',
            'data': msg.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error sending student message: {str(e)}")
        return jsonify({'error': 'Failed to send message'}), 500


@messaging_bp.route('/student/conversation', methods=['GET'])
@jwt_required()
def student_conversation():
    """Get the full conversation thread between student and super-admin"""
    try:
        student_id = get_jwt_identity()
        student = Student.query.get(student_id)
        if not student:
            return jsonify({'error': 'Student not found'}), 404

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)

        # Get conversations with any super-admin
        query = Message.query.filter(
            or_(
                and_(
                    Message.sender_id == student_id,
                    Message.sender_type == 'student',
                    Message.recipient_type == 'super_admin'
                ),
                and_(
                    Message.recipient_id == student_id,
                    Message.recipient_type == 'student',
                    Message.sender_type == 'super_admin'
                )
            )
        ).order_by(Message.created_at.asc())

        paginated = query.paginate(page=page, per_page=per_page, error_out=False)

        # Mark unread messages from admin as read
        unread_msgs = Message.query.filter(
            Message.recipient_id == student_id,
            Message.recipient_type == 'student',
            Message.sender_type == 'super_admin',
            Message.is_read == False
        ).all()
        for msg in unread_msgs:
            msg.is_read = True
            msg.read_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'success': True,
            'messages': [msg.to_dict() for msg in paginated.items],
            'pagination': {
                'page': paginated.page,
                'per_page': paginated.per_page,
                'total': paginated.total,
                'pages': paginated.pages,
                'has_next': paginated.has_next,
                'has_prev': paginated.has_prev
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error fetching student conversation: {str(e)}")
        return jsonify({'error': 'Failed to fetch conversation'}), 500


@messaging_bp.route('/student/reply/<int:message_id>', methods=['POST'])
@jwt_required()
def student_reply_message(message_id):
    """Student replies to a specific message from super-admin"""
    try:
        student_id = get_jwt_identity()
        student = Student.query.get(student_id)
        if not student:
            return jsonify({'error': 'Student not found'}), 404

        # Find the original message
        original_msg = Message.query.get(message_id)
        if not original_msg:
            return jsonify({'error': 'Original message not found'}), 404

        # Verify the student is the recipient of the original message
        if original_msg.recipient_id != student_id or original_msg.recipient_type != 'student':
            return jsonify({'error': 'You can only reply to messages sent to you'}), 403

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        message_body = data.get('message_body', '').strip()
        if not message_body:
            return jsonify({'error': 'Message body is required'}), 400

        # Create reply message sent to the original sender
        reply = Message(
            sender_id=student.id,
            sender_type='student',
            recipient_id=original_msg.sender_id,
            recipient_type=original_msg.sender_type,
            subject=f"Re: {original_msg.subject}",
            message_body=message_body,
            message_type='general',
            priority='normal',
            is_broadcast=False
        )
        db.session.add(reply)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Reply sent successfully',
            'data': reply.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error sending reply: {str(e)}")
        return jsonify({'error': 'Failed to send reply'}), 500


@messaging_bp.route('/read/<int:message_id>', methods=['PUT'])
@jwt_required()
def mark_message_read(message_id):
    """Mark a message as read"""
    try:
        student_id = get_jwt_identity()
        msg = Message.query.get(message_id)

        if not msg:
            return jsonify({'error': 'Message not found'}), 404

        if msg.recipient_id != student_id or msg.recipient_type != 'student':
            return jsonify({'error': 'Not authorized'}), 403

        msg.is_read = True
        msg.read_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Message marked as read'
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error marking message as read: {str(e)}")
        return jsonify({'error': 'Failed to mark message as read'}), 500


@messaging_bp.route('/student/unread-count', methods=['GET'])
@jwt_required()
def student_unread_count():
    """Get the unread message count for the student"""
    try:
        student_id = get_jwt_identity()
        count = Message.query.filter_by(
            recipient_id=student_id,
            recipient_type='student',
            is_read=False
        ).count()

        return jsonify({
            'success': True,
            'unread_count': count
        }), 200

    except Exception as e:
        logger.error(f"Error getting unread count: {str(e)}")
        return jsonify({'error': 'Failed to get unread count'}), 500


@messaging_bp.route('/admin/reply/<int:message_id>', methods=['POST'])
@super_admin_auth_required
def admin_reply_message(message_id):
    """Super-admin replies to a student message"""
    try:
        admin = request.current_admin
        original_msg = Message.query.get(message_id)

        if not original_msg:
            return jsonify({'error': 'Original message not found'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        message_body = data.get('message_body', '').strip()
        if not message_body:
            return jsonify({'error': 'Message body is required'}), 400

        reply = Message(
            sender_id=admin.id,
            sender_type='super_admin',
            recipient_id=original_msg.sender_id,
            recipient_type=original_msg.sender_type,
            subject=f"Re: {original_msg.subject}",
            message_body=message_body,
            message_type='general',
            priority='normal',
            is_broadcast=False
        )
        db.session.add(reply)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Reply sent successfully',
            'data': reply.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error sending admin reply: {str(e)}")
        return jsonify({'error': 'Failed to send reply'}), 500


@messaging_bp.route('/admin/unread-count', methods=['GET'])
@super_admin_auth_required
def admin_unread_count():
    """Get the unread message count for super-admin"""
    try:
        admin = request.current_admin
        count = Message.query.filter_by(
            recipient_id=admin.id,
            recipient_type='super_admin',
            is_read=False
        ).count()

        return jsonify({
            'success': True,
            'unread_count': count
        }), 200

    except Exception as e:
        logger.error(f"Error getting admin unread count: {str(e)}")
        return jsonify({'error': 'Failed to get unread count'}), 500
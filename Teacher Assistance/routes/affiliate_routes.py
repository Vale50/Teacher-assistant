from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from datetime import datetime, timedelta
from functools import wraps
import uuid

# Import your models - adjust paths as needed
try:
    from auth.models import Affiliate, AffiliateProductLink, Referral, Commission, Payout, AffiliateClick
    from auth.models import User
except ImportError:
    # If models don't exist yet, create placeholder to avoid import error
    Affiliate = None
    AffiliateProductLink = None
    Referral = None
    Commission = None
    Payout = None
    AffiliateClick = None
    User = None

# Create Blueprint
affiliate_bp = Blueprint('affiliate', __name__, url_prefix='/api/affiliate')


def affiliate_required(f):
    """Decorator to check if user has affiliate account"""
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        if Affiliate is None:
            return jsonify({'error': 'Affiliate system not configured'}), 500
            
        user_id = get_jwt_identity()
        affiliate = Affiliate.query.filter_by(user_id=user_id).first()
        
        if not affiliate:
            return jsonify({'error': 'Affiliate account required'}), 403
        
        if affiliate.status == 'suspended':
            return jsonify({'error': 'Account suspended'}), 403
            
        return f(affiliate, *args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to check if user is admin"""
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        if User is None:
            return jsonify({'error': 'User system not configured'}), 500
            
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
            
        return f(*args, **kwargs)
    return decorated_function


# ==================== ROUTES ====================

@affiliate_bp.route('/register', methods=['POST'])
@jwt_required()
def register_affiliate():
    """Register as affiliate"""
    if Affiliate is None:
        return jsonify({'error': 'Affiliate system not configured'}), 500
        
    user_id = get_jwt_identity()
    
    existing = Affiliate.query.filter_by(user_id=user_id).first()
    if existing:
        return jsonify({
            'success': True,
            'affiliate': existing.to_dict(),
            'message': 'Account already exists'
        }), 200
    
    data = request.get_json() or {}
    
    try:
        affiliate = Affiliate(
            user_id=user_id,
            affiliate_code=Affiliate.generate_code(),
            status='active',
            terms_accepted=True,
            terms_accepted_at=datetime.utcnow(),
            payment_method=data.get('payment_method'),
            payment_email=data.get('payment_email')
        )
        
        db.session.add(affiliate)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'affiliate': affiliate.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@affiliate_bp.route('/dashboard/stats', methods=['GET'])
@affiliate_required
def get_dashboard_stats(affiliate):
    """Get dashboard statistics"""
    stats = {
        'overview': {
            'total_referrals': affiliate.total_referrals,
            'total_conversions': affiliate.total_conversions,
            'active_referrals': affiliate.get_active_referrals_count() if hasattr(affiliate, 'get_active_referrals_count') else 0,
            'churned_referrals': affiliate.get_churned_referrals_count() if hasattr(affiliate, 'get_churned_referrals_count') else 0,
            'conversion_rate': affiliate.calculate_conversion_rate() if hasattr(affiliate, 'calculate_conversion_rate') else 0,
        },
        'earnings': {
            'total_earnings': round(affiliate.total_earnings, 2),
            'pending_earnings': round(affiliate.pending_earnings, 2),
            'paid_earnings': round(affiliate.paid_earnings, 2),
            'next_payout_eligible': affiliate.pending_earnings >= affiliate.minimum_payout_threshold,
            'minimum_threshold': affiliate.minimum_payout_threshold
        },
        'commissions': {
            'pending': 0,
            'approved': 0,
            'paid': 0,
        }
    }
    
    return jsonify(stats), 200


@affiliate_bp.route('/dashboard/products', methods=['GET'])
@affiliate_required
def get_affiliate_products(affiliate):
    """Get products with affiliate links"""
    
    products = [
        {
            'id': 'student_portal',
            'type': 'product',
            'name': 'Student Portal',
            'description': 'Complete learning management system',
            'price': 49.99,
            'commission_rate': 20
        },
        {
            'id': 'lesson_planner',
            'type': 'product',
            'name': 'Lesson Planner',
            'description': 'AI-powered lesson planning',
            'price': 29.99,
            'commission_rate': 20
        },
        {
            'id': 'quiz_creator',
            'type': 'product',
            'name': 'Quiz Creator',
            'description': 'Interactive quiz builder',
            'price': 19.99,
            'commission_rate': 20
        }
    ]
    
    courses = [
        {
            'id': 'video_editing',
            'type': 'course',
            'name': 'Video Editing Masterclass',
            'description': 'Professional video editing course',
            'price': 99.99,
            'commission_rate': 15
        },
        {
            'id': 'social_media',
            'type': 'course',
            'name': 'Social Media Management',
            'description': 'Master social media marketing',
            'price': 79.99,
            'commission_rate': 15
        },
        {
            'id': 'graphic_design',
            'type': 'course',
            'name': 'Graphic Design Fundamentals',
            'description': 'Learn design principles',
            'price': 89.99,
            'commission_rate': 15
        }
    ]
    
    all_items = products + courses
    result = []
    
    for item in all_items:
        if AffiliateProductLink is None:
            # Fallback if model not available
            item['tracking_link'] = f"{request.host_url}ref/{affiliate.affiliate_code}/{item['id']}"
            item['click_count'] = 0
            item['conversion_count'] = 0
            item['earnings'] = 0.0
            result.append(item)
            continue
            
        existing_link = AffiliateProductLink.query.filter_by(
            affiliate_id=affiliate.id,
            product_id=item['id']
        ).first()
        
        if not existing_link:
            short_code = str(uuid.uuid4())[:8]
            tracking_link = f"{request.host_url.rstrip('/')}/api/affiliate/track/{short_code}"
            
            new_link = AffiliateProductLink(
                affiliate_id=affiliate.id,
                product_type=item['type'],
                product_id=item['id'],
                product_name=item['name'],
                tracking_link=tracking_link,
                short_code=short_code
            )
            
            db.session.add(new_link)
            db.session.flush()
            
            link_data = new_link.to_dict()
        else:
            link_data = existing_link.to_dict()
        
        item_data = {**item, **link_data}
        result.append(item_data)
    
    db.session.commit()
    
    return jsonify({
        'products': [r for r in result if r['type'] == 'product'],
        'courses': [r for r in result if r['type'] == 'course']
    }), 200


@affiliate_bp.route('/dashboard/referrals', methods=['GET'])
@affiliate_required
def get_referrals(affiliate):
    """Get referrals"""
    if Referral is None:
        return jsonify({'referrals': [], 'total': 0, 'pages': 0, 'current_page': 1}), 200
    
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    
    query = Referral.query.filter_by(affiliate_id=affiliate.id)
    query = query.order_by(Referral.created_at.desc())
    
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'referrals': [r.to_dict() for r in paginated.items],
        'total': paginated.total,
        'pages': paginated.pages,
        'current_page': page
    }), 200


@affiliate_bp.route('/dashboard/commissions', methods=['GET'])
@affiliate_required
def get_commissions(affiliate):
    """Get commissions"""
    if Commission is None:
        return jsonify({'commissions': [], 'total': 0, 'pages': 0, 'current_page': 1}), 200
    
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    
    query = Commission.query.filter_by(affiliate_id=affiliate.id)
    query = query.order_by(Commission.created_at.desc())
    
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'commissions': [c.to_dict() for c in paginated.items],
        'total': paginated.total,
        'pages': paginated.pages,
        'current_page': page
    }), 200


@affiliate_bp.route('/dashboard/payouts', methods=['GET'])
@affiliate_required
def get_payouts(affiliate):
    """Get payouts"""
    if Payout is None:
        return jsonify({'payouts': [], 'total': 0, 'pages': 0, 'current_page': 1}), 200
    
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    
    query = Payout.query.filter_by(affiliate_id=affiliate.id)
    query = query.order_by(Payout.created_at.desc())
    
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'payouts': [p.to_dict() for p in paginated.items],
        'total': paginated.total,
        'pages': paginated.pages,
        'current_page': page
    }), 200


@affiliate_bp.route('/admin/stats', methods=['GET'])
@admin_required
def get_admin_stats():
    """Admin stats"""
    if Affiliate is None:
        return jsonify({'error': 'System not configured'}), 500
    
    from sqlalchemy import func
    
    total_affiliates = Affiliate.query.count()
    active_affiliates = Affiliate.query.filter_by(status='active').count()
    
    total_earnings_paid = db.session.query(func.sum(Affiliate.paid_earnings)).scalar() or 0
    total_earnings_pending = db.session.query(func.sum(Affiliate.pending_earnings)).scalar() or 0
    
    total_referrals = db.session.query(func.sum(Affiliate.total_referrals)).scalar() or 0
    total_conversions = db.session.query(func.sum(Affiliate.total_conversions)).scalar() or 0
    
    return jsonify({
        'affiliates': {
            'total': total_affiliates,
            'active': active_affiliates,
            'inactive': Affiliate.query.filter_by(status='inactive').count(),
            'suspended': Affiliate.query.filter_by(status='suspended').count()
        },
        'earnings': {
            'total_paid': round(total_earnings_paid, 2),
            'total_pending': round(total_earnings_pending, 2),
            'total_combined': round(total_earnings_paid + total_earnings_pending, 2)
        },
        'performance': {
            'total_referrals': int(total_referrals),
            'total_conversions': int(total_conversions),
            'conversion_rate': round((total_conversions / total_referrals * 100) if total_referrals > 0 else 0, 2)
        },
        'pending_actions': {
            'payouts': 0,
            'commissions': 0
        }
    }), 200


@affiliate_bp.route('/admin/affiliates', methods=['GET'])
@admin_required
def get_all_affiliates():
    """Get all affiliates"""
    if Affiliate is None:
        return jsonify({'affiliates': [], 'total': 0}), 200
    
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    
    query = Affiliate.query.order_by(Affiliate.created_at.desc())
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    
    affiliates_data = []
    for aff in paginated.items:
        aff_dict = aff.to_dict()
        aff_dict['user'] = {
            'id': aff.user.id,
            'name': aff.user.name,
            'email': aff.user.email
        }
        affiliates_data.append(aff_dict)
    
    return jsonify({
        'affiliates': affiliates_data,
        'total': paginated.total,
        'pages': paginated.pages,
        'current_page': page
    }), 200


@affiliate_bp.route('/admin/affiliate/<affiliate_id>', methods=['GET', 'PUT'])
@admin_required
def manage_affiliate(affiliate_id):
    """Manage specific affiliate"""
    if Affiliate is None:
        return jsonify({'error': 'System not configured'}), 500
    
    affiliate = Affiliate.query.get_or_404(affiliate_id)
    
    if request.method == 'GET':
        data = affiliate.to_dict()
        data['user'] = {
            'id': affiliate.user.id,
            'name': affiliate.user.name,
            'email': affiliate.user.email
        }
        return jsonify(data), 200
    
    # UPDATE
    data = request.get_json()
    
    if 'total_referrals' in data:
        affiliate.total_referrals = int(data['total_referrals'])
    
    if 'total_conversions' in data:
        affiliate.total_conversions = int(data['total_conversions'])
    
    if 'total_earnings' in data:
        affiliate.total_earnings = float(data['total_earnings'])
    
    if 'pending_earnings' in data:
        affiliate.pending_earnings = float(data['pending_earnings'])
    
    if 'paid_earnings' in data:
        affiliate.paid_earnings = float(data['paid_earnings'])
    
    if 'status' in data:
        affiliate.status = data['status']
    
    affiliate.updated_at = datetime.utcnow()
    
    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'affiliate': affiliate.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# Health check endpoint
@affiliate_bp.route('/health', methods=['GET'])
def health_check():
    """Health check"""
    return jsonify({
        'status': 'ok',
        'service': 'affiliate',
        'models_loaded': Affiliate is not None
    }), 200
"""
Commission Automation Service
Handles automatic commission creation based on user actions
"""

from datetime import datetime, timedelta
from auth.models import Affiliate, Referral, Commission, AffiliateClick
from extensions import db
from sqlalchemy import and_
import logging

logger = logging.getLogger(__name__)


class CommissionService:
    """Service for handling automatic commission generation"""
    
    @staticmethod
    def create_trial_signup_commission(user_id, referral_id=None):
        """
        Create commission when a user signs up for trial
        $2 per trial signup
        """
        try:
            # Find the referral if not provided
            if not referral_id:
                referral = Referral.query.filter_by(
                    referred_user_id=user_id,
                    status='pending'
                ).first()
            else:
                referral = Referral.query.get(referral_id)
            
            if not referral:
                logger.warning(f"No referral found for user {user_id}")
                return None
            
            # Get affiliate
            affiliate = Affiliate.query.get(referral.affiliate_id)
            if not affiliate or affiliate.status != 'active':
                logger.warning(f"Affiliate {referral.affiliate_id} not active")
                return None
            
            # Check if commission already exists
            existing = Commission.query.filter_by(
                referral_id=referral.id,
                commission_type='trial_signup'
            ).first()
            
            if existing:
                logger.info(f"Trial commission already exists for referral {referral.id}")
                return existing
            
            # Create commission
            commission = Commission(
                affiliate_id=affiliate.id,
                referral_id=referral.id,
                amount=affiliate.trial_signup_commission,
                commission_type='trial_signup',
                status='pending'  # Needs approval
            )
            
            db.session.add(commission)
            
            # Update referral status
            referral.status = 'trial'
            referral.trial_started_at = datetime.utcnow()
            
            db.session.commit()
            
            logger.info(f"Created trial commission ${commission.amount} for affiliate {affiliate.id}")
            return commission
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating trial commission: {str(e)}")
            return None
    
    @staticmethod
    def create_conversion_commission(user_id, subscription_id=None):
        """
        Create commission when user converts to paid subscription
        $5 per conversion
        """
        try:
            # Find the referral
            referral = Referral.query.filter_by(
                referred_user_id=user_id
            ).first()
            
            if not referral:
                logger.warning(f"No referral found for user {user_id}")
                return None
            
            # Get affiliate
            affiliate = Affiliate.query.get(referral.affiliate_id)
            if not affiliate or affiliate.status != 'active':
                logger.warning(f"Affiliate {referral.affiliate_id} not active")
                return None
            
            # Check if conversion commission already exists
            existing = Commission.query.filter_by(
                referral_id=referral.id,
                commission_type='conversion'
            ).first()
            
            if existing:
                logger.info(f"Conversion commission already exists for referral {referral.id}")
                return existing
            
            # Create commission
            commission = Commission(
                affiliate_id=affiliate.id,
                referral_id=referral.id,
                amount=affiliate.paid_conversion_commission,
                commission_type='conversion',
                status='approved',  # Auto-approved
                subscription_id=subscription_id,
                approved_at=datetime.utcnow()
            )
            
            db.session.add(commission)
            
            # Update referral status
            referral.status = 'converted'
            referral.conversion_at = datetime.utcnow()
            referral.subscription_status = 'active'
            
            # Update affiliate stats
            affiliate.total_conversions += 1
            affiliate.pending_earnings += commission.amount
            affiliate.total_earnings += commission.amount
            
            # Update product link stats if available
            if referral.product_link_id:
                from auth.models import AffiliateProductLink
                product_link = AffiliateProductLink.query.get(referral.product_link_id)
                if product_link:
                    product_link.conversion_count += 1
                    product_link.earnings += commission.amount
            
            db.session.commit()
            
            logger.info(f"Created conversion commission ${commission.amount} for affiliate {affiliate.id}")
            return commission
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating conversion commission: {str(e)}")
            return None
    
    @staticmethod
    def create_recurring_commission(user_id, month_number, subscription_id=None):
        """
        Create recurring commission for active subscription
        $5 per month while subscription is active
        """
        try:
            # Find the referral
            referral = Referral.query.filter_by(
                referred_user_id=user_id,
                status='converted'
            ).first()
            
            if not referral:
                logger.warning(f"No active referral found for user {user_id}")
                return None
            
            # Get affiliate
            affiliate = Affiliate.query.get(referral.affiliate_id)
            if not affiliate or affiliate.status != 'active':
                logger.warning(f"Affiliate {referral.affiliate_id} not active")
                return None
            
            # Check if affiliate has recurring commissions enabled
            if not affiliate.recurring_commission_enabled:
                logger.info(f"Recurring commissions not enabled for affiliate {affiliate.id}")
                return None
            
            # Check if this month's commission already exists
            existing = Commission.query.filter_by(
                referral_id=referral.id,
                commission_type=f'recurring_month_{month_number}',
                recurring_month=month_number
            ).first()
            
            if existing:
                logger.info(f"Recurring commission for month {month_number} already exists")
                return existing
            
            # Create commission
            commission = Commission(
                affiliate_id=affiliate.id,
                referral_id=referral.id,
                amount=affiliate.recurring_commission,
                commission_type=f'recurring_month_{month_number}',
                status='approved',
                is_recurring=True,
                recurring_month=month_number,
                subscription_id=subscription_id,
                approved_at=datetime.utcnow()
            )
            
            db.session.add(commission)
            
            # Update affiliate earnings
            affiliate.pending_earnings += commission.amount
            affiliate.total_earnings += commission.amount
            
            # Update referral stats
            referral.months_subscribed = month_number
            referral.total_commissions_paid += commission.amount
            
            db.session.commit()
            
            logger.info(f"Created recurring commission ${commission.amount} for affiliate {affiliate.id}, month {month_number}")
            return commission
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating recurring commission: {str(e)}")
            return None
    
    @staticmethod
    def handle_subscription_cancelled(user_id):
        """
        Handle when a subscription is cancelled
        Mark referral as churned
        """
        try:
            referral = Referral.query.filter_by(
                referred_user_id=user_id,
                status='converted'
            ).first()
            
            if not referral:
                return
            
            referral.status = 'churned'
            referral.churned_at = datetime.utcnow()
            referral.subscription_status = 'canceled'
            
            db.session.commit()
            
            logger.info(f"Marked referral {referral.id} as churned")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error handling cancellation: {str(e)}")
    
    @staticmethod
    def process_monthly_recurring_commissions():
        """
        Batch process all active referrals for recurring commissions
        This should be run monthly via cron job
        """
        try:
            # Get all active converted referrals
            active_referrals = Referral.query.filter_by(
                status='converted',
                subscription_status='active'
            ).all()
            
            processed = 0
            errors = 0
            
            for referral in active_referrals:
                try:
                    # Calculate which month this is
                    if not referral.conversion_at:
                        continue
                    
                    months_since_conversion = (
                        (datetime.utcnow() - referral.conversion_at).days // 30
                    )
                    
                    # Skip if not yet time for next month
                    if months_since_conversion <= referral.months_subscribed:
                        continue
                    
                    # Create recurring commission
                    next_month = referral.months_subscribed + 1
                    commission = CommissionService.create_recurring_commission(
                        referral.referred_user_id,
                        next_month
                    )
                    
                    if commission:
                        processed += 1
                    else:
                        errors += 1
                        
                except Exception as e:
                    logger.error(f"Error processing referral {referral.id}: {str(e)}")
                    errors += 1
                    continue
            
            logger.info(f"Processed {processed} recurring commissions, {errors} errors")
            return {'processed': processed, 'errors': errors}
            
        except Exception as e:
            logger.error(f"Error in batch processing: {str(e)}")
            return {'processed': 0, 'errors': 0}
    
    @staticmethod
    def detect_fraud(affiliate_id):
        """
        Simple fraud detection
        Check for suspicious patterns
        """
        try:
            affiliate = Affiliate.query.get(affiliate_id)
            if not affiliate:
                return False
            
            # Check 1: Too many clicks from same IP
            recent_clicks = AffiliateClick.query.filter(
                AffiliateClick.affiliate_id == affiliate_id,
                AffiliateClick.created_at >= datetime.utcnow() - timedelta(days=1)
            ).all()
            
            ip_counts = {}
            for click in recent_clicks:
                ip = click.ip_address
                ip_counts[ip] = ip_counts.get(ip, 0) + 1
            
            # Flag if any IP has more than 10 clicks in 24 hours
            if any(count > 10 for count in ip_counts.values()):
                affiliate.suspicious_activity_count += 1
                affiliate.fraud_flag = True
                db.session.commit()
                logger.warning(f"Fraud detected for affiliate {affiliate_id}: Excessive clicks from single IP")
                return True
            
            # Check 2: Unusual conversion rate (too high might indicate fraud)
            if affiliate.total_referrals > 20:
                conversion_rate = (affiliate.total_conversions / affiliate.total_referrals) * 100
                if conversion_rate > 80:  # Unrealistically high
                    affiliate.suspicious_activity_count += 1
                    affiliate.fraud_flag = True
                    db.session.commit()
                    logger.warning(f"Fraud detected for affiliate {affiliate_id}: Suspicious conversion rate {conversion_rate}%")
                    return True
            
            # Check 3: Self-referrals (same email domain)
            referrals = Referral.query.filter_by(affiliate_id=affiliate_id).all()
            affiliate_email_domain = affiliate.user.email.split('@')[1]
            
            suspicious_count = 0
            for referral in referrals:
                if referral.referred_email and '@' in referral.referred_email:
                    ref_domain = referral.referred_email.split('@')[1]
                    if ref_domain == affiliate_email_domain:
                        suspicious_count += 1
            
            if suspicious_count > 3:  # More than 3 referrals from same domain
                affiliate.suspicious_activity_count += 1
                logger.warning(f"Potential self-referral fraud for affiliate {affiliate_id}")
            
            return False
            
        except Exception as e:
            logger.error(f"Error in fraud detection: {str(e)}")
            return False


class WebhookHandler:
    """Handle webhooks from payment providers (Stripe, PayPal, etc.)"""
    
    @staticmethod
    def handle_stripe_webhook(event_type, data):
        """
        Handle Stripe webhook events
        
        Event types:
        - customer.subscription.created
        - customer.subscription.updated
        - customer.subscription.deleted
        - invoice.payment_succeeded
        """
        try:
            if event_type == 'customer.subscription.created':
                # New subscription created
                user_email = data.get('customer_email')
                subscription_id = data.get('id')
                
                # Find user and create conversion commission
                from models.user import User
                user = User.query.filter_by(email=user_email).first()
                if user:
                    CommissionService.create_conversion_commission(
                        user.id,
                        subscription_id
                    )
            
            elif event_type == 'invoice.payment_succeeded':
                # Recurring payment succeeded
                subscription_id = data.get('subscription')
                user_email = data.get('customer_email')
                
                from models.user import User
                user = User.query.filter_by(email=user_email).first()
                if user:
                    # Get referral to determine which month this is
                    referral = Referral.query.filter_by(
                        referred_user_id=user.id,
                        status='converted'
                    ).first()
                    
                    if referral:
                        next_month = referral.months_subscribed + 1
                        CommissionService.create_recurring_commission(
                            user.id,
                            next_month,
                            subscription_id
                        )
            
            elif event_type == 'customer.subscription.deleted':
                # Subscription cancelled
                user_email = data.get('customer_email')
                
                from models.user import User
                user = User.query.filter_by(email=user_email).first()
                if user:
                    CommissionService.handle_subscription_cancelled(user.id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling Stripe webhook: {str(e)}")
            return False
    
    @staticmethod
    def handle_paypal_webhook(event_type, data):
        """Handle PayPal webhook events"""
        # Similar implementation for PayPal
        pass
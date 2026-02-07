# models.py
import uuid
from datetime import datetime
import json
from sqlalchemy import Numeric
from datetime import datetime
import json
from extensions import db
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.types import Float
from flask import current_app
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import jwt

# At the very top of social_media_models.py
JWT_SECRET_KEY = "dtTHo1VSKHmNz3LXG_LjKPBwz8tnN0BTAiMgYrCWXbA"

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)  # Changed to nullable for Google users
    country = db.Column(db.String(100))
    last_login = db.Column(db.DateTime)
    trial_ends_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    email_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(255), nullable=True)
    
    # Add these new fields for Google auth and email verification
    verification_token_expires = db.Column(db.DateTime, nullable=True)
    google_id = db.Column(db.String(255), nullable=True, unique=True)
    auth_provider = db.Column(db.String(20), default='email') 
    reset_token = db.Column(db.String(255), nullable=True)
    reset_token_expires = db.Column(db.DateTime, nullable=True)
     # 'email' or 'google'

import uuid
from datetime import datetime

# Your existing models here
# ...

# Flashcard models
class FlashcardSet(db.Model):
    __tablename__ = 'flashcard_sets'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    title = db.Column(db.String(255), nullable=False)
    topic = db.Column(db.String(255), nullable=False)
    grade_level = db.Column(db.String(50), nullable=False)
    card_count = db.Column(db.Integer, default=0)
    time_per_card = db.Column(db.Integer, default=30)  # in seconds
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_public = db.Column(db.Boolean, default=False)
    source = db.Column(db.String(50), nullable=True)  # 'lesson_plan', 'manual', etc.
    source_id = db.Column(db.String(36), nullable=True)  # ID of source (e.g., lesson plan ID)
    
    # Define relationship to lesson plan
    lesson_plan_id = db.Column(db.String(36), db.ForeignKey('lesson_plans.id', ondelete='SET NULL'), nullable=True)


class Flashcard(db.Model):
    __tablename__ = 'flashcards'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    flashcard_set_id = db.Column(db.String(36), db.ForeignKey('flashcard_sets.id', ondelete='CASCADE'))
    front = db.Column(db.Text, nullable=False)
    back = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), default='definition')  # definition, concept, question, factoid
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    stripe_subscription_id = db.Column(db.String(255), unique=True)
    plan_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ends_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

class LessonPlanModel(db.Model):
    __tablename__ = 'lesson_plans'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id') if User else None)
    title = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    topic = db.Column(db.String(255), nullable=False)
    grade_level = db.Column(db.String(50), nullable=False)
    content_json = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)    

class Quiz(db.Model):
    __tablename__ = 'quizzes'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    title = db.Column(db.String(255), nullable=False)
    topic = db.Column(db.String(255), nullable=False)
    grade_level = db.Column(db.String(50), nullable=False)
    time_limit = db.Column(db.Integer, nullable=False)
    mode = db.Column(db.String(50), default='list')
    questions_json = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Add these new fields for lesson plan integration
    source = db.Column(db.String(50), nullable=True)  # 'lesson_plan', 'manual', etc.
    source_id = db.Column(db.String(36), nullable=True)  # ID of source (e.g., lesson plan ID)

class QuizSubmission(db.Model):
    __tablename__ = 'quiz_submissions'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    quiz_id = db.Column(db.String(36), db.ForeignKey('quizzes.id'))
    quiz_owner_id = db.Column(db.String(36))  # Add this line
    student_name = db.Column(db.String(255), nullable=False)
    score = db.Column(db.Integer)
    max_score = db.Column(db.Integer)
    answers = db.Column(db.Text)  # Store answers as JSON
    time_taken = db.Column(db.Integer)  # In seconds
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

# User Feedback Model
class UserFeedback(db.Model):
    __tablename__ = 'user_feedback'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), nullable=True)  # Optional, can be anonymous
    rating = db.Column(db.Integer, nullable=False)  # 1-5 star rating
    comment = db.Column(db.Text, nullable=True)  # Optional comment
    display_name = db.Column(db.String(100), nullable=True)  # Optional display name
    platform = db.Column(db.String(50), nullable=True)  # Device platform
    page = db.Column(db.String(255), nullable=True)  # Page where feedback was submitted
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'rating': self.rating,
            'comment': self.comment,
            'display_name': self.display_name,
            'platform': self.platform,
            'page': self.page,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


# Parent Feedback Model - for lesson feedback from parents
class ParentFeedback(db.Model):
    __tablename__ = 'parent_feedback'
    __table_args__ = {'mysql_charset': 'utf8mb3'}

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = db.Column(db.String(36), nullable=True)
    tutor_id = db.Column(db.String(36), nullable=True)
    lesson_id = db.Column(db.String(36), nullable=True)
    student_name = db.Column(db.String(255), nullable=True)
    tutor_name = db.Column(db.String(255), nullable=True)
    subject = db.Column(db.String(100), nullable=True)
    lesson_date = db.Column(db.String(100), nullable=True)
    rating = db.Column(db.String(50), nullable=False)  # very-dissatisfied, dissatisfied, neutral, satisfied, very-satisfied
    positive_comments = db.Column(db.Text, nullable=True)  # JSON array of selected positive feedback
    negative_comments = db.Column(db.Text, nullable=True)  # JSON array of selected improvement areas
    additional_comments = db.Column(db.Text, nullable=True)  # Free text comments
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'tutor_id': self.tutor_id,
            'lesson_id': self.lesson_id,
            'student_name': self.student_name,
            'tutor_name': self.tutor_name,
            'subject': self.subject,
            'lesson_date': self.lesson_date,
            'rating': self.rating,
            'positive_comments': json.loads(self.positive_comments) if self.positive_comments else [],
            'negative_comments': json.loads(self.negative_comments) if self.negative_comments else [],
            'additional_comments': self.additional_comments,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Enrollment(db.Model):
    __tablename__ = 'enrollments'
    __table_args__ = (
        {'mysql_charset': 'utf8mb3'},  # Match existing tables
    )
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.String(36), nullable=False)
    payment_status = db.Column(db.String(20), default='pending')
    payment_method = db.Column(db.String(20))
    transaction_id = db.Column(db.String(100))
    amount_paid = db.Column(db.Float)
    enrollment_date = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<Enrollment {self.id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'course_id': self.course_id,
            'payment_status': self.payment_status,
            'payment_method': self.payment_method,
            'amount_paid': self.amount_paid,
            'enrollment_date': self.enrollment_date.isoformat() if self.enrollment_date else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_active': self.is_active
        }
    
# models.py

class TeamSubmission(db.Model):
    __tablename__ = 'team_submissions'
    __table_args__ = {'mysql_charset': 'utf8mb3'}
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    quiz_id = db.Column(db.String(36))  # Removed ForeignKey
    team_id = db.Column(db.Integer)  # Changed to Integer, removed ForeignKey
    team_name = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Integer)
    max_score = db.Column(db.Integer)
    answers_json = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Comment out relationships for now
    # team = db.relationship('QuizTeam', backref='submissions')

class QuizTeam(db.Model):
    __tablename__ = 'quiz_teams'
    __table_args__ = {'mysql_charset': 'utf8mb3'}
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # Changed to Integer
    quiz_id = db.Column(db.String(36))  # Removed ForeignKey
    name = db.Column(db.String(255), nullable=False)
    members_json = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def members(self):
        return json.loads(self.members_json) if self.members_json else []
    
    @members.setter
    def members(self, value):
        self.members_json = json.dumps(value)
    
    # Relationship        
    @property
    def answers(self):
        return json.loads(self.answers_json) if self.answers_json else {}
    
    @answers.setter
    def answers(self, value):
        self.answers_json = json.dumps(value)

# Add this to models.py

class BlogSubscription(db.Model):
    __tablename__ = 'blog_subscriptions'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    subscription_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    preferences_json = db.Column(db.Text, nullable=True)  # Store subscription preferences as JSON
    source = db.Column(db.String(100), nullable=True)  # Where they subscribed from (e.g., 'job_bundle')
    
    # Define relationship to user
    user = db.relationship('User', backref=db.backref('blog_subscriptions', lazy=True))
    
    def __repr__(self):
        return f'<BlogSubscription {self.email}>'
    
    @property
    def preferences(self):
        if self.preferences_json:
            return json.loads(self.preferences_json)
        return {}
    
    @preferences.setter
    def preferences(self, value):
        self.preferences_json = json.dumps(value)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'email': self.email,
            'name': self.name,
            'subscription_date': self.subscription_date.isoformat() if self.subscription_date else None,
            'is_active': self.is_active,
            'preferences': self.preferences,
            'source': self.source
        } 

class GeometryQuiz(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    topic = db.Column(db.String(200), nullable=False)
    grade_level = db.Column(db.String(50), nullable=False)
    time_limit = db.Column(db.Integer, default=30)
    mode = db.Column(db.String(20), default='list')
    questions_json = db.Column(db.Text, nullable=False)
    geometry_types = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<GeometryQuiz {self.id} - {self.title}>'
        

# GeometryQuizSubmission Database Model
class GeometryQuizSubmission(db.Model):
    __tablename__ = 'geometry_quiz_submissions'
    
    id = db.Column(db.String(36), primary_key=True)
    quiz_id = db.Column(db.String(36), nullable=False)  # Simple string, no FK for now
    student_name = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Float, nullable=False)
    max_score = db.Column(db.Float, nullable=False)
    answers_json = db.Column(db.Text, nullable=True)
    time_taken = db.Column(db.Integer, nullable=True)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # REMOVED: relationship to avoid FK issues
    
    def __repr__(self):
        return f'<GeometryQuizSubmission {self.id} - {self.student_name} - {self.score}/{self.max_score}>'
        
# Add this to your models.py file

class CourseInterestLead(db.Model):
    __tablename__ = 'course_interest_leads'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    course_selected = db.Column(db.String(100), nullable=False)
    cohort_date = db.Column(db.String(50), nullable=False)
    full_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    career_goals = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='new')  # new, contacted, converted, etc.
    source = db.Column(db.String(50), default='landing_page')
    utm_source = db.Column(db.String(100), nullable=True)
    utm_medium = db.Column(db.String(100), nullable=True)
    utm_campaign = db.Column(db.String(100), nullable=True)
    
    def __repr__(self):
        return f'<CourseInterestLead {self.full_name} - {self.course_selected}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'course_selected': self.course_selected,
            'cohort_date': self.cohort_date,
            'full_name': self.full_name,
            'email': self.email,
            'career_goals': self.career_goals,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'status': self.status,
            'source': self.source,
            'utm_source': self.utm_source,
            'utm_medium': self.utm_medium,
            'utm_campaign': self.utm_campaign
        }
class MathLessonPlanModel(db.Model):
    __tablename__ = 'math_lesson_plans'
    
    # Primary fields
    id = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.String(36), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(100), nullable=False, default='mathematics')
    topic = db.Column(db.String(255), nullable=False)
    grade_level = db.Column(db.String(50), nullable=False)
    
    # Lesson specifications
    duration_minutes = db.Column(db.Integer, nullable=False, default=50)
    difficulty_level = db.Column(db.String(20), nullable=False, default='intermediate')
    objectives = db.Column(db.Text)
    
    # Content storage
    content_json = db.Column(db.Text, nullable=False)  # Main lesson content
    features_enabled = db.Column(db.JSON)  # JSON field for feature flags
    
    # Quick lookup flags for better querying
    has_graphs = db.Column(db.Boolean, default=False)
    has_formulas = db.Column(db.Boolean, default=False)
    has_examples = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, **kwargs):
        super(MathLessonPlanModel, self).__init__(**kwargs)
        # Auto-set feature flags based on content
        if self.content_json:
            self._update_feature_flags()
    
    def _update_feature_flags(self):
        """Update boolean flags based on content for faster querying"""
        try:
            content = json.loads(self.content_json) if isinstance(self.content_json, str) else self.content_json
            
            # Check for graphs
            self.has_graphs = bool(content.get('graphs') or 
                                 any('graph' in str(v).lower() for v in content.values() if isinstance(v, str)))
            
            # Check for formulas
            self.has_formulas = bool(content.get('key_formulas') or 
                                   content.get('formulas') or
                                   any('formula' in str(v).lower() for v in content.values() if isinstance(v, str)))
            
            # Check for examples
            self.has_examples = bool(content.get('worked_examples') or 
                                   content.get('examples') or
                                   any('example' in str(v).lower() for v in content.values() if isinstance(v, str)))
        except (json.JSONDecodeError, AttributeError):
            # Fallback to False if content parsing fails
            self.has_graphs = False
            self.has_formulas = False
            self.has_examples = False
    
    def to_dict(self):
        """Convert model to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'subject': self.subject,
            'topic': self.topic,
            'grade_level': self.grade_level,
            'duration_minutes': self.duration_minutes,
            'difficulty_level': self.difficulty_level,
            'objectives': self.objectives,
            'content_json': json.loads(self.content_json) if isinstance(self.content_json, str) else self.content_json,
            'features_enabled': self.features_enabled,
            'has_graphs': self.has_graphs,
            'has_formulas': self.has_formulas,
            'has_examples': self.has_examples,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_by_user(cls, user_id, limit=50, offset=0):
        """Get math lesson plans for a specific user"""
        return cls.query.filter_by(user_id=user_id)\
                       .order_by(cls.created_at.desc())\
                       .limit(limit)\
                       .offset(offset)\
                       .all()
    
    @classmethod
    def get_by_subject_and_grade(cls, user_id, subject, grade_level):
        """Get lesson plans filtered by subject and grade level"""
        return cls.query.filter_by(
            user_id=user_id,
            subject=subject,
            grade_level=grade_level
        ).order_by(cls.created_at.desc()).all()
    
    @classmethod
    def search_by_topic(cls, user_id, topic_keyword):
        """Search lesson plans by topic keyword"""
        return cls.query.filter(
            cls.user_id == user_id,
            cls.topic.contains(topic_keyword)
        ).order_by(cls.created_at.desc()).all()
    
    def __repr__(self):
        return f'<MathLessonPlan {self.id}: {self.title}>'


# =============================================
# UTILITY FUNCTIONS FOR MATH LESSON PLANS
# =============================================

def create_math_lesson_plan(user_id, title, subject, topic, grade_level, 
                           duration_minutes, difficulty_level, objectives, 
                           content_data, features_enabled=None):
    """
    Helper function to create a new math lesson plan
    
    Args:
        user_id (str): User identifier
        title (str): Lesson plan title
        subject (str): Subject (mathematics, physics, etc.)
        topic (str): Specific topic
        grade_level (str): Grade level
        duration_minutes (int): Lesson duration
        difficulty_level (str): Difficulty level
        objectives (str): Learning objectives
        content_data (dict): Lesson content
        features_enabled (dict): Feature flags
    
    Returns:
        MathLessonPlanModel: Created lesson plan instance
    """
    import uuid
    
    lesson_plan_model = MathLessonPlanModel(
        id=str(uuid.uuid4()),
        user_id=user_id,
        title=title,
        subject=subject,
        topic=topic,
        grade_level=grade_level,
        duration_minutes=duration_minutes,
        difficulty_level=difficulty_level,
        objectives=objectives,
        content_json=json.dumps(content_data),
        features_enabled=features_enabled or {}
    )
    
    return lesson_plan

def get_math_lesson_stats(user_id):
    """Get statistics about user's math lesson plans"""
    total_lessons = MathLessonPlanModel.query.filter_by(user_id=user_id).count()
    
    subject_breakdown = db.session.query(
        MathLessonPlanModel.subject,
        db.func.count(MathLessonPlanModel.id)
    ).filter_by(user_id=user_id).group_by(MathLessonPlanModel.subject).all()
    
    grade_breakdown = db.session.query(
        MathLessonPlanModel.grade_level,
        db.func.count(MathLessonPlanModel.id)
    ).filter_by(user_id=user_id).group_by(MathLessonPlanModel.grade_level).all()
    
    return {
        'total_lessons': total_lessons,
        'subjects': dict(subject_breakdown),
        'grade_levels': dict(grade_breakdown),
        'lessons_with_graphs': MathLessonPlanModel.query.filter_by(user_id=user_id, has_graphs=True).count(),
        'lessons_with_formulas': MathLessonPlanModel.query.filter_by(user_id=user_id, has_formulas=True).count(),
        'lessons_with_examples': MathLessonPlanModel.query.filter_by(user_id=user_id, has_examples=True).count()
    }

# Database Model
class WebinarRegistration(db.Model):
    __tablename__ = 'webinar_registrations'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    parent_type = db.Column(db.String(50), nullable=False)
    parent_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, index=True)
    phone_number = db.Column(db.String(20), nullable=True)
    kids_ages = db.Column(db.Text, nullable=False)
    challenges = db.Column(db.Text, nullable=True)
    expectations = db.Column(db.Text, nullable=True)
    webinar_date = db.Column(db.String(20), nullable=False)
    webinar_time = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'parent_type': self.parent_type,
            'parent_name': self.parent_name,
            'email': self.email,
            'phone_number': self.phone_number,
            'kids_ages': self.kids_ages,
            'challenges': self.challenges,
            'expectations': self.expectations,
            'webinar_date': self.webinar_date,
            'webinar_time': self.webinar_time,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# Database Model for Webinar Feedback
class WebinarFeedback(db.Model):
    __tablename__ = 'webinar_feedback'
    
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # parent, tutor, guardian, educator
    sessions_attended = db.Column(db.Text, nullable=False)  # JSON string of attended sessions
    rating = db.Column(db.Integer, nullable=True)  # 1-5 star rating
    experience = db.Column(db.Text, nullable=False)
    improvements = db.Column(db.Text, nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    webinar_date = db.Column(db.String(20), default='2025-08-09')  # Which webinar this feedback is for
    
    def __repr__(self):
        return f'<WebinarFeedback {self.full_name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'email': self.email,
            'location': self.location,
            'category': self.category,
            'sessions_attended': json.loads(self.sessions_attended) if self.sessions_attended else [],
            'rating': self.rating,
            'experience': self.experience,
            'improvements': self.improvements,
            'submitted_at': self.submitted_at.isoformat(),
            'webinar_date': self.webinar_date
        }
        
# Updated Database Models for Deciph.AI Backend

class Admin(db.Model):
    """Enhanced Admin model with proper schema"""
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='admin')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Admin {self.email}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

class Student(db.Model):
    """Enhanced Student model with comprehensive schema"""
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=True)
    phone_number = db.Column(db.String(20), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=True)  # Allow NULL for Google OAuth users
    age = db.Column(db.Integer, nullable=True)
    grade_level = db.Column(db.String(10), nullable=True)
    school_name = db.Column(db.String(200), nullable=True)
    profile_complete = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    auth_provider = db.Column(db.String(20), default='email')
    email_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(255))
    verification_token_expires = db.Column(db.DateTime)
    total_points = db.Column(db.Integer, default=0)
    current_level = db.Column(db.Integer, default=1)
    achievements = db.Column(db.Text)  # JSON string of achievements
    preferred_service = db.Column(db.String(20))
    acard_balance = db.Column(db.Numeric(10, 2), default=0.00)

    # Profile fields for student timeline/social features
    workshop = db.Column(db.String(20), nullable=True)  # coding, graphics, video_editor
    birthday = db.Column(db.Date, nullable=True)
    favourite_game = db.Column(db.String(100), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    profile_picture_url = db.Column(db.String(500), nullable=True)
    portfolio_link = db.Column(db.String(100), unique=True, nullable=True)  # Unique shareable portfolio link

    def __repr__(self):
        return f'<Student {self.email}>'
    
    @property
    def pending_tasks_count(self):
        """Get count of pending tasks for this student"""
        return StudentTask.query.filter_by(student_id=self.id, status='pending').count()
    
    @property
    def completed_tasks_count(self):
        """Get count of completed tasks for this student"""
        return StudentTask.query.filter_by(student_id=self.id, status='completed').count()
    
    @property
    def achievements_list(self):
        """Get achievements as a list"""
        if self.achievements:
            try:
                return json.loads(self.achievements)
            except:
                return []
        return []
    
    def add_achievement(self, achievement):
        """Add a new achievement"""
        achievements = self.achievements_list
        if achievement not in achievements:
            achievements.append(achievement)
            self.achievements = json.dumps(achievements)
    
    def get_missing_fields(self):
        """Get list of missing profile fields"""
        missing = []
        if not self.age:
            missing.append('age')
        if not self.grade_level:
            missing.append('grade_level')
        if not self.school_name:
            missing.append('school_name')
        return missing

    def update_profile_complete_status(self):
        """Update profile_complete based on required fields"""
        self.profile_complete = len(self.get_missing_fields()) == 0

    def to_dict(self):
        result = {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'username': self.username,
            'phone_number': self.phone_number,
            'age': self.age,
            'grade_level': self.grade_level,
            'school_name': self.school_name,
            'profile_complete': self.profile_complete,
            'total_points': self.total_points,
            'current_level': self.current_level,
            'acard_balance': float(self.acard_balance),
            'pending_tasks': self.pending_tasks_count,
            'completed_tasks': self.completed_tasks_count,
            'is_active': self.is_active,
            'achievements': self.achievements_list,
            'preferred_service': self.preferred_service,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

        # New profile fields - only include if they exist (for backward compatibility)
        if hasattr(self, 'workshop'):
            result['workshop'] = self.workshop
        if hasattr(self, 'birthday'):
            result['birthday'] = self.birthday.isoformat() if self.birthday else None
        if hasattr(self, 'favourite_game'):
            result['favourite_game'] = self.favourite_game
        if hasattr(self, 'bio'):
            result['bio'] = self.bio
        if hasattr(self, 'profile_picture_url'):
            result['profile_picture_url'] = self.profile_picture_url
        if hasattr(self, 'portfolio_link'):
            result['portfolio_link'] = self.portfolio_link

        return result

class StudentTask(db.Model):
    """Enhanced StudentTask model with external URL support and proper relationships"""
    __tablename__ = 'student_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=False)
    task_type = db.Column(db.String(20), nullable=False)  # mathematics, english, etc.
    task_title = db.Column(db.String(200), nullable=False)
    task_description = db.Column(db.Text)
    task_data = db.Column(db.Text)  # JSON string for flexible data storage
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed, expired
    points_reward = db.Column(db.Integer, default=0)
    acard_credit = db.Column(db.Numeric(10, 2), default=0.00)
    due_date = db.Column(db.DateTime)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Relationships
    student = db.relationship('Student', backref=db.backref('tasks', lazy=True))
    admin = db.relationship('Admin', backref=db.backref('assigned_tasks', lazy=True))
    
    def __repr__(self):
        return f'<StudentTask {self.task_title} for {self.student_id}>'
    
    @property
    def task_data_dict(self):
        """Get task_data as a dictionary"""
        if self.task_data:
            try:
                return json.loads(self.task_data)
            except:
                return {}
        return {}
    
    @property
    def is_overdue(self):
        """Check if task is overdue"""
        return (self.due_date and 
                datetime.utcnow() > self.due_date and 
                self.status != 'completed')
    
    @property
    def external_url(self):
        """Get external URL if this is an external task"""
        data = self.task_data_dict
        return data.get('external_url')
    
    @property
    def task_file(self):
        """Get task file name if specified"""
        data = self.task_data_dict
        return data.get('task_file')
    
    @property
    def is_external(self):
        """Check if this is an external task"""
        return bool(self.external_url or self.task_file)
    
    @property
    def completion_data(self):
        """Get completion data"""
        data = self.task_data_dict
        return data.get('completion_data', {})
    
    @property
    def is_weekly_task(self):
        """Check if this is a weekly scheduled task"""
        data = self.task_data_dict
        return data.get('schedule_type') == 'weekly'
    
    @property
    def scheduled_day(self):
        """Get scheduled day for weekly tasks"""
        data = self.task_data_dict
        return data.get('scheduled_day')
    
    def update_task_data(self, new_data):
        """Update task_data with new information"""
        current_data = self.task_data_dict
        current_data.update(new_data)
        self.task_data = json.dumps(current_data)
    
    def mark_completed(self, completion_data=None):
        """Mark task as completed with optional completion data"""
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
        
        if completion_data:
            self.update_task_data({'completion_data': completion_data})
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'admin_id': self.admin_id,
            'task_type': self.task_type,
            'task_title': self.task_title,
            'task_description': self.task_description,
            'task_data': self.task_data_dict,
            'status': self.status,
            'points_reward': self.points_reward,
            'acard_credit': float(self.acard_credit),
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'assigned_at': self.assigned_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'is_overdue': self.is_overdue,
            'external_url': self.external_url,
            'task_file': self.task_file,
            'is_external': self.is_external,
            'completion_data': self.completion_data,
            'is_weekly_task': self.is_weekly_task,
            'scheduled_day': self.scheduled_day
        }


class StudentPost(db.Model):
    """Student post model for timeline/social features"""
    __tablename__ = 'student_posts'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    content = db.Column(db.Text, nullable=True)
    post_type = db.Column(db.String(20), default='text')  # text, image, video, mixed
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    student = db.relationship('Student', backref=db.backref('posts', lazy='dynamic'))
    media = db.relationship('PostMedia', backref='post', lazy='dynamic')
    likes = db.relationship('PostLike', backref='post', lazy='dynamic')
    comments = db.relationship('PostComment', backref='post', lazy='dynamic')

    def __repr__(self):
        return f'<StudentPost {self.id} by Student {self.student_id}>'

    def to_dict(self, current_student_id=None):
        """Convert post to dictionary with optional current student context"""
        # Get active likes and comments counts
        active_likes = [like for like in self.likes if like.is_active]
        active_comments = [comment for comment in self.comments if comment.is_active]

        # Check if current student has liked this post
        has_liked = False
        if current_student_id:
            has_liked = any(like.student_id == current_student_id and like.is_active for like in self.likes)

        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.name if self.student else 'Unknown',
            'student_username': self.student.username if self.student else None,
            'student_profile_picture': self.student.profile_picture_url if self.student else None,
            'content': self.content,
            'post_type': self.post_type,
            'media': [m.to_dict() for m in self.media if m.is_active],
            'likes_count': len(active_likes),
            'comments_count': len(active_comments),
            'has_liked': has_liked,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class PostMedia(db.Model):
    """Media attachments for student posts"""
    __tablename__ = 'post_media'

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('student_posts.id'), nullable=False)
    media_type = db.Column(db.String(20), nullable=False)  # image, video, avatar
    media_url = db.Column(db.String(500), nullable=False)  # S3 URL
    s3_key = db.Column(db.String(500), nullable=False)  # S3 key for deletion
    file_name = db.Column(db.String(255), nullable=True)
    file_size_mb = db.Column(db.Float, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<PostMedia {self.id} for Post {self.post_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'post_id': self.post_id,
            'media_type': self.media_type,
            'media_url': self.media_url,
            'file_name': self.file_name,
            'file_size_mb': self.file_size_mb,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class PostLike(db.Model):
    """Likes for student posts"""
    __tablename__ = 'post_likes'

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('student_posts.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    student = db.relationship('Student', backref=db.backref('likes', lazy='dynamic'))

    # Ensure unique constraint: one like per student per post
    __table_args__ = (db.UniqueConstraint('post_id', 'student_id', name='unique_post_like'),)

    def __repr__(self):
        return f'<PostLike {self.id} by Student {self.student_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'post_id': self.post_id,
            'student_id': self.student_id,
            'student_name': self.student.name if self.student else 'Unknown',
            'student_username': self.student.username if self.student else None,
            'student_profile_picture': self.student.profile_picture_url if self.student else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class PostComment(db.Model):
    """Comments for student posts"""
    __tablename__ = 'post_comments'

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('student_posts.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    student = db.relationship('Student', backref=db.backref('comments', lazy='dynamic'))

    def __repr__(self):
        return f'<PostComment {self.id} by Student {self.student_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'post_id': self.post_id,
            'student_id': self.student_id,
            'student_name': self.student.name if self.student else 'Unknown',
            'student_username': self.student.username if self.student else None,
            'student_profile_picture': self.student.profile_picture_url if self.student else None,
            'content': self.content,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class PortfolioItem(db.Model):
    """Portfolio items for certificates, awards, achievements"""
    __tablename__ = 'portfolio_items'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    item_type = db.Column(db.String(50), nullable=False)  # certificate, award, achievement, file
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    issuer = db.Column(db.String(200), nullable=True)  # Organization/institution that issued
    issue_date = db.Column(db.Date, nullable=True)
    file_url = db.Column(db.String(500), nullable=True)  # S3 URL for uploaded file
    s3_key = db.Column(db.String(500), nullable=True)
    file_name = db.Column(db.String(255), nullable=True)
    file_size_mb = db.Column(db.Float, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    student = db.relationship('Student', backref=db.backref('portfolio_items', lazy='dynamic'))

    def __repr__(self):
        return f'<PortfolioItem {self.title} - {self.item_type}>'

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'item_type': self.item_type,
            'title': self.title,
            'description': self.description,
            'issuer': self.issuer,
            'issue_date': self.issue_date.isoformat() if self.issue_date else None,
            'file_url': self.file_url,
            'file_name': self.file_name,
            'file_size_mb': self.file_size_mb,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class PortfolioProject(db.Model):
    """Detailed projects for student portfolio"""
    __tablename__ = 'portfolio_projects'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    project_type = db.Column(db.String(50), nullable=False)  # top_project, in_class_project, personal_project
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    technologies = db.Column(db.Text, nullable=True)  # JSON array of technologies used
    project_url = db.Column(db.String(500), nullable=True)  # Live project URL
    github_url = db.Column(db.String(500), nullable=True)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    is_featured = db.Column(db.Boolean, default=False)
    display_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    student = db.relationship('Student', backref=db.backref('portfolio_projects', lazy='dynamic'))
    media = db.relationship('PortfolioMedia', backref='project', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<PortfolioProject {self.title}>'

    @property
    def technologies_list(self):
        """Get technologies as a list"""
        if self.technologies:
            try:
                return json.loads(self.technologies)
            except:
                return []
        return []

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'project_type': self.project_type,
            'title': self.title,
            'description': self.description,
            'technologies': self.technologies_list,
            'project_url': self.project_url,
            'github_url': self.github_url,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'is_featured': self.is_featured,
            'display_order': self.display_order,
            'is_active': self.is_active,
            'media': [m.to_dict() for m in self.media if m.is_active],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class PortfolioMedia(db.Model):
    """Media files (images, videos) for portfolio projects"""
    __tablename__ = 'portfolio_media'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('portfolio_projects.id'), nullable=False)
    media_type = db.Column(db.String(20), nullable=False)  # image, video
    media_url = db.Column(db.String(500), nullable=False)
    s3_key = db.Column(db.String(500), nullable=False)
    file_name = db.Column(db.String(255), nullable=True)
    file_size_mb = db.Column(db.Float, nullable=True)
    caption = db.Column(db.String(500), nullable=True)
    display_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<PortfolioMedia {self.media_type} for Project {self.project_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'media_type': self.media_type,
            'media_url': self.media_url,
            'file_name': self.file_name,
            'file_size_mb': self.file_size_mb,
            'caption': self.caption,
            'display_order': self.display_order,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class PortfolioReview(db.Model):
    """Reviews and testimonials for student portfolio"""
    __tablename__ = 'portfolio_reviews'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    reviewer_name = db.Column(db.String(200), nullable=False)
    reviewer_title = db.Column(db.String(200), nullable=True)  # e.g., "Teacher", "Project Partner"
    reviewer_organization = db.Column(db.String(200), nullable=True)
    review_text = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=True)  # 1-5 stars
    project_id = db.Column(db.Integer, db.ForeignKey('portfolio_projects.id'), nullable=True)  # Optional link to project
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    student = db.relationship('Student', backref=db.backref('portfolio_reviews', lazy='dynamic'))

    def __repr__(self):
        return f'<PortfolioReview by {self.reviewer_name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'reviewer_name': self.reviewer_name,
            'reviewer_title': self.reviewer_title,
            'reviewer_organization': self.reviewer_organization,
            'review_text': self.review_text,
            'rating': self.rating,
            'project_id': self.project_id,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class SchemeOfWork(db.Model):
    """Scheme of Work model for students to upload their work plans"""
    __tablename__ = 'scheme_of_works'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    file_type = db.Column(db.String(20), nullable=False)  # image, document, text
    file_url = db.Column(db.String(500), nullable=True)  # S3 URL for image/document uploads
    text_content = db.Column(db.Text, nullable=True)  # For text-based scheme of work
    s3_key = db.Column(db.String(500), nullable=True)  # S3 key for file deletion
    file_name = db.Column(db.String(255), nullable=True)
    file_size_mb = db.Column(db.Float, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    student = db.relationship('Student', backref=db.backref('scheme_of_works', lazy='dynamic'))

    def __repr__(self):
        return f'<SchemeOfWork {self.title} by Student {self.student_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'title': self.title,
            'description': self.description,
            'file_type': self.file_type,
            'file_url': self.file_url,
            'text_content': self.text_content,
            'file_name': self.file_name,
            'file_size_mb': self.file_size_mb,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ACardTransaction(db.Model):
    """A-Card transaction model with proper relationships"""
    __tablename__ = 'acard_transactions'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=True)
    task_id = db.Column(db.Integer, db.ForeignKey('student_tasks.id'), nullable=True)
    transaction_type = db.Column(db.String(20), nullable=False)  # manual_credit, task_reward, admin_completion, debit
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.String(200))
    balance_after = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    student = db.relationship('Student', backref=db.backref('acard_transactions', lazy=True))
    admin = db.relationship('Admin', backref=db.backref('acard_actions', lazy=True))
    task = db.relationship('StudentTask', backref=db.backref('acard_transaction', lazy=True))
    
    def __repr__(self):
        return f'<ACardTransaction {self.transaction_type} ${self.amount} for {self.student_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'admin_id': self.admin_id,
            'task_id': self.task_id,
            'transaction_type': self.transaction_type,
            'amount': float(self.amount),
            'description': self.description,
            'balance_after': float(self.balance_after),
            'created_at': self.created_at.isoformat(),
            'student_name': self.student.name if self.student else None,
            'admin_name': self.admin.name if self.admin else None,
            'task_title': self.task.task_title if self.task else None
        }

class LearnEarnConfig(db.Model):
    """Learn and Earn AI configuration model - supports grade/subject/skill specific configs"""
    __tablename__ = 'learn_earn_config'

    id = db.Column(db.Integer, primary_key=True)
    grade_level = db.Column(db.String(20), nullable=False)  # elementary, middle, senior
    category_type = db.Column(db.String(20), nullable=False)  # subject or skill
    category_name = db.Column(db.String(50), nullable=False)  # mathematics, english, science, graphics, coding, video-editing
    topics = db.Column(db.Text, nullable=False)  # JSON array of topics
    num_topics = db.Column(db.Integer, default=5)
    countdown_minutes = db.Column(db.Float, default=2.5)
    daily_limit = db.Column(db.Integer, default=5)
    min_words = db.Column(db.Integer, default=35)
    max_words = db.Column(db.Integer, default=50)
    summary_words = db.Column(db.Integer, default=15)
    complexity_level = db.Column(db.String(20), default='moderate')  # basic, moderate, advanced
    rewards_config = db.Column(db.Text, nullable=False)  # JSON object with reward tiers
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<LearnEarnConfig {self.grade_level} - {self.category_name}>'

    def get_topics(self):
        """Get topics as a list"""
        if self.topics:
            try:
                return json.loads(self.topics)
            except:
                return []
        return []

    def set_topics(self, topics_list):
        """Set topics from a list"""
        self.topics = json.dumps(topics_list)

    def get_rewards(self):
        """Get rewards configuration as a dict"""
        if self.rewards_config:
            try:
                return json.loads(self.rewards_config)
            except:
                return self.default_rewards()
        return self.default_rewards()

    def set_rewards(self, rewards_dict):
        """Set rewards configuration from a dict"""
        self.rewards_config = json.dumps(rewards_dict)

    @staticmethod
    def default_rewards():
        """Return default rewards configuration"""
        return {
            'low_points': 0,
            'low_acard': 0,
            'medium_points': 2.5,
            'medium_acard': 2.5,
            'high_points': 5,
            'high_acard': 5
        }

    @staticmethod
    def get_default_topics(grade_level, category_type, category_name):
        """Get default topics for a specific grade/category combination"""
        defaults = {
            # Elementary - Subjects
            ('elementary', 'subject', 'mathematics'): ['Counting', 'Addition', 'Subtraction', 'Shapes', 'Patterns'],
            ('elementary', 'subject', 'english'): ['Alphabet', 'Phonics', 'Simple Sentences', 'Rhyming Words', 'Story Elements'],
            ('elementary', 'subject', 'science'): ['Plants', 'Animals', 'Weather', 'The Sun', 'Water Cycle'],
            # Elementary - Skills
            ('elementary', 'skill', 'graphics'): ['Basic Shapes', 'Colors', 'Drawing Lines', 'Simple Patterns', 'Coloring'],
            ('elementary', 'skill', 'coding'): ['Sequences', 'Loops', 'Patterns', 'Problem Solving', 'Debugging'],
            ('elementary', 'skill', 'video-editing'): ['Video Basics', 'Cutting Clips', 'Adding Music', 'Transitions', 'Titles'],

            # Middle - Subjects
            ('middle', 'subject', 'mathematics'): ['Fractions', 'Decimals', 'Algebra Basics', 'Geometry', 'Ratios'],
            ('middle', 'subject', 'english'): ['Grammar', 'Paragraphs', 'Essay Structure', 'Literary Devices', 'Vocabulary'],
            ('middle', 'subject', 'science'): ['Cell', 'Photosynthesis', 'Forces', 'Energy', 'Ecosystems'],
            # Middle - Skills
            ('middle', 'skill', 'graphics'): ['Digital Art', 'Layers', 'Typography', 'Image Editing', 'Composition'],
            ('middle', 'skill', 'coding'): ['Variables', 'Functions', 'Conditionals', 'Arrays', 'Objects'],
            ('middle', 'skill', 'video-editing'): ['Timeline Editing', 'Effects', 'Audio Mixing', 'Color Grading', 'Keyframes'],

            # Senior - Subjects
            ('senior', 'subject', 'mathematics'): ['Calculus', 'Statistics', 'Trigonometry', 'Matrices', 'Probability'],
            ('senior', 'subject', 'english'): ['Rhetorical Analysis', 'Thesis Development', 'Research Papers', 'Critical Reading', 'Argumentation'],
            ('senior', 'subject', 'science'): ['DNA', 'Evolution', 'Chemical Reactions', 'Physics Laws', 'Organic Chemistry'],
            # Senior - Skills
            ('senior', 'skill', 'graphics'): ['Vector Graphics', 'Branding', 'UI Design', 'Photo Manipulation', '3D Basics'],
            ('senior', 'skill', 'coding'): ['OOP', 'APIs', 'Databases', 'Algorithms', 'Data Structures'],
            ('senior', 'skill', 'video-editing'): ['Motion Graphics', 'VFX', 'Advanced Color', 'Sound Design', 'Export Optimization'],
        }

        key = (grade_level, category_type, category_name)
        return defaults.get(key, ['Topic 1', 'Topic 2', 'Topic 3', 'Topic 4', 'Topic 5'])

    @staticmethod
    def get_default_config(grade_level, category_type, category_name):
        """Get complete default configuration for a specific grade/category"""
        # Base configuration by grade level
        grade_configs = {
            'elementary': {
                'min_words': 25,
                'max_words': 35,
                'summary_words': 10,
                'complexity_level': 'basic',
                'countdown_minutes': 3.0,
                'daily_limit': 5,
                'rewards': {
                    'low_points': 0,
                    'low_acard': 0,
                    'medium_points': 2,
                    'medium_acard': 2,
                    'high_points': 4,
                    'high_acard': 4
                }
            },
            'middle': {
                'min_words': 35,
                'max_words': 50,
                'summary_words': 15,
                'complexity_level': 'moderate',
                'countdown_minutes': 2.5,
                'daily_limit': 5,
                'rewards': {
                    'low_points': 0,
                    'low_acard': 0,
                    'medium_points': 2.5,
                    'medium_acard': 2.5,
                    'high_points': 5,
                    'high_acard': 5
                }
            },
            'senior': {
                'min_words': 45,
                'max_words': 65,
                'summary_words': 20,
                'complexity_level': 'advanced',
                'countdown_minutes': 2.0,
                'daily_limit': 5,
                'rewards': {
                    'low_points': 0,
                    'low_acard': 0,
                    'medium_points': 3,
                    'medium_acard': 3,
                    'high_points': 6,
                    'high_acard': 6
                }
            }
        }

        base_config = grade_configs.get(grade_level, grade_configs['middle'])
        topics = LearnEarnConfig.get_default_topics(grade_level, category_type, category_name)

        return {
            'grade_level': grade_level,
            'category_type': category_type,
            'category_name': category_name,
            'topics': topics,
            'num_topics': len(topics),
            **base_config
        }

    def to_dict(self):
        return {
            'id': self.id,
            'grade_level': self.grade_level,
            'category_type': self.category_type,
            'category_name': self.category_name,
            'topics': self.get_topics(),
            'num_topics': self.num_topics,
            'countdown_minutes': float(self.countdown_minutes),
            'daily_limit': self.daily_limit,
            'min_words': self.min_words,
            'max_words': self.max_words,
            'summary_words': self.summary_words,
            'complexity_level': self.complexity_level,
            'rewards': self.get_rewards(),
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class TaskNotification(db.Model):
    """Task notification model for student notifications"""
    __tablename__ = 'task_notifications'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('student_tasks.id'), nullable=True)
    notification_type = db.Column(db.String(30), nullable=False)  # assignment, reminder, completion, reward
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime)
    
    # Relationships
    student = db.relationship('Student', backref=db.backref('notifications', lazy=True))
    task = db.relationship('StudentTask', backref=db.backref('notifications', lazy=True))
    
    def __repr__(self):
        return f'<TaskNotification {self.notification_type} for {self.student_id}>'
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.read_at = datetime.utcnow()
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'task_id': self.task_id,
            'notification_type': self.notification_type,
            'title': self.title,
            'message': self.message,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat(),
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'task_title': self.task.task_title if self.task else None
        }

# Additional Models for Enhanced Functionality

class StudentLevel(db.Model):
    """Student level progression model"""
    __tablename__ = 'student_levels'
    
    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.Integer, unique=True, nullable=False)
    points_required = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    rewards = db.Column(db.Text)  # JSON string of rewards
    
    def __repr__(self):
        return f'<StudentLevel {self.level}: {self.title}>'
    
    @property
    def rewards_list(self):
        """Get rewards as a list"""
        if self.rewards:
            try:
                return json.loads(self.rewards)
            except:
                return []
        return []

class TaskTemplate(db.Model):
    """Task template model for reusable tasks"""
    __tablename__ = 'task_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=False)
    template_name = db.Column(db.String(200), nullable=False)
    task_type = db.Column(db.String(20), nullable=False)
    task_title = db.Column(db.String(200), nullable=False)
    task_description = db.Column(db.Text)
    default_points = db.Column(db.Integer, default=0)
    default_acard_credit = db.Column(db.Numeric(10, 2), default=0.00)
    template_data = db.Column(db.Text)  # JSON string
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    admin = db.relationship('Admin', backref=db.backref('task_templates', lazy=True))
    
    def __repr__(self):
        return f'<TaskTemplate {self.template_name}>'

class SchoolCircle(db.Model):
    """School circle model for managing school-based chat groups"""
    __tablename__ = 'school_circles'
    
    id = db.Column(db.Integer, primary_key=True)
    school_name = db.Column(db.String(200), unique=True, nullable=False)
    is_locked = db.Column(db.Boolean, default=False)
    locked_by_admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=True)
    locked_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    locked_by_admin = db.relationship('Admin', backref=db.backref('locked_circles', lazy=True))
    
    def __repr__(self):
        return f'<SchoolCircle {self.school_name}>'
    
    @property
    def student_count(self):
        """Get number of students in this school"""
        return Student.query.filter_by(school_name=self.school_name).count()
    
    def lock_circle(self, admin_id):
        """Lock the circle"""
        self.is_locked = True
        self.locked_by_admin_id = admin_id
        self.locked_at = datetime.utcnow()
    
    def unlock_circle(self):
        """Unlock the circle"""
        self.is_locked = False
        self.locked_by_admin_id = None
        self.locked_at = None
    
    def to_dict(self):
        return {
            'id': self.id,
            'school_name': self.school_name,
            'is_locked': self.is_locked,
            'student_count': self.student_count,
            'locked_by_admin': self.locked_by_admin.name if self.locked_by_admin else None,
            'locked_at': self.locked_at.isoformat() if self.locked_at else None,
            'created_at': self.created_at.isoformat()
        }

class CircleActivity(db.Model):
    """Circle activity log model"""
    __tablename__ = 'circle_activities'
    
    id = db.Column(db.Integer, primary_key=True)
    circle_id = db.Column(db.Integer, db.ForeignKey('school_circles.id'), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=False)
    action = db.Column(db.String(20), nullable=False)  # locked, unlocked
    students_notified = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    circle = db.relationship('SchoolCircle', backref=db.backref('activities', lazy=True))
    admin = db.relationship('Admin', backref=db.backref('circle_activities', lazy=True))
    
    def __repr__(self):
        return f'<CircleActivity {self.action} on {self.circle.school_name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'school_name': self.circle.school_name,
            'action': self.action,
            'admin_name': self.admin.name,
            'students_notified': self.students_notified,
            'created_at': self.created_at.isoformat()
        }

# Utility Functions for Models

def create_notification(student_id, notification_type, title, message, task_id=None):
    """Create a new task notification"""
    notification = TaskNotification(
        student_id=student_id,
        task_id=task_id,
        notification_type=notification_type,
        title=title,
        message=message
    )
    db.session.add(notification)
    return notification

def create_acard_transaction(student_id, amount, transaction_type, description, 
                           admin_id=None, task_id=None):
    """Create a new A-Card transaction"""
    student = Student.query.get(student_id)
    if not student:
        raise ValueError("Student not found")
    
    # Calculate new balance
    current_balance = float(student.acard_balance or 0)
    new_balance = current_balance + float(amount)
    
    # Update student balance
    student.acard_balance = new_balance
    
    # Create transaction record
    transaction = ACardTransaction(
        student_id=student_id,
        admin_id=admin_id,
        task_id=task_id,
        transaction_type=transaction_type,
        amount=amount,
        description=description,
        balance_after=new_balance
    )
    
    db.session.add(transaction)
    return transaction

def get_student_level(points):
    """Get student level based on points"""
    level = StudentLevel.query.filter(
        StudentLevel.points_required <= points
    ).order_by(StudentLevel.points_required.desc()).first()
    
    return level.level if level else 1

def calculate_level_progress(student):
    """Calculate student's progress to next level"""
    current_level = StudentLevel.query.filter_by(level=student.current_level).first()
    next_level = StudentLevel.query.filter_by(level=student.current_level + 1).first()
    
    if not next_level:
        return 100  # Max level reached
    
    current_points = current_level.points_required if current_level else 0
    next_points = next_level.points_required
    student_points = student.total_points
    
    if student_points >= next_points:
        return 100
    
    progress = ((student_points - current_points) / (next_points - current_points)) * 100
    return max(0, min(100, progress))

# Database initialization function
def init_default_data():
    """Initialize default data for the application"""
    try:
        # Create default student levels
        if StudentLevel.query.count() == 0:
            levels = [
                {'level': 1, 'points_required': 0, 'title': 'Beginner', 'description': 'Welcome to Deciph.AI!'},
                {'level': 2, 'points_required': 100, 'title': 'Learner', 'description': 'You are getting started!'},
                {'level': 3, 'points_required': 250, 'title': 'Scholar', 'description': 'Making good progress!'},
                {'level': 4, 'points_required': 500, 'title': 'Expert', 'description': 'You are becoming an expert!'},
                {'level': 5, 'points_required': 1000, 'title': 'Master', 'description': 'Mastery achieved!'},
            ]
            
            for level_data in levels:
                level = StudentLevel(**level_data)
                db.session.add(level)
        
        db.session.commit()
        
    except Exception as e:
        print(f"Error initializing default data: {str(e)}")
        db.session.rollback()

# Export all models for easy importing
__all__ = [
    'db',
    'Admin',
    'Student', 
    'StudentTask',
    'ACardTransaction',
    'TaskNotification',
    'StudentLevel',
    'TaskTemplate',
    'SchoolCircle',
    'CircleActivity',
    'create_notification',
    'create_acard_transaction',
    'get_student_level',
    'calculate_level_progress',
    'init_default_data'
]

question_number = db.Column(db.Integer, nullable=False)
question_text = db.Column(db.Text)  # Optional if include_questions is False
expected_answer = db.Column(db.Text, nullable=False)
question_type = db.Column(db.String(50), default='factual')  # 'factual', 'analytical', 'descriptive'
points = db.Column(db.Integer, default=10)
order = db.Column(db.Integer, default=0)

# Question settings
include_question = db.Column(db.Boolean, default=True)
is_required = db.Column(db.Boolean, default=True)

created_at = db.Column(db.DateTime, default=datetime.utcnow)
updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Relationships

def to_dict(self):
    return {
        'questionNumber': self.question_number,
        'questionText': self.question_text,
        'expectedAnswer': self.expected_answer,
        'questionType': self.question_type,
        'points': self.points,
        'includeQuestion': self.include_question
    }

def __repr__(self):
    return f'<WorksheetQuestion {self.question_number}>'

class WorksheetSubmission(db.Model):
    """Student submissions for worksheets with timer tracking"""
    __tablename__ = 'worksheet_submissions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    worksheet_id = db.Column(db.String(36), db.ForeignKey('worksheets.id'), nullable=False)
    student_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    
    # Student info (for anonymous users)
    student_name = db.Column(db.String(255))
    student_email = db.Column(db.String(255))
    
    # Submission data
    answers = db.Column(db.JSON)
    evaluation_results = db.Column(db.JSON)
    final_score = db.Column(db.Float)
    total_points = db.Column(db.Integer)
    
    # Timer tracking
    time_limit_seconds = db.Column(db.Integer)
    time_taken_seconds = db.Column(db.Integer)
    extra_time_used = db.Column(db.Boolean, default=False)
    extra_time_requested_at = db.Column(db.DateTime)
    extra_time_granted_at = db.Column(db.DateTime)
    extra_time_seconds = db.Column(db.Integer, default=0)
    
    # Submission status
    auto_submitted = db.Column(db.Boolean, default=False)
    completed = db.Column(db.Boolean, default=False)
    attempt_number = db.Column(db.Integer, default=1)
    
    # Timestamps
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    submitted_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    # Browser/device info for monitoring
    user_agent = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    screen_resolution = db.Column(db.String(20))
    
    # Anti-cheat monitoring
    tab_switches = db.Column(db.Integer, default=0)
    focus_lost_count = db.Column(db.Integer, default=0)
    suspicious_activity = db.Column(db.JSON)
    
    
    
    def calculate_score_percentage(self):
        """Calculate percentage score"""
        if self.total_points and self.total_points > 0:
            return round((self.final_score / self.total_points) * 100, 1)
        return 0.0
    
    def get_time_performance(self):
        """Get time performance metrics"""
        if not self.time_limit_seconds:
            return {}
        
        time_used = self.time_taken_seconds
        time_limit = self.time_limit_seconds
        
        if self.extra_time_used:
            time_limit += self.extra_time_seconds
        
        return {
            'time_used_seconds': time_used,
            'time_limit_seconds': time_limit,
            'time_remaining_seconds': max(0, time_limit - time_used),
            'time_efficiency': round((time_used / time_limit) * 100, 1) if time_limit > 0 else 0,
            'extra_time_used': self.extra_time_used,
            'auto_submitted': self.auto_submitted
        }
    
    def to_dict(self):
        return {
            'id': self.id,
            'worksheet_id': self.worksheet_id,
            'student_name': self.student_name,
            'final_score': self.final_score,
            'score_percentage': self.calculate_score_percentage(),
            'time_performance': self.get_time_performance(),
            'completed': self.completed,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'attempt_number': self.attempt_number
        }
    
    def __repr__(self):
        return f'<WorksheetSubmission {self.id}>'

class ExtraTimeRequest(db.Model):
    """Track extra time requests from students"""
    __tablename__ = 'extra_time_requests'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    submission_id = db.Column(db.String(36), db.ForeignKey('worksheet_submissions.id'), nullable=False)
    worksheet_id = db.Column(db.String(36), db.ForeignKey('worksheets.id'), nullable=False)
    student_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    
    # Request details
    requested_time_seconds = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.Text)  # Optional reason from student
    
    # Request status
    status = db.Column(db.String(20), default='pending')  # 'pending', 'approved', 'denied'
    approved_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    
    # Timestamps
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    responded_at = db.Column(db.DateTime)
    
    # Auto-approval settings
    auto_approved = db.Column(db.Boolean, default=False)
   
    
    def approve(self, approver_id=None, auto=False):
        """Approve the extra time request"""
        self.status = 'approved'
        self.approved_by = approver_id
        self.auto_approved = auto
        self.responded_at = datetime.utcnow()
        
        # Update the submission
        if self.submission:
            self.submission.extra_time_used = True
            self.submission.extra_time_granted_at = datetime.utcnow()
            self.submission.extra_time_seconds = self.requested_time_seconds
    
    def deny(self, approver_id=None):
        """Deny the extra time request"""
        self.status = 'denied'
        self.approved_by = approver_id
        self.responded_at = datetime.utcnow()
    
    def to_dict(self):
        return {
            'id': self.id,
            'submission_id': self.submission_id,
            'requested_time_seconds': self.requested_time_seconds,
            'requested_time_minutes': round(self.requested_time_seconds / 60, 1),
            'reason': self.reason,
            'status': self.status,
            'auto_approved': self.auto_approved,
            'requested_at': self.requested_at.isoformat() if self.requested_at else None,
            'responded_at': self.responded_at.isoformat() if self.responded_at else None
        }
    
    def __repr__(self):
        return f'<ExtraTimeRequest {self.id} - {self.status}>'

class WorksheetAnalytics(db.Model):
    __tablename__ = 'worksheet_analytics'
    __table_args__ = {'mysql_charset': 'utf8mb3'}
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    worksheet_id = db.Column(db.String(36), nullable=False)  # Removed ForeignKey
    
    total_submissions = db.Column(db.Integer, default=0)
    completed_submissions = db.Column(db.Integer, default=0)
    average_score = db.Column(db.Float, default=0.0)
    average_time_taken = db.Column(db.Integer, default=0)
    auto_submissions = db.Column(db.Integer, default=0)
    extra_time_requests = db.Column(db.Integer, default=0)
    extra_time_granted = db.Column(db.Integer, default=0)
    average_extra_time_used = db.Column(db.Integer, default=0)
    question_performance = db.Column(db.JSON)
    time_distribution = db.Column(db.JSON)
    last_calculated = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Question analytics
    question_performance = db.Column(db.JSON)  # {question_number: {avg_score, difficulty_index}}
    
    # Time distribution
    time_distribution = db.Column(db.JSON)  # {time_range: count}
    
    # Last updated
    last_calculated = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    
    def update_analytics(self):
        """Recalculate analytics based on current submissions"""
        submissions = WorksheetSubmission.query.filter_by(worksheet_id=self.worksheet_id).all()
        
        if not submissions:
            return
        
        # Basic metrics
        self.total_submissions = len(submissions)
        completed = [s for s in submissions if s.completed]
        self.completed_submissions = len(completed)
        
        if completed:
            # Score analytics
            scores = [s.final_score for s in completed if s.final_score is not None]
            self.average_score = sum(scores) / len(scores) if scores else 0.0
            
            # Time analytics
            times = [s.time_taken_seconds for s in completed if s.time_taken_seconds is not None]
            self.average_time_taken = sum(times) // len(times) if times else 0
            
            # Timer-specific analytics
            self.auto_submissions = len([s for s in completed if s.auto_submitted])
            self.extra_time_requests = len([s for s in completed if s.extra_time_used])
            
            # Calculate question performance
            question_scores = {}
            for submission in completed:
                if submission.evaluation_results:
                    for q_num, result in submission.evaluation_results.items():
                        if q_num not in question_scores:
                            question_scores[q_num] = []
                        question_scores[q_num].append(result.get('score', 0))
            
            # Average scores per question
            self.question_performance = {
                q_num: {
                    'average_score': sum(scores) / len(scores),
                    'difficulty_index': 100 - (sum(scores) / len(scores))  # Higher = more difficult
                }
                for q_num, scores in question_scores.items() if scores
            }
        
        self.last_calculated = datetime.utcnow()
    
    def to_dict(self):
        return {
            'worksheet_id': self.worksheet_id,
            'total_submissions': self.total_submissions,
            'completed_submissions': self.completed_submissions,
            'completion_rate': round((self.completed_submissions / self.total_submissions) * 100, 1) if self.total_submissions > 0 else 0,
            'average_score': round(self.average_score, 1),
            'average_time_taken_minutes': round(self.average_time_taken / 60, 1) if self.average_time_taken else 0,
            'auto_submissions': self.auto_submissions,
            'auto_submission_rate': round((self.auto_submissions / self.completed_submissions) * 100, 1) if self.completed_submissions > 0 else 0,
            'extra_time_requests': self.extra_time_requests,
            'extra_time_request_rate': round((self.extra_time_requests / self.completed_submissions) * 100, 1) if self.completed_submissions > 0 else 0,
            'question_performance': self.question_performance,
            'last_calculated': self.last_calculated.isoformat() if self.last_calculated else None
        }
    
    def __repr__(self):
        return f'<WorksheetAnalytics {self.worksheet_id}>'

# =============================================
# UTILITY FUNCTIONS FOR WORKSHEET MANAGEMENT
# =============================================

def create_worksheet_with_timer(tutor_id, title, subject, questions, time_settings, **kwargs):
    """Create a new worksheet with timer settings"""
    
    # Calculate total seconds
    total_seconds = (
        time_settings.get('hours', 0) * 3600 +
        time_settings.get('minutes', 30) * 60 +
        time_settings.get('seconds', 0)
    )
    
    # Create worksheet
    worksheet = Worksheet(
        tutor_id=tutor_id,
        title=title,
        subject=subject,
        time_limit_hours=time_settings.get('hours', 0),
        time_limit_minutes=time_settings.get('minutes', 30),
        time_limit_seconds=time_settings.get('seconds', 0),
        total_time_limit_seconds=total_seconds,
        allow_extra_time=kwargs.get('allow_extra_time', False),
        extra_time_minutes=kwargs.get('extra_time_minutes', 10),
        include_questions=kwargs.get('include_questions', True),
        **kwargs
    )
    
    db.session.add(worksheet)
    db.session.flush()  # Get the worksheet ID
    
    # Add questions
    for i, question_data in enumerate(questions, 1):
        question = WorksheetQuestion(
            worksheet_id=worksheet.id,
            question_number=i,
            question_text=question_data.get('questionText', ''),
            expected_answer=question_data['expectedAnswer'],
            question_type=question_data.get('questionType', 'factual'),
            points=question_data.get('points', 10),
            include_question=question_data.get('includeQuestion', True),
            order=i
        )
        db.session.add(question)
    
    # Create analytics record
    analytics = WorksheetAnalytics(worksheet_id=worksheet.id)
    db.session.add(analytics)
    
    db.session.commit()
    return worksheet

def start_worksheet_session(worksheet_id, student_id=None, student_name=None, student_email=None):
    """Start a new worksheet session for a student"""
    
    worksheet = Worksheet.query.get(worksheet_id)
    if not worksheet:
        raise ValueError("Worksheet not found")
    
    # Check if student already has a submission
    existing_submission = WorksheetSubmission.query.filter_by(
        worksheet_id=worksheet_id,
        student_id=student_id,
        completed=False
    ).first()
    
    if existing_submission:
        return existing_submission
    
    # Create new submission
    submission = WorksheetSubmission(
        worksheet_id=worksheet_id,
        student_id=student_id,
        student_name=student_name,
        student_email=student_email,
        time_limit_seconds=worksheet.total_time_limit_seconds,
        total_points=sum(q.points for q in worksheet.questions)
    )
    
    db.session.add(submission)
    db.session.commit()
    
    return submission

def request_extra_time(submission_id, requested_seconds, reason=None):
    """Request extra time for a worksheet submission"""
    
    submission = WorksheetSubmission.query.get(submission_id)
    if not submission:
        raise ValueError("Submission not found")
    
    if submission.completed:
        raise ValueError("Cannot request extra time for completed submission")
    
    # Check if extra time is allowed
    worksheet = submission.worksheet
    if not worksheet.allow_extra_time:
        raise ValueError("Extra time not allowed for this worksheet")
    
    # Check if already requested
    existing_request = ExtraTimeRequest.query.filter_by(
        submission_id=submission_id,
        status='pending'
    ).first()
    
    if existing_request:
        raise ValueError("Extra time request already pending")
    
    # Create request
    request_obj = ExtraTimeRequest(
        submission_id=submission_id,
        worksheet_id=worksheet.id,
        student_id=submission.student_id,
        requested_time_seconds=requested_seconds,
        reason=reason
    )
    
    db.session.add(request_obj)
    
    # Auto-approve if configured (for demo purposes)
    if worksheet.allow_extra_time:
        request_obj.approve(auto=True)
    
    db.session.commit()
    return request_obj

def submit_worksheet(submission_id, answers, evaluation_results, auto_submit=False):
    """Submit a completed worksheet"""
    
    submission = WorksheetSubmission.query.get(submission_id)
    if not submission:
        raise ValueError("Submission not found")
    
    # Calculate final score
    scores = [result.get('score', 0) for result in evaluation_results.values()]
    final_score = sum(scores) / len(scores) if scores else 0
    
    # Calculate time taken
    time_taken = int((datetime.utcnow() - submission.started_at).total_seconds())
    
    # Update submission
    submission.answers = answers
    submission.evaluation_results = evaluation_results
    submission.final_score = final_score
    submission.time_taken_seconds = time_taken
    submission.auto_submitted = auto_submit
    submission.completed = True
    submission.submitted_at = datetime.utcnow()
    submission.completed_at = datetime.utcnow()
    
    db.session.commit()
    
    # Update analytics
    analytics = WorksheetAnalytics.query.filter_by(worksheet_id=submission.worksheet_id).first()
    if analytics:
        analytics.update_analytics()
        db.session.commit()
    
    return submission

def get_worksheet_with_timer_info(worksheet_id):
    """Get worksheet with all timer-related information"""
    
    worksheet = Worksheet.query.get(worksheet_id)
    if not worksheet:
        return None
    
    result = worksheet.to_dict()
    result['questions'] = [q.to_dict() for q in worksheet.questions]
    
    # Add analytics if available
    if worksheet.analytics:
        result['analytics'] = worksheet.analytics.to_dict()
    
    return result# worksheet_models.py - Extended models with timer functionality


class WorksheetTemplate(db.Model):
    __tablename__ = 'worksheet_templates'
    __table_args__ = {'mysql_charset': 'utf8mb3'}
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    subject = db.Column(db.String(100), nullable=False)
    default_time_limit_minutes = db.Column(db.Integer, default=30)
    allows_extra_time = db.Column(db.Boolean, default=True)
    default_extra_time_minutes = db.Column(db.Integer, default=10)
    created_by = db.Column(db.String(36))  # NO ForeignKey
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # NO relationships
    
    def __repr__(self):
        return f'<WorksheetTemplate {self.name}>'

class Worksheet(db.Model):
    """Main worksheet model with timer settings"""
    __tablename__ = 'worksheets'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tutor_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    template_id = db.Column(db.String(36), db.ForeignKey('worksheet_templates.id'), nullable=True)
    
    # Basic worksheet info
    title = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    include_questions = db.Column(db.Boolean, default=True)
    
    # Timer settings
    time_limit_hours = db.Column(db.Integer, default=0)
    time_limit_minutes = db.Column(db.Integer, default=30)
    time_limit_seconds = db.Column(db.Integer, default=0)
    total_time_limit_seconds = db.Column(db.Integer, nullable=False)  # Calculated field
    
    # Extra time settings
    allow_extra_time = db.Column(db.Boolean, default=False)
    extra_time_minutes = db.Column(db.Integer, default=10)
    extra_time_seconds = db.Column(db.Integer, default=600)  # Calculated field
    
    # Media settings
    has_media = db.Column(db.Boolean, default=False)
    media_type = db.Column(db.String(20))  # 'image', 'video', 'audio'
    media_filename = db.Column(db.String(255))
    media_url = db.Column(db.String(500))
    media_file_size = db.Column(db.Integer)
    
    # Worksheet status
    status = db.Column(db.String(20), default='draft')  # 'draft', 'published', 'archived'
    is_active = db.Column(db.Boolean, default=True)
    
    # Assignment settings
    assigned_to_all = db.Column(db.Boolean, default=True)
    max_attempts = db.Column(db.Integer, default=1)
    show_results_immediately = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = db.Column(db.DateTime)
    
    # Relationships
    tutor = db.relationship('User', backref=db.backref('created_worksheets', lazy=True))
    template = db.relationship('WorksheetTemplate', backref=db.backref('worksheets', lazy=True))
    
    def __init__(self, **kwargs):
        super(Worksheet, self).__init__(**kwargs)
        # Auto-calculate total seconds
        self.calculate_time_limits()
    
    def calculate_time_limits(self):
        """Calculate total seconds from hours, minutes, seconds"""
        self.total_time_limit_seconds = (
            (self.time_limit_hours or 0) * 3600 + 
            (self.time_limit_minutes or 0) * 60 + 
            (self.time_limit_seconds or 0)
        )
        
        if self.allow_extra_time:
            self.extra_time_seconds = (self.extra_time_minutes or 0) * 60
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'title': self.title,
            'subject': self.subject,
            'description': self.description,
            'include_questions': self.include_questions,
            'timeLimit': {
                'hours': self.time_limit_hours,
                'minutes': self.time_limit_minutes,
                'seconds': self.time_limit_seconds,
                'totalSeconds': self.total_time_limit_seconds
            },
            'extraTime': {
                'allowed': self.allow_extra_time,
                'minutes': self.extra_time_minutes,
                'seconds': self.extra_time_seconds
            },
            'mediaFile': {
                'type': self.media_type,
                'url': self.media_url,
                'name': self.media_filename
            } if self.has_media else None,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'published_at': self.published_at.isoformat() if self.published_at else None
        }
    
    def __repr__(self):
        return f'<Worksheet {self.title}>'

class WorksheetQuestion(db.Model):
    """Questions within a worksheet"""
    __tablename__ = 'worksheet_questions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    worksheet_id = db.Column(db.String(36), db.ForeignKey('worksheets.id', ondelete='CASCADE'), nullable=False)
    
    question_number = db.Column(db.Integer, nullable=False)

# Add these new models to your existing models section in app.py
# Add these new models to your existing models section in app.py

# After your system is working, add these corrected models
# The key fix is using 'admins.id' instead of 'admin.id' to match your table name

class AdminAssignment(db.Model):
    """Tracks admin assignments to grade sections and students"""
    __tablename__ = 'admin_assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=False)  # Fixed: admins.id not admin.id
    assignment_type = db.Column(db.String(20), nullable=False, default='grade_section')
    grade_section = db.Column(db.String(20))  # '1-3', '4-6', '7-9', '10-12'
    student_ids = db.Column(db.JSON)  # List of assigned student IDs
    max_acard_amount = db.Column(db.Float, default=0.00)  # Using Float instead of Numeric
    permissions = db.Column(db.JSON)  # Admin permissions
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('admins.id'))  # Fixed: admins.id not admin.id
    
    # Simplified relationships without backref conflicts
    def __repr__(self):
        return f'<AdminAssignment {self.admin_id}:{self.grade_section}>'

class AdminResource(db.Model):
    """Resources (files/links) assigned to admins for their grade sections"""
    __tablename__ = 'admin_resources'
    
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=False)
    grade_section = db.Column(db.String(20), nullable=False)
    resource_type = db.Column(db.String(20), nullable=False)
    resource_title = db.Column(db.String(255), nullable=False)
    resource_url = db.Column(db.Text)
    task_file = db.Column(db.String(255))
    subject_category = db.Column(db.String(100))
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('admins.id'))
    
    def __repr__(self):
        return f'<AdminResource {self.resource_title}>'

class Tutor(db.Model):
    __tablename__ = 'tutors'
    
    id = Column(Integer, primary_key=True)
    
    # Personal Information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(20), nullable=False)
    date_of_birth = Column(DateTime, nullable=False)
    country = Column(String(100), nullable=False)
    timezone = Column(String(50), nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    # Teaching Information
    subjects = Column(JSON, nullable=False)  # Array of subjects
    education_level = Column(String(100), nullable=False)
    teaching_experience = Column(String(50))
    bio = Column(Text, nullable=False)
    schedule_preferences = Column(JSON)  # Array of preferred time slots
    motivation = Column(Text, nullable=False)
    
    # Application Status
    application_status = Column(String(50), default='pending')  # pending, approved, rejected
    resume_filename = Column(String(255))
    
    # Metadata
    email_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Assessment and Onboarding
    assessment_completed = Column(Boolean, default=False)
    assessment_score = Column(Integer)
    onboarding_completed = Column(Boolean, default=False)
    
    # Profile completion
    profile_video_url = Column(String(500))
    is_active = Column(Boolean, default=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'phone': self.phone,
            'country': self.country,
            'subjects': self.subjects,
            'education_level': self.education_level,
            'teaching_experience': self.teaching_experience,
            'application_status': self.application_status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class WithdrawalRequest(db.Model):
    __tablename__ = 'withdrawal_requests'
    
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, db.ForeignKey('students.id'), nullable=False)
    admin_id = Column(Integer, db.ForeignKey('admins.id'), nullable=True)  #Approver
    
    # Request details
    request_type = Column(String(20), nullable=False)  # 'cash' or 'gift'
    amount = Column(Float, nullable=False)
    status = Column(String(20), default='pending')  # 'pending', 'approved', 'rejected', 'completed'
    
    # Cash withdrawal specific
    user_location = Column(String(50), nullable=True)
    bank_details = Column(JSON, nullable=True)
    
    # Gift specific
    gift_name = Column(String(200), nullable=True)
    delivery_address = Column(Text, nullable=True)
    phone_number = Column(String(20), nullable=True)
    special_instructions = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Admin notes
    admin_notes = Column(Text, nullable=True)
    
    # Relationships
    student = db.relationship('Student', backref='withdrawal_requests')
    admin = db.relationship('Admin', backref='approved_withdrawals')

# Database Models for Interactive Evaluation

# models.py

class LessonPlanEvaluation(db.Model):
    __tablename__ = 'lesson_plan_evaluations'
    __table_args__ = {'mysql_charset': 'utf8mb3'}
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lesson_plan_id = db.Column(db.String(36), nullable=False)  # NO ForeignKey
    evaluation_type = db.Column(db.String(50), nullable=False)
    questions_json = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # NO relationships
    
    def get_lesson_plan(self):
        """Get the related lesson plan"""
        from models import MathLessonPlanModel
        return MathLessonPlanModel.query.get(self.lesson_plan_id)
    
    def to_dict(self):
        return {
            'id': self.id,
            'lesson_plan_id': self.lesson_plan_id,
            'evaluation_type': self.evaluation_type,
            'questions': json.loads(self.questions_json),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def __repr__(self):
        return f'<LessonPlanEvaluation {self.id}>'


class StudentEvaluationAttempt(db.Model):
    __tablename__ = 'student_evaluation_attempts'
    __table_args__ = {'mysql_charset': 'utf8mb3'}
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    evaluation_id = db.Column(db.String(36), nullable=False)  # NO ForeignKey
    user_id = db.Column(db.String(36))  # NO ForeignKey
    answers_json = db.Column(db.Text, nullable=False)
    score = db.Column(db.Float, nullable=False)
    feedback_json = db.Column(db.Text)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # NO relationships
    
    def get_evaluation(self):
        """Get the related evaluation"""
        return LessonPlanEvaluation.query.get(self.evaluation_id)
    
    def get_user(self):
        """Get the related user"""
        from models import User
        return User.query.get(self.user_id) if self.user_id else None
    
    def to_dict(self):
        return {
            'id': self.id,
            'evaluation_id': self.evaluation_id,
            'answers': json.loads(self.answers_json),
            'score': self.score,
            'feedback': json.loads(self.feedback_json) if self.feedback_json else None,
            'completed_at': self.completed_at.isoformat()
        }
    
    def __repr__(self):
        return f'<StudentEvaluationAttempt {self.id}>'

# Backend API Endpoints for Lesson Plan Editor System

# Additional Database Models
class LessonPlanSection(db.Model):
    __tablename__ = 'lesson_plan_sections'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lesson_plan_id = db.Column(db.String(36), db.ForeignKey('math_lesson_plans.id'), nullable=False)
    section_id = db.Column(db.String(100), nullable=False)  # Frontend-generated ID
    section_type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content_json = db.Column(db.Text, nullable=False)
    order_index = db.Column(db.Integer, nullable=False, default=0)
    is_original = db.Column(db.Boolean, default=False)  # True if from AI generation
    original_key = db.Column(db.String(100), nullable=True)  # Key from original content
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    lesson_plan = db.relationship('MathLessonPlanModel', backref='custom_sections')
    
    def to_dict(self):
        return {
            'id': self.id,
            'section_id': self.section_id,
            'section_type': self.section_type,
            'title': self.title,
            'content': json.loads(self.content_json),
            'order_index': self.order_index,
            'is_original': self.is_original,
            'original_key': self.original_key,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class PublishedLessonPlan(db.Model):
    __tablename__ = 'published_lesson_plans'
    __table_args__ = {'extend_existing': True}  # Add this line
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lesson_plan_id = db.Column(db.String(36), db.ForeignKey('math_lesson_plans.id'), nullable=False)
    public_url_slug = db.Column(db.String(100), nullable=False, unique=True)
    access_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    published_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    lesson_plan = db.relationship('MathLessonPlanModel', backref='published_versions')
    
    def to_dict(self):
        return {
            'id': self.id,
            'public_url_slug': self.public_url_slug,
            'access_count': self.access_count,
            'is_active': self.is_active,
            'published_at': self.published_at.isoformat() if self.published_at else None
        }
    
from datetime import datetime
import secrets
import string
import uuid

# models.py

class Affiliate(db.Model):
    __tablename__ = 'affiliates'
    __table_args__ = {'mysql_charset': 'utf8mb3'}
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False)
    affiliate_code = db.Column(db.String(20), unique=True, nullable=False)
    status = db.Column(db.String(20), default='active')
    
    # Earnings tracking
    total_referrals = db.Column(db.Integer, default=0)
    total_conversions = db.Column(db.Integer, default=0)
    total_earnings = db.Column(db.Float, default=0.0)
    pending_earnings = db.Column(db.Float, default=0.0)
    paid_earnings = db.Column(db.Float, default=0.0)
    
    # Commission rates
    trial_signup_commission = db.Column(db.Float, default=2.0)
    paid_conversion_commission = db.Column(db.Float, default=5.0)
    recurring_commission = db.Column(db.Float, default=5.0)
    recurring_commission_enabled = db.Column(db.Boolean, default=True)
    
    # Payment details
    payment_method = db.Column(db.String(50))
    payment_email = db.Column(db.String(255))
    payment_details = db.Column(db.Text)
    minimum_payout_threshold = db.Column(db.Float, default=50.0)
    
    # Agreement tracking
    terms_accepted = db.Column(db.Boolean, default=False)
    terms_accepted_at = db.Column(db.DateTime)
    terms_version = db.Column(db.String(10), default='1.0')
    
    # Fraud prevention
    last_click_ip = db.Column(db.String(50))
    suspicious_activity_count = db.Column(db.Integer, default=0)
    fraud_flag = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_payout_at = db.Column(db.DateTime)
    
    # ❌ REMOVE ALL THESE RELATIONSHIPS:
    # user = db.relationship('User', backref='affiliate_profile')
    # referrals = db.relationship('Referral', backref='affiliate', lazy='dynamic')
    # commissions = db.relationship('Commission', backref='affiliate', lazy='dynamic')
    # payouts = db.relationship('Payout', backref='affiliate', lazy='dynamic')
    # product_links = db.relationship('AffiliateProductLink', backref='affiliate', lazy='dynamic')
    
    # NO RELATIONSHIPS - query manually when needed
    
    def get_user(self):
        """Get the related user"""
        from models import User
        return User.query.get(self.user_id)
    
    def get_referrals(self):
        """Get affiliate referrals"""
        return Referral.query.filter_by(affiliate_id=self.id).all()
    
    def get_product_links(self):
        """Get product links"""
        return AffiliateProductLink.query.filter_by(affiliate_id=self.id).all()
    
    @staticmethod
    def generate_code(prefix='AFF'):
        """Generate unique affiliate code"""
        import secrets
        while True:
            code = f"{prefix}{secrets.token_hex(4).upper()}"
            if not Affiliate.query.filter_by(affiliate_code=code).first():
                return code
    
    def calculate_conversion_rate(self):
        """Calculate conversion rate percentage"""
        if self.total_referrals == 0:
            return 0.0
        return round((self.total_conversions / self.total_referrals) * 100, 2)
    
    def get_active_referrals_count(self):
        """Count referrals with active subscriptions"""
        return Referral.query.filter_by(affiliate_id=self.id, status='converted').count()
    
    def get_churned_referrals_count(self):
        """Count referrals that churned"""
        return Referral.query.filter_by(affiliate_id=self.id, status='churned').count()
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'affiliate_code': self.affiliate_code,
            'status': self.status,
            'total_referrals': self.total_referrals,
            'total_conversions': self.total_conversions,
            'active_referrals': self.get_active_referrals_count(),
            'churned_referrals': self.get_churned_referrals_count(),
            'total_earnings': round(self.total_earnings, 2),
            'pending_earnings': round(self.pending_earnings, 2),
            'paid_earnings': round(self.paid_earnings, 2),
            'conversion_rate': self.calculate_conversion_rate(),
            'payment_method': self.payment_method,
            'payment_email': self.payment_email,
            'minimum_payout_threshold': self.minimum_payout_threshold,
            'terms_accepted': self.terms_accepted,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_payout_at': self.last_payout_at.isoformat() if self.last_payout_at else None
        }
    
    def __repr__(self):
        return f'<Affiliate {self.affiliate_code}>'


# models .py

class AffiliateProductLink(db.Model):
    """Tracks unique affiliate links for each product/course"""
    __tablename__ = 'affiliate_product_links'
    __table_args__ = {'mysql_charset': 'utf8mb3'}
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    affiliate_id = db.Column(db.String(36), nullable=False)  # NO ForeignKey
    
    product_type = db.Column(db.String(50), nullable=False)
    product_id = db.Column(db.String(100), nullable=False)
    product_name = db.Column(db.String(255), nullable=False)
    
    tracking_link = db.Column(db.String(500), unique=True, nullable=False)
    short_code = db.Column(db.String(20), unique=True, nullable=False)
    
    click_count = db.Column(db.Integer, default=0)
    conversion_count = db.Column(db.Integer, default=0)
    earnings = db.Column(db.Float, default=0.0)
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # NO relationships
    
    def get_affiliate(self):
        """Get the related affiliate"""
        return Affiliate.query.get(self.affiliate_id)
    
    @staticmethod
    def generate_short_code():
        """Generate unique short code for tracking links"""
        import secrets
        while True:
            code = secrets.token_urlsafe(6)
            if not AffiliateProductLink.query.filter_by(short_code=code).first():
                return code
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_type': self.product_type,
            'product_id': self.product_id,
            'product_name': self.product_name,
            'tracking_link': self.tracking_link,
            'short_code': self.short_code,
            'click_count': self.click_count,
            'conversion_count': self.conversion_count,
            'earnings': round(self.earnings, 2),
            'conversion_rate': round((self.conversion_count / self.click_count * 100) if self.click_count > 0 else 0, 2),
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<AffiliateProductLink {self.short_code}>'


class Referral(db.Model):
    __tablename__ = 'referrals'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    affiliate_id = db.Column(db.String(36), db.ForeignKey('affiliates.id'), nullable=False, index=True)
    product_link_id = db.Column(db.String(36), db.ForeignKey('affiliate_product_links.id'))
    
    referred_user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True, index=True)  
    referred_email = db.Column(db.String(255), index=True)
    
    status = db.Column(db.String(20), default='pending')  # pending, signed_up, trial, converted, churned
    subscription_status = db.Column(db.String(20))  # active, canceled, paused
    
    # Tracking info
    source = db.Column(db.String(100))  # landing_page, dashboard, blog, etc.
    utm_source = db.Column(db.String(100))
    utm_medium = db.Column(db.String(100))
    utm_campaign = db.Column(db.String(100))
    
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.Text)
    country = db.Column(db.String(100))
    device_type = db.Column(db.String(20))  # desktop, mobile, tablet
    
    # Engagement tracking
    click_count = db.Column(db.Integer, default=1)
    first_click_at = db.Column(db.DateTime, default=datetime.utcnow)
    signup_at = db.Column(db.DateTime)
    trial_started_at = db.Column(db.DateTime)
    conversion_at = db.Column(db.DateTime)
    churned_at = db.Column(db.DateTime)
    
    # Value tracking
    lifetime_value = db.Column(db.Float, default=0.0)
    total_commissions_paid = db.Column(db.Float, default=0.0)
    months_subscribed = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    referred_user = db.relationship('User', backref='referral_source', foreign_keys=[referred_user_id])
    commissions = db.relationship('Commission', backref='referral', lazy='dynamic', cascade='all, delete-orphan')
    product_link = db.relationship('AffiliateProductLink', backref='referrals')
    
    def to_dict(self):
        return {
            'id': self.id,
            'affiliate_id': self.affiliate_id,
            'referred_email': self.referred_email,
            'status': self.status,
            'subscription_status': self.subscription_status,
            'source': self.source,
            'click_count': self.click_count,
            'lifetime_value': round(self.lifetime_value, 2),
            'total_commissions_paid': round(self.total_commissions_paid, 2),
            'months_subscribed': self.months_subscribed,
            'first_click_at': self.first_click_at.isoformat() if self.first_click_at else None,
            'signup_at': self.signup_at.isoformat() if self.signup_at else None,
            'conversion_at': self.conversion_at.isoformat() if self.conversion_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Commission(db.Model):
    __tablename__ = 'commissions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    affiliate_id = db.Column(db.String(36), db.ForeignKey('affiliates.id'), nullable=False, index=True)
    referral_id = db.Column(db.String(36), db.ForeignKey('referrals.id'), nullable=False, index=True)
    
    amount = db.Column(db.Float, nullable=False)
    commission_type = db.Column(db.String(50))  # trial_signup, conversion, recurring_month_1, recurring_month_2, etc.
    
    status = db.Column(db.String(20), default='pending')  # pending, approved, paid, rejected, reversed
    
    # Transaction tracking
    transaction_id = db.Column(db.String(100))  # Link to payment transaction
    subscription_id = db.Column(db.String(100))  # Stripe/payment provider subscription ID
    
    notes = db.Column(db.Text)
    rejection_reason = db.Column(db.Text)
    
    # Approval tracking
    approved_at = db.Column(db.DateTime)
    approved_by = db.Column(db.String(36), db.ForeignKey('users.id')) 
    
    # Payout tracking
    paid_at = db.Column(db.DateTime)
    payout_id = db.Column(db.String(36), db.ForeignKey('payouts.id'))
    
    # Recurring commission tracking
    is_recurring = db.Column(db.Boolean, default=False)
    recurring_month = db.Column(db.Integer)  # Which month of subscription (1, 2, 3...)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'affiliate_id': self.affiliate_id,
            'referral_id': self.referral_id,
            'amount': round(self.amount, 2),
            'commission_type': self.commission_type,
            'status': self.status,
            'is_recurring': self.is_recurring,
            'recurring_month': self.recurring_month,
            'transaction_id': self.transaction_id,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Payout(db.Model):
    __tablename__ = 'payouts'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    affiliate_id = db.Column(db.String(36), db.ForeignKey('affiliates.id'), nullable=False, index=True)
    
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50))
    payment_email = db.Column(db.String(255))
    payment_reference = db.Column(db.String(255))  # PayPal transaction ID, bank reference, etc.
    
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed, canceled
    
    commission_ids = db.Column(db.Text)  # JSON array of commission IDs included in this payout
    commission_count = db.Column(db.Integer, default=0)
    
    notes = db.Column(db.Text)
    failure_reason = db.Column(db.Text)
    
    processed_by = db.Column(db.String(36), db.ForeignKey('users.id'))  # Changed from Integer
    processed_at = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    commissions_list = db.relationship('Commission', backref='payout_batch', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'affiliate_id': self.affiliate_id,
            'amount': round(self.amount, 2),
            'payment_method': self.payment_method,
            'payment_email': self.payment_email,
            'payment_reference': self.payment_reference,
            'status': self.status,
            'commission_count': self.commission_count,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class AffiliateClick(db.Model):
    __tablename__ = 'affiliate_clicks'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    affiliate_id = db.Column(db.String(36), db.ForeignKey('affiliates.id'), nullable=False, index=True)
    product_link_id = db.Column(db.String(36), db.ForeignKey('affiliate_product_links.id'))
    referral_id = db.Column(db.String(36), db.ForeignKey('referrals.id'), index=True)
    
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.Text)
    referer = db.Column(db.String(500))
    landing_page = db.Column(db.String(500))
    
    country = db.Column(db.String(2))
    city = db.Column(db.String(100))
    device_type = db.Column(db.String(20))  # desktop, mobile, tablet
    browser = db.Column(db.String(50))
    os = db.Column(db.String(50))
    
    # Fraud detection
    is_suspicious = db.Column(db.Boolean, default=False)
    is_duplicate = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'affiliate_id': self.affiliate_id,
            'landing_page': self.landing_page,
            'device_type': self.device_type,
            'country': self.country,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
# Add these models to your existing models.py

class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, nullable=False)
    sender_type = db.Column(db.String(20), nullable=False)  # 'admin', 'super_admin', 'student'
    recipient_id = db.Column(db.Integer, nullable=False)
    recipient_type = db.Column(db.String(20), nullable=False)  # 'admin', 'super_admin', 'student'
    subject = db.Column(db.String(200), nullable=False)
    message_body = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(50), default='general')  # general, announcement, urgent, reminder, system
    priority = db.Column(db.String(20), default='normal')  # low, normal, high, urgent
    is_read = db.Column(db.Boolean, default=False)
    is_broadcast = db.Column(db.Boolean, default=False)
    broadcast_group_id = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'sender_type': self.sender_type,
            'sender_name': self.get_sender_name(),
            'recipient_id': self.recipient_id,
            'recipient_type': self.recipient_type,
            'recipient_name': self.get_recipient_name(),
            'subject': self.subject,
            'message_body': self.message_body,
            'message_type': self.message_type,
            'priority': self.priority,
            'is_read': self.is_read,
            'is_broadcast': self.is_broadcast,
            'broadcast_group_id': self.broadcast_group_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'time_ago': self.get_time_ago()
        }
    
    def get_sender_name(self):
        if self.sender_type == 'admin' or self.sender_type == 'super_admin':
            admin = Admin.query.get(self.sender_id)
            return admin.name if admin else 'System Administrator'
        elif self.sender_type == 'student':
            student = Student.query.get(self.sender_id)
            return student.name if student else 'Student'
        return 'System'
    
    def get_recipient_name(self):
        if self.recipient_type == 'admin' or self.recipient_type == 'super_admin':
            admin = Admin.query.get(self.recipient_id)
            return admin.name if admin else 'Administrator'
        elif self.recipient_type == 'student':
            student = Student.query.get(self.recipient_id)
            return student.name if student else 'Student'
        return 'System'
    
    def get_time_ago(self):
        if not self.created_at:
            return 'Unknown'
        
        now = datetime.utcnow()
        diff = now - self.created_at
        
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "Just now"

# Social Media Student Models and Authentication
# Add these to your existing models.py file

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class SocialMediaStudent(db.Model):
    __tablename__ = 'social_media_students'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    
    # NEW FIELDS FOR WORKSHOP REGISTRATION
    age_range = db.Column(db.String(20), nullable=True)  # 5-10, 10-15, 15-20, 20-25, 25+
    birth_month = db.Column(db.String(2), nullable=True)  # 01-12
    birth_day = db.Column(db.String(2), nullable=True)    # 01-31
    institution_type = db.Column(db.String(50), nullable=True)  # school, university, polytechnic, college
    institution_name = db.Column(db.String(200), nullable=True)
    
    # Existing fields
    location = db.Column(db.String(200), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    skill_level = db.Column(db.String(50), default='Beginner')
    category = db.Column(db.String(100), nullable=True)  # social-media, video-editing, graphics-design, coding
    
    # Progress tracking
    total_points = db.Column(db.Integer, default=0)
    total_tasks_completed = db.Column(db.Integer, default=0)
    
    # Status and timestamps
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    tasks = db.relationship('SocialMediaTask', backref='student', lazy='dynamic')
    progress = db.relationship('SocialMediaProgress', backref='student', lazy='dynamic')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'full_name': self.full_name,
            'email': self.email,
            'phone_number': self.phone_number,
            'age_range': self.age_range,
            'birth_month': self.birth_month,
            'birth_day': self.birth_day,
            'institution_type': self.institution_type,
            'institution_name': self.institution_name,
            'location': self.location,
            'bio': self.bio,
            'skill_level': self.skill_level,
            'category': self.category,
            'total_points': self.total_points,
            'total_tasks_completed': self.total_tasks_completed,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

class SocialMediaTask(db.Model):
    __tablename__ = 'social_media_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('social_media_students.id'), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=True)
    
    # Task details
    task_type = db.Column(db.String(50), nullable=False)  # social-media, video-editing, graphics-design, coding
    skill_category = db.Column(db.String(100), nullable=False)  # e.g., "Content Creation", "Video Production"
    task_title = db.Column(db.String(255), nullable=False)
    task_description = db.Column(db.Text, nullable=True)
    
    # Task content
    week_number = db.Column(db.Integer, nullable=True)  # Week 1, 2, 3, 4
    day_number = db.Column(db.Integer, nullable=True)  # Day 1-5
    lesson_type = db.Column(db.String(50), nullable=True)  # lesson, live, practical
    video_url = db.Column(db.String(500), nullable=True)
    zoom_passcode = db.Column(db.String(50), nullable=True)
    duration = db.Column(db.String(50), nullable=True)  # e.g., "45 min"
    
    # Progress and rewards
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed
    points_reward = db.Column(db.Integer, default=0)
    
    # Quiz scores - NEW COLUMNS
    quiz_score = db.Column(db.Integer)
    quiz_max_score = db.Column(db.Integer)
    completion_percentage = db.Column(db.Numeric(5, 2))  # KEEP ONLY ONE
    
    # Additional data
    task_data = db.Column(db.Text, nullable=True)  # JSON field for flexible data
    access_code = db.Column(db.String(50), nullable=True)  # For accessing specific lessons
    
    # Timestamps
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)

    # REMOVE THIS LINE - the relationship is already defined in SocialMediaStudent
    # student = db.relationship('SocialMediaStudent', backref='tasks')
    
    def mark_as_started(self):
        """Mark task as started"""
        if self.status == 'pending':
            self.status = 'in_progress'
            self.started_at = datetime.utcnow()
            db.session.commit()
    
    def mark_as_completed(self, completion_percentage=100):
        """Mark task as completed"""
        self.status = 'completed'
        self.completion_percentage = completion_percentage
        self.completed_at = datetime.utcnow()
        
        # Update student's total
        if self.student:
            self.student.total_tasks_completed += 1
            self.student.total_points += self.points_reward
        
        db.session.commit()
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'task_type': self.task_type,
            'skill_category': self.skill_category,
            'task_title': self.task_title,
            'task_description': self.task_description,
            'week_number': self.week_number,
            'day_number': self.day_number,
            'lesson_type': self.lesson_type,
            'video_url': self.video_url,
            'zoom_passcode': self.zoom_passcode,
            'duration': self.duration,
            'status': self.status,
            'points_reward': self.points_reward,
            'completion_percentage': float(self.completion_percentage) if self.completion_percentage else 0,
            'quiz_score': self.quiz_score,
            'quiz_max_score': self.quiz_max_score,
            'task_data': self.task_data,
            'access_code': self.access_code,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

# Social Media Progress Tracking
class SocialMediaProgress(db.Model):
    __tablename__ = 'social_media_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('social_media_students.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('social_media_tasks.id'), nullable=True)
    
    # Progress details
    week_number = db.Column(db.Integer, nullable=False)
    completed_lessons = db.Column(db.Integer, default=0)
    total_lessons = db.Column(db.Integer, default=0)
    progress_percentage = db.Column(db.Integer, default=0)
    
    # Time tracking
    time_spent_minutes = db.Column(db.Integer, default=0)
    
    # Notes and feedback
    notes = db.Column(db.Text, nullable=True)
    feedback = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def update_progress(self):
        """Calculate and update progress percentage"""
        if self.total_lessons > 0:
            self.progress_percentage = int((self.completed_lessons / self.total_lessons) * 100)
        else:
            self.progress_percentage = 0
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'task_id': self.task_id,
            'week_number': self.week_number,
            'completed_lessons': self.completed_lessons,
            'total_lessons': self.total_lessons,
            'progress_percentage': self.progress_percentage,
            'time_spent_minutes': self.time_spent_minutes,
            'notes': self.notes,
            'feedback': self.feedback,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# Initial data seeding function
def seed_social_media_students():
    """Seed the database with initial social media students"""
    students_data = [
        {
            'username': 'Emma@decipher.com',
            'password': 'MmA773E',
            'full_name': 'Emma Johnson',
            'email': 'emma@decipher.com',
            'phone_number': '+234 801 234 5678',
            'location': 'Lagos, Nigeria'
        },
        {
            'username': 'Khairat@decipher.com',
            'password': 'KhA032K',
            'full_name': 'Khairat Abdul',
            'email': 'khairat@decipher.com',
            'phone_number': '+234 802 345 6789',
            'location': 'Abuja, Nigeria'
        },
        {
            'username': 'Gozie@decipher.com',
            'password': 'HoZ261G',
            'full_name': 'Gozie Okafor',
            'email': 'gozie@decipher.com',
            'phone_number': '+234 803 456 7890',
            'location': 'Port Harcourt, Nigeria'
        }
    ]
    
    for student_data in students_data:
        # Check if student already exists
        existing = SocialMediaStudent.query.filter_by(username=student_data['username']).first()
        if not existing:
            student = SocialMediaStudent(
                username=student_data['username'],
                full_name=student_data['full_name'],
                email=student_data['email'],
                phone_number=student_data.get('phone_number'),
                location=student_data.get('location'),
                is_active=True
            )
            student.set_password(student_data['password'])
            db.session.add(student)
            print(f"✅ Created social media student: {student.full_name}")
        else:
            print(f"⚠️ Student already exists: {student_data['username']}")
    
    db.session.commit()
    print("✅ Social media students seeding completed!")


# Helper function to create JWT token for social media students
def create_sm_student_token(student_id):
    """Create JWT token for social media student"""
    import jwt
    from datetime import timedelta
    
    payload = {
        'student_id': student_id,
        'student_type': 'social_media',
        'exp': datetime.utcnow() + timedelta(days=7)
    }
    
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm='HS256')
    return token            

# =========================================
# Coach Management Models
# =========================================

class Coach(db.Model):
    """Coach model for managing course instructors"""
    __tablename__ = 'coaches'
    
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(20))
    bio = db.Column(db.Text)
    
    # Professional details
    specialization = db.Column(db.String(100), nullable=False)
    years_experience = db.Column(db.Integer, default=0)
    professional_title = db.Column(db.String(255))
    linkedin_url = db.Column(db.String(500))
    portfolio_url = db.Column(db.String(500))
    
    # Permissions and limits
    max_courses_allowed = db.Column(db.Integer, default=10)
    can_upload_video = db.Column(db.Boolean, default=True)
    can_upload_pdf = db.Column(db.Boolean, default=True)
    storage_quota_gb = db.Column(db.Numeric(10, 2), default=50.00)
    storage_used_gb = db.Column(db.Numeric(10, 2), default=0.00)
    can_create_access_codes = db.Column(db.Boolean, default=True)
    can_assign_tasks = db.Column(db.Boolean, default=True)
    can_view_all_students = db.Column(db.Boolean, default=False)
    
    # Status and metadata
    account_status = db.Column(db.String(20), default='pending', index=True)  # active, inactive, suspended, pending
    created_by = db.Column(db.Integer, db.ForeignKey('admins.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    courses = db.relationship('CoachCourse', backref='coach', lazy='dynamic', cascade='all, delete-orphan')
    student_enrollments = db.relationship('CoachStudentEnrollment', backref='coach', lazy='dynamic', cascade='all, delete-orphan')
    tasks = db.relationship('CoachTask', backref='coach', lazy='dynamic', cascade='all, delete-orphan')
    s3_uploads = db.relationship('CoachS3Upload', backref='coach', lazy='dynamic', cascade='all, delete-orphan')
    analytics = db.relationship('CoachAnalytics', backref='coach', lazy='dynamic', cascade='all, delete-orphan')


class CoachCourse(db.Model):
    """Coach course model"""
    __tablename__ = 'coach_courses'
    
    id = db.Column(db.Integer, primary_key=True)
    coach_id = db.Column(db.Integer, db.ForeignKey('coaches.id', ondelete='CASCADE'), nullable=False, index=True)
    course_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    course_name = db.Column(db.String(255), nullable=False)
    course_description = db.Column(db.Text)
    course_category = db.Column(db.String(100))
    course_icon = db.Column(db.String(10), default='📚')
    course_color = db.Column(db.String(20), default='#FF3B30')
    total_weeks = db.Column(db.Integer, default=4)
    total_lessons = db.Column(db.Integer, default=0)
    
    # Template and customization
    page_template = db.Column(db.String(20), default='sm-style')  # sm-style, ve-style, custom
    custom_css = db.Column(db.Text)
    custom_html = db.Column(db.Text)
    
    # Publishing and sharing
    is_published = db.Column(db.Boolean, default=False, index=True)
    requires_access_code = db.Column(db.Boolean, default=False)
    enrollment_limit = db.Column(db.Integer, default=100)
    current_enrollment = db.Column(db.Integer, default=0)
    
    # Shareable URL
    unique_url = db.Column(db.String(100), unique=True, nullable=False, index=True)
    share_url_enabled = db.Column(db.Boolean, default=True)
    view_count = db.Column(db.Integer, default=0)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = db.Column(db.DateTime)
    
    # Relationships
    lessons = db.relationship('CoachCourseLesson', backref='course', lazy='dynamic', cascade='all, delete-orphan')
    student_enrollments = db.relationship('CoachStudentEnrollment', backref='course', lazy='dynamic', cascade='all, delete-orphan')
    tasks = db.relationship('CoachTask', backref='course', lazy='dynamic', cascade='all, delete-orphan')
    s3_uploads = db.relationship('CoachS3Upload', backref='course', lazy='dynamic')


class CoachCourseLesson(db.Model):
    """Coach course lesson model"""
    __tablename__ = 'coach_course_lessons'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('coach_courses.id', ondelete='CASCADE'), nullable=False, index=True)
    lesson_id = db.Column(db.String(100), nullable=False, index=True)
    lesson_title = db.Column(db.String(255), nullable=False)
    lesson_description = db.Column(db.Text)
    lesson_type = db.Column(db.String(20), default='lesson')  # lesson, live, practical
    
    # Organization
    week_number = db.Column(db.Integer)
    day_number = db.Column(db.Integer)
    duration = db.Column(db.String(20))
    order_index = db.Column(db.Integer, default=0)
    
    # Content
    video_url = db.Column(db.String(1000))
    pdf_url = db.Column(db.String(1000))
    quiz_links = db.Column(db.Text)  # JSON array of quiz link objects
    access_code = db.Column(db.String(50))
    category = db.Column(db.String(100))
    points_reward = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True, index=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint('course_id', 'lesson_id', name='unique_lesson'),
    )


class CoachS3Upload(db.Model):
    """Coach S3 upload tracking"""
    __tablename__ = 'coach_s3_uploads'
    
    id = db.Column(db.Integer, primary_key=True)
    coach_id = db.Column(db.Integer, db.ForeignKey('coaches.id', ondelete='CASCADE'), nullable=False, index=True)
    course_id = db.Column(db.Integer, db.ForeignKey('coach_courses.id', ondelete='SET NULL'), index=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey('coach_course_lessons.id', ondelete='SET NULL'))
    
    # File information
    file_name = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(20), nullable=False)  # video, pdf, image
    file_size_mb = db.Column(db.Numeric(10, 2), nullable=False)
    
    # S3 information
    s3_bucket = db.Column(db.String(255), nullable=False)
    s3_key = db.Column(db.String(500), nullable=False)
    s3_url = db.Column(db.String(1000), nullable=False)
    cloudfront_url = db.Column(db.String(1000))
    
    # Status
    upload_status = db.Column(db.String(20), default='uploading', index=True)  # uploading, completed, failed
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)


class CoachStudentEnrollment(db.Model):
    """Coach student enrollment tracking"""
    __tablename__ = 'coach_student_enrollments'
    
    id = db.Column(db.Integer, primary_key=True)
    coach_id = db.Column(db.Integer, db.ForeignKey('coaches.id', ondelete='CASCADE'), nullable=False, index=True)
    course_id = db.Column(db.Integer, db.ForeignKey('coach_courses.id', ondelete='CASCADE'), nullable=False)
    student_id = db.Column(db.Integer, index=True)  # Reference to student (can be from different student tables)
    
    # Progress tracking
    enrollment_date = db.Column(db.DateTime, default=datetime.utcnow)
    completion_percentage = db.Column(db.Numeric(5, 2), default=0.00)
    last_accessed = db.Column(db.DateTime)
    
    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint('course_id', 'student_id', name='unique_enrollment'),
    )


class CoachQuizScore(db.Model):
    """Track student quiz scores for coach courses"""
    __tablename__ = 'coach_quiz_scores'

    id = db.Column(db.Integer, primary_key=True)
    coach_id = db.Column(db.Integer, db.ForeignKey('coaches.id', ondelete='CASCADE'), nullable=False, index=True)
    course_id = db.Column(db.Integer, db.ForeignKey('coach_courses.id', ondelete='CASCADE'), nullable=False, index=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey('coach_course_lessons.id', ondelete='CASCADE'), index=True)
    student_id = db.Column(db.Integer, nullable=False, index=True)

    # Quiz details
    quiz_url = db.Column(db.String(1000), nullable=False)
    quiz_id = db.Column(db.String(255))  # Extracted quiz ID if it's a decipher quiz
    quiz_title = db.Column(db.String(255))

    # Score tracking
    score = db.Column(db.Integer, nullable=False)  # Points earned
    total_questions = db.Column(db.Integer, nullable=False)  # Total questions
    percentage = db.Column(db.Numeric(5, 2))  # Percentage score
    time_taken_seconds = db.Column(db.Integer)  # Time taken to complete

    # Metadata
    attempt_number = db.Column(db.Integer, default=1)  # Track multiple attempts
    completed_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # Store answers as JSON for review
    answers_json = db.Column(db.Text)  # Store student's answers


class CoachTask(db.Model):
    """Coach task assignment"""
    __tablename__ = 'coach_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    coach_id = db.Column(db.Integer, db.ForeignKey('coaches.id', ondelete='CASCADE'), nullable=False, index=True)
    course_id = db.Column(db.Integer, db.ForeignKey('coach_courses.id', ondelete='CASCADE'), nullable=False, index=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey('coach_course_lessons.id', ondelete='SET NULL'))
    
    # Task details
    task_title = db.Column(db.String(255), nullable=False)
    task_description = db.Column(db.Text)
    task_type = db.Column(db.String(50))
    points_reward = db.Column(db.Integer, default=0)
    due_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    assignments = db.relationship('CoachTaskAssignment', backref='task', lazy='dynamic', cascade='all, delete-orphan')


class CoachTaskAssignment(db.Model):
    """Coach task student assignment"""
    __tablename__ = 'coach_task_assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('coach_tasks.id', ondelete='CASCADE'), nullable=False, index=True)
    student_id = db.Column(db.Integer, nullable=False, index=True)
    
    # Submission
    status = db.Column(db.String(20), default='pending', index=True)  # pending, in_progress, completed, graded
    submission_url = db.Column(db.String(1000))
    submission_text = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime)
    
    # Grading
    grade = db.Column(db.Numeric(5, 2))
    feedback = db.Column(db.Text)
    graded_at = db.Column(db.DateTime)
    graded_by = db.Column(db.Integer, db.ForeignKey('coaches.id', ondelete='SET NULL'))


class CoachAnalytics(db.Model):
    """Coach analytics tracking"""
    __tablename__ = 'coach_analytics'
    
    id = db.Column(db.Integer, primary_key=True)
    coach_id = db.Column(db.Integer, db.ForeignKey('coaches.id', ondelete='CASCADE'), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    
    # Metrics
    total_students = db.Column(db.Integer, default=0)
    active_students = db.Column(db.Integer, default=0)
    tasks_assigned = db.Column(db.Integer, default=0)
    tasks_completed = db.Column(db.Integer, default=0)
    average_completion_rate = db.Column(db.Numeric(5, 2), default=0.00)
    total_video_views = db.Column(db.Integer, default=0)
    total_pdf_downloads = db.Column(db.Integer, default=0)
    
    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint('coach_id', 'date', name='unique_analytics'),
    )


class StartCourseEnrollment(db.Model):
    """Start-course page enrollment tracking"""
    __tablename__ = 'start_course_enrollments'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='SET NULL'), index=True)

    # Personal information
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False, index=True)
    phone = db.Column(db.String(20))
    grade_level = db.Column(db.String(50))
    country = db.Column(db.String(100))

    # Course and schedule selections (stored as JSON)
    selected_courses = db.Column(db.Text)  # JSON array of selected courses
    selected_schedules = db.Column(db.Text)  # JSON array of selected schedules

    # Additional information
    notes = db.Column(db.Text)  # Special requirements or questions

    # Status tracking
    enrollment_status = db.Column(db.String(20), default='pending', index=True)  # pending, approved, rejected, contacted

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Follow-up tracking
    contacted_at = db.Column(db.DateTime)
    contacted_by = db.Column(db.Integer, db.ForeignKey('coaches.id', ondelete='SET NULL'))
    admin_notes = db.Column(db.Text)  # Internal notes from admin/coach


class QuizMasRegistration(db.Model):
    """Quiz-mas workshop registration"""
    __tablename__ = 'quiz_mas_registrations'

    id = db.Column(db.Integer, primary_key=True)
    
    # Workshop info
    workshop = db.Column(db.String(100), nullable=False)  # Video Editing, Graphics Design, Coding
    number_of_children = db.Column(db.Integer, nullable=False)

    # Child 1 details
    child1_name = db.Column(db.String(255))
    child1_grade = db.Column(db.String(50))
    child1_birthdate = db.Column(db.Date)
    child1_signed_in = db.Column(db.String(10))
    child1_device = db.Column(db.String(50))
    child1_contact_method = db.Column(db.String(50))
    child1_contact_value = db.Column(db.String(255))  # NEW: Email/Phone/WhatsApp

    # Child 2 details
    child2_name = db.Column(db.String(255), nullable=True)
    child2_grade = db.Column(db.String(50), nullable=True)
    child2_birthdate = db.Column(db.Date, nullable=True)
    child2_signed_in = db.Column(db.String(10), nullable=True)
    child2_device = db.Column(db.String(50), nullable=True)
    child2_contact_method = db.Column(db.String(50), nullable=True)
    child2_contact_value = db.Column(db.String(255), nullable=True)  # NEW: Email/Phone/WhatsApp

    # Child 3 details
    child3_name = db.Column(db.String(255), nullable=True)
    child3_grade = db.Column(db.String(50), nullable=True)
    child3_birthdate = db.Column(db.Date, nullable=True)
    child3_signed_in = db.Column(db.String(10), nullable=True)
    child3_device = db.Column(db.String(50), nullable=True)
    child3_contact_method = db.Column(db.String(50), nullable=True)
    child3_contact_value = db.Column(db.String(255), nullable=True)  # NEW: Email/Phone/WhatsApp

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        data = {
            'id': self.id,
            'workshop': self.workshop,
            'number_of_children': self.number_of_children,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'children': []
        }

        # Add child 1
        if self.child1_name:
            data['children'].append({
                'name': self.child1_name,
                'grade': self.child1_grade,
                'birthdate': self.child1_birthdate.isoformat() if self.child1_birthdate else None,
                'signed_in': self.child1_signed_in,
                'device': self.child1_device,
                'contact_method': self.child1_contact_method,
                'contact_value': self.child1_contact_value  # NEW
            })

        # Add child 2
        if self.child2_name:
            data['children'].append({
                'name': self.child2_name,
                'grade': self.child2_grade,
                'birthdate': self.child2_birthdate.isoformat() if self.child2_birthdate else None,
                'signed_in': self.child2_signed_in,
                'device': self.child2_device,
                'contact_method': self.child2_contact_method,
                'contact_value': self.child2_contact_value  # NEW
            })

        # Add child 3
        if self.child3_name:
            data['children'].append({
                'name': self.child3_name,
                'grade': self.child3_grade,
                'birthdate': self.child3_birthdate.isoformat() if self.child3_birthdate else None,
                'signed_in': self.child3_signed_in,
                'device': self.child3_device,
                'contact_method': self.child3_contact_method,
                'contact_value': self.child3_contact_value  # NEW
            })

        return data

    def __repr__(self):
        return f'<QuizMasRegistration {self.id}: {self.workshop} - {self.number_of_children} child(ren)>'


class QuizMasGameResult(db.Model):
    """Quiz-mas 2025 Prize Spinner Game Results"""
    __tablename__ = 'quiz_mas_game_results'

    id = db.Column(db.Integer, primary_key=True)

    # Player information
    name = db.Column(db.String(255), nullable=False, unique=True, index=True)
    grade = db.Column(db.Integer, nullable=False)

    # Game results
    prize_won = db.Column(db.String(100), nullable=False)
    time_used = db.Column(db.Integer, nullable=False)  # Time in seconds
    completed = db.Column(db.Boolean, default=False)  # Whether they completed the puzzle

    # Metadata
    date_played = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'grade': self.grade,
            'prize_won': self.prize_won,
            'time_used': self.time_used,
            'completed': self.completed,
            'date_played': self.date_played.isoformat() if self.date_played else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<QuizMasGameResult {self.id}: {self.name} - Grade {self.grade} - Prize: {self.prize_won}>'


class SupportChatSession(db.Model):
    """Customer Support Chat Sessions"""
    __tablename__ = 'support_chat_sessions'

    id = db.Column(db.Integer, primary_key=True)

    # Customer information
    customer_name = db.Column(db.String(200), nullable=True)
    customer_email = db.Column(db.String(200), nullable=True)
    customer_phone = db.Column(db.String(50), nullable=True)

    # Session metadata
    session_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    status = db.Column(db.String(20), default='active')  # active, closed, waiting
    priority = db.Column(db.String(20), default='normal')  # low, normal, high, urgent
    inquiry_type = db.Column(db.String(10), nullable=True)  # 1-7 representing inquiry category
    inquiry_topic = db.Column(db.String(100), nullable=True)  # Enrollment, Payment, etc.

    # Assignment
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=True)
    assigned_to = db.relationship('Admin', backref='assigned_chats', foreign_keys=[assigned_to_id])

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_message_at = db.Column(db.DateTime, default=datetime.utcnow)
    closed_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    messages = db.relationship('SupportChatMessage', backref='session', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'customer_name': self.customer_name,
            'customer_email': self.customer_email,
            'customer_phone': self.customer_phone,
            'status': self.status,
            'priority': self.priority,
            'inquiry_type': self.inquiry_type,
            'inquiry_topic': self.inquiry_topic,
            'assigned_to_id': self.assigned_to_id,
            'assigned_to_name': self.assigned_to.name if self.assigned_to else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_message_at': self.last_message_at.isoformat() if self.last_message_at else None,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None,
            'message_count': self.messages.count(),
            'unread_count': self.messages.filter_by(is_read=False, sender_type='customer').count()
        }

    def get_time_ago(self):
        """Get time ago string for last message"""
        if not self.last_message_at:
            return 'Unknown'

        now = datetime.utcnow()
        diff = now - self.last_message_at

        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "Just now"

    def __repr__(self):
        return f'<SupportChatSession {self.id}: {self.session_id} - {self.status}>'


class SupportChatMessage(db.Model):
    """Customer Support Chat Messages"""
    __tablename__ = 'support_chat_messages'

    id = db.Column(db.Integer, primary_key=True)

    # Session reference
    session_id = db.Column(db.Integer, db.ForeignKey('support_chat_sessions.id'), nullable=False)

    # Message content
    message_text = db.Column(db.Text, nullable=False)
    sender_type = db.Column(db.String(20), nullable=False)  # 'customer', 'support'
    sender_name = db.Column(db.String(200), nullable=True)

    # Support agent info (if sender is support)
    support_agent_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=True)
    support_agent = db.relationship('Admin', backref='support_messages', foreign_keys=[support_agent_id])

    # Message metadata
    is_read = db.Column(db.Boolean, default=False)
    is_system_message = db.Column(db.Boolean, default=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'message_text': self.message_text,
            'sender_type': self.sender_type,
            'sender_name': self.sender_name,
            'support_agent_id': self.support_agent_id,
            'support_agent_name': self.support_agent.name if self.support_agent else None,
            'is_read': self.is_read,
            'is_system_message': self.is_system_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None
        }

    def mark_as_read(self):
        """Mark message as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = datetime.utcnow()
            db.session.commit()

    def __repr__(self):
        return f'<SupportChatMessage {self.id}: {self.sender_type} - Session {self.session_id}>'


# Subject Management Models for Student Dashboard
class Subject(db.Model):
    """Subject model for managing academic subjects"""
    __tablename__ = 'subjects'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)  # Mathematics, English-Language, etc.
    code = db.Column(db.String(50), unique=True, nullable=False)  # math, english-language, etc.
    description = db.Column(db.Text, nullable=True)
    icon_color = db.Column(db.String(20), default='#4A90E2')  # Hex color for UI card
    icon_name = db.Column(db.String(50), nullable=True)  # Icon identifier for frontend
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Subject {self.name}>'

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'icon_color': self.icon_color,
            'icon_name': self.icon_name,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class StudentSubject(db.Model):
    """StudentSubject model for assigning subjects to students"""
    __tablename__ = 'student_subjects'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=False)  # Who assigned it
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # Custom display properties (optional overrides)
    custom_name = db.Column(db.String(100), nullable=True)  # Allow custom display name
    custom_description = db.Column(db.Text, nullable=True)

    # Relationships
    student = db.relationship('Student', backref=db.backref('student_subjects', lazy=True))
    subject = db.relationship('Subject', backref=db.backref('subject_students', lazy=True))
    admin = db.relationship('Admin', backref=db.backref('subject_assignments', lazy=True))

    # Unique constraint to prevent duplicate assignments
    __table_args__ = (
        db.UniqueConstraint('student_id', 'subject_id', name='unique_student_subject'),
    )

    def __repr__(self):
        return f'<StudentSubject student_id={self.student_id} subject_id={self.subject_id}>'

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'subject_id': self.subject_id,
            'subject': self.subject.to_dict() if self.subject else None,
            'admin_id': self.admin_id,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'is_active': self.is_active,
            'custom_name': self.custom_name,
            'custom_description': self.custom_description,
            'display_name': self.custom_name if self.custom_name else (self.subject.name if self.subject else None),
            'display_description': self.custom_description if self.custom_description else (self.subject.description if self.subject else None),
            'icon_color': self.subject.icon_color if self.subject else '#4A90E2',
            'icon_name': self.subject.icon_name if self.subject else None
        }

# Skill Management Models for Student Dashboard
class Skill(db.Model):
    """Skill model for managing technical and soft skills"""
    __tablename__ = 'skills'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)  # Graphics Design, Coding, etc.
    code = db.Column(db.String(50), unique=True, nullable=False)  # graphics-design, coding, etc.
    description = db.Column(db.Text, nullable=True)
    icon_color = db.Column(db.String(20), default='#10B981')  # Hex color for UI card
    icon_name = db.Column(db.String(50), nullable=True)  # Icon identifier for frontend
    category = db.Column(db.String(50), nullable=True)  # e.g., 'technical', 'creative', 'soft-skills'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Skill {self.name}>'

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'icon_color': self.icon_color,
            'icon_name': self.icon_name,
            'category': self.category,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class StudentSkill(db.Model):
    """StudentSkill model for assigning skills to students"""
    __tablename__ = 'student_skills'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=False)  # Who assigned it
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # Progress tracking
    proficiency_level = db.Column(db.String(20), nullable=True)  # beginner, intermediate, advanced, expert
    progress_percentage = db.Column(db.Integer, default=0)  # 0-100

    # Custom display properties (optional overrides)
    custom_name = db.Column(db.String(100), nullable=True)  # Allow custom display name
    custom_description = db.Column(db.Text, nullable=True)

    # Relationships
    student = db.relationship('Student', backref=db.backref('student_skills', lazy=True))
    skill = db.relationship('Skill', backref=db.backref('skill_students', lazy=True))
    admin = db.relationship('Admin', backref=db.backref('skill_assignments', lazy=True))

    # Unique constraint to prevent duplicate assignments
    __table_args__ = (
        db.UniqueConstraint('student_id', 'skill_id', name='unique_student_skill'),
    )

    def __repr__(self):
        return f'<StudentSkill student_id={self.student_id} skill_id={self.skill_id}>'

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'skill_id': self.skill_id,
            'skill': self.skill.to_dict() if self.skill else None,
            'admin_id': self.admin_id,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'is_active': self.is_active,
            'proficiency_level': self.proficiency_level,
            'progress_percentage': self.progress_percentage,
            'custom_name': self.custom_name,
            'custom_description': self.custom_description,
            'display_name': self.custom_name if self.custom_name else (self.skill.name if self.skill else None),
            'display_description': self.custom_description if self.custom_description else (self.skill.description if self.skill else None),
            'icon_color': self.skill.icon_color if self.skill else '#10B981',
            'icon_name': self.skill.icon_name if self.skill else None,
            'category': self.skill.category if self.skill else None
        }


# ============================================================================
# TUTORING PROJECT MODELS
# Models for the integrated tutoring system (tutor applications, bookings, reviews)
# Uses tutoring_ prefixed table names to avoid conflicts with existing models
# ============================================================================

class TutoringTutor(db.Model):
    """Tutor application and profile for the tutoring system"""
    __tablename__ = 'tutoring_tutors'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    phone = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.String(20), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    timezone = db.Column(db.String(100), nullable=False)
    languages = db.Column(db.String(500), nullable=False)
    profile_photo_path = db.Column(db.String(500))
    highest_degree = db.Column(db.String(200), nullable=False)
    field_of_study = db.Column(db.String(200), nullable=False)
    university = db.Column(db.String(300), nullable=False)
    years_experience = db.Column(db.Integer, nullable=False)
    certifications = db.Column(db.Text)
    linkedin_profile = db.Column(db.String(500))
    subjects = db.Column(db.Text, nullable=False)  # JSON string
    exams = db.Column(db.Text, nullable=False)  # JSON string
    grade_levels = db.Column(db.Text, nullable=False)  # JSON string
    bio = db.Column(db.Text, nullable=False)
    hourly_rate = db.Column(db.Float, nullable=False)
    intro_video_path = db.Column(db.String(500), nullable=False)
    video_duration = db.Column(db.Integer)
    status = db.Column(db.String(20), default='pending')
    admin_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)

    # Relationships
    certificates = db.relationship('TutoringCertificate', backref='tutor', lazy=True)
    admin_actions = db.relationship('TutoringAdminAction', backref='tutor', lazy=True)
    sessions = db.relationship('TutoringSession', backref='tutor', lazy=True)
    reviews = db.relationship('TutoringReview', backref='tutor', lazy=True)

    def to_dict(self):
        import json as _json
        return {
            'id': self.id,
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'date_of_birth': self.date_of_birth,
            'country': self.country,
            'timezone': self.timezone,
            'languages': self.languages,
            'profile_photo_path': self.profile_photo_path,
            'highest_degree': self.highest_degree,
            'field_of_study': self.field_of_study,
            'university': self.university,
            'years_experience': self.years_experience,
            'certifications': self.certifications,
            'linkedin_profile': self.linkedin_profile,
            'subjects': _json.loads(self.subjects) if self.subjects else [],
            'exams': _json.loads(self.exams) if self.exams else [],
            'grade_levels': _json.loads(self.grade_levels) if self.grade_levels else [],
            'bio': self.bio,
            'hourly_rate': self.hourly_rate,
            'intro_video_path': self.intro_video_path,
            'video_duration': self.video_duration,
            'status': self.status,
            'admin_notes': self.admin_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'certificates': [c.certificate_path for c in self.certificates] if self.certificates else []
        }


class TutoringCertificate(db.Model):
    """Tutor uploaded certificates"""
    __tablename__ = 'tutoring_certificates'

    id = db.Column(db.Integer, primary_key=True)
    tutor_id = db.Column(db.Integer, db.ForeignKey('tutoring_tutors.id'), nullable=False)
    certificate_path = db.Column(db.String(500), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)


class TutoringAdminAction(db.Model):
    """Admin actions on tutor applications"""
    __tablename__ = 'tutoring_admin_actions'

    id = db.Column(db.Integer, primary_key=True)
    tutor_id = db.Column(db.Integer, db.ForeignKey('tutoring_tutors.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    admin_notes = db.Column(db.Text)
    action_date = db.Column(db.DateTime, default=datetime.utcnow)


class TutoringStudent(db.Model):
    """Student accounts for the tutoring system"""
    __tablename__ = 'tutoring_students'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    grade_level = db.Column(db.String(50))
    profile_photo_path = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    sessions = db.relationship('TutoringSession', backref='student', lazy=True)
    reviews = db.relationship('TutoringReview', backref='student', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'grade_level': self.grade_level,
            'profile_photo_path': self.profile_photo_path,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'is_active': self.is_active
        }


class TutoringSession(db.Model):
    """Tutoring session bookings"""
    __tablename__ = 'tutoring_sessions'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('tutoring_students.id'), nullable=False)
    tutor_id = db.Column(db.Integer, db.ForeignKey('tutoring_tutors.id'), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    session_date = db.Column(db.String(20), nullable=False)
    session_time = db.Column(db.String(20), nullable=False)
    duration = db.Column(db.Integer, default=60)
    status = db.Column(db.String(20), default='pending')
    amount = db.Column(db.Float, nullable=False)
    payment_status = db.Column(db.String(20), default='pending')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    reviews = db.relationship('TutoringReview', backref='session', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'tutor_id': self.tutor_id,
            'subject': self.subject,
            'session_date': self.session_date,
            'session_time': self.session_time,
            'duration': self.duration,
            'status': self.status,
            'amount': self.amount,
            'payment_status': self.payment_status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class TutoringReview(db.Model):
    """Reviews for tutoring sessions"""
    __tablename__ = 'tutoring_reviews'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('tutoring_sessions.id'), nullable=False)
    tutor_id = db.Column(db.Integer, db.ForeignKey('tutoring_tutors.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('tutoring_students.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    review = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'tutor_id': self.tutor_id,
            'student_id': self.student_id,
            'rating': self.rating,
            'review': self.review,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
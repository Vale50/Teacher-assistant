"""
Lesson Plan Blueprint - Contains all lesson plan-related endpoints
"""
from flask import Blueprint, request, jsonify, send_from_directory, send_file, make_response
import os
import uuid
import logging
import json
import re
from datetime import datetime
from extensions import db
from anthropic import Anthropic
import io

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Blueprint
lesson_plan_bp = Blueprint('lesson_plan_routes', __name__)

# Initialize Anthropic client
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None


# Helper functions
def get_grade_level_text(grade_level):
    """Get human-readable grade level text"""
    grade_level_map = {
        'elementary': 'elementary school (grades 1-5)',
        'elementary-lower': 'elementary school (grades 1-2)',
        'elementary-upper': 'elementary school (grades 3-5)',
        'middle': 'middle school (grades 6-8)',
        'high': 'high school (grades 9-12)',
        'college': 'college/university level'
    }
    return grade_level_map.get(grade_level, grade_level)


def strip_html(html_content):
    """Remove HTML tags from content"""
    if not html_content:
        return ""

    clean_text = re.sub(r'<[^>]*>', '', html_content)
    clean_text = clean_text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()

    return clean_text


def parse_main_content(content):
    """Parse the main content text into structured components"""

    def clean_text(text):
        text = re.sub(r'(?i)(SUBTOPIC\s*\d*:?|CATEGORY:|TOPIC OVERVIEW:|PRACTICE ACTIVITIES:|DISCUSSION QUESTIONS:|KEY POINTS:)', '', text)
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
        text = text.replace('**', '')
        return text.strip()

    structured_content = {
        "overview": "",
        "subtopics": [],
        "practice_activities": [],
        "discussion_questions": [],
        "key_points": []
    }

    # Extract overview section
    overview_pattern = r"(?i)TOPIC OVERVIEW:(.*?)(?=SUBTOPIC:|$)"
    overview_match = re.search(overview_pattern, content, re.DOTALL | re.IGNORECASE)
    if overview_match:
        structured_content["overview"] = f"<p>{clean_text(overview_match.group(1))}</p>"
    else:
        paragraphs = content.split('\n\n')
        if paragraphs:
            structured_content["overview"] = f"<p>{clean_text(paragraphs[0])}</p>"

    # Extract subtopics
    subtopic_pattern = r"(?i)SUBTOPIC:(.*?)(?=SUBTOPIC:|PRACTICE ACTIVITIES:|DISCUSSION QUESTIONS:|KEY POINTS:|$)"
    subtopic_matches = list(re.finditer(subtopic_pattern, content, re.DOTALL | re.IGNORECASE))

    for i, match in enumerate(subtopic_matches[:2]):
        subtopic_text = match.group(1).strip()

        title_match = re.search(r'\*\*(.*?)\*\*', subtopic_text) or re.search(r'^(.*?)$', subtopic_text, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else f"Subtopic {i+1}"

        intro_pattern = r"(.*?)(?=CATEGORY:|$)"
        intro_match = re.search(intro_pattern, subtopic_text, re.DOTALL)
        introduction = clean_text(intro_match.group(1)) if intro_match else ""

        category = {"title": "", "items": []}

        category_pattern = r"(?i)CATEGORY:(.*?)(?=SUBTOPIC:|PRACTICE ACTIVITIES:|DISCUSSION QUESTIONS:|KEY POINTS:|$)"
        category_match = re.search(category_pattern, subtopic_text, re.DOTALL | re.IGNORECASE)

        if category_match:
            category_text = category_match.group(1).strip()

            cat_title_match = re.search(r'\*\*(.*?)\*\*', category_text) or re.search(r'^(.*?)$', category_text, re.MULTILINE)
            category["title"] = clean_text(cat_title_match.group(1)) if cat_title_match else f"Category {i+1}"

        structured_content["subtopics"].append({
            "title": title,
            "introduction": f"<p>{introduction}</p>",
            "category": category
        })

    # Ensure we have exactly 2 subtopics
    while len(structured_content["subtopics"]) < 2:
        structured_content["subtopics"].append({
            "title": "Additional Information",
            "introduction": "<p>Further exploration of this topic reveals additional important concepts.</p>",
            "category": {
                "title": "Key Elements",
                "items": []
            }
        })

    # Extract practice activities
    activities_pattern = r"PRACTICE ACTIVITIES:(.*?)(?=DISCUSSION QUESTIONS:|KEY POINTS:|$)"
    activities_match = re.search(activities_pattern, content, re.DOTALL | re.IGNORECASE)
    if activities_match:
        activities_text = clean_text(activities_match.group(1))
        activity_items = re.findall(r"(?:\d+\.|[\*\-])\s+(.*?)(?=(?:\d+\.|[\*\-])|$)", activities_text, re.DOTALL)
        if activity_items:
            structured_content["practice_activities"] = [clean_text(item) for item in activity_items if clean_text(item)]

    # Extract discussion questions
    questions_pattern = r"DISCUSSION QUESTIONS:(.*?)(?=KEY POINTS:|$)"
    questions_match = re.search(questions_pattern, content, re.DOTALL | re.IGNORECASE)
    if questions_match:
        questions_text = clean_text(questions_match.group(1))
        question_items = re.findall(r"(?:\d+\.|[\*\-])\s+(.*?)(?=(?:\d+\.|[\*\-])|$)", questions_text, re.DOTALL)
        if question_items:
            structured_content["discussion_questions"] = [clean_text(item) for item in question_items if clean_text(item)]

    # Extract key points
    key_points_pattern = r"KEY POINTS:(.*?)$"
    key_points_match = re.search(key_points_pattern, content, re.DOTALL | re.IGNORECASE)
    if key_points_match:
        key_points_text = clean_text(key_points_match.group(1))
        point_items = re.findall(r"(?:\d+\.|[\*\-])\s+(.*?)(?=(?:\d+\.|[\*\-])|$)", key_points_text, re.DOTALL)
        if point_items:
            structured_content["key_points"] = [clean_text(item) for item in point_items if clean_text(item)]

    return structured_content


def format_structured_content_html(structured_content):
    """Format the structured content components with HTML tags"""
    if structured_content["overview"]:
        if not structured_content["overview"].startswith("<p>"):
            structured_content["overview"] = "<p>" + structured_content['overview'].replace('\n\n', '</p><p>') + "</p>"

    for subtopic in structured_content["subtopics"]:
        if subtopic["introduction"] and not subtopic["introduction"].startswith("<p>"):
            intro_text = subtopic['introduction'].replace('\n\n', '</p><p>')
            subtopic["introduction"] = f"<p>{intro_text}</p>"

        category = subtopic["category"]
        if category and "items" in category:
            formatted_items = []

            for item in category["items"]:
                if "number" in item:
                    del item["number"]

                if not item.get("description", "").startswith("<p>"):
                    desc_text = item.get('description', '').replace('\n\n', '</p><p>')
                    item["description"] = f"<p>{desc_text}</p>"

                formatted_items.append(item)

            category["items"] = formatted_items

    for section in ["practice_activities", "discussion_questions", "key_points"]:
        if structured_content[section] and isinstance(structured_content[section], list):
            items_html = "".join([f"<li>{item}</li>" for item in structured_content[section]])
            structured_content[section] = f"<ol>{items_html}</ol>"


# Static page routes
@lesson_plan_bp.route('/lesson-plan')
def serve_lesson_plan():
    return send_from_directory('.', 'lesson-plan.html')

@lesson_plan_bp.route('/lesson-preview')
def serve_lesson_preview():
    return send_from_directory('.', 'lesson-preview.html')

@lesson_plan_bp.route('/view-lesson')
def serve_view_lesson():
    return send_from_directory('.', 'view-lesson.html')

@lesson_plan_bp.route('/stem-plan')
def serve_maths_plan():
    return send_from_directory('.', 'stem-plan.html')


# API endpoints
@lesson_plan_bp.route('/api/generate-lesson-content', methods=['POST'])
def generate_lesson_content():
    """Generate lesson content for a specific section"""
    from app import token_required as app_token_required

    @app_token_required
    def _generate_lesson_content(current_user):
        try:
            data = request.get_json()

            section = data.get('section', '')
            subject = data.get('subject', '')
            topic = data.get('topic', '')
            grade_level = data.get('grade_level', '')
            prompt = data.get('prompt', '')

            if not all([section, subject, topic, grade_level, prompt]):
                return jsonify({'error': 'Missing required fields'}), 400

            # Check if Anthropic client is initialized
            if not anthropic_client:
                logger.error("Anthropic client is not initialized. ANTHROPIC_API_KEY may not be set.")
                return jsonify({'error': 'AI service is not configured. Please contact the administrator.'}), 503

            logger.debug(f"Generating content for section: {section}")

            try:
                response = anthropic_client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=1000,
                    temperature=0.7,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )

                content = response.content[0].text
                logger.info(f"Generated content for {section}: {len(content)} characters")

                return jsonify({
                    'content': content,
                    'section': section
                }), 200

            except Exception as claude_error:
                logger.error(f"Claude API error: {str(claude_error)}")
                return jsonify({'error': 'Failed to generate content'}), 500

        except Exception as e:
            logger.error(f"Content generation error: {str(e)}")
            return jsonify({'error': str(e)}), 500

    return _generate_lesson_content()


@lesson_plan_bp.route('/api/generate-lesson-plan', methods=['POST'])
def generate_lesson_plan():
    """Generate a complete lesson plan"""
    from app import token_required as app_token_required

    @app_token_required
    def _generate_lesson_plan(current_user):
        try:
            data = request.get_json()

            subject = data.get('subject', '')
            topic = data.get('topic', '')
            grade_level = data.get('grade_level', '')
            duration = data.get('duration', '45')
            add_evaluation = data.get('add_evaluation', False)
            add_homework = data.get('add_homework', False)

            if not all([subject, topic, grade_level]):
                return jsonify({'error': 'Missing required fields: subject, topic, and grade_level are required'}), 400

            # Check if Anthropic client is initialized
            if not anthropic_client:
                logger.error("Anthropic client is not initialized. ANTHROPIC_API_KEY may not be set.")
                return jsonify({'error': 'AI service is not configured. Please contact the administrator.'}), 503

            lesson_plan_id = str(uuid.uuid4())
            grade_level_text = get_grade_level_text(grade_level)

            # Core prompt
            core_prompt = f"""
Create an engaging, detailed lesson plan on "{topic}" for {grade_level_text} students in {subject}. Duration: {duration} minutes.

Please create an INFORMATIONAL CONTENT LESSON with the following structured format:

1. OBJECTIVES (3-4 specific learning objectives)
Create 4-6 clear, measurable learning objectives that start with "Students will be able to..." (SWBAT).

2. INTRODUCTION (300-400 words)
Write an engaging, detailed introduction that provides overview of {topic}.

3. MAIN CONTENT (800-1000 words total)
Include:
- TOPIC OVERVIEW (150-200 words)
- SUBTOPIC 1 with CATEGORY (450-500 words)
- SUBTOPIC 2 with CATEGORY (250-300 words)

4. ADDITIONAL CONTENT:
- PRACTICE ACTIVITIES (3 activities)
- DISCUSSION QUESTIONS (4 questions)
- KEY POINTS (5 summary points)

Format ALL content as student-facing material, not as teacher instructions.
"""

            try:
                core_response = anthropic_client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=4000,
                    temperature=0.7,
                    messages=[{"role": "user", "content": core_prompt}]
                )

                core_content = core_response.content[0].text
                logger.info(f"Generated core content: {len(core_content)} characters")

                # Parse sections
                objectives_section = ""
                introduction_section = ""
                main_content_section = ""

                current_section = None
                lines = core_content.split('\n')

                for line in lines:
                    if "OBJECTIVES" in line.upper():
                        current_section = "objectives"
                        continue
                    elif "INTRODUCTION" in line.upper():
                        current_section = "introduction"
                        continue
                    elif "MAIN CONTENT" in line.upper():
                        current_section = "main_content"
                        continue

                    if current_section == "objectives":
                        objectives_section += line + "\n"
                    elif current_section == "introduction":
                        introduction_section += line + "\n"
                    elif current_section == "main_content":
                        main_content_section += line + "\n"

                # Parse objectives into a list
                objectives_list = []
                for line in objectives_section.split('\n'):
                    line = line.strip()
                    if line.startswith('-') or line.startswith('*') or line.startswith('"'):
                        objectives_list.append(line[1:].strip())
                    elif line.startswith('SWBAT') or line.startswith('Students will'):
                        objectives_list.append(line)

                if not objectives_list:
                    objectives_list = [objectives_section.strip()]

                main_content_structured = parse_main_content(main_content_section)

                # Generate supplementary content
                fun_prompt = f"""
Create engaging supplementary content for a lesson on "{topic}" for {grade_level_text} students.

Generate:
1. QUOTE - A meaningful, relevant quote
2. DID YOU KNOW - An interesting fact
3. REAL-WORLD CONNECTION - How topic applies to real life
4. FUN FACTS (3-5 facts)
5. RIDDLE - A thought-provoking riddle with answer
6. MATERIALS - List of materials needed
7. ASSESSMENT (200+ words)
8. DIFFERENTIATION (200+ words)
9. CLOSURE (100+ words)
10. STUDENT SUMMARY (300-400 words)

Format each section with its heading.
"""

                fun_response = anthropic_client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=4000,
                    temperature=0.7,
                    messages=[{"role": "user", "content": fun_prompt}]
                )

                fun_content = fun_response.content[0].text
                logger.info(f"Generated fun content: {len(fun_content)} characters")

                # Parse fun content
                quote = ""
                did_you_know = ""
                real_world = ""
                fun_facts_text = ""
                riddle_text = ""
                materials_text = ""
                assessment_text = ""
                differentiation_text = ""
                closure_text = ""
                student_summary = ""

                current_section = None
                lines = fun_content.split('\n')

                for line in lines:
                    if "QUOTE" in line.upper():
                        current_section = "quote"
                        continue
                    elif "DID YOU KNOW" in line.upper():
                        current_section = "did_you_know"
                        continue
                    elif "REAL-WORLD" in line.upper():
                        current_section = "real_world"
                        continue
                    elif "FUN FACTS" in line.upper():
                        current_section = "fun_facts"
                        continue
                    elif "RIDDLE" in line.upper():
                        current_section = "riddle"
                        continue
                    elif "MATERIALS" in line.upper():
                        current_section = "materials"
                        continue
                    elif "ASSESSMENT" in line.upper():
                        current_section = "assessment"
                        continue
                    elif "DIFFERENTIATION" in line.upper():
                        current_section = "differentiation"
                        continue
                    elif "CLOSURE" in line.upper():
                        current_section = "closure"
                        continue
                    elif "STUDENT SUMMARY" in line.upper():
                        current_section = "student_summary"
                        continue

                    if current_section == "quote":
                        quote += line + "\n"
                    elif current_section == "did_you_know":
                        did_you_know += line + "\n"
                    elif current_section == "real_world":
                        real_world += line + "\n"
                    elif current_section == "fun_facts":
                        fun_facts_text += line + "\n"
                    elif current_section == "riddle":
                        riddle_text += line + "\n"
                    elif current_section == "materials":
                        materials_text += line + "\n"
                    elif current_section == "assessment":
                        assessment_text += line + "\n"
                    elif current_section == "differentiation":
                        differentiation_text += line + "\n"
                    elif current_section == "closure":
                        closure_text += line + "\n"
                    elif current_section == "student_summary":
                        student_summary += line + "\n"

                # Parse fun facts into list
                fun_facts_list = []
                for line in fun_facts_text.split('\n'):
                    line = line.strip()
                    if line.startswith('-') or line.startswith('*') or line.startswith('"') or re.match(r'^\d+\.', line):
                        fact = re.sub(r'^[\d\.\-\*\"\s]+', '', line).strip()
                        if fact:
                            fun_facts_list.append(fact)

                if not fun_facts_list:
                    fun_facts_list = [fun_facts_text.strip()]

                # Parse materials
                materials_list = []
                for line in materials_text.split('\n'):
                    line = line.strip()
                    if line.startswith('-') or line.startswith('*') or line.startswith('"'):
                        materials_list.append(line[1:].strip())

                if not materials_list:
                    materials_list = ["Required materials for this lesson"]

                # Parse riddle
                riddle = {"question": riddle_text.strip(), "answer": ""}

                # Construct the lesson plan
                lesson_plan_data = {
                    "title": f"{subject}: {topic} - Lesson Plan",
                    "grade_level": grade_level_text,
                    "duration": f"{duration} minutes",
                    "objectives": objectives_list,
                    "introduction": introduction_section,
                    "quote": quote.strip(),
                    "main_content_structured": main_content_structured,
                    "did_you_know": did_you_know.strip(),
                    "real_world_connection": real_world.strip(),
                    "materials": materials_list,
                    "fun_facts": fun_facts_list,
                    "riddle": riddle,
                    "assessment": assessment_text.strip(),
                    "differentiation": differentiation_text.strip(),
                    "closure": closure_text.strip(),
                    "student_summary": student_summary.strip()
                }

                # Add evaluation if requested
                if add_evaluation:
                    eval_prompt = f"""
Create 5-7 assessment questions for a lesson on "{topic}" for {grade_level_text} students.
Include a mix of question types.
"""
                    eval_response = anthropic_client.messages.create(
                        model="claude-3-haiku-20240307",
                        max_tokens=1000,
                        temperature=0.7,
                        messages=[{"role": "user", "content": eval_prompt}]
                    )

                    lesson_plan_data["evaluation_test"] = [eval_response.content[0].text]

                # Add homework if requested
                if add_homework:
                    homework_prompt = f"""
Create a meaningful homework assignment for a lesson on "{topic}" for {grade_level_text} students.
"""
                    homework_response = anthropic_client.messages.create(
                        model="claude-3-haiku-20240307",
                        max_tokens=1000,
                        temperature=0.7,
                        messages=[{"role": "user", "content": homework_prompt}]
                    )

                    lesson_plan_data["homework"] = homework_response.content[0].text

                # Format HTML for text sections
                for section in ["introduction", "did_you_know", "real_world_connection",
                              "assessment", "differentiation", "closure", "student_summary"]:
                    if section in lesson_plan_data and lesson_plan_data[section]:
                        text = lesson_plan_data[section]
                        text = text.replace("\n\n", "</p><p>")
                        text = f"<p>{text}</p>"
                        lesson_plan_data[section] = text

                format_structured_content_html(lesson_plan_data["main_content_structured"])

                return jsonify({
                    'message': 'Lesson plan created successfully',
                    'lesson_plan_id': lesson_plan_id,
                    'lesson_plan': lesson_plan_data,
                    'validation_passed': True
                }), 201

            except Exception as claude_error:
                logger.error(f"Claude API error: {str(claude_error)}")
                return jsonify({'error': 'Failed to generate lesson plan with Claude API'}), 500

        except Exception as e:
            logger.error(f"Lesson plan generation error: {str(e)}")
            return jsonify({'error': str(e)}), 500

    return _generate_lesson_plan()


@lesson_plan_bp.route('/api/generate-lesson-section', methods=['POST'])
def generate_lesson_section():
    """Generate a specific section of a lesson plan"""
    from app import token_required as app_token_required

    @app_token_required
    def _generate_lesson_section(current_user):
        try:
            data = request.get_json()

            section_type = data.get('section_type', '')
            topic = data.get('topic', '')
            grade_level = data.get('grade_level', '')
            prompt = data.get('prompt', '')

            if not prompt:
                return jsonify({'error': 'Prompt is required'}), 400

            # Check if Anthropic client is initialized
            if not anthropic_client:
                logger.error("Anthropic client is not initialized. ANTHROPIC_API_KEY may not be set.")
                return jsonify({'error': 'AI service is not configured. Please contact the administrator.'}), 503

            try:
                response = anthropic_client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=2000,
                    temperature=0.7,
                    messages=[{"role": "user", "content": prompt}]
                )

                content = response.content[0].text
                logger.info(f"Generated section content: {len(content)} characters")

                return jsonify({
                    'content': content,
                    'section_type': section_type
                }), 200

            except Exception as claude_error:
                logger.error(f"Claude API error: {str(claude_error)}")
                return jsonify({'error': 'Failed to generate section content'}), 500

        except Exception as e:
            logger.error(f"Section generation error: {str(e)}")
            return jsonify({'error': str(e)}), 500

    return _generate_lesson_section()


@lesson_plan_bp.route('/api/lesson-to-flashcard-data', methods=['GET'])
def get_lesson_plan_for_flashcards():
    """Get lesson plan data formatted for flashcard creation."""
    from app import token_required as app_token_required
    from auth.models import LessonPlanModel

    @app_token_required
    def _get_lesson_plan_for_flashcards(current_user):
        try:
            lesson_plan_id = request.args.get('lesson_plan_id')

            if not lesson_plan_id:
                return jsonify({'error': 'Lesson plan ID is required'}), 400

            lesson_plan = LessonPlanModel.query.filter_by(id=lesson_plan_id).first()

            if not lesson_plan:
                return jsonify({'error': 'Lesson plan not found'}), 404

            if lesson_plan.user_id != current_user.id:
                return jsonify({'error': 'Unauthorized access to lesson plan'}), 403

            # Format data for flashcards
            formatted_data = {
                'lesson_plan_id': lesson_plan.id,
                'title': getattr(lesson_plan, 'title', ''),
                'topic': getattr(lesson_plan, 'topic', ''),
                'grade_level': getattr(lesson_plan, 'grade_level', ''),
                'content': ''
            }

            return jsonify({
                'success': True,
                'lesson_plan_data': formatted_data
            }), 200

        except Exception as e:
            logger.error(f"Error fetching lesson plan for flashcards: {str(e)}")
            return jsonify({'error': str(e)}), 500

    return _get_lesson_plan_for_flashcards()


@lesson_plan_bp.route('/api/lesson-to-quiz-data', methods=['GET'])
def get_lesson_plan_for_quiz():
    """Get lesson plan data formatted for quiz creation."""
    from app import token_required as app_token_required
    from auth.models import LessonPlanModel

    @app_token_required
    def _get_lesson_plan_for_quiz(current_user):
        try:
            lesson_plan_id = request.args.get('lesson_plan_id')

            if not lesson_plan_id:
                return jsonify({'error': 'Lesson plan ID is required'}), 400

            lesson_plan = LessonPlanModel.query.filter_by(id=lesson_plan_id).first()

            if not lesson_plan:
                return jsonify({'error': 'Lesson plan not found'}), 404

            if lesson_plan.user_id != current_user.id:
                return jsonify({'error': 'Unauthorized access to lesson plan'}), 403

            # Format data for quiz
            formatted_data = {
                'lesson_plan_id': lesson_plan.id,
                'title': getattr(lesson_plan, 'title', ''),
                'topic': getattr(lesson_plan, 'topic', ''),
                'grade_level': getattr(lesson_plan, 'grade_level', ''),
                'content': ''
            }

            return jsonify({
                'success': True,
                'lesson_plan_data': formatted_data
            }), 200

        except Exception as e:
            logger.error(f"Error fetching lesson plan for quiz: {str(e)}")
            return jsonify({'error': str(e)}), 500

    return _get_lesson_plan_for_quiz()


@lesson_plan_bp.route('/api/math-lesson-plans', methods=['GET'])
def get_math_lesson_plans():
    """Get list of math lesson plans"""
    from app import token_required as app_token_required
    from auth.models import MathLessonPlanModel

    @app_token_required
    def _get_math_lesson_plans(current_user):
        try:
            plans = MathLessonPlanModel.query.filter_by(user_id=current_user.id).order_by(
                MathLessonPlanModel.created_at.desc()
            ).all()

            plans_data = []
            for plan in plans:
                plans_data.append({
                    'id': plan.id,
                    'title': plan.title,
                    'topic': plan.topic,
                    'grade_level': plan.grade_level,
                    'created_at': plan.created_at.isoformat() if plan.created_at else None
                })

            return jsonify({
                'lesson_plans': plans_data
            }), 200

        except Exception as e:
            logger.error(f"Error getting math lesson plans: {str(e)}")
            return jsonify({'error': str(e)}), 500

    return _get_math_lesson_plans()


@lesson_plan_bp.route('/api/math-lesson-plans/<lesson_id>', methods=['GET'])
def get_math_lesson_plan(lesson_id):
    """Get a specific math lesson plan"""
    from app import token_required as app_token_required
    from auth.models import MathLessonPlanModel

    @app_token_required
    def _get_math_lesson_plan(current_user):
        try:
            plan = MathLessonPlanModel.query.filter_by(
                id=lesson_id,
                user_id=current_user.id
            ).first()

            if not plan:
                return jsonify({'error': 'Lesson plan not found'}), 404

            # Build lesson dict matching original format
            lesson_dict = {
                'id': plan.id,
                'title': plan.title,
                'topic': plan.topic,
                'grade_level': plan.grade_level,
                'subject': getattr(plan, 'subject', ''),
                'duration': getattr(plan, 'duration', ''),
                'created_at': plan.created_at.isoformat() if plan.created_at else None,
                'updated_at': plan.updated_at.isoformat() if hasattr(plan, 'updated_at') and plan.updated_at else None
            }

            # CRITICAL: Parse content_json properly
            if plan.content_json:
                try:
                    lesson_dict['content'] = json.loads(plan.content_json)
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse content_json for lesson {lesson_id}")
                    lesson_dict['content'] = {}
            else:
                lesson_dict['content'] = {}

            # Return in expected format with lesson_plan wrapper
            response_data = {'lesson_plan': lesson_dict}
            logger.info(f"Successfully fetched lesson plan {lesson_id}")
            logger.info(f"Response keys: {list(response_data.keys())}")
            logger.info(f"Lesson plan has content: {bool(lesson_dict.get('content'))}")
            return jsonify(response_data), 200

        except Exception as e:
            logger.error(f"Error getting math lesson plan: {str(e)}")
            return jsonify({'error': str(e)}), 500

    return _get_math_lesson_plan()


@lesson_plan_bp.route('/api/math-lesson-plans/<lesson_id>', methods=['DELETE'])
def delete_math_lesson_plan(lesson_id):
    """Delete a math lesson plan"""
    from app import token_required as app_token_required
    from auth.models import MathLessonPlanModel

    @app_token_required
    def _delete_math_lesson_plan(current_user):
        try:
            plan = MathLessonPlanModel.query.get(lesson_id)

            if not plan:
                return jsonify({'error': 'Lesson plan not found'}), 404

            if plan.user_id != current_user.id:
                return jsonify({'error': 'Unauthorized access'}), 403

            db.session.delete(plan)
            db.session.commit()

            return jsonify({'message': 'Lesson plan deleted successfully'}), 200

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting math lesson plan: {str(e)}")
            return jsonify({'error': str(e)}), 500

    return _delete_math_lesson_plan()


@lesson_plan_bp.route('/api/math-lesson-plans/<lesson_id>', methods=['PUT'])
def update_math_lesson_plan(lesson_id):
    """Update a math lesson plan"""
    from app import token_required as app_token_required
    from auth.models import MathLessonPlanModel

    @app_token_required
    def _update_math_lesson_plan(current_user):
        try:
            plan = MathLessonPlanModel.query.filter_by(
                id=lesson_id,
                user_id=current_user.id
            ).first()

            if not plan:
                return jsonify({'error': 'Lesson plan not found'}), 404

            data = request.get_json()
            logger.info(f"Updating lesson plan {lesson_id}")
            logger.debug(f"Update payload size: {len(json.dumps(data))} bytes")

            # Update basic fields if provided
            if 'title' in data:
                plan.title = data['title']
            if 'topic' in data:
                plan.topic = data['topic']
            if 'grade_level' in data:
                plan.grade_level = data['grade_level']
            if 'subject' in data:
                plan.subject = data['subject']
            if 'duration' in data:
                # Handle both "45 minutes" format and numeric values
                duration_str = str(data['duration'])
                duration_num = int(duration_str.split()[0]) if ' ' in duration_str else int(duration_str)
                plan.duration_minutes = duration_num

            # Update content_json - this contains custom_sections and other lesson content
            if 'content' in data:
                plan.content_json = json.dumps(data['content'])
            elif 'custom_sections' in data:
                # Handle direct custom_sections update
                content_data = json.loads(plan.content_json) if plan.content_json else {}
                content_data['custom_sections'] = data['custom_sections']

                # Update other content fields if provided
                for field in ['learning_objectives', 'materials_needed', 'assessment_methods']:
                    if field in data:
                        content_data[field] = data[field]

                plan.content_json = json.dumps(content_data)

            # Update the updated_at timestamp
            plan.updated_at = datetime.utcnow()

            db.session.commit()

            logger.info(f"Successfully updated lesson plan {lesson_id}")
            return jsonify({
                'message': 'Lesson plan updated successfully',
                'lesson_plan_id': lesson_id
            }), 200

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating math lesson plan: {str(e)}")
            return jsonify({'error': str(e)}), 500

    return _update_math_lesson_plan()


@lesson_plan_bp.route('/api/upload-lesson-image', methods=['POST'])
def upload_lesson_image():
    """Upload an image for a lesson plan"""
    from app import token_required as app_token_required

    @app_token_required
    def _upload_lesson_image(current_user):
        try:
            if 'image' not in request.files:
                return jsonify({'error': 'No image file provided'}), 400

            file = request.files['image']

            if file.filename == '':
                return jsonify({'error': 'No selected file'}), 400

            # Generate unique filename
            filename = f"{uuid.uuid4()}_{file.filename}"

            # Save to uploads directory
            upload_folder = os.path.join('static', 'lesson_images')
            os.makedirs(upload_folder, exist_ok=True)

            filepath = os.path.join(upload_folder, filename)
            file.save(filepath)

            # Return the URL
            image_url = f"/static/lesson_images/{filename}"

            return jsonify({
                'success': True,
                'image_url': image_url
            }), 200

        except Exception as e:
            logger.error(f"Error uploading lesson image: {str(e)}")
            return jsonify({'error': str(e)}), 500

    return _upload_lesson_image()


@lesson_plan_bp.route('/api/lesson-preview/<lesson_id>', methods=['GET'])
def get_lesson_preview(lesson_id):
    """Get lesson plan data for preview page"""
    from app import token_required as app_token_required
    from auth.models import MathLessonPlanModel
    import json

    @app_token_required
    def _get_lesson_preview(current_user):
        try:
            # Query lesson plan for this user
            plan = MathLessonPlanModel.query.filter_by(
                id=lesson_id,
                user_id=current_user.id
            ).first()

            if not plan:
                logger.warning(f"Lesson plan not found: {lesson_id} for user {current_user.id}")
                return jsonify({'error': 'Lesson plan not found'}), 404

            # Parse content_json to get custom_sections and other content
            content_data = {}
            if plan.content_json:
                try:
                    content_data = json.loads(plan.content_json)
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse content_json for lesson {lesson_id}")
                    content_data = {}

            # Build response in the format expected by the frontend
            response = {
                'id': plan.id,
                'title': plan.title,
                'topic': plan.topic,
                'grade_level': plan.grade_level,
                'subject': getattr(plan, 'subject', ''),
                'duration': getattr(plan, 'duration', ''),
                'created_at': plan.created_at.isoformat() if plan.created_at else None,
                'updated_at': plan.updated_at.isoformat() if hasattr(plan, 'updated_at') and plan.updated_at else None,
                # Include all content fields at the top level for frontend compatibility
                'custom_sections': content_data.get('custom_sections', []),
                'learning_objectives': content_data.get('learning_objectives', ''),
                'materials_needed': content_data.get('materials_needed', ''),
                'assessment_methods': content_data.get('assessment_methods', ''),
            }

            logger.info(f"Successfully fetched lesson preview for {lesson_id}")
            return jsonify(response), 200

        except Exception as e:
            logger.error(f"Error getting lesson preview: {str(e)}")
            return jsonify({'error': str(e)}), 500

    return _get_lesson_preview()


# Helper functions for STEM lesson plan parsing
def extract_list_items(text):
    """Extract list items from text (bullets, numbers, etc.)"""
    lines = text.split('\n')
    items = []

    for line in lines:
        line = line.strip()
        # Match various list formats
        if re.match(r'^[-*•]\s+', line) or re.match(r'^\d+\.\s+', line) or line.startswith('- '):
            # Clean the line
            clean_line = re.sub(r'^[-*•\d+\.]\s*', '', line).strip()
            if clean_line and not clean_line.upper().startswith('LEARNING') and not clean_line.upper().startswith('FUN FACTS'):
                items.append(clean_line)

    return items if items else [text.strip()]


def extract_numbered_items(text):
    """Extract numbered items from text"""
    # Look for numbered items (1., 2., etc.)
    pattern = r'(\d+)\.\s+(.*?)(?=\d+\.|$)'
    matches = re.findall(pattern, text, re.DOTALL)

    if matches:
        return [match[1].strip() for match in matches]
    else:
        # Fallback to line-by-line extraction
        return extract_list_items(text)


def extract_formulas(text):
    """Extract mathematical formulas from text"""
    lines = text.split('\n')
    formulas = []

    for line in lines:
        line = line.strip()
        # Look for formula patterns
        if ':' in line and not line.upper().startswith('KEY FORMULAS'):
            formula_parts = line.split(':', 1)
            if len(formula_parts) == 2:
                formula_name = formula_parts[0].strip()
                formula_expr = formula_parts[1].strip()
                if formula_expr:
                    formulas.append(f"{formula_name}: {formula_expr}")
        elif re.match(r'^\d+\.\s+', line):
            clean_line = re.sub(r'^\d+\.\s*', '', line).strip()
            if clean_line and not clean_line.upper().startswith('KEY FORMULAS'):
                formulas.append(clean_line)

    return formulas if formulas else [text.strip()]


def extract_worked_examples(text):
    """Extract worked examples with their solutions"""
    # Split by "Example" keyword
    example_pattern = r'Example\s+\d+[:\s]*(.*?)(?=Example\s+\d+|$)'
    matches = re.findall(example_pattern, text, re.DOTALL | re.IGNORECASE)

    if matches:
        examples = []
        for i, match in enumerate(matches, 1):
            example_text = match.strip()
            if example_text:
                examples.append(f"Example {i}: {example_text}")
        return examples
    else:
        # Fallback to section-based extraction
        return extract_numbered_items(text)


def parse_stem_lesson_content(content, topic, subject, features, content_type='calculation'):
    """Parse the generated content into structured lesson plan data"""
    lesson_data = {}

    # More robust section splitting - match numbered sections like "1. TITLE" or "## TITLE"
    # Also handle cases where the AI might use different numbering
    section_headers = [
        'LEARNING OBJECTIVES', 'OBJECTIVES',
        'INSPIRATIONAL QUOTE', 'QUOTE',
        'KEY FORMULAS', 'KEY CONCEPTS', 'FORMULAS',
        'STEP-BY-STEP',
        'LESSON NOTES',
        'WORKED EXAMPLES', 'EXAMPLES', 'ILLUSTRATIVE EXAMPLES',
        'PRACTICE PROBLEMS', 'PRACTICE', 'REVIEW QUESTIONS',
        'REAL-WORLD APPLICATIONS', 'REAL WORLD APPLICATIONS', 'APPLICATIONS',
        'ASSESSMENT METHODS', 'ASSESSMENT',
        'FUN FACTS',
        'VISUAL AIDS',
        'GRAPHS AND VISUAL AIDS',
    ]

    # Build a regex pattern that splits on any of the known section headers
    # Match lines like "5. LESSON NOTES" or "LESSON NOTES:" or "## LESSON NOTES"
    header_pattern = '|'.join(re.escape(h) for h in section_headers)
    split_pattern = rf'\n(?=\d+\.\s*(?:{header_pattern}))'
    sections = re.split(split_pattern, content, flags=re.IGNORECASE)

    # If splitting produced very few sections, try alternative split
    if len(sections) < 4:
        # Try splitting on any numbered header
        sections = re.split(r'\n(?=\d+\.\s+[A-Z])', content)

    # If still too few sections, try to split on common patterns
    if len(sections) < 4:
        alt_pattern = rf'\n(?=(?:{header_pattern})\s*[:\n])'
        sections = re.split(alt_pattern, content, flags=re.IGNORECASE)

    for section in sections:
        section = section.strip()
        if not section:
            continue

        section_upper = section.upper()

        # Parse lesson notes - check FIRST to avoid matching "APPLICATIONS" in notes text
        if 'LESSON NOTES' in section_upper:
            notes_text = re.sub(r'^\d+\.\s*LESSON NOTES\s*(?:\([^)]*\))?\s*[:\s]*', '', section, flags=re.IGNORECASE)
            lesson_data['lesson_notes'] = notes_text.strip()

        # Parse objectives
        elif 'LEARNING OBJECTIVES' in section_upper or (
            'OBJECTIVES' in section_upper and 'LEARNING' in section_upper[:50].upper()
        ):
            objectives = extract_list_items(section)
            lesson_data['objectives'] = objectives

        # Parse quote
        elif 'INSPIRATIONAL QUOTE' in section_upper or (
            'QUOTE' in section_upper and len(section) < 500
        ):
            quote_text = re.sub(r'^\d+\.\s*INSPIRATIONAL QUOTE[:\s]*', '', section, flags=re.IGNORECASE)
            lesson_data['quote'] = quote_text.strip().strip('"').strip("'")

        # Parse key formulas/concepts
        elif 'KEY FORMULAS' in section_upper or 'KEY CONCEPTS' in section_upper:
            formulas = extract_formulas(section)
            lesson_data['key_formulas'] = formulas

        # Parse step-by-step method
        elif 'STEP-BY-STEP' in section_upper:
            steps = extract_numbered_items(section)
            lesson_data['step_by_step'] = steps

        # Parse worked examples / illustrative examples
        elif 'WORKED EXAMPLES' in section_upper or (
            'EXAMPLES' in section_upper and 'WORKED' in section_upper[:50]
        ) or 'ILLUSTRATIVE EXAMPLES' in section_upper:
            examples = extract_worked_examples(section)
            lesson_data['worked_examples'] = examples

        # Parse practice problems / review questions
        elif 'PRACTICE PROBLEMS' in section_upper or (
            'PRACTICE' in section_upper and 'PROBLEM' in section_upper
        ) or 'REVIEW QUESTIONS' in section_upper:
            problems = extract_numbered_items(section)
            lesson_data['practice_problems'] = problems

        # Parse real-world applications
        elif 'REAL-WORLD' in section_upper or 'REAL WORLD' in section_upper:
            applications_text = re.sub(
                r'^\d+\.\s*REAL[- ]WORLD APPLICATIONS\s*(?:\([^)]*\))?\s*[:\s]*',
                '', section, flags=re.IGNORECASE
            )
            lesson_data['real_world_applications'] = applications_text.strip()

        # Parse assessment
        elif 'ASSESSMENT' in section_upper:
            assessment_text = re.sub(r'^\d+\.\s*ASSESSMENT\s*(?:METHODS)?\s*[:\s]*', '', section, flags=re.IGNORECASE)
            lesson_data['assessment'] = assessment_text.strip()

        # Parse fun facts
        elif 'FUN FACTS' in section_upper:
            facts = extract_list_items(section)
            lesson_data['fun_facts'] = facts

        # Parse visual aids
        elif 'VISUAL AIDS' in section_upper:
            aids = extract_list_items(section)
            lesson_data['visual_aids'] = aids

    # Safety check: if lesson_notes is still empty, try to extract it from any section
    # that may have gotten merged with real_world_applications
    if not lesson_data.get('lesson_notes') and lesson_data.get('real_world_applications'):
        rwa = lesson_data['real_world_applications']
        # Check if LESSON NOTES content got merged into real_world_applications
        notes_match = re.search(r'(?:\d+\.\s*)?LESSON NOTES\s*(?:\([^)]*\))?\s*[:\s]*(.*)', rwa, re.IGNORECASE | re.DOTALL)
        if notes_match:
            lesson_data['lesson_notes'] = notes_match.group(1).strip()
            # Remove the lesson notes from real_world_applications
            lesson_data['real_world_applications'] = rwa[:notes_match.start()].strip()

    # Safety check: if real_world_applications has lesson notes merged in
    if lesson_data.get('real_world_applications'):
        rwa = lesson_data['real_world_applications']
        if 'LESSON NOTES' in rwa.upper():
            parts = re.split(r'(?:\d+\.\s*)?LESSON NOTES', rwa, flags=re.IGNORECASE)
            lesson_data['real_world_applications'] = parts[0].strip()
            if len(parts) > 1 and not lesson_data.get('lesson_notes'):
                notes = re.sub(r'^\s*(?:\([^)]*\))?\s*[:\s]*', '', parts[1])
                lesson_data['lesson_notes'] = notes.strip()

    # For conceptual content, remove step-by-step if it was accidentally generated
    # and store content_type so frontends can adapt rendering
    lesson_data['content_type'] = content_type
    if content_type == 'conceptual':
        lesson_data.pop('step_by_step', None)

    return lesson_data


def generate_physics_motion_data(initial_velocity=0, acceleration=4, time_max=5, num_points=11):
    """
    Dynamically generate physics motion graph data using kinematic equations.
    s = ut + 0.5at² (displacement)
    v = u + at (velocity)
    """
    import math

    time_step = time_max / (num_points - 1)
    displacement_data = []
    velocity_data = []
    acceleration_data = []
    distance_data = []

    total_distance = 0
    prev_displacement = 0

    for i in range(num_points):
        t = round(i * time_step, 2)

        # Calculate using kinematic equations
        # s = ut + 0.5at²
        displacement = initial_velocity * t + 0.5 * acceleration * (t ** 2)
        # v = u + at
        velocity = initial_velocity + acceleration * t
        # a = constant
        acc = acceleration

        # Distance (always positive, cumulative)
        if i > 0:
            total_distance += abs(displacement - prev_displacement)
        prev_displacement = displacement

        displacement_data.append({'x': t, 'y': round(displacement, 2)})
        velocity_data.append({'x': t, 'y': round(velocity, 2)})
        acceleration_data.append({'x': t, 'y': round(acc, 2)})
        distance_data.append({'x': t, 'y': round(total_distance, 2)})

    return {
        'displacement': displacement_data,
        'velocity': velocity_data,
        'acceleration': acceleration_data,
        'distance': distance_data,
        'params': {
            'initial_velocity': initial_velocity,
            'acceleration': acceleration,
            'time_max': time_max
        }
    }


def generate_projectile_data(initial_velocity=20, angle=45, g=9.8, num_points=21):
    """
    Dynamically generate projectile motion trajectory data.
    x = v₀cosθ × t
    y = v₀sinθ × t - 0.5gt²
    """
    import math

    angle_rad = math.radians(angle)
    vx = initial_velocity * math.cos(angle_rad)
    vy = initial_velocity * math.sin(angle_rad)

    # Time of flight: t = 2v₀sinθ/g
    time_of_flight = (2 * vy) / g
    time_step = time_of_flight / (num_points - 1)

    trajectory_data = []
    max_height = 0
    range_distance = 0

    for i in range(num_points):
        t = i * time_step
        x = vx * t
        y = vy * t - 0.5 * g * (t ** 2)

        if y >= 0:  # Only include points above ground
            trajectory_data.append({'x': round(x, 2), 'y': round(max(0, y), 2)})
            if y > max_height:
                max_height = y
            range_distance = x

    return {
        'trajectory': trajectory_data,
        'params': {
            'initial_velocity': initial_velocity,
            'angle': angle,
            'max_height': round(max_height, 2),
            'range': round(range_distance, 2),
            'time_of_flight': round(time_of_flight, 2)
        }
    }


def generate_wave_data(amplitude=1, wavelength=2, num_points=51):
    """
    Dynamically generate sinusoidal wave data.
    y = A sin(2πx/λ)
    """
    import math

    wave_data = []
    x_max = 2 * wavelength  # Show 2 complete wavelengths

    for i in range(num_points):
        x = (i / (num_points - 1)) * x_max
        y = amplitude * math.sin(2 * math.pi * x / wavelength)
        wave_data.append({'x': round(x, 3), 'y': round(y, 3)})

    return {
        'wave': wave_data,
        'params': {
            'amplitude': amplitude,
            'wavelength': wavelength,
            'period': wavelength,  # For spatial wave
            'frequency': 1 / wavelength
        }
    }


def generate_free_fall_data(initial_velocity=0, g=9.8, time_max=5, num_points=11):
    """
    Dynamically generate free fall motion data.
    v = u + gt (velocity increases linearly)
    s = ut + 0.5gt² (displacement is parabolic)
    """
    time_step = time_max / (num_points - 1)
    velocity_data = []
    displacement_data = []

    for i in range(num_points):
        t = round(i * time_step, 2)
        v = initial_velocity + g * t
        s = initial_velocity * t + 0.5 * g * (t ** 2)

        velocity_data.append({'x': t, 'y': round(v, 2)})
        displacement_data.append({'x': t, 'y': round(s, 2)})

    return {
        'velocity': velocity_data,
        'displacement': displacement_data,
        'params': {
            'initial_velocity': initial_velocity,
            'g': g,
            'time_max': time_max
        }
    }


def generate_shm_data(amplitude=2, period=4, num_points=51):
    """
    Dynamically generate Simple Harmonic Motion data.
    x = A cos(ωt) where ω = 2π/T
    v = -Aω sin(ωt)
    a = -Aω² cos(ωt)
    """
    import math

    omega = 2 * math.pi / period
    t_max = 2 * period  # Show 2 complete oscillations

    displacement_data = []
    velocity_data = []
    acceleration_data = []

    for i in range(num_points):
        t = (i / (num_points - 1)) * t_max
        x = amplitude * math.cos(omega * t)
        v = -amplitude * omega * math.sin(omega * t)
        a = -amplitude * (omega ** 2) * math.cos(omega * t)

        displacement_data.append({'x': round(t, 3), 'y': round(x, 3)})
        velocity_data.append({'x': round(t, 3), 'y': round(v, 3)})
        acceleration_data.append({'x': round(t, 3), 'y': round(a, 3)})

    return {
        'displacement': displacement_data,
        'velocity': velocity_data,
        'acceleration': acceleration_data,
        'params': {
            'amplitude': amplitude,
            'period': period,
            'angular_frequency': round(omega, 3),
            'max_velocity': round(amplitude * omega, 3),
            'max_acceleration': round(amplitude * omega ** 2, 3)
        }
    }


def generate_subject_graphs(topic, subject, grade_level):
    """Generate appropriate graphs based on the topic and subject with dynamic data"""
    graphs = []
    topic_lower = topic.lower()

    # Math-specific graphs
    if subject == 'mathematics':
        if any(keyword in topic_lower for keyword in ['quadratic', 'parabola', 'function']):
            # Generate quadratic data dynamically
            quad_data = []
            for x in range(-5, 6):
                quad_data.append({'x': x, 'y': x**2})
            graphs.append({
                'title': f'Graph of {topic}',
                'type': 'quadratic',
                'graph_type': 'math_function',
                'x_label': 'x',
                'y_label': 'y = x²',
                'data_points': quad_data,
                'formula': 'y = x²',
                'description': f'Visual representation of {topic} showing key features like vertex, axis of symmetry, and intercepts.',
                'key_features': ['Vertex at (0, 0)', 'Axis of symmetry: x = 0', 'Parabola opens upward']
            })
        elif any(keyword in topic_lower for keyword in ['linear', 'slope', 'line']):
            linear_data = []
            for x in range(-5, 6):
                linear_data.append({'x': x, 'y': 2*x + 3})
            graphs.append({
                'title': f'Linear Function Example',
                'type': 'linear',
                'graph_type': 'math_function',
                'x_label': 'x',
                'y_label': 'y = 2x + 3',
                'data_points': linear_data,
                'formula': 'y = 2x + 3',
                'gradient_info': 'Gradient (slope) = 2',
                'description': f'Graph showing {topic} with slope and y-intercept clearly marked.',
                'key_features': ['Slope = 2', 'Y-intercept = 3', 'X-intercept = -1.5']
            })
        elif any(keyword in topic_lower for keyword in ['exponential', 'growth', 'decay']):
            exp_data = []
            for x in range(-3, 6):
                exp_data.append({'x': x, 'y': round(2**x, 3)})
            graphs.append({
                'title': f'Exponential Function',
                'type': 'exponential',
                'graph_type': 'math_function',
                'x_label': 'x',
                'y_label': 'y = 2ˣ',
                'data_points': exp_data,
                'formula': 'y = 2ˣ',
                'description': f'Exponential function demonstrating {topic} behavior.',
                'key_features': ['Passes through (0, 1)', 'Horizontal asymptote at y = 0', 'Rapid growth for x > 0']
            })
        elif any(keyword in topic_lower for keyword in ['trigonometry', 'sine', 'cosine', 'tan']):
            import math
            trig_data = []
            for i in range(51):
                x = -2 * math.pi + (i / 50) * 4 * math.pi
                trig_data.append({'x': round(x, 3), 'y': round(math.sin(x), 3)})
            graphs.append({
                'title': f'Trigonometric Functions',
                'type': 'trigonometric',
                'graph_type': 'math_function',
                'x_label': 'x (radians)',
                'y_label': 'y = sin(x)',
                'data_points': trig_data,
                'formula': 'y = sin(x)',
                'description': f'Graph showing {topic} with period, amplitude, and key values marked.',
                'key_features': ['Amplitude = 1', 'Period = 2π', 'Passes through origin']
            })

    # Physics-specific graphs - Limited to 2 graphs based on examples
    elif subject == 'physics':
        if any(keyword in topic_lower for keyword in ['motion', 'velocity', 'speed', 'acceleration', 'kinematics', 'displacement', 'distance']):
            # Generate dynamic motion data
            motion_data = generate_physics_motion_data(initial_velocity=0, acceleration=4, time_max=5)

            # Graph 1: Displacement-Time Graph (for basic example)
            graphs.append({
                'title': 'Displacement-Time Graph (s-t)',
                'type': 'displacement_time',
                'graph_type': 'physics_motion',
                'x_label': 'Time t (s)',
                'y_label': 'Displacement s (m)',
                'data_points': motion_data['displacement'],
                'formula': 's = ut + (1/2)at² = 0 + (1/2)(4)t² = 2t²',
                'gradient_info': 'Gradient = Velocity (v = ds/dt = 4t)',
                'parameters': motion_data['params'],
                'description': 'Shows how displacement changes with time. The gradient at any point gives the instantaneous velocity.',
                'key_features': [
                    'Gradient at any point = instantaneous velocity',
                    'Curved line indicates acceleration is present'
                ]
            })

            # Graph 2: Velocity-Time Graph (for advanced example)
            graphs.append({
                'title': 'Velocity-Time Graph (v-t)',
                'type': 'velocity_time',
                'graph_type': 'physics_motion',
                'x_label': 'Time t (s)',
                'y_label': 'Velocity v (m/s)',
                'data_points': motion_data['velocity'],
                'formula': 'v = u + at = 0 + 4t = 4t',
                'gradient_info': 'Gradient = Acceleration (a = dv/dt = 4 m/s²)',
                'area_info': 'Area under curve = Displacement',
                'parameters': motion_data['params'],
                'description': 'Shows how velocity changes with time. The gradient gives acceleration, and the area under the curve gives total displacement.',
                'key_features': [
                    'Gradient = acceleration (4 m/s²)',
                    'Area under curve = displacement'
                ]
            })
            # Only 2 graphs for motion topics - removed acceleration-time and distance-time

        elif any(keyword in topic_lower for keyword in ['projectile', 'trajectory', 'parabolic']):
            proj_data = generate_projectile_data(initial_velocity=20, angle=45)
            graphs.append({
                'title': 'Projectile Motion Trajectory',
                'type': 'projectile',
                'graph_type': 'physics_motion',
                'x_label': 'Horizontal Distance x (m)',
                'y_label': 'Vertical Height y (m)',
                'data_points': proj_data['trajectory'],
                'formula': 'y = x tan(θ) - gx²/(2v₀²cos²θ)',
                'parameters': proj_data['params'],
                'description': f"Parabolic path of a projectile. Initial velocity: {proj_data['params']['initial_velocity']} m/s at {proj_data['params']['angle']}°",
                'key_features': [
                    f"Maximum height: {proj_data['params']['max_height']} m",
                    f"Range: {proj_data['params']['range']} m",
                    f"Time of flight: {proj_data['params']['time_of_flight']} s",
                    'Horizontal velocity remains constant',
                    'Vertical motion affected by gravity'
                ]
            })

        elif any(keyword in topic_lower for keyword in ['free fall', 'gravity', 'falling']):
            fall_data = generate_free_fall_data(initial_velocity=0, g=9.8)
            graphs.append({
                'title': 'Free Fall Velocity-Time Graph',
                'type': 'free_fall_velocity',
                'graph_type': 'physics_motion',
                'x_label': 'Time t (s)',
                'y_label': 'Velocity v (m/s)',
                'data_points': fall_data['velocity'],
                'formula': 'v = u + gt = 0 + 9.8t',
                'gradient_info': 'Gradient = g = 9.8 m/s² (acceleration due to gravity)',
                'parameters': fall_data['params'],
                'description': 'Velocity-time graph for an object in free fall, showing constant acceleration due to gravity.',
                'key_features': [
                    'Constant gradient = g = 9.8 m/s²',
                    'Velocity increases linearly with time',
                    'Starting from rest (u = 0)',
                    'Air resistance ignored'
                ]
            })
            graphs.append({
                'title': 'Free Fall Displacement-Time Graph',
                'type': 'free_fall_displacement',
                'graph_type': 'physics_motion',
                'x_label': 'Time t (s)',
                'y_label': 'Displacement s (m)',
                'data_points': fall_data['displacement'],
                'formula': 's = ut + (1/2)gt² = (1/2)(9.8)t² = 4.9t²',
                'gradient_info': 'Gradient = Instantaneous velocity = gt',
                'parameters': fall_data['params'],
                'description': 'Displacement-time graph showing parabolic motion during free fall.',
                'key_features': [
                    'Parabolic curve (quadratic relationship)',
                    'Gradient increases with time (velocity increasing)',
                    's ∝ t² for motion from rest',
                    'Steeper curve = higher velocity'
                ]
            })

        elif any(keyword in topic_lower for keyword in ['wave', 'oscillation', 'frequency', 'amplitude', 'wavelength']):
            wave_data = generate_wave_data(amplitude=2, wavelength=4)
            graphs.append({
                'title': 'Transverse Wave Displacement Graph',
                'type': 'wave',
                'graph_type': 'physics_wave',
                'x_label': 'Position x (m)',
                'y_label': 'Displacement y (m)',
                'data_points': wave_data['wave'],
                'formula': 'y = A sin(2πx/λ) = 2 sin(πx/2)',
                'parameters': wave_data['params'],
                'description': 'Sinusoidal wave showing amplitude, wavelength, and periodic nature.',
                'key_features': [
                    f"Amplitude (A) = {wave_data['params']['amplitude']} m",
                    f"Wavelength (λ) = {wave_data['params']['wavelength']} m",
                    'Crest = maximum positive displacement',
                    'Trough = maximum negative displacement'
                ]
            })

        elif any(keyword in topic_lower for keyword in ['shm', 'simple harmonic', 'pendulum', 'spring', 'oscillat']):
            shm_data = generate_shm_data(amplitude=2, period=4)
            graphs.append({
                'title': 'SHM Displacement-Time Graph',
                'type': 'shm_displacement',
                'graph_type': 'physics_wave',
                'x_label': 'Time t (s)',
                'y_label': 'Displacement x (m)',
                'data_points': shm_data['displacement'],
                'formula': 'x = A cos(ωt) = 2 cos(πt/2)',
                'parameters': shm_data['params'],
                'description': 'Displacement varies sinusoidally with time in simple harmonic motion.',
                'key_features': [
                    f"Amplitude = {shm_data['params']['amplitude']} m",
                    f"Period = {shm_data['params']['period']} s",
                    f"Angular frequency ω = {shm_data['params']['angular_frequency']} rad/s",
                    'Starts at maximum displacement'
                ]
            })
            graphs.append({
                'title': 'SHM Velocity-Time Graph',
                'type': 'shm_velocity',
                'graph_type': 'physics_wave',
                'x_label': 'Time t (s)',
                'y_label': 'Velocity v (m/s)',
                'data_points': shm_data['velocity'],
                'formula': 'v = -Aω sin(ωt)',
                'parameters': shm_data['params'],
                'description': 'Velocity leads displacement by π/2 (90°) in SHM.',
                'key_features': [
                    f"Maximum velocity = {shm_data['params']['max_velocity']} m/s",
                    'Velocity = 0 at maximum displacement',
                    'Maximum velocity at equilibrium position',
                    'Phase difference: 90° ahead of displacement'
                ]
            })

        elif any(keyword in topic_lower for keyword in ['force', 'newton', 'momentum']):
            # Generate impulse data (force varies with time)
            force_data = []
            for i in range(11):
                t = i * 0.5
                # Triangular force profile for collision
                if t <= 2.5:
                    f = 8 * t / 2.5
                else:
                    f = 8 * (5 - t) / 2.5
                force_data.append({'x': t, 'y': round(max(0, f), 2)})

            graphs.append({
                'title': 'Force-Time Graph (Impulse)',
                'type': 'force_time',
                'graph_type': 'physics_force',
                'x_label': 'Time t (s)',
                'y_label': 'Force F (N)',
                'data_points': force_data,
                'formula': 'Impulse J = ∫F dt = Area under curve',
                'area_info': 'Area = Impulse = Change in momentum (Δp)',
                'description': 'Shows how force varies with time during a collision. The area under the curve represents impulse.',
                'key_features': [
                    'Area under curve = Impulse (J = Ft)',
                    'Impulse = Change in momentum (Δp = mv - mu)',
                    'Peak force at center of collision',
                    'Total impulse ≈ 20 N·s'
                ]
            })

    # Chemistry-specific graphs
    elif subject == 'chemistry':
        if any(keyword in topic_lower for keyword in ['reaction', 'rate', 'concentration']):
            graphs.append({
                'title': f'Reaction Rate Graph',
                'type': 'reaction_rate',
                'url': f'/api/math-graph/reaction_{uuid.uuid4()}?type=reaction',
                'description': f'Concentration vs time graph for {topic}.'
            })
        elif any(keyword in topic_lower for keyword in ['ph', 'acid', 'base', 'titration']):
            graphs.append({
                'title': f'pH Curve',
                'type': 'titration',
                'url': f'/api/math-graph/titration_{uuid.uuid4()}?type=titration',
                'description': f'Titration curve showing pH changes for {topic}.'
            })

    # Biology-specific graphs
    elif subject == 'biology':
        if any(keyword in topic_lower for keyword in ['population', 'growth', 'ecology']):
            graphs.append({
                'title': f'Population Growth Curve',
                'type': 'population',
                'url': f'/api/math-graph/population_{uuid.uuid4()}?type=population',
                'description': f'Population dynamics graph for {topic}.'
            })
        elif any(keyword in topic_lower for keyword in ['enzyme', 'reaction', 'substrate']):
            graphs.append({
                'title': f'Enzyme Activity Graph',
                'type': 'enzyme',
                'url': f'/api/math-graph/enzyme_{uuid.uuid4()}?type=enzyme',
                'description': f'Michaelis-Menten curve for enzyme kinetics in {topic}.'
            })

    # General/Statistics graphs
    if any(keyword in topic_lower for keyword in ['statistics', 'data', 'distribution']):
        graphs.append({
            'title': f'Statistical Distribution',
            'type': 'histogram',
            'url': f'/api/math-graph/stats_{uuid.uuid4()}?type=histogram&data=60,65,70,75,80,85,90&bins=7',
            'description': f'Data visualization for {topic} showing distribution patterns.'
        })
    elif any(keyword in topic_lower for keyword in ['probability', 'normal', 'bell curve']):
        graphs.append({
            'title': f'Probability Distribution',
            'type': 'normal',
            'url': f'/api/math-graph/prob_{uuid.uuid4()}?type=normal&mean=0&std=1&x_min=-4&x_max=4',
            'description': f'Normal distribution curve illustrating {topic} concepts.'
        })

    # Add a general coordinate system graph if no specific graph was generated
    if not graphs:
        graphs.append({
            'title': f'Coordinate System for {topic}',
            'type': 'coordinate',
            'url': f'/api/math-graph/coord_{uuid.uuid4()}?type=coordinate&x_min=-10&x_max=10&y_min=-10&y_max=10',
            'description': f'Coordinate plane for plotting and analyzing {topic}.'
        })

    return graphs


def generate_interactive_evaluation(topic, subject, grade_level_text, difficulty, lesson_data, lesson_plan_id):
    """Generate interactive evaluation questions based on lesson content using Claude AI"""
    from auth.models import LessonPlanEvaluation

    # Build context from lesson data
    lesson_context_parts = []
    if lesson_data.get('objectives'):
        lesson_context_parts.append(f"Learning Objectives: {', '.join(lesson_data['objectives'][:4])}")
    if lesson_data.get('key_formulas'):
        lesson_context_parts.append(f"Key Formulas: {', '.join(lesson_data['key_formulas'][:4])}")
    if lesson_data.get('lesson_notes'):
        lesson_context_parts.append(f"Lesson Notes Summary: {lesson_data['lesson_notes'][:500]}")
    if lesson_data.get('step_by_step'):
        lesson_context_parts.append(f"Steps: {', '.join(lesson_data['step_by_step'][:5])}")

    lesson_context = '\n'.join(lesson_context_parts)

    evaluation_prompt = f"""Generate an interactive evaluation for a {subject} lesson on "{topic}" for {grade_level_text} students. Difficulty: {difficulty}.

Lesson Context:
{lesson_context}

You MUST respond with ONLY valid JSON (no markdown, no code blocks, no explanation). Generate exactly 5 questions in this exact JSON structure:

{{
  "questions": [
    {{
      "id": "q1",
      "type": "multiple_choice",
      "question": "A clear question about the topic",
      "options": [
        {{"text": "Option A text", "correct": false, "explanation": "Why this is wrong"}},
        {{"text": "Option B text", "correct": true, "explanation": "Why this is correct"}},
        {{"text": "Option C text", "correct": false, "explanation": "Why this is wrong"}},
        {{"text": "Option D text", "correct": false, "explanation": "Why this is wrong"}}
      ]
    }},
    {{
      "id": "q2",
      "type": "multiple_choice",
      "question": "Another question about the topic",
      "options": [
        {{"text": "Option A", "correct": false, "explanation": "Explanation"}},
        {{"text": "Option B", "correct": false, "explanation": "Explanation"}},
        {{"text": "Option C", "correct": true, "explanation": "Explanation"}},
        {{"text": "Option D", "correct": false, "explanation": "Explanation"}}
      ]
    }},
    {{
      "id": "q3",
      "type": "drag_drop_matching",
      "question": "Match each term with its correct definition",
      "pairs": [
        {{"term": "Term 1", "definition": "Definition 1"}},
        {{"term": "Term 2", "definition": "Definition 2"}},
        {{"term": "Term 3", "definition": "Definition 3"}},
        {{"term": "Term 4", "definition": "Definition 4"}}
      ]
    }},
    {{
      "id": "q4",
      "type": "drag_drop_ordering",
      "question": "Put these steps in the correct order",
      "items": [
        {{"step": "First step description", "order": 1}},
        {{"step": "Second step description", "order": 2}},
        {{"step": "Third step description", "order": 3}},
        {{"step": "Fourth step description", "order": 4}}
      ]
    }},
    {{
      "id": "q5",
      "type": "paragraph",
      "question": "Explain in your own words how [concept] works and provide an example.",
      "rubric": "Student should mention: key concept 1, key concept 2, provide a valid example"
    }}
  ]
}}

REQUIREMENTS:
- Questions must be directly related to the lesson content on "{topic}"
- Multiple choice: exactly 4 options, exactly 1 correct
- Matching: exactly 4 term-definition pairs relevant to the topic
- Ordering: exactly 4 steps in a logical process from the lesson
- Paragraph: open-ended question requiring explanation
- All content appropriate for {grade_level_text} level
- Use proper {subject} terminology
- Output ONLY the JSON, nothing else"""

    try:
        eval_response = anthropic_client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=2500,
            temperature=0.5,
            messages=[{"role": "user", "content": evaluation_prompt}]
        )

        eval_text = eval_response.content[0].text.strip()

        # Clean up response - remove any markdown code blocks if present
        if eval_text.startswith('```'):
            eval_text = re.sub(r'^```(?:json)?\s*', '', eval_text)
            eval_text = re.sub(r'\s*```$', '', eval_text)

        evaluation_json = json.loads(eval_text)

        # Validate structure
        if 'questions' not in evaluation_json or not isinstance(evaluation_json['questions'], list):
            logger.error("Invalid evaluation structure: missing questions array")
            return None

        # Create evaluation record in database
        evaluation_id = str(uuid.uuid4())
        evaluation_record = LessonPlanEvaluation(
            id=evaluation_id,
            lesson_plan_id=lesson_plan_id,
            evaluation_type='interactive',
            questions_json=json.dumps(evaluation_json)
        )
        db.session.add(evaluation_record)
        # Don't commit yet - will be committed with the lesson plan

        # Return data for frontend
        evaluation_json['evaluation_id'] = evaluation_id
        return evaluation_json

    except json.JSONDecodeError as je:
        logger.error(f"Failed to parse evaluation JSON: {str(je)}")
        return None
    except Exception as e:
        logger.error(f"Error generating evaluation: {str(e)}")
        return None


def search_youtube_video(topic, subject):
    """Search for a relevant YouTube educational video on the topic"""
    import urllib.parse
    import urllib.request

    try:
        # Build search query for educational content
        search_query = f"{topic} {subject} lesson tutorial education"
        encoded_query = urllib.parse.quote(search_query)

        # Use YouTube search results page and extract video ID
        search_url = f"https://www.youtube.com/results?search_query={encoded_query}"

        req = urllib.request.Request(
            search_url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept-Language': 'en-US,en;q=0.9'
            }
        )

        with urllib.request.urlopen(req, timeout=8) as response:
            html_content = response.read().decode('utf-8', errors='ignore')

        # Extract video IDs from the search results
        video_ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', html_content)

        if not video_ids:
            # Fallback pattern
            video_ids = re.findall(r'/watch\?v=([a-zA-Z0-9_-]{11})', html_content)

        if not video_ids:
            logger.info(f"No YouTube videos found for topic: {topic}")
            return None

        # Get first unique video ID
        seen = set()
        unique_ids = []
        for vid in video_ids:
            if vid not in seen:
                seen.add(vid)
                unique_ids.append(vid)
            if len(unique_ids) >= 3:
                break

        primary_video_id = unique_ids[0] if unique_ids else None

        if not primary_video_id:
            return None

        return {
            'video_id': primary_video_id,
            'url': f'https://www.youtube.com/watch?v={primary_video_id}',
            'embed_url': f'https://www.youtube.com/embed/{primary_video_id}',
            'search_query': search_query,
            'auto_selected': True,
            'alternative_ids': unique_ids[1:] if len(unique_ids) > 1 else []
        }

    except Exception as e:
        logger.error(f"YouTube search failed: {str(e)}")
        return None


@lesson_plan_bp.route('/api/update-lesson-youtube', methods=['POST'])
def update_lesson_youtube():
    """Allow tutors to update the YouTube video link for a lesson plan"""
    from app import token_required as app_token_required
    from auth.models import MathLessonPlanModel

    @app_token_required
    def _update_youtube(current_user):
        try:
            data = request.get_json()
            lesson_plan_id = data.get('lesson_plan_id')
            youtube_url = data.get('youtube_url', '').strip()

            if not lesson_plan_id:
                return jsonify({'error': 'Missing lesson_plan_id'}), 400

            lesson_plan = MathLessonPlanModel.query.filter_by(
                id=lesson_plan_id,
                user_id=current_user.id
            ).first()

            if not lesson_plan:
                return jsonify({'error': 'Lesson plan not found'}), 404

            # Parse existing content
            content_data = json.loads(lesson_plan.content_json) if lesson_plan.content_json else {}

            if youtube_url:
                # Extract video ID from various YouTube URL formats
                video_id = None
                yt_patterns = [
                    r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
                    r'^([a-zA-Z0-9_-]{11})$'
                ]
                for pattern in yt_patterns:
                    match = re.search(pattern, youtube_url)
                    if match:
                        video_id = match.group(1)
                        break

                if not video_id:
                    return jsonify({'error': 'Invalid YouTube URL format'}), 400

                content_data['youtube_video'] = {
                    'video_id': video_id,
                    'url': f'https://www.youtube.com/watch?v={video_id}',
                    'embed_url': f'https://www.youtube.com/embed/{video_id}',
                    'auto_selected': False,
                    'custom_url': True
                }
            else:
                # Remove YouTube video
                content_data.pop('youtube_video', None)

            lesson_plan.content_json = json.dumps(content_data)
            db.session.commit()

            return jsonify({
                'success': True,
                'youtube_video': content_data.get('youtube_video')
            }), 200

        except Exception as e:
            logger.error(f"Error updating YouTube link: {str(e)}")
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    return _update_youtube()


def topic_requires_calculations(subject, topic):
    """
    Determine whether a topic requires calculation-based content (step-by-step
    solutions, worked numerical examples) or conceptual content (process
    descriptions, explanations, case studies).

    Returns True if the topic is calculation-heavy, False if conceptual.
    """
    topic_lower = topic.lower().strip()

    # Mathematics: virtually all topics are calculation-based
    if subject == 'mathematics':
        return True

    # Physics: most topics are calculation-based, with few conceptual exceptions
    if subject == 'physics':
        conceptual_physics = [
            'history of physics', 'scientific method', 'nature of physics',
            'modern physics overview', 'quantum theory concepts',
            'relativity concepts', 'philosophy of science',
        ]
        for phrase in conceptual_physics:
            if phrase in topic_lower:
                return False
        return True

    # Chemistry: mixed — check for calculation-related keywords
    if subject == 'chemistry':
        calculation_keywords = [
            'stoichiometry', 'mole', 'molar', 'molarity', 'concentration',
            'dilution', 'titration', 'ph ', 'poh', 'equilibrium constant',
            'gas law', 'ideal gas', 'boyle', 'charles', 'avogadro',
            'thermochemistry', 'enthalpy', 'hess', 'calorimetry',
            'reaction rate', 'rate law', 'order of reaction',
            'electrochemistry', 'cell potential', 'nernst',
            'mass percent', 'empirical formula', 'molecular formula',
            'percent composition', 'yield', 'limiting reagent',
            'colligative', 'osmotic pressure', 'boiling point elevation',
            'freezing point depression', 'solubility product',
            'buffer', 'henderson', 'acid-base calculation',
            'half-life', 'radioactive decay', 'nuclear equation',
            'dalton', 'partial pressure',
        ]
        for kw in calculation_keywords:
            if kw in topic_lower:
                return True
        return False

    # Biology: mostly conceptual, with a few quantitative exceptions
    if subject == 'biology':
        calculation_keywords = [
            'punnett', 'hardy-weinberg', 'hardy weinberg',
            'chi-square', 'chi square', 'population growth rate',
            'carrying capacity calculation', 'enzyme kinetics',
            'michaelis', 'lineweaver', 'genetics probability',
            'allele frequency', 'genotype frequency',
            'water potential', 'dilution', 'serial dilution',
            'hemocytometer', 'cell counting',
        ]
        for kw in calculation_keywords:
            if kw in topic_lower:
                return True
        return False

    # General Science: mostly conceptual
    if subject == 'general':
        calculation_keywords = [
            'measurement', 'unit conversion', 'significant figures',
            'scientific notation', 'data analysis', 'graphing data',
            'density calculation', 'speed calculation',
        ]
        for kw in calculation_keywords:
            if kw in topic_lower:
                return True
        return False

    # Fallback: default to calculations for unknown subjects
    return True


@lesson_plan_bp.route('/api/generate-math-lesson-plan', methods=['POST'])
def generate_stem_lesson_plan():
    """Generate comprehensive STEM lesson plans (Math, Physics, Chemistry, Biology, General)"""
    from app import token_required as app_token_required
    from auth.models import MathLessonPlanModel

    @app_token_required
    def _generate_stem_lesson_plan(current_user):
        try:
            data = request.get_json()

            # Extract data from request
            subject = data.get('subject', 'mathematics')
            topic = data.get('topic', '')
            grade_level = data.get('grade_level', '')
            duration = data.get('duration', '50')
            difficulty = data.get('difficulty', 'intermediate')
            objectives = data.get('objectives', '')
            features = data.get('features', {})

            # Validate required fields
            if not all([topic, grade_level]):
                return jsonify({'error': 'Missing required fields: topic and grade_level are required'}), 400

            # Check if Anthropic client is initialized
            if not anthropic_client:
                logger.error("Anthropic client is not initialized. ANTHROPIC_API_KEY may not be set.")
                return jsonify({'error': 'AI service is not configured. Please contact the administrator.'}), 503

            # Create a lesson plan ID
            lesson_plan_id = str(uuid.uuid4())

            # Get grade level text
            grade_level_text = get_grade_level_text(grade_level)

            # Get subject display name
            subject_names = {
                'mathematics': 'Mathematics',
                'physics': 'Physics',
                'chemistry': 'Chemistry',
                'biology': 'Biology',
                'general': 'General Science'
            }
            subject_display = subject_names.get(subject, subject.title())

            # Determine if this topic requires calculations or is conceptual
            needs_calculations = topic_requires_calculations(subject, topic)
            content_type = 'calculation' if needs_calculations else 'conceptual'

            # Build comprehensive STEM-focused prompt adapted to content type
            if needs_calculations:
                # ===== CALCULATION-BASED PROMPT (Math, Physics, calc-heavy Chemistry) =====
                core_prompt = f"""
Create a comprehensive {subject_display} lesson plan on "{topic}" for {grade_level_text} students. Duration: {duration} minutes. Difficulty: {difficulty}.

IMPORTANT: This is a {subject_display.upper()} lesson plan that should focus on:
- Step-by-step problem solving with clear notation
- Worked examples with detailed solutions
- Key formulas, equations, and concepts
- Practice problems with varying difficulty
- Scientific reasoning and logic
- Real-world applications with quantitative analysis

Generate content with proper scientific notation using:
- Superscripts: x^2, x^3, 10^6, etc.
- Subscripts: x_1, x_2, H_2O, CO_2, etc.
- Greek letters: pi, theta, alpha, beta, delta, etc.
- Mathematical symbols: ±, ≤, ≥, ∞, √, etc.
- Units: m^2, cm^3, s^-1, mol/L, J/kg, etc.

Structure the lesson plan as follows:

1. LEARNING OBJECTIVES (3-4 specific, measurable objectives)
Create clear learning objectives that start with "Students will be able to..."

2. INSPIRATIONAL QUOTE
Select a meaningful quote from a famous scientist, mathematician, or expert related to {topic}.

3. KEY FORMULAS/CONCEPTS
List the 4-6 most important formulas, equations, or principles related to {topic}.
Format each as: "Formula/Concept Name: expression or description"

4. STEP-BY-STEP SOLUTION METHOD
Provide a detailed, numbered step-by-step method for solving typical {topic} problems.
Include 5-7 clear steps with explanations.

5. LESSON NOTES (500-700 words)
Write comprehensive lesson notes that serve as study material for students. These notes should:
- Provide a clear, detailed explanation of {topic} suitable for {grade_level_text} students
- Cover the fundamental concepts, definitions, and principles
- Explain the "why" behind the concepts, not just the "what"
- Include relevant examples integrated into the explanation
- Use clear, student-friendly language while maintaining scientific accuracy
- Connect concepts to prior knowledge students may have
- Highlight key terms and their definitions
- Explain common mistakes to avoid
- Build understanding progressively from basic to more complex ideas
The lesson notes should read like a well-written textbook section that students can use for independent study and revision.

6. WORKED EXAMPLES
Create exactly 2 worked examples (one basic, one advanced):

Example 1 (Basic): A straightforward problem applying the core concept directly
Example 2 (Advanced): A more challenging problem requiring deeper understanding

For each example, format the solution with CLEAR LINE BREAKS:
- Problem statement with specific numbers
- Each calculation step on its OWN LINE (use newlines between steps)
- Show the formula, then substitution, then result on SEPARATE LINES
- Final answer with proper units

IMPORTANT FORMATTING: When showing calculations, put each step on a new line like this:
Using the formula: v = u + at
v = 0 + (4)(5)
v = 20 m/s

NOT all on one line like: Using the formula: v = u + at v = 0 + (4)(5) v = 20 m/s

Use plain text notation for fractions: 1/2 instead of HTML fraction tags
Use superscripts like: t^2, x^3, etc.

7. PRACTICE PROBLEMS
Generate 5 practice problems of varying difficulty:
- 2 basic problems (applying direct formulas)
- 2 intermediate problems (requiring multiple steps)
- 1 advanced problem (requiring deeper reasoning)

8. REAL-WORLD APPLICATIONS (300-350 words)
Describe 2-3 concrete real-world applications of {topic} with:
- Specific examples from industry, science, or daily life
- Quantitative aspects and measurements
- Why this concept is important
Keep the real-world applications section between 300-350 words. Format with proper paragraphs.

9. ASSESSMENT METHODS
Describe specific ways to assess student understanding including:
- Formative assessment techniques
- Problem-solving demonstrations
- Common misconceptions to watch for

10. FUN FACTS
Include 2-3 interesting facts related to {topic}.

IMPORTANT: Each section MUST start with its number and title on a new line (e.g., "1. LEARNING OBJECTIVES", "5. LESSON NOTES", "6. WORKED EXAMPLES", etc.). Do NOT merge sections together.
"""
            else:
                # ===== CONCEPTUAL PROMPT (Biology, General, conceptual Chemistry) =====
                core_prompt = f"""
Create a comprehensive {subject_display} lesson plan on "{topic}" for {grade_level_text} students. Duration: {duration} minutes. Difficulty: {difficulty}.

IMPORTANT: This is a {subject_display.upper()} lesson plan that should focus on:
- Clear conceptual explanations and descriptions of processes
- Key terminology, definitions, and principles
- Illustrative examples and case studies (NOT numerical calculations)
- Critical thinking and analysis questions
- Scientific reasoning and understanding
- Real-world connections and relevance

DO NOT include mathematical calculations, numerical problem-solving steps, or formula-based worked examples.
This topic is conceptual in nature and should be taught through explanation, description, and understanding — not through calculations.

Generate content with proper scientific notation where relevant:
- Subscripts for chemical formulas: H_2O, CO_2, etc.
- Greek letters for scientific terms: alpha, beta, etc.
- Standard scientific terminology and nomenclature

Structure the lesson plan as follows:

1. LEARNING OBJECTIVES (3-4 specific, measurable objectives)
Create clear learning objectives that start with "Students will be able to..."
Focus on understanding, explaining, comparing, analyzing, and describing — not calculating.

2. INSPIRATIONAL QUOTE
Select a meaningful quote from a famous scientist or expert related to {topic}.

3. KEY CONCEPTS
List the 4-6 most important concepts, principles, or terms related to {topic}.
Format each as: "Concept Name: clear definition or description"
These should be definitions, principles, and key ideas — NOT mathematical formulas.

4. LESSON NOTES (500-700 words)
Write comprehensive lesson notes that serve as study material for students. These notes should:
- Provide a clear, detailed explanation of {topic} suitable for {grade_level_text} students
- Cover the fundamental concepts, definitions, and principles
- Explain the "why" behind the concepts, not just the "what"
- Describe processes, mechanisms, or phenomena step by step in words
- Include relevant examples integrated into the explanation
- Use clear, student-friendly language while maintaining scientific accuracy
- Connect concepts to prior knowledge students may have
- Highlight key terms and their definitions
- Explain common misconceptions to avoid
- Build understanding progressively from basic to more complex ideas
The lesson notes should read like a well-written textbook section that students can use for independent study and revision.

5. ILLUSTRATIVE EXAMPLES
Create exactly 2 illustrative examples (one basic, one advanced):

Example 1 (Basic): A straightforward scenario that clearly demonstrates the core concept
Example 2 (Advanced): A more complex scenario requiring deeper analysis and understanding

For each example:
- Describe the scenario or case study clearly
- Explain how the concept applies in this context
- Walk through the reasoning or process in a logical sequence
- Highlight the key takeaway or conclusion
Do NOT include numerical calculations or formula substitutions.

6. REVIEW QUESTIONS
Generate 5 review questions of varying difficulty:
- 2 basic questions (recall and understanding)
- 2 intermediate questions (application and analysis)
- 1 advanced question (evaluation or synthesis)
These should be descriptive, analytical, or discussion-based questions — NOT calculation problems.

7. REAL-WORLD APPLICATIONS (300-350 words)
Describe 2-3 concrete real-world applications of {topic} with:
- Specific examples from industry, science, medicine, or daily life
- How this concept impacts the real world
- Why this concept is important to understand
Keep the real-world applications section between 300-350 words. Format with proper paragraphs.

8. ASSESSMENT METHODS
Describe specific ways to assess student understanding including:
- Formative assessment techniques
- Concept-mapping or diagram-based demonstrations
- Common misconceptions to watch for

9. FUN FACTS
Include 2-3 interesting facts related to {topic}.

IMPORTANT: Each section MUST start with its number and title on a new line (e.g., "1. LEARNING OBJECTIVES", "4. LESSON NOTES", "5. ILLUSTRATIVE EXAMPLES", etc.). Do NOT merge sections together.
"""

            # Graphs and visual aids are handled programmatically, not by AI
            if needs_calculations:
                core_prompt += f"""

CONTENT REQUIREMENTS:
- Use precise scientific language and notation
- Include numerical examples with actual calculations
- Show all steps in calculations
- Provide solutions with proper significant figures/decimal places
- Use appropriate units throughout
- Include error analysis or checking methods where applicable

SUBJECT-SPECIFIC GUIDELINES:
"""
            else:
                core_prompt += f"""

CONTENT REQUIREMENTS:
- Use precise scientific language and terminology
- Explain processes, mechanisms, and concepts clearly in words
- Use proper scientific nomenclature
- Include descriptive examples, analogies, and case studies
- Focus on understanding and critical thinking, NOT calculations
- Describe relationships between concepts clearly

SUBJECT-SPECIFIC GUIDELINES:
"""

            # Add subject-specific guidelines
            if subject == 'mathematics':
                core_prompt += """
- Focus on mathematical reasoning, proof techniques, and problem-solving strategies
- Include multiple solution methods where applicable
- Emphasize mathematical connections and patterns
- Use mathematical modeling for real-world problems
"""
            elif subject == 'physics':
                if needs_calculations:
                    core_prompt += """
- Include fundamental physics principles and laws
- Show dimensional analysis and unit conversions
- Emphasize experimental verification and measurement
- Connect mathematical equations to physical phenomena
- Include vector analysis where applicable
"""
                else:
                    core_prompt += """
- Explain fundamental physics principles and laws conceptually
- Emphasize understanding of physical phenomena
- Describe experimental methods and observations
- Connect concepts to everyday experiences
"""
            elif subject == 'chemistry':
                if needs_calculations:
                    core_prompt += """
- Include chemical equations and stoichiometry
- Show molecular and ionic calculations
- Emphasize laboratory safety and experimental procedures
- Use periodic table properties and trends
- Include concentration calculations and reaction rates
"""
                else:
                    core_prompt += """
- Describe chemical processes, structures, and properties clearly
- Explain bonding, reactions, and trends conceptually
- Emphasize laboratory safety and experimental procedures
- Use periodic table properties and trends
- Focus on understanding molecular behavior and chemical principles
- Include diagrams and descriptions of molecular structures
"""
            elif subject == 'biology':
                core_prompt += """
- Describe biological processes and mechanisms in clear detail
- Explain structures and their functions
- Emphasize experimental design and data interpretation
- Include descriptions of biological structures and diagrams
- Connect concepts to ecological and evolutionary frameworks where applicable
- Use analogies to help students understand complex processes
"""
            elif subject == 'general':
                core_prompt += """
- Explain scientific concepts and phenomena clearly
- Emphasize the scientific method and critical thinking
- Use real-world observations and examples
- Include cross-disciplinary connections
- Focus on understanding and analysis over memorization
"""

            core_prompt += f"""

FORMATTING REQUIREMENTS:
- Use clear headings for each section
- Format expressions consistently
- Include proper notation
- Use bullet points for lists
- Separate major concepts clearly
{"- Ensure all calculations are accurate" if needs_calculations else "- Ensure all explanations are scientifically accurate"}

The lesson should be practical, engaging, and rigorous for {grade_level_text} students.
"""

            try:
                # Generate core content
                core_response = anthropic_client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=4000,
                    temperature=0.7,
                    messages=[{"role": "user", "content": core_prompt}]
                )

                core_content = core_response.content[0].text
                logger.info(f"Generated STEM lesson content: {len(core_content)} characters")

                # Parse the generated content into structured sections
                lesson_data = parse_stem_lesson_content(core_content, topic, subject, features, content_type)

                # Generate graphs if requested
                if features.get('autoGraphs', True):
                    lesson_data['graphs'] = generate_subject_graphs(topic, subject, grade_level)

                # Generate interactive evaluation if requested
                if features.get('interactiveEvaluation', False):
                    try:
                        evaluation_data = generate_interactive_evaluation(
                            topic, subject, grade_level_text, difficulty,
                            lesson_data, lesson_plan_id
                        )
                        if evaluation_data:
                            lesson_data['interactive_evaluation'] = evaluation_data
                            logger.info(f"Generated interactive evaluation for lesson plan {lesson_plan_id}")
                    except Exception as eval_error:
                        logger.error(f"Failed to generate interactive evaluation: {str(eval_error)}")
                        # Don't fail the whole request if evaluation generation fails

                # Search for a relevant YouTube video on the topic
                try:
                    youtube_data = search_youtube_video(topic, subject)
                    if youtube_data:
                        lesson_data['youtube_video'] = youtube_data
                        logger.info(f"Found YouTube video for topic: {topic}")
                except Exception as yt_error:
                    logger.error(f"Failed to search YouTube video: {str(yt_error)}")

                # Add metadata including content_type for frontend rendering
                lesson_data.update({
                    'title': f"{topic} - {subject_display} Lesson Plan",
                    'subject': subject,
                    'grade_level': grade_level_text,
                    'duration': f"{duration} minutes",
                    'difficulty': difficulty,
                    'topic': topic,
                    'content_type': content_type
                })

                # Store in database
                stem_lesson_plan = MathLessonPlanModel(
                    id=lesson_plan_id,
                    user_id=current_user.id,
                    title=lesson_data['title'],
                    subject=subject,
                    topic=topic,
                    grade_level=grade_level,
                    duration_minutes=int(duration) if duration.isdigit() else 50,
                    difficulty_level=difficulty,
                    objectives=objectives,
                    content_json=json.dumps(lesson_data),
                    features_enabled=json.dumps(features)
                )

                # Save to database
                db.session.add(stem_lesson_plan)
                db.session.commit()

                logger.info(f"Successfully created STEM lesson plan with ID: {lesson_plan_id}")

                return jsonify({
                    'message': f'{subject_display} lesson plan created successfully',
                    'lesson_plan_id': lesson_plan_id,
                    'lesson_plan': lesson_data
                }), 201

            except Exception as claude_error:
                logger.error(f"Claude API error: {str(claude_error)}")
                db.session.rollback()
                return jsonify({'error': 'Failed to generate lesson plan with Claude API'}), 500

        except Exception as e:
            logger.error(f"STEM lesson plan generation error: {str(e)}")
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    return _generate_stem_lesson_plan()


@lesson_plan_bp.route('/api/generate-more-examples', methods=['POST'])
def generate_more_examples():
    """Generate additional examples for existing lesson plan"""
    from app import token_required as app_token_required

    @app_token_required
    def _generate_more_examples(current_user):
        try:
            data = request.get_json()
            subject = data.get('subject', 'mathematics')
            topic = data.get('topic', '')
            count = data.get('count', 3)

            if not topic:
                return jsonify({'error': 'Topic is required'}), 400

            # Check if Anthropic client is initialized
            if not anthropic_client:
                logger.error("Anthropic client is not initialized. ANTHROPIC_API_KEY may not be set.")
                return jsonify({'error': 'AI service is not configured. Please contact the administrator.'}), 503

            prompt = f"""
Generate {count} additional worked examples for the topic "{topic}" in {subject}.

For each example, provide:
1. Problem statement with specific numbers
2. Complete step-by-step solution
3. Final answer with proper units
4. Brief explanation of the method

Format each example clearly with "Example N:" header.
"""

            try:
                response = anthropic_client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=2000,
                    temperature=0.7,
                    messages=[{"role": "user", "content": prompt}]
                )

                examples_content = response.content[0].text
                examples = extract_worked_examples(examples_content)

                return jsonify({
                    'examples': examples,
                    'count': len(examples)
                }), 200

            except Exception as claude_error:
                logger.error(f"Claude API error: {str(claude_error)}")
                return jsonify({'error': 'Failed to generate examples'}), 500

        except Exception as e:
            logger.error(f"Error generating examples: {str(e)}")
            return jsonify({'error': str(e)}), 500

    return _generate_more_examples()


def generate_url_slug(length=12):
    """Generate a random URL-safe slug"""
    import secrets
    import string
    chars = string.ascii_lowercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))


@lesson_plan_bp.route('/api/publish-lesson-plan/<lesson_id>', methods=['POST'])
def publish_lesson_plan(lesson_id):
    """Publish a lesson plan and generate a shareable URL"""
    from app import token_required as app_token_required
    from auth.models import MathLessonPlanModel, PublishedLessonPlan

    @app_token_required
    def _publish_lesson_plan(current_user):
        try:
            # Get the lesson plan
            lesson_plan = MathLessonPlanModel.query.filter_by(
                id=lesson_id,
                user_id=current_user.id
            ).first()

            if not lesson_plan:
                return jsonify({'error': 'Lesson plan not found'}), 404

            # Check if already published
            existing_published = PublishedLessonPlan.query.filter_by(
                lesson_plan_id=lesson_id,
                is_active=True
            ).first()

            if existing_published:
                # Return existing public URL
                base_url = os.getenv('BASE_URL', 'https://deciph.ai.deciphersacad.online')
                public_url = f"{base_url}/shared-lesson/{existing_published.public_url_slug}"
                return jsonify({
                    'message': 'Lesson plan already published',
                    'public_url': public_url,
                    'slug': existing_published.public_url_slug
                }), 200

            # Generate unique slug
            slug = generate_url_slug()
            while PublishedLessonPlan.query.filter_by(public_url_slug=slug).first():
                slug = generate_url_slug()

            # Create published lesson plan entry
            published = PublishedLessonPlan(
                lesson_plan_id=lesson_id,
                public_url_slug=slug
            )

            db.session.add(published)
            db.session.commit()

            base_url = os.getenv('BASE_URL', 'https://deciph.ai.deciphersacad.online')
            public_url = f"{base_url}/shared-lesson/{slug}"

            logger.info(f"Published lesson plan {lesson_id} with slug {slug}")

            return jsonify({
                'message': 'Lesson plan published successfully',
                'public_url': public_url,
                'slug': slug
            }), 201

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error publishing lesson plan: {str(e)}")
            return jsonify({'error': str(e)}), 500

    return _publish_lesson_plan()


@lesson_plan_bp.route('/api/shared-lesson/<slug>', methods=['GET'])
def get_shared_lesson(slug):
    """Get a published lesson plan by its public URL slug (no auth required)"""
    from auth.models import MathLessonPlanModel, PublishedLessonPlan

    try:
        # Find the published lesson
        published = PublishedLessonPlan.query.filter_by(
            public_url_slug=slug,
            is_active=True
        ).first()

        if not published:
            return jsonify({'error': 'Lesson not found or no longer available'}), 404

        # Get the lesson plan
        lesson_plan = MathLessonPlanModel.query.filter_by(id=published.lesson_plan_id).first()

        if not lesson_plan:
            return jsonify({'error': 'Lesson plan data not found'}), 404

        # Increment access count
        published.access_count += 1
        db.session.commit()

        # Parse content JSON
        content_data = {}
        if lesson_plan.content_json:
            try:
                content_data = json.loads(lesson_plan.content_json)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse content_json for lesson {lesson_plan.id}")
                content_data = {}

        # Get interactive evaluation if it exists
        evaluation_data = content_data.get('interactive_evaluation', None)
        if not evaluation_data:
            # Try to find evaluation from the evaluations table
            try:
                from auth.models import LessonPlanEvaluation
                evaluation_record = LessonPlanEvaluation.query.filter_by(
                    lesson_plan_id=lesson_plan.id
                ).order_by(LessonPlanEvaluation.created_at.desc()).first()
                if evaluation_record:
                    evaluation_data = json.loads(evaluation_record.questions_json)
                    evaluation_data['evaluation_id'] = evaluation_record.id
            except Exception as eval_err:
                logger.error(f"Error fetching evaluation: {str(eval_err)}")

        # Build response with full lesson plan data
        lesson_data = {
            'id': lesson_plan.id,
            'title': lesson_plan.title,
            'topic': lesson_plan.topic,
            'subject': getattr(lesson_plan, 'subject', 'mathematics'),
            'grade_level': lesson_plan.grade_level,
            'duration': f"{lesson_plan.duration_minutes} minutes" if lesson_plan.duration_minutes else '50 minutes',
            'difficulty': getattr(lesson_plan, 'difficulty_level', 'intermediate'),
            'created_at': lesson_plan.created_at.isoformat() if lesson_plan.created_at else None,
            # Include all content fields
            'objectives': content_data.get('objectives', []),
            'quote': content_data.get('quote', ''),
            'key_formulas': content_data.get('key_formulas', []),
            'step_by_step': content_data.get('step_by_step', []),
            'worked_examples': content_data.get('worked_examples', []),
            'practice_problems': content_data.get('practice_problems', []),
            'real_world_applications': content_data.get('real_world_applications', ''),
            'assessment': content_data.get('assessment', ''),
            'fun_facts': content_data.get('fun_facts', []),
            'lesson_notes': content_data.get('lesson_notes', ''),
            'visual_aids': content_data.get('visual_aids', []),
            'graphs': content_data.get('graphs', []),
            'interactive_evaluation': evaluation_data,
            'youtube_video': content_data.get('youtube_video', None),
            # Full content for backward compatibility
            'content': content_data
        }

        return jsonify({
            'success': True,
            'lesson_plan': lesson_data,
            'access_count': published.access_count,
            'published_at': published.published_at.isoformat() if published.published_at else None
        }), 200

    except Exception as e:
        logger.error(f"Error fetching shared lesson: {str(e)}")
        return jsonify({'error': str(e)}), 500


@lesson_plan_bp.route('/shared-lesson/<slug>')
def serve_shared_lesson_page(slug):
    """Serve the shared lesson view page"""
    return send_from_directory('.', 'shared-lesson.html')


@lesson_plan_bp.route('/api/unpublish-lesson-plan/<lesson_id>', methods=['POST'])
def unpublish_lesson_plan(lesson_id):
    """Unpublish a lesson plan"""
    from app import token_required as app_token_required
    from auth.models import MathLessonPlanModel, PublishedLessonPlan

    @app_token_required
    def _unpublish_lesson_plan(current_user):
        try:
            # Verify ownership
            lesson_plan = MathLessonPlanModel.query.filter_by(
                id=lesson_id,
                user_id=current_user.id
            ).first()

            if not lesson_plan:
                return jsonify({'error': 'Lesson plan not found'}), 404

            # Deactivate all published versions
            PublishedLessonPlan.query.filter_by(
                lesson_plan_id=lesson_id
            ).update({'is_active': False})

            db.session.commit()

            logger.info(f"Unpublished lesson plan {lesson_id}")

            return jsonify({
                'message': 'Lesson plan unpublished successfully'
            }), 200

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error unpublishing lesson plan: {str(e)}")
            return jsonify({'error': str(e)}), 500

    return _unpublish_lesson_plan()


@lesson_plan_bp.route('/api/generate-example-steps', methods=['POST'])
def generate_example_steps():
    """Generate step-by-step solutions for an example problem (public - used by shared lessons)"""
    try:
        if not anthropic_client:
            return jsonify({
                'error': 'AI service not available',
                'steps': []
            }), 503

        data = request.get_json()
        example_text = data.get('example_text', '')
        topic = data.get('topic', 'mathematics')
        request_type = data.get('request_type', 'step_by_step_solution')

        if not example_text:
            return jsonify({
                'error': 'No example text provided',
                'steps': []
            }), 400

        # Limit example text length to prevent abuse
        if len(example_text) > 2000:
            example_text = example_text[:2000]

        # Generate step-by-step solution using AI
        prompt = f"""Analyze this problem and provide a detailed step-by-step solution:

Problem: {example_text}
Topic: {topic}

Provide exactly 3-4 clear steps to solve this problem. For each step, provide:
1. A brief description of what we're doing in this step
2. The calculation or work involved
3. The result of this step

Format your response as JSON array with this structure:
[
  {{
    "description": "Identify the given values",
    "work": "Initial velocity u = 0 m/s, acceleration a = 4 m/s², time t = 5 s",
    "answer": "Given: u = 0, a = 4 m/s², t = 5 s"
  }},
  {{
    "description": "Apply the kinematic equation",
    "work": "Using v = u + at\\nv = 0 + (4)(5)\\nv = 20 m/s",
    "answer": "v = 20 m/s"
  }}
]

Use \\n for line breaks in the work section to show each step of calculation on a new line.
Return ONLY valid JSON, no other text."""

        try:
            response = anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1500,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text.strip()

            # Clean up the response if needed
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]

            steps = json.loads(response_text)

            return jsonify({
                'success': True,
                'steps': steps
            }), 200

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI steps response: {e}")
            return jsonify({
                'success': True,
                'steps': [
                    {
                        'description': 'Solution',
                        'work': example_text,
                        'answer': 'See worked solution above'
                    }
                ]
            }), 200

    except Exception as e:
        logger.error(f"Error generating example steps: {str(e)}")
        return jsonify({
            'error': str(e),
            'steps': []
        }), 500


def register_lesson_plan_blueprint(app):
    """Register the lesson plan blueprint with the Flask app"""
    app.register_blueprint(lesson_plan_bp)
    logger.info("Lesson Plan blueprint registered successfully")
    return lesson_plan_bp


# For backwards compatibility
def register_blueprint(app, db=None):
    """Legacy registration function"""
    return register_lesson_plan_blueprint(app)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from .models import UserRegister, Lesson , LessonContent
from .forms import RegisterForm, LessonForm , LessonContentForm


def landing_page_view(request):
    return render(request, 'index.html')

# ---------------- Authentication ----------------

# Register
def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.password_hash = form.cleaned_data["password_hash"]
            user.save()
            messages.success(request, "Registration successful! Please login.")
            return redirect("login")
    else:
        form = RegisterForm()
    return render(request, "register.html", {"form": form})

# Login
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        try:
            user = UserRegister.objects.get(username=username)
            if check_password(password, user.password_hash):
                # Store session data
                request.session["user_id"] = user.user_id
                request.session["username"] = user.username
                request.session["usertype"] = user.usertype

                if user.usertype == "student":
                    return redirect("student_dashboard")
                elif user.usertype == "teacher":
                    return redirect("teacher_dashboard")
                else:
                    messages.error(request, "Invalid user type.")
                    return redirect("login")
            else:
                messages.error(request, "Invalid password.")
        except UserRegister.DoesNotExist:
            messages.error(request, "User not found.")
    return render(request, "login.html")

# Logout
def logout_view(request):
    request.session.flush()
    return redirect("login")

# ---------------- Dashboards ----------------

from django.db.models import Count
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse
from django.contrib import messages
from .models import Certificate, StudentProgress, Lesson, UserRegister, StudentPoints, StudentBadge, Badge
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import io

def award_certificate(student, skill_level, request=None):
    """
    Check if student has completed all lessons in a skill level by completing each lesson's specific exercise.
    Returns True if certificate awarded, False otherwise with a message.
    """
    lessons = Lesson.objects.filter(skill_level=skill_level)
    if not lessons.exists():
        if request:
            messages.info(request, f"No lessons found for {skill_level.capitalize()} level.")
        return False

    for lesson in lessons:
        progress = StudentProgress.objects.filter(student=student, lesson=lesson).first()
        if not progress:
            if request:
                messages.info(request, f"You need to complete the exercise for '{lesson.title}' to earn a {skill_level.capitalize()} certificate.")
            return False

        exercise_type = lesson.category.lower()
        if exercise_type == 'grammar':
            if not progress.completed_quiz:
                if request:
                    messages.info(request, f"Complete the quiz for '{lesson.title}' to earn a {skill_level.capitalize()} certificate.")
                return False
        elif exercise_type == 'vocabulary':
            if not progress.completed_writing:
                if request:
                    messages.info(request, f"Complete the writing exercise for '{lesson.title}' to earn a {skill_level.capitalize()} certificate.")
                return False
        elif exercise_type == 'listening':
            if not progress.completed_listening:
                if request:
                    messages.info(request, f"Complete the listening exercise for '{lesson.title}' to earn a {skill_level.capitalize()} certificate.")
                return False
        elif exercise_type == 'speaking':
            if not progress.completed_speaking:
                if request:
                    messages.info(request, f"Complete the speaking exercise for '{lesson.title}' to earn a {skill_level.capitalize()} certificate.")
                return False

    if not Certificate.objects.filter(student=student, skill_level=skill_level).exists():
        certificate = Certificate.objects.create(
            student=student,
            skill_level=skill_level
        )
        if request:
            messages.success(request, f"Congratulations! You've earned a {skill_level.capitalize()} Certificate ({certificate.certificate_id})!")
        return True
    else:
        if request:
            messages.info(request, f"You already have a {skill_level.capitalize()} Certificate.")
        return False

def check_and_award_certificates(student, request=None):
    """
    Manual check for all skill levels and award certificates if eligible.
    """
    skill_levels = ['beginner', 'intermediate', 'advanced']
    awarded = False
    for skill_level in skill_levels:
        if award_certificate(student, skill_level, request):
            awarded = True
    return awarded

def student_dashboard(request):
    username = request.session.get("username")
    student = get_object_or_404(UserRegister, username=username, usertype="student")

    lessons = Lesson.objects.all()

    # Build lessons with progress in a single list
    lessons_with_progress = []
    for lesson in lessons:
        prog = StudentProgress.objects.filter(student=student, lesson=lesson).first()
        lessons_with_progress.append({
            "lesson": lesson,
            "progress": prog,
            "completion_percentage": prog.completion_percentage() if prog else 0,
            "quiz_score": prog.quiz_score if prog and prog.quiz_score is not None else None,
            "speaking_score": prog.speaking_score if prog and prog.speaking_score is not None else None,
        })

    # Calculate total points
    total_points = StudentPoints.objects.filter(student=student).aggregate(models.Sum('points'))['points__sum'] or 0

    # Get earned badges
    student_badges = StudentBadge.objects.filter(student=student).select_related('badge')

    # Calculate progress toward unearned badges
    unearned_badges = Badge.objects.exclude(student_badges__student=student).filter(badge_type='points')
    badge_progress = [
        {
            'badge': badge,
            'points_needed': badge.points_required,
            'progress_percentage': min((total_points / badge.points_required * 100), 100) if badge.points_required > 0 else 0
        }
        for badge in unearned_badges
    ]

    # Manual check for certificates
    check_and_award_certificates(student, request)

    # Get certificates (after potential award)
    certificates = Certificate.objects.filter(student=student)

    # Calculate certificate eligibility progress for each skill level
    skill_levels = ['beginner', 'intermediate', 'advanced']
    certificate_progress = []
    for level in skill_levels:
        lessons = Lesson.objects.filter(skill_level=level)
        if lessons.exists():
            completed_lessons = 0
            for lesson in lessons:
                progress = StudentProgress.objects.filter(student=student, lesson=lesson).first()
                if progress:
                    exercise_type = lesson.category.lower()
                    if (exercise_type == 'grammar' and progress.completed_quiz) or \
                       (exercise_type == 'vocabulary' and progress.completed_writing) or \
                       (exercise_type == 'listening' and progress.completed_listening) or \
                       (exercise_type == 'speaking' and progress.completed_speaking):
                        completed_lessons += 1
            total_lessons = lessons.count()
            remaining_lessons = total_lessons - completed_lessons
            certificate_progress.append({
                'skill_level': level,
                'completed_lessons': completed_lessons,
                'total_lessons': total_lessons,
                'remaining_lessons': remaining_lessons,
                'completion_percentage': (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0,
                'has_certificate': Certificate.objects.filter(student=student, skill_level=level).exists()
            })

    return render(request, "student_dashboard.html", {
        "username": student.username,
        "lessons_with_progress": lessons_with_progress,
        "total_points": total_points,
        "student_badges": student_badges,
        "badge_progress": badge_progress,
        "certificates": certificates,
        "certificate_progress": certificate_progress,
    })

def certificate_pdf(request, certificate_id):
    """
    Generate and download certificate as PDF using ReportLab.
    """
    student = get_object_or_404(UserRegister, username=request.session.get("username"))
    certificate = get_object_or_404(Certificate, certificate_id=certificate_id, student=student)

    # Create PDF response
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=inch, bottomMargin=inch, leftMargin=inch, rightMargin=inch)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        name='Title',
        fontSize=24,
        leading=28,
        alignment=1,  # Center
        textColor=colors.darkgreen,
        spaceAfter=20,
    )
    name_style = ParagraphStyle(
        name='Name',
        fontSize=18,
        leading=22,
        alignment=1,
        spaceAfter=15,
    )
    body_style = ParagraphStyle(
        name='Body',
        fontSize=14,
        leading=18,
        alignment=1,
        spaceAfter=10,
    )
    small_style = ParagraphStyle(
        name='Small',
        fontSize=12,
        leading=14,
        alignment=1,
        spaceAfter=10,
    )

    # Build PDF content
    content = []
    content.append(Paragraph("Certificate of Completion", title_style))
    content.append(Spacer(1, 0.2 * inch))
    content.append(Paragraph("This certifies that", body_style))
    content.append(Paragraph(student.full_name, name_style))
    content.append(Paragraph(
        f"has successfully completed all lessons at the <b>{certificate.skill_level.upper()}</b> level.",
        body_style
    ))
    content.append(Paragraph(f"Certificate ID: {certificate.certificate_id}", small_style))
    content.append(Paragraph(f"Issued on: {certificate.issued_at.strftime('%B %d, %Y')}", small_style))
    content.append(Spacer(1, 0.2 * inch))
    content.append(Paragraph("Keep learning!", body_style))

    # Build and save PDF
    doc.build(content)
    pdf = buffer.getvalue()
    buffer.close()

    # Return as download
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{certificate.skill_level}_certificate_{certificate.certificate_id}.pdf"'
    return response

def lesson_by_level(request, level):
    if request.session.get("usertype") != "student":
        return redirect("login")

    lessons = Lesson.objects.filter(skill_level=level)
    return render(request, "lessons_by_level.html", {
        "level": level.capitalize(),
        "lessons": lessons
    })


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import UserRegister, StudentProgress, WritingSubmission, SpeakingSubmission, Lesson

def teacher_dashboard(request):
    if request.session.get("usertype") != "teacher":
        return redirect("login")

    username = request.session.get("username")
    teacher = UserRegister.objects.get(username=username, usertype="teacher")

    # Fetch lessons created by this teacher
    lessons = Lesson.objects.filter(created_by=teacher)

    # Fetch all students with their progress
    student_progress = StudentProgress.objects.select_related("student", "lesson").all()

    # Fetch submissions (writing + speaking)
    writing_submissions = WritingSubmission.objects.select_related("student", "exercise").all()
    speaking_submissions = SpeakingSubmission.objects.select_related("student", "exercise").all()

    return render(request, "teacher_dashboard.html", {
        "username": username,
        "lessons": lessons,
        "student_progress": student_progress,
        "writing_submissions": writing_submissions,
        "speaking_submissions": speaking_submissions,
    })

# ---------------- Teacher Lesson CRUD ----------------

def lesson_list(request):
    if request.session.get("usertype") != "teacher":
        return redirect("login")

    teacher_id = request.session.get("user_id")
    lessons = Lesson.objects.filter(created_by_id=teacher_id)
    return render(request, "teacher/lesson_list.html", {"lessons": lessons})

def lesson_create(request):
    if request.session.get("usertype") != "teacher":
        return redirect("login")

    if request.method == "POST":
        form = LessonForm(request.POST)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.created_by_id = request.session.get("user_id")
            lesson.save()
            messages.success(request, "Lesson created successfully!")
            return redirect("lesson_list")
    else:
        form = LessonForm()
    return render(request, "teacher/lesson_form.html", {"form": form, "title": "Create Lesson"})

def lesson_update(request, pk):
    if request.session.get("usertype") != "teacher":
        return redirect("login")

    teacher_id = request.session.get("user_id")
    lesson = get_object_or_404(Lesson, pk=pk, created_by_id=teacher_id)

    if request.method == "POST":
        form = LessonForm(request.POST, instance=lesson)
        if form.is_valid():
            form.save()
            messages.success(request, "Lesson updated successfully!")
            return redirect("lesson_list")
    else:
        form = LessonForm(instance=lesson)
    return render(request, "teacher/lesson_form.html", {"form": form, "title": "Edit Lesson"})

def lesson_delete(request, pk):
    if request.session.get("usertype") != "teacher":
        return redirect("login")

    teacher_id = request.session.get("user_id")
    lesson = get_object_or_404(Lesson, pk=pk, created_by_id=teacher_id)

    if request.method == "POST":
        lesson.delete()
        messages.success(request, "Lesson deleted successfully!")
        return redirect("lesson_list")
    return render(request, "teacher/lesson_confirm_delete.html", {"lesson": lesson})



# ---------------- Lesson Content CRUD ----------------

def content_list(request):
    if request.session.get("usertype") != "teacher":
        return redirect("login")

    teacher_id = request.session.get("user_id")
    contents = LessonContent.objects.filter(lesson__created_by_id=teacher_id)
    return render(request, "teacher/content_list.html", {"contents": contents})


def content_create(request):
    if request.session.get("usertype") != "teacher":
        return redirect("login")

    if request.method == "POST":
        form = LessonContentForm(request.POST, request.FILES)
        if form.is_valid():
            content = form.save()
            messages.success(request, "Lesson content created successfully!")
            return redirect("content_list")
    else:
        form = LessonContentForm()
    return render(request, "teacher/content_form.html", {"form": form, "title": "Add Lesson Content"})


def content_update(request, pk):
    if request.session.get("usertype") != "teacher":
        return redirect("login")

    teacher_id = request.session.get("user_id")
    content = get_object_or_404(LessonContent, pk=pk, lesson__created_by_id=teacher_id)

    if request.method == "POST":
        form = LessonContentForm(request.POST, request.FILES, instance=content)
        if form.is_valid():
            form.save()
            messages.success(request, "Lesson content updated successfully!")
            return redirect("content_list")
    else:
        form = LessonContentForm(instance=content)
    return render(request, "teacher/content_form.html", {"form": form, "title": "Edit Lesson Content"})


def content_delete(request, pk):
    if request.session.get("usertype") != "teacher":
        return redirect("login")

    teacher_id = request.session.get("user_id")
    content = get_object_or_404(LessonContent, pk=pk, lesson__created_by_id=teacher_id)

    if request.method == "POST":
        content.delete()
        messages.success(request, "Lesson content deleted successfully!")
        return redirect("content_list")
    return render(request, "teacher/content_confirm_delete.html", {"content": content})


def exercise_home(request):
    if not request.session.get("user_id"):
        return redirect("login")

    return render(request, "exercises/exercise_home.html")



from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Quiz
from .forms import QuizForm

def quiz_list(request):
    if request.session.get("usertype") != "teacher":
        return redirect("login")
    quizzes = Quiz.objects.all()
    return render(request, "teacher/quiz_list.html", {"quizzes": quizzes})

def quiz_create(request):
    if request.session.get("usertype") != "teacher":
        return redirect("login")
    if request.method == "POST":
        form = QuizForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Quiz created successfully!")
            return redirect("quiz_list")
    else:
        form = QuizForm()
    return render(request, "teacher/quiz_form.html", {"form": form, "title": "Create Quiz"})

def quiz_update(request, pk):
    if request.session.get("usertype") != "teacher":
        return redirect("login")
    quiz = get_object_or_404(Quiz, pk=pk)
    if request.method == "POST":
        form = QuizForm(request.POST, instance=quiz)
        if form.is_valid():
            form.save()
            messages.success(request, "Quiz updated successfully!")
            return redirect("quiz_list")
    else:
        form = QuizForm(instance=quiz)
    return render(request, "teacher/quiz_form.html", {"form": form, "title": "Edit Quiz"})

def quiz_delete(request, pk):
    if request.session.get("usertype") != "teacher":
        return redirect("login")
    quiz = get_object_or_404(Quiz, pk=pk)
    if request.method == "POST":
        quiz.delete()
        messages.success(request, "Quiz deleted successfully!")
        return redirect("quiz_list")
    return render(request, "teacher/quiz_confirm_delete.html", {"quiz": quiz})



from .models import SpeakingExercise
from .forms import SpeakingExerciseForm

def speaking_exercise_list(request):
    if request.session.get("usertype") != "teacher":
        return redirect("login")
    exercises = SpeakingExercise.objects.all()
    return render(request, "teacher/speaking_exercise_list.html", {"exercises": exercises})

def speaking_exercise_create(request):
    if request.session.get("usertype") != "teacher":
        return redirect("login")
    if request.method == "POST":
        form = SpeakingExerciseForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Speaking Exercise created successfully!")
            return redirect("speaking_exercise_list")
    else:
        form = SpeakingExerciseForm()
    return render(request, "teacher/speaking_exercise_form.html", {"form": form, "title": "Create Speaking Exercise"})

def speaking_exercise_update(request, pk):
    if request.session.get("usertype") != "teacher":
        return redirect("login")
    exercise = get_object_or_404(SpeakingExercise, pk=pk)
    if request.method == "POST":
        form = SpeakingExerciseForm(request.POST, request.FILES, instance=exercise)
        if form.is_valid():
            form.save()
            messages.success(request, "Speaking Exercise updated successfully!")
            return redirect("speaking_exercise_list")
    else:
        form = SpeakingExerciseForm(instance=exercise)
    return render(request, "teacher/speaking_exercise_form.html", {"form": form, "title": "Edit Speaking Exercise"})

def speaking_exercise_delete(request, pk):
    if request.session.get("usertype") != "teacher":
        return redirect("login")
    exercise = get_object_or_404(SpeakingExercise, pk=pk)
    if request.method == "POST":
        exercise.delete()
        messages.success(request, "Speaking Exercise deleted successfully!")
        return redirect("speaking_exercise_list")
    return render(request, "teacher/speaking_exercise_confirm_delete.html", {"exercise": exercise})


from .models import WritingExercise
from .forms import WritingExerciseForm

def writing_exercise_list(request):
    if request.session.get("usertype") != "teacher":
        return redirect("login")
    exercises = WritingExercise.objects.all()
    return render(request, "teacher/writing_exercise_list.html", {"exercises": exercises})

def writing_exercise_create(request):
    if request.session.get("usertype") != "teacher":
        return redirect("login")
    if request.method == "POST":
        form = WritingExerciseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Writing Exercise created successfully!")
            return redirect("writing_exercise_list")
    else:
        form = WritingExerciseForm()
    return render(request, "teacher/writing_exercise_form.html", {"form": form, "title": "Create Writing Exercise"})

def writing_exercise_update(request, pk):
    if request.session.get("usertype") != "teacher":
        return redirect("login")
    exercise = get_object_or_404(WritingExercise, pk=pk)
    if request.method == "POST":
        form = WritingExerciseForm(request.POST, instance=exercise)
        if form.is_valid():
            form.save()
            messages.success(request, "Writing Exercise updated successfully!")
            return redirect("writing_exercise_list")
    else:
        form = WritingExerciseForm(instance=exercise)
    return render(request, "teacher/writing_exercise_form.html", {"form": form, "title": "Edit Writing Exercise"})

def writing_exercise_delete(request, pk):
    if request.session.get("usertype") != "teacher":
        return redirect("login")
    exercise = get_object_or_404(WritingExercise, pk=pk)
    if request.method == "POST":
        exercise.delete()
        messages.success(request, "Writing Exercise deleted successfully!")
        return redirect("writing_exercise_list")
    return render(request, "teacher/writing_exercise_confirm_delete.html", {"exercise": exercise})


from .models import ListeningExercise
from .forms import ListeningExerciseForm

def listening_exercise_list(request):
    if request.session.get("usertype") != "teacher":
        return redirect("login")
    exercises = ListeningExercise.objects.all()
    return render(request, "teacher/listening_exercise_list.html", {"exercises": exercises})

def listening_exercise_create(request):
    if request.session.get("usertype") != "teacher":
        return redirect("login")
    if request.method == "POST":
        form = ListeningExerciseForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Listening Exercise created successfully!")
            return redirect("listening_exercise_list")
    else:
        form = ListeningExerciseForm()
    return render(request, "teacher/listening_exercise_form.html", {"form": form, "title": "Create Listening Exercise"})

def listening_exercise_update(request, pk):
    if request.session.get("usertype") != "teacher":
        return redirect("login")
    exercise = get_object_or_404(ListeningExercise, pk=pk)
    if request.method == "POST":
        form = ListeningExerciseForm(request.POST, request.FILES, instance=exercise)
        if form.is_valid():
            form.save()
            messages.success(request, "Listening Exercise updated successfully!")
            return redirect("listening_exercise_list")
    else:
        form = ListeningExerciseForm(instance=exercise)
    return render(request, "teacher/listening_exercise_form.html", {"form": form, "title": "Edit Listening Exercise"})

def listening_exercise_delete(request, pk):
    if request.session.get("usertype") != "teacher":
        return redirect("login")
    exercise = get_object_or_404(ListeningExercise, pk=pk)
    if request.method == "POST":
        exercise.delete()
        messages.success(request, "Listening Exercise deleted successfully!")
        return redirect("listening_exercise_list")
    return render(request, "teacher/listening_exercise_confirm_delete.html", {"exercise": exercise})



def lesson_detail(request, pk):
    if request.session.get("usertype") != "student":
        return redirect("login")

    lesson = Lesson.objects.get(pk=pk)
    contents = lesson.contents.all()

    return render(request, "lesson_detail.html", {
        "lesson": lesson,
        "contents": contents
    })

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Lesson, Quiz, StudentProgress, UserRegister

def lesson_exercises(request, lesson_id):
    if request.session.get("usertype") != "student":
        return redirect("login")

    lesson = get_object_or_404(Lesson, id=lesson_id)
    return render(request, "lesson_exercises.html", {"lesson": lesson})


import string
import pyttsx3
import speech_recognition as sr
from difflib import SequenceMatcher
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import models
from spellchecker import SpellChecker
from .models import Lesson, UserRegister, StudentProgress, Quiz, WritingExercise, WritingSubmission, SpeakingExercise, SpeakingSubmission, ListeningExercise, StudentPoints, Badge, StudentBadge

def attempt_quiz(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    quizzes = lesson.quizzes.all()

    if request.method == "POST":
        score = 0
        total = quizzes.count()
        for quiz in quizzes:
            selected = request.POST.get(f"q{quiz.id}")
            if selected == quiz.correct_option:
                score += 1
        percentage_score = (score / total) * 100 if total > 0 else 0
        messages.success(request, f"You scored {score} out of {total}")

        student = get_object_or_404(UserRegister, username=request.session.get("username"))
        progress, created = StudentProgress.objects.get_or_create(student=student, lesson=lesson)
        progress.completed_quiz = True
        progress.quiz_score = percentage_score  # Assuming quiz_score field exists
        progress.save()

        # Award points and badges
        update_points_and_badges(student, 'quiz_completed', lesson, percentage_score, request)
        if percentage_score >= 90:
            update_points_and_badges(student, 'quiz_high_score', lesson, percentage_score, request)

        # Check for lesson completion
        if all([progress.completed_quiz, progress.completed_writing, progress.completed_listening, progress.completed_speaking]):
            update_points_and_badges(student, 'lesson_completed', lesson, request=request)

        return redirect("lesson_exercises", lesson_id=lesson.id)

    return render(request, "quiz_attempt.html", {"lesson": lesson, "quizzes": quizzes})

def attempt_writing(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    exercises = lesson.writing_exercises.all()

    student = get_object_or_404(UserRegister, username=request.session.get("username"))

    if request.method == "POST":
        exercise_id = request.POST.get("exercise_id")
        exercise = get_object_or_404(WritingExercise, id=exercise_id, lesson=lesson)

        essay_text = request.POST.get("essay_text", "").strip()

        # Spell check
        spell = SpellChecker()
        words = essay_text.split()
        clean_words = [w.strip(string.punctuation).lower() for w in words if w.strip()]
        misspelled = spell.unknown(clean_words)
        spelling_feedback = ", ".join(misspelled) if misspelled else "No spelling mistakes found."

        # Simple grammar check (repeated words)
        grammar_feedback = ""
        prev_word = ""
        for w in clean_words:
            if w == prev_word:
                grammar_feedback += f"Repeated word: {w}\n"
            prev_word = w

        # Save submission
        WritingSubmission.objects.create(
            student=student,
            exercise=exercise,
            essay_text=essay_text,
            grammar_feedback=grammar_feedback,
            spelling_feedback=spelling_feedback
        )

        # Mark student progress
        progress, created = StudentProgress.objects.get_or_create(student=student, lesson=lesson)
        progress.completed_writing = True
        progress.save()

        # Award points and badges
        update_points_and_badges(student, 'writing_completed', lesson, request=request)

        # Check for lesson completion
        if all([progress.completed_quiz, progress.completed_writing, progress.completed_listening, progress.completed_speaking]):
            update_points_and_badges(student, 'lesson_completed', lesson, request=request)

        messages.success(request, "Your essay has been submitted with feedback!")
        return render(request, "writing_feedback.html", {
            "lesson": lesson,
            "exercise": exercise,
            "essay_text": essay_text,
            "grammar_feedback": grammar_feedback or "No grammar issues found.",
            "spelling_feedback": spelling_feedback,
        })

    return render(request, "writing_attempt.html", {
        "lesson": lesson,
        "exercises": exercises
    })

def attempt_listening(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    exercises = lesson.listening_exercises.all()

    if request.method == "POST":
        student = get_object_or_404(UserRegister, username=request.session.get("username"))
        progress, created = StudentProgress.objects.get_or_create(student=student, lesson=lesson)
        progress.completed_listening = True
        progress.save()

        # Award points and badges
        update_points_and_badges(student, 'listening_completed', lesson, request=request)

        # Check for lesson completion
        if all([progress.completed_quiz, progress.completed_writing, progress.completed_listening, progress.completed_speaking]):
            update_points_and_badges(student, 'lesson_completed', lesson, request=request)

        messages.success(request, "You completed the listening exercise!")
        return redirect("lesson_exercises", lesson_id=lesson.id)

    return render(request, "listening_attempt.html", {"lesson": lesson, "exercises": exercises})

def attempt_speaking(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    exercises = lesson.speaking_exercises.all()

    student = get_object_or_404(UserRegister, username=request.session.get("username"))

    spoken_text = ""
    feedback = ""
    score = None

    if request.method == "POST":
        exercise_id = request.POST.get("exercise_id")
        exercise = get_object_or_404(SpeakingExercise, id=exercise_id, lesson=lesson)

        # --- Step 1: Speak instructions with pyttsx3 ---
        engine = pyttsx3.init()
        engine.say(exercise.target_phrase)
        engine.runAndWait()

        # --- Step 2: Capture voice via microphone ---
        recognizer = sr.Recognizer()
        mic = sr.Microphone()

        try:
            with mic as source:
                recognizer.adjust_for_ambient_noise(source)
                messages.info(request, "Listening... please speak the target phrase.")
                audio = recognizer.listen(source)

            try:
                spoken_text = recognizer.recognize_google(audio)
            except sr.UnknownValueError:
                spoken_text = ""
                feedback = "Could not understand your speech."
            except sr.RequestError:
                spoken_text = ""
                feedback = "Speech recognition service unavailable."
        except Exception as e:
            spoken_text = ""
            feedback = f"Microphone error: {str(e)}"

        # --- Step 3: Compare similarity ---
        expected_text = exercise.target_phrase.strip().lower()
        spoken_clean = spoken_text.strip().lower()

        similarity = SequenceMatcher(None, expected_text, spoken_clean).ratio()
        score = round(similarity * 100, 1)

        feedback += f"\nExpected: {exercise.target_phrase}\nYou said: {spoken_text}\nScore: {score}%"

        # --- Step 4: Save submission ---
        SpeakingSubmission.objects.create(
            student=student,
            exercise=exercise,
            spoken_text=spoken_text,
            similarity_score=score if score else 0,
            feedback=feedback
        )

        # --- Step 5: Update progress ---
        progress, created = StudentProgress.objects.get_or_create(student=student, lesson=lesson)
        progress.completed_speaking = True
        progress.speaking_score = score  # Assuming speaking_score field exists
        progress.save()

        # Award points and badges
        update_points_and_badges(student, 'speaking_completed', lesson, score, request)
        if score >= 90:
            update_points_and_badges(student, 'speaking_high_score', lesson, score, request)

        # Check for lesson completion
        if all([progress.completed_quiz, progress.completed_writing, progress.completed_listening, progress.completed_speaking]):
            update_points_and_badges(student, 'lesson_completed', lesson, request=request)

        messages.success(request, f"You scored {score}% for '{exercise.title}'")
        return render(request, "speaking_feedback.html", {
            "lesson": lesson,
            "exercise": exercise,
            "spoken_text": spoken_text,
            "score": score,
            "feedback": feedback
        })

    return render(request, "speaking_attempt.html", {"lesson": lesson, "exercises": exercises})

def award_points(student, action, lesson=None, score=None):
    """
    Award points to a student for a specific action.
    Returns the number of points awarded.
    """
    points = 0
    if action == 'lesson_completed':
        points = 50  # Completing all exercises in a lesson
    elif action in ['quiz_completed', 'writing_completed', 'speaking_completed', 'listening_completed']:
        points = 20  # Completing an individual exercise
    elif action == 'quiz_high_score' and score >= 90:
        points = 30  # Bonus for high quiz score
    elif action == 'speaking_high_score' and score >= 90:
        points = 30  # Bonus for high speaking score

    if points > 0:
        StudentPoints.objects.create(
            student=student,
            points=points,
            action=action,
            lesson=lesson
        )
    return points

def award_badges(student, request=None):
    """
    Check if student's total points qualify for any badges and award them.
    """
    total_points = StudentPoints.objects.filter(student=student).aggregate(models.Sum('points'))['points__sum'] or 0
    badges = Badge.objects.filter(badge_type='points', points_required__lte=total_points)

    for badge in badges:
        if not StudentBadge.objects.filter(student=student, badge=badge).exists():
            StudentBadge.objects.create(student=student, badge=badge)
            if request:
                messages.success(request, f"Congratulations! You've earned the '{badge.name}' badge!")

def update_points_and_badges(student, action, lesson=None, score=None, request=None):
    """
    Award points and check for badges in one go.
    """
    award_points(student, action, lesson, score)
    award_badges(student, request)


from django.shortcuts import render, get_object_or_404
from django.db.models import Sum
from .models import UserRegister, StudentPoints

def student_leaderboard(request):
    username = request.session.get("username")
    if not username:
        return redirect("login")  # Redirect to login if not authenticated

    student = get_object_or_404(UserRegister, username=username, usertype="student")

    # Get all students with their total points
    leaderboard = UserRegister.objects.filter(usertype="student").annotate(
        total_points=Sum('points__points')
    ).order_by('-total_points')

    # Handle cases where total_points is None (no points earned)
    leaderboard = [
        {
            'student': entry,
            'total_points': entry.total_points or 0,
        }
        for entry in leaderboard
    ]

    # Assign ranks, handling ties
    ranked_leaderboard = []
    current_rank = 1
    previous_points = None
    for index, entry in enumerate(leaderboard):
        if entry['total_points'] != previous_points and previous_points is not None:
            current_rank = index + 1
        ranked_leaderboard.append({
            'rank': current_rank,
            'username': entry['student'].username,
            'total_points': entry['total_points'],
            'is_current_user': entry['student'].username == username
        })
        previous_points = entry['total_points']

    return render(request, "student_leaderboard.html", {
        "username": username,
        "leaderboard": ranked_leaderboard,
    })



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import LiveSession, UserRegister
from .forms import LiveSessionForm


def live_session_list(request):
    if request.session.get("usertype") != "teacher":
        return redirect("login")

    tutor = get_object_or_404(UserRegister, user_id=request.session.get("user_id"))
    sessions = LiveSession.objects.filter(tutor=tutor).order_by('-start_time')
    return render(request, "teacher/live_session_list.html", {"sessions": sessions})


def live_session_create(request):
    if request.session.get("usertype") != "teacher":
        return redirect("login")

    tutor = get_object_or_404(UserRegister, user_id=request.session.get("user_id"))

    if request.method == "POST":
        form = LiveSessionForm(request.POST)
        if form.is_valid():
            live_session = form.save(commit=False)
            live_session.tutor = tutor  # assign current logged-in teacher
            live_session.save()
            messages.success(request, "Live Session created successfully!")
            return redirect("live_session_list")
    else:
        form = LiveSessionForm()

    return render(request, "teacher/live_session_form.html", {"form": form, "title": "Create Live Session"})


def live_session_update(request, pk):
    if request.session.get("usertype") != "teacher":
        return redirect("login")

    tutor = get_object_or_404(UserRegister, user_id=request.session.get("user_id"))
    session = get_object_or_404(LiveSession, pk=pk, tutor=tutor)

    if request.method == "POST":
        form = LiveSessionForm(request.POST, instance=session)
        if form.is_valid():
            form.save()
            messages.success(request, "Live Session updated successfully!")
            return redirect("live_session_list")
    else:
        form = LiveSessionForm(instance=session)

    return render(request, "teacher/live_session_form.html", {"form": form, "title": "Edit Live Session"})


def live_session_delete(request, pk):
    if request.session.get("usertype") != "teacher":
        return redirect("login")

    tutor = get_object_or_404(UserRegister, user_id=request.session.get("user_id"))
    session = get_object_or_404(LiveSession, pk=pk, tutor=tutor)

    if request.method == "POST":
        session.delete()
        messages.success(request, "Live Session deleted successfully!")
        return redirect("live_session_list")

    return render(request, "teacher/live_session_confirm_delete.html", {"session": session})


from django.shortcuts import render, redirect
from .models import LiveSession

def student_live_sessions(request):
    if request.session.get("usertype") != "student":
        return redirect("login")

    sessions = LiveSession.objects.all().order_by('-start_time')
    return render(request, "live_session_list.html", {"sessions": sessions, "title": "Live Sessions"})


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from .models import UserRegister, PeerChat
from .forms import PeerChatForm

def peer_chat_view(request):
    if not request.session.get("user_id"):
        return redirect("login")

    current_user = get_object_or_404(UserRegister, user_id=request.session.get("user_id"))
    usertype = request.session.get("usertype")

    # Determine chat partner list
    if usertype == "student":
        chat_partners = UserRegister.objects.filter(usertype="teacher")
    else:
        chat_partners = UserRegister.objects.filter(usertype="student")

    selected_user_id = request.GET.get("user")
    selected_user = None
    chats = []

    if selected_user_id:
        selected_user = get_object_or_404(UserRegister, user_id=selected_user_id)

        # Retrieve all messages between the two
        chats = PeerChat.objects.filter(
            Q(sender=current_user, receiver=selected_user) | 
            Q(sender=selected_user, receiver=current_user)
        ).order_by("sent_at")

        # Mark messages as read
        PeerChat.objects.filter(receiver=current_user, sender=selected_user, is_read=False).update(is_read=True)

    if request.method == "POST":
        form = PeerChatForm(request.POST)
        if form.is_valid():
            chat = form.save(commit=False)
            chat.sender = current_user
            chat.save()
            messages.success(request, "Message sent successfully.")
            return redirect(f"{request.path}?user={chat.receiver.user_id}")
    else:
        form = PeerChatForm()

    return render(request, "peer_chat.html", {
        "form": form,
        "chats": chats,
        "chat_partners": chat_partners,
        "selected_user": selected_user,
        "current_user": current_user,
    })



from django.shortcuts import render, redirect, get_object_or_404
from .models import DiscussionThread, DiscussionPost, UserRegister
from .forms import DiscussionThreadForm, DiscussionPostForm


# ------------------------------
# View all discussion threads
# ------------------------------
def discussion_threads(request):
    if not request.session.get("user_id"):
        return redirect("login")

    threads = DiscussionThread.objects.all().order_by('-created_at')
    return render(request, 'discussion_threads.html', {'threads': threads})


# ------------------------------
# Create a new discussion thread
# ------------------------------
def create_thread(request):
    if not request.session.get("user_id"):
        return redirect("login")

    user_id = request.session.get("user_id")
    user = get_object_or_404(UserRegister, user_id=user_id)  # fixed field here

    if request.method == 'POST':
        form = DiscussionThreadForm(request.POST)
        if form.is_valid():
            thread = form.save(commit=False)
            thread.created_by = user
            thread.save()
            return redirect('discussion_threads')
    else:
        form = DiscussionThreadForm()
    return render(request, 'create_thread.html', {'form': form})


# ------------------------------
# View single thread and its posts
# ------------------------------
def thread_detail(request, thread_id):
    if not request.session.get("user_id"):
        return redirect("login")

    user_id = request.session.get("user_id")
    user = get_object_or_404(UserRegister, user_id=user_id)  # fixed field here

    thread = get_object_or_404(DiscussionThread, id=thread_id)
    posts = thread.posts.all().order_by('created_at')

    if request.method == 'POST':
        form = DiscussionPostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.thread = thread
            post.author = user
            post.save()
            return redirect('thread_detail', thread_id=thread.id)
    else:
        form = DiscussionPostForm()

    return render(request, 'thread_detail.html', {
        'thread': thread,
        'posts': posts,
        'form': form
    })


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import TeacherSuggestion, UserRegister
from .forms import TeacherSuggestionForm

# List all suggestions by logged-in teacher
def teacher_suggestions(request):
    if not request.session.get("user_id") or request.session.get("usertype") != "teacher":
        return redirect("login")

    teacher_id = request.session.get("user_id")
    suggestions = TeacherSuggestion.objects.filter(teacher_id=teacher_id).order_by('-created_at')
    return render(request, 'teacher/teacher_suggestions.html', {'suggestions': suggestions})

# Add a new suggestion
def add_suggestion(request):
    if not request.session.get("user_id") or request.session.get("usertype") != "teacher":
        return redirect("login")

    teacher = get_object_or_404(UserRegister, user_id=request.session.get("user_id"))

    if request.method == 'POST':
        form = TeacherSuggestionForm(request.POST)
        if form.is_valid():
            suggestion = form.save(commit=False)
            suggestion.teacher = teacher
            suggestion.save()
            messages.success(request, "Suggestion added successfully.")
            return redirect('teacher_suggestions')
    else:
        form = TeacherSuggestionForm()

    return render(request, 'teacher/add_suggestion.html', {'form': form})

# Edit an existing suggestion
def edit_suggestion(request, suggestion_id):
    if not request.session.get("user_id") or request.session.get("usertype") != "teacher":
        return redirect("login")

    teacher = get_object_or_404(UserRegister, user_id=request.session.get("user_id"))
    suggestion = get_object_or_404(TeacherSuggestion, id=suggestion_id, teacher=teacher)

    if request.method == 'POST':
        form = TeacherSuggestionForm(request.POST, instance=suggestion)
        if form.is_valid():
            form.save()
            messages.success(request, "Suggestion updated successfully.")
            return redirect('teacher_suggestions')
    else:
        form = TeacherSuggestionForm(instance=suggestion)

    return render(request, 'teacher/edit_suggestion.html', {'form': form})

# Delete a suggestion
def delete_suggestion(request, suggestion_id):
    if not request.session.get("user_id") or request.session.get("usertype") != "teacher":
        return redirect("login")

    teacher = get_object_or_404(UserRegister, user_id=request.session.get("user_id"))
    suggestion = get_object_or_404(TeacherSuggestion, id=suggestion_id, teacher=teacher)
    suggestion.delete()
    messages.success(request, "Suggestion deleted successfully.")
    return redirect('teacher_suggestions')


from django.shortcuts import render, redirect, get_object_or_404
from .models import TeacherSuggestion, UserRegister

# View suggestions received by logged-in student
def student_suggestions(request):
    if not request.session.get("user_id") or request.session.get("usertype") != "student":
        return redirect("login")

    student_id = request.session.get("user_id")
    suggestions = TeacherSuggestion.objects.filter(student_id=student_id).order_by('-created_at')

    return render(request, 'student_suggestions.html', {'suggestions': suggestions})

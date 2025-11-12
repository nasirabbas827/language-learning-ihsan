from django.db import models
from django.utils import timezone


class UserRegister(models.Model):
    USER_TYPE_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher/Tutor'),
    ]

    user_id = models.AutoField(primary_key=True)
    full_name = models.CharField(max_length=100)
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, unique=True)
    password_hash = models.CharField(max_length=255)
    usertype = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='student')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.username} ({self.usertype})"


class Lesson(models.Model):
    SKILL_LEVEL_CHOICES = [
        ("beginner", "Beginner"),
        ("intermediate", "Intermediate"),
        ("advanced", "Advanced"),
    ]

    CATEGORY_CHOICES = [
        ("grammar", "Grammar"),
        ("vocabulary", "Vocabulary"),
        ("listening", "Listening"),
        ("speaking", "Speaking"),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    skill_level = models.CharField(max_length=20, choices=SKILL_LEVEL_CHOICES)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    created_by = models.ForeignKey(
        UserRegister,
        on_delete=models.SET_NULL,
        null=True,
        related_name="lessons_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class LessonContent(models.Model):
    """
    Content for lessons including text, images, audio, video, and flashcards.
    """
    CONTENT_TYPE_CHOICES = (
        ('text', 'Text'),
        ('image', 'Image'),
        ('audio', 'Audio'),
        ('video', 'Video'),
        ('flashcard', 'Flashcard'),
    )

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='contents')
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPE_CHOICES)
    content = models.TextField(blank=True, null=True)  # For text content or URLs
    media_file = models.FileField(upload_to='lesson_media/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.lesson.title} - {self.content_type}"



class Quiz(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="quizzes")
    question = models.CharField(max_length=200)
    option1 = models.CharField(max_length=200)
    option2 = models.CharField(max_length=200)
    option3 = models.CharField(max_length=200)
    option4 = models.CharField(max_length=200)
    correct_option = models.CharField(
        max_length=10,
        choices=(
            ("option1", "Option 1"),
            ("option2", "Option 2"),
            ("option3", "Option 3"),
            ("option4", "Option 4"),
        )
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.lesson.title} - {self.question}"


class SpeakingExercise(models.Model):
    """
    Represents a speaking practice exercise with speech recognition.
    """
    EXERCISE_TYPE_CHOICES = (
        ('pronunciation', 'Pronunciation Practice'),
        ('dialogue', 'Dialogue Simulation'),
        ('response', 'Prompt Response'),
    )

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="speaking_exercises")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    exercise_type = models.CharField(max_length=20, choices=EXERCISE_TYPE_CHOICES)
    target_phrase = models.TextField(help_text="Target phrase for pronunciation practice")
    audio_example = models.FileField(upload_to='speaking_examples/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.lesson.title} - {self.title}"


class WritingExercise(models.Model):
    """
    Represents a writing practice exercise.
    """
    EXERCISE_TYPE_CHOICES = (
        ('essay', 'Essay Writing'),
        ('sentence', 'Sentence Construction'),
        ('correction', 'Error Correction'),
        ('summary', 'Summary Writing'),
    )

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="writing_exercises")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    exercise_type = models.CharField(max_length=20, choices=EXERCISE_TYPE_CHOICES)
    prompt = models.TextField(help_text="Writing prompt or instructions")
    example_response = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.lesson.title} - {self.title}"



class ListeningExercise(models.Model):
    """
    Represents a listening comprehension exercise.
    """
    EXERCISE_TYPE_CHOICES = (
        ('audio_questions', 'Audio with Questions'),
        ('video_scenario', 'Video Scenario'),
    )

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="listening_exercises")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    exercise_type = models.CharField(max_length=20, choices=EXERCISE_TYPE_CHOICES)
    audio_file = models.FileField(upload_to="listening_audio/", blank=True, null=True)
    video_file = models.URLField(blank=True, null=True, help_text="Paste video URL (e.g. YouTube/Vimeo link)")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.lesson.title} - {self.title}"



from django.db import models
from django.utils import timezone

class StudentProgress(models.Model):
    student = models.ForeignKey('UserRegister', on_delete=models.CASCADE, related_name="progress")
    lesson = models.ForeignKey('Lesson', on_delete=models.CASCADE, related_name="progress")
    completed_quiz = models.BooleanField(default=False)
    quiz_score = models.FloatField(null=True, blank=True, default=None)
    completed_writing = models.BooleanField(default=False)
    completed_listening = models.BooleanField(default=False)
    completed_speaking = models.BooleanField(default=False)
    speaking_score = models.FloatField(null=True, blank=True, default=None)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("student", "lesson")

    def __str__(self):
        return f"{self.student.username} - {self.lesson.title} Progress"

    def completion_percentage(self):
        total = 4  # Number of exercise types
        completed = sum([
            self.completed_quiz,
            self.completed_writing,
            self.completed_listening,
            self.completed_speaking
        ])
        return (completed / total) * 100


class WritingSubmission(models.Model):
    student = models.ForeignKey(UserRegister, on_delete=models.CASCADE, related_name="writing_submissions")
    exercise = models.ForeignKey(WritingExercise, on_delete=models.CASCADE, related_name="submissions")
    essay_text = models.TextField()
    grammar_feedback = models.TextField(blank=True, null=True)
    spelling_feedback = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} - {self.exercise.title} Submission"


class SpeakingSubmission(models.Model):
    student = models.ForeignKey(UserRegister, on_delete=models.CASCADE, related_name="speaking_submissions")
    exercise = models.ForeignKey(SpeakingExercise, on_delete=models.CASCADE, related_name="submissions")
    spoken_text = models.TextField(blank=True, null=True)
    similarity_score = models.FloatField(default=0.0)
    feedback = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} - {self.exercise.title} ({self.similarity_score}%)"



from django.db import models
from django.utils import timezone

class StudentPoints(models.Model):
    student = models.ForeignKey('UserRegister', on_delete=models.CASCADE, related_name='points')
    points = models.PositiveIntegerField(default=0)
    action = models.CharField(max_length=50, choices=[
        ('lesson_completed', 'Lesson Completed'),
        ('quiz_completed', 'Quiz Completed'),
        ('writing_completed', 'Writing Exercise Completed'),
        ('speaking_completed', 'Speaking Exercise Completed'),
        ('listening_completed', 'Listening Exercise Completed'),
        ('quiz_high_score', 'Quiz High Score (90%+)'),
        ('speaking_high_score', 'Speaking High Score (90%+)'),
    ])
    awarded_at = models.DateTimeField(auto_now_add=True)
    lesson = models.ForeignKey('Lesson', on_delete=models.SET_NULL, null=True, blank=True, related_name='points')

    def __str__(self):
        return f"{self.student.username} - {self.points} points for {self.action}"

class Badge(models.Model):
    BADGE_TYPE_CHOICES = [
        ('points', 'Points-Based'),
        ('milestone', 'Milestone'),
    ]
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    badge_type = models.CharField(max_length=20, choices=BADGE_TYPE_CHOICES, default='points')
    icon = models.FileField(upload_to='badge_icons/', blank=True, null=True)
    points_required = models.PositiveIntegerField(help_text="Points needed to earn this badge", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class StudentBadge(models.Model):
    student = models.ForeignKey('UserRegister', on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='student_badges')
    awarded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('student', 'badge')

    def __str__(self):
        return f"{self.student.username} - {self.badge.name}"
    

class LiveSession(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
    ]
    title = models.CharField(max_length=150)
    tutor = models.ForeignKey(
        UserRegister,
        on_delete=models.CASCADE,
        limit_choices_to={'usertype': 'teacher'},
        related_name='tutor_sessions'
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    session_url = models.URLField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')


class PeerChat(models.Model):
    sender = models.ForeignKey(UserRegister, on_delete=models.CASCADE, related_name='sent_chats')
    receiver = models.ForeignKey(UserRegister, on_delete=models.CASCADE, related_name='received_chats')
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Message from {self.sender.full_name} to {self.receiver.full_name}"


# ------------------------------------
# 1) Discussion Thread / Topic Model
# ------------------------------------
class DiscussionThread(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        UserRegister,
        on_delete=models.CASCADE,
        related_name='created_threads'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# ------------------------------------
# 2) Posts/Replies under a Thread
# ------------------------------------
class DiscussionPost(models.Model):
    thread = models.ForeignKey(
        DiscussionThread,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    author = models.ForeignKey(
        UserRegister,
        on_delete=models.CASCADE,
        related_name='discussion_posts'
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.author.full_name} - {self.thread.title}"


class Certificate(models.Model):
    student = models.ForeignKey('UserRegister', on_delete=models.CASCADE, related_name='certificates')
    skill_level = models.CharField(max_length=20, choices=Lesson.SKILL_LEVEL_CHOICES)
    issued_at = models.DateTimeField(auto_now_add=True)
    certificate_id = models.CharField(max_length=50, unique=True, editable=False)

    class Meta:
        unique_together = ('student', 'skill_level')

    def save(self, *args, **kwargs):
        if not self.certificate_id:
            # Generate unique certificate ID (e.g., STU123-BEG-2025)
            self.certificate_id = f"STU{self.student.user_id}-{self.skill_level.upper()[:3]}-{timezone.now().strftime('%Y')}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.username} - {self.skill_level} Certificate"

from django.db import models
from django.utils import timezone

class TeacherSuggestion(models.Model):
    teacher = models.ForeignKey(
        'UserRegister',
        on_delete=models.CASCADE,
        limit_choices_to={'usertype': 'teacher'},
        related_name='given_suggestions'
    )
    student = models.ForeignKey(
        'UserRegister',
        on_delete=models.CASCADE,
        limit_choices_to={'usertype': 'student'},
        related_name='received_suggestions'
    )
    suggestion_text = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Suggestion by {self.teacher.username} to {self.student.username}"

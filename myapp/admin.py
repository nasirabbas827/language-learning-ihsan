from django.contrib import admin
from .models import (
    UserRegister, Lesson, LessonContent, Quiz, SpeakingExercise, WritingExercise,
    ListeningExercise, StudentProgress, WritingSubmission, SpeakingSubmission,
    StudentPoints, Badge, StudentBadge, LiveSession, PeerChat,
    DiscussionThread, DiscussionPost, Certificate
)

# -----------------------
# User Register
# -----------------------
@admin.register(UserRegister)
class UserRegisterAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'username', 'full_name', 'usertype', 'email', 'phone', 'created_at')
    search_fields = ('username', 'full_name', 'email', 'phone')
    list_filter = ('usertype',)
    ordering = ('-created_at',)


# -----------------------
# Lesson and Content
# -----------------------
@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'skill_level', 'category', 'created_by', 'created_at')
    list_filter = ('skill_level', 'category')
    search_fields = ('title', 'description', 'created_by__username')


@admin.register(LessonContent)
class LessonContentAdmin(admin.ModelAdmin):
    list_display = ('lesson', 'content_type', 'created_at')
    list_filter = ('content_type',)
    search_fields = ('lesson__title', 'content')


# -----------------------
# Exercises and Quizzes
# -----------------------
@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('lesson', 'question', 'created_at')
    search_fields = ('lesson__title', 'question')


@admin.register(SpeakingExercise)
class SpeakingExerciseAdmin(admin.ModelAdmin):
    list_display = ('lesson', 'title', 'exercise_type', 'created_at')
    list_filter = ('exercise_type',)
    search_fields = ('lesson__title', 'title')


@admin.register(WritingExercise)
class WritingExerciseAdmin(admin.ModelAdmin):
    list_display = ('lesson', 'title', 'exercise_type', 'created_at')
    list_filter = ('exercise_type',)
    search_fields = ('lesson__title', 'title')


@admin.register(ListeningExercise)
class ListeningExerciseAdmin(admin.ModelAdmin):
    list_display = ('lesson', 'title', 'exercise_type', 'created_at')
    list_filter = ('exercise_type',)
    search_fields = ('lesson__title', 'title')


# -----------------------
# Student Progress & Submissions
# -----------------------
@admin.register(StudentProgress)
class StudentProgressAdmin(admin.ModelAdmin):
    list_display = ('student', 'lesson', 'completion_percentage', 'last_updated')
    search_fields = ('student__username', 'lesson__title')
    list_filter = ('completed_quiz', 'completed_writing', 'completed_listening', 'completed_speaking')


@admin.register(WritingSubmission)
class WritingSubmissionAdmin(admin.ModelAdmin):
    list_display = ('student', 'exercise', 'submitted_at')
    search_fields = ('student__username', 'exercise__title')


@admin.register(SpeakingSubmission)
class SpeakingSubmissionAdmin(admin.ModelAdmin):
    list_display = ('student', 'exercise', 'similarity_score', 'submitted_at')
    search_fields = ('student__username', 'exercise__title')


# -----------------------
# Points and Badges
# -----------------------
@admin.register(StudentPoints)
class StudentPointsAdmin(admin.ModelAdmin):
    list_display = ('student', 'points', 'action', 'lesson', 'awarded_at')
    list_filter = ('action',)
    search_fields = ('student__username', 'lesson__title')


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('name', 'badge_type', 'points_required', 'created_at')
    list_filter = ('badge_type',)


@admin.register(StudentBadge)
class StudentBadgeAdmin(admin.ModelAdmin):
    list_display = ('student', 'badge', 'awarded_at')
    search_fields = ('student__username', 'badge__name')


# -----------------------
# Live Sessions
# -----------------------
@admin.register(LiveSession)
class LiveSessionAdmin(admin.ModelAdmin):
    list_display = ('title', 'tutor', 'start_time', 'end_time', 'status')
    list_filter = ('status', 'tutor')
    search_fields = ('title', 'tutor__username')


# -----------------------
# Peer Chat
# -----------------------
@admin.register(PeerChat)
class PeerChatAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'sent_at', 'is_read')
    list_filter = ('is_read',)
    search_fields = ('sender__username', 'receiver__username', 'message')


# -----------------------
# Discussion Threads and Posts
# -----------------------
@admin.register(DiscussionThread)
class DiscussionThreadAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'created_at')
    search_fields = ('title', 'description', 'created_by__username')


@admin.register(DiscussionPost)
class DiscussionPostAdmin(admin.ModelAdmin):
    list_display = ('thread', 'author', 'created_at', 'updated_at')
    search_fields = ('thread__title', 'author__username', 'content')


# -----------------------
# Certificates
# -----------------------
@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('student', 'skill_level', 'certificate_id', 'issued_at')
    search_fields = ('student__username', 'certificate_id')
    list_filter = ('skill_level',)


from django.contrib import admin
from .models import TeacherSuggestion

@admin.register(TeacherSuggestion)
class TeacherSuggestionAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'student', 'created_at', 'updated_at')
    list_filter = ('teacher', 'student')
    search_fields = ('teacher__username', 'student__username', 'suggestion_text')

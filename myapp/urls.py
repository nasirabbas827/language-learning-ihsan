from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views

urlpatterns = [
    path("", views.landing_page_view, name="index"),
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # Dashboards by role
    path("student/dashboard/", views.student_dashboard, name="student_dashboard"),
    path('student/leaderboard/', views.student_leaderboard, name='student_leaderboard'),

    # Student lesson filtering by level
    path("lessons/<str:level>/", views.lesson_by_level, name="lesson_by_level"),
    path("lesson/<int:pk>/", views.lesson_detail, name="lesson_detail"),

    # Exercises and attempts
    path("lesson/<int:lesson_id>/exercises/", views.lesson_exercises, name="lesson_exercises"),
    path("lesson/<int:lesson_id>/quiz/", views.attempt_quiz, name="attempt_quiz"),
    path("lesson/<int:lesson_id>/writing/", views.attempt_writing, name="attempt_writing"),
    path("lesson/<int:lesson_id>/listening/", views.attempt_listening, name="attempt_listening"),
    path("lesson/<int:lesson_id>/speaking/", views.attempt_speaking, name="attempt_speaking"),

    # Teacher dashboard
    path("teacher/dashboard/", views.teacher_dashboard, name="teacher_dashboard"),

    # Lesson CRUD
    path("lessons/", views.lesson_list, name="lesson_list"),
    path("create/", views.lesson_create, name="lesson_create"),
    path("lessons/<int:pk>/edit/", views.lesson_update, name="lesson_update"),
    path("lessons/<int:pk>/delete/", views.lesson_delete, name="lesson_delete"),

    # Lesson Content CRUD
    path("teacher/contents/", views.content_list, name="content_list"),
    path("teacher/contents/create/", views.content_create, name="content_create"),
    path("teacher/contents/<int:pk>/edit/", views.content_update, name="content_update"),
    path("teacher/contents/<int:pk>/delete/", views.content_delete, name="content_delete"),

    # Exercises Home
    path("exercises/", views.exercise_home, name="exercise_home"),

    # Quiz CRUD
    path("teacher/quizzes/", views.quiz_list, name="quiz_list"),
    path("teacher/quizzes/create/", views.quiz_create, name="quiz_create"),
    path("teacher/quizzes/<int:pk>/edit/", views.quiz_update, name="quiz_update"),
    path("teacher/quizzes/<int:pk>/delete/", views.quiz_delete, name="quiz_delete"),

    # Speaking Exercise CRUD
    path("teacher/speaking-exercises/", views.speaking_exercise_list, name="speaking_exercise_list"),
    path("teacher/speaking-exercises/create/", views.speaking_exercise_create, name="speaking_exercise_create"),
    path("teacher/speaking-exercises/<int:pk>/edit/", views.speaking_exercise_update, name="speaking_exercise_update"),
    path("teacher/speaking-exercises/<int:pk>/delete/", views.speaking_exercise_delete, name="speaking_exercise_delete"),

    # Writing Exercise CRUD
    path("teacher/writing-exercises/", views.writing_exercise_list, name="writing_exercise_list"),
    path("teacher/writing-exercises/create/", views.writing_exercise_create, name="writing_exercise_create"),
    path("teacher/writing-exercises/<int:pk>/edit/", views.writing_exercise_update, name="writing_exercise_update"),
    path("teacher/writing-exercises/<int:pk>/delete/", views.writing_exercise_delete, name="writing_exercise_delete"),

    # Listening Exercise CRUD
    path("teacher/listening-exercises/", views.listening_exercise_list, name="listening_exercise_list"),
    path("teacher/listening-exercises/create/", views.listening_exercise_create, name="listening_exercise_create"),
    path("teacher/listening-exercises/<int:pk>/edit/", views.listening_exercise_update, name="listening_exercise_update"),
    path("teacher/listening-exercises/<int:pk>/delete/", views.listening_exercise_delete, name="listening_exercise_delete"),

    path("teacher/live-sessions/", views.live_session_list, name="live_session_list"),
    path("teacher/live-sessions/create/", views.live_session_create, name="live_session_create"),
    path("teacher/live-sessions/<int:pk>/edit/", views.live_session_update, name="live_session_update"),
    path("teacher/live-sessions/<int:pk>/delete/", views.live_session_delete, name="live_session_delete"),
    path("student/live-sessions/", views.student_live_sessions, name="student_live_sessions"),
    path("chat/", views.peer_chat_view, name="peer_chat"),
    path('discussions/', views.discussion_threads, name='discussion_threads'),
    path('discussions/create/', views.create_thread, name='create_thread'),
    path('discussions/<int:thread_id>/', views.thread_detail, name='thread_detail'),
    path('student/certificate/<str:certificate_id>/pdf/', views.certificate_pdf, name='certificate_pdf'),
    path('teacher/suggestions/', views.teacher_suggestions, name='teacher_suggestions'),
    path('teacher/suggestions/add/', views.add_suggestion, name='add_suggestion'),
    path('teacher/suggestions/edit/<int:suggestion_id>/', views.edit_suggestion, name='edit_suggestion'),
    path('teacher/suggestions/delete/<int:suggestion_id>/', views.delete_suggestion, name='delete_suggestion'),
    path('student/suggestions/', views.student_suggestions, name='student_suggestions'),


]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

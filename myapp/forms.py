from django import forms
from .models import UserRegister
from django.contrib.auth.hashers import make_password

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = UserRegister
        fields = ['full_name', 'username', 'email', 'phone', 'usertype', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")

        cleaned_data["password_hash"] = make_password(password)
        return cleaned_data


from django import forms
from .models import Lesson

class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ["title", "description", "skill_level", "category"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control"}),
            "skill_level": forms.Select(attrs={"class": "form-control"}),
            "category": forms.Select(attrs={"class": "form-control"}),
        }


from django import forms
from .models import LessonContent

class LessonContentForm(forms.ModelForm):
    class Meta:
        model = LessonContent
        fields = ["lesson", "content_type", "content", "media_file"]


from django import forms
from .models import Quiz

class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ["lesson", "question", "option1", "option2", "option3", "option4", "correct_option"]


from django import forms
from .models import SpeakingExercise

class SpeakingExerciseForm(forms.ModelForm):
    class Meta:
        model = SpeakingExercise
        fields = ["lesson", "title", "description", "exercise_type", "target_phrase", "audio_example"]

from django import forms
from .models import WritingExercise

class WritingExerciseForm(forms.ModelForm):
    class Meta:
        model = WritingExercise
        fields = ["lesson", "title", "description", "exercise_type", "prompt", "example_response"]


from django import forms
from .models import ListeningExercise

class ListeningExerciseForm(forms.ModelForm):
    class Meta:
        model = ListeningExercise
        fields = ["lesson", "title", "description", "exercise_type", "audio_file", "video_file"]


from django import forms
from .models import LiveSession

class LiveSessionForm(forms.ModelForm):
    class Meta:
        model = LiveSession
        fields = ["title", "start_time", "end_time", "session_url", "status"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter session title"}),
            "start_time": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
            "end_time": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
            "session_url": forms.URLInput(attrs={"class": "form-control", "placeholder": "Enter meeting link"}),
            "status": forms.Select(attrs={"class": "form-control"}),
        }


from django import forms
from .models import PeerChat

class PeerChatForm(forms.ModelForm):
    class Meta:
        model = PeerChat
        fields = ['receiver', 'message']
        widgets = {
            'receiver': forms.Select(attrs={'class': 'form-select'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Type your message...'}),
        }

from django import forms
from .models import DiscussionThread, DiscussionPost

class DiscussionThreadForm(forms.ModelForm):
    class Meta:
        model = DiscussionThread
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter thread title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter description'}),
        }


class DiscussionPostForm(forms.ModelForm):
    class Meta:
        model = DiscussionPost
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Write your reply...'}),
        }


from django import forms
from .models import TeacherSuggestion, UserRegister

class TeacherSuggestionForm(forms.ModelForm):
    class Meta:
        model = TeacherSuggestion
        fields = ['student', 'suggestion_text']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'suggestion_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }



from django import forms
from .models import WritingSubmission, SpeakingSubmission

class WritingSubmissionFeedbackForm(forms.ModelForm):
    class Meta:
        model = WritingSubmission
        fields = ['grammar_feedback', 'spelling_feedback']
        widgets = {
            'grammar_feedback': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'spelling_feedback': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }

class SpeakingSubmissionFeedbackForm(forms.ModelForm):
    class Meta:
        model = SpeakingSubmission
        fields = ['feedback']
        widgets = {
            'feedback': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }
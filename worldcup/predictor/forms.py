"""Forms for the FIFA World Cup 2026 Family Prediction League."""

from django import forms

from .models import Participant


class PredictionForm(forms.Form):
    """Form for submitting or editing a match prediction."""

    home_score = forms.IntegerField(
        min_value=0,
        max_value=20,
        widget=forms.NumberInput(
            attrs={
                'class': 'form-control form-control-lg text-center fw-bold',
                'min': '0',
                'max': '20',
                'placeholder': '-',
            }
        ),
    )
    away_score = forms.IntegerField(
        min_value=0,
        max_value=20,
        widget=forms.NumberInput(
            attrs={
                'class': 'form-control form-control-lg text-center fw-bold',
                'min': '0',
                'max': '20',
                'placeholder': '-',
            }
        ),
    )


class ParticipantLoginForm(forms.Form):
    """Form for participant login with name dropdown and secret code."""

    name = forms.ModelChoiceField(
        queryset=Participant.objects.filter(is_active=True, is_admin=False),
        widget=forms.Select(
            attrs={
                'class': 'form-select form-select-lg',
            }
        ),
    )
    secret_code = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control form-control-lg',
            }
        ),
        label='Secret Code',
    )


class InlinePredictionForm(forms.Form):
    """Compact prediction form for AJAX inline submissions on the today page."""

    home_score = forms.IntegerField(
        min_value=0,
        max_value=20,
        widget=forms.NumberInput(
            attrs={
                'class': 'form-control text-center fw-bold inline-score',
                'min': '0',
                'max': '20',
                'placeholder': '-',
                'size': '3',
            }
        ),
    )
    away_score = forms.IntegerField(
        min_value=0,
        max_value=20,
        widget=forms.NumberInput(
            attrs={
                'class': 'form-control text-center fw-bold inline-score',
                'min': '0',
                'max': '20',
                'placeholder': '-',
                'size': '3',
            }
        ),
    )

"""Views for the FIFA World Cup 2026 Family Prediction League."""

import itertools

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import InlinePredictionForm, ParticipantLoginForm, PredictionForm
from .models import Match, Participant, Prediction


def get_leaderboard():
    """Calculate full leaderboard data.

    Returns a list of dicts sorted by points (desc), then exact_predictions (desc),
    each containing: participant, points, exact_predictions, matches_predicted, rank.
    """
    participants = Participant.objects.filter(is_active=True)
    board = []
    for p in participants:
        predictions = p.predictions.select_related('match')
        total_points = sum(pred.points for pred in predictions)
        exact_count = sum(1 for pred in predictions if pred.is_exact)
        predicted_count = predictions.count()
        board.append({
            'participant': p,
            'points': total_points,
            'exact_predictions': exact_count,
            'matches_predicted': predicted_count,
        })
    board.sort(key=lambda x: (x['points'], x['exact_predictions']), reverse=True)
    for i, entry in enumerate(board):
        entry['rank'] = i + 1
    return board


def get_current_participant(request):
    """Return the currently logged-in participant from session, or None."""
    participant_id = request.session.get('participant_id')
    if participant_id:
        try:
            return Participant.objects.get(pk=participant_id, is_active=True)
        except Participant.DoesNotExist:
            return None
    return None


# ---------------------------------------------------------------------------
# Authentication views
# ---------------------------------------------------------------------------

def login_view(request):
    """Handle participant login via name + secret_code.

    GET: Display login form with name dropdown and secret code field.
    POST: Validate credentials; on success store participant_id in session
          and redirect to home. On failure, show error via Django messages.
    """
    if request.method == 'POST':
        form = ParticipantLoginForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            secret_code = form.cleaned_data['secret_code']
            try:
                participant = Participant.objects.get(
                    name=name, secret_code=secret_code, is_active=True
                )
                request.session['participant_id'] = participant.id
                messages.success(
                    request,
                    f"Welcome back, {participant.name}! 🎉"
                )
                return redirect('predictor:home')
            except Participant.DoesNotExist:
                messages.error(
                    request,
                    "Invalid name or secret code. Please try again."
                )
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ParticipantLoginForm()

    return render(request, 'predictor/login.html', {'form': form})


def logout_view(request):
    """Log out the current participant by clearing session data.

    Redirects to home page after logout.
    """
    participant_id = request.session.get('participant_id')
    if participant_id:
        try:
            participant = Participant.objects.get(pk=participant_id)
            messages.info(request, f"Goodbye, {participant.name}! See you soon.")
        except Participant.DoesNotExist:
            pass
    request.session.pop('participant_id', None)
    return redirect('predictor:home')


# ---------------------------------------------------------------------------
# Main pages
# ---------------------------------------------------------------------------

def home(request):
    """Render the home page with overview data.

    Context:
        next_match: The next upcoming match for countdown.
        participant_count: Total number of active participants.
        top5: Top 5 leaderboard entries.
        upcoming_matches: Next 5 upcoming matches.
        recent_matches: Last 5 completed matches with results.
        current_participant: The logged-in participant (or None).
    """
    now = timezone.now()

    # Next upcoming match for countdown
    next_match = (
        Match.objects.filter(kickoff_datetime__gt=now)
        .order_by('kickoff_datetime')
        .first()
    )

    # Participant count
    participant_count = Participant.objects.filter(is_active=True).count()

    # Top 5 leaderboard
    full_board = get_leaderboard()
    top5 = full_board[:5]

    # Upcoming matches (next 5)
    upcoming_matches = (
        Match.objects.filter(kickoff_datetime__gt=now)
        .order_by('kickoff_datetime')[:5]
    )

    # Recent completed matches (last 5)
    recent_matches = (
        Match.objects.filter(status='completed')
        .order_by('-kickoff_datetime')[:5]
    )

    # Current participant
    current_participant = get_current_participant(request)

    context = {
        'next_match': next_match,
        'participant_count': participant_count,
        'top5': top5,
        'upcoming_matches': upcoming_matches,
        'recent_matches': recent_matches,
        'current_participant': current_participant,
    }
    return render(request, 'predictor/home.html', context)


def today(request):
    """Render today's matches page.

    Matches are grouped by status (open, locked, completed).
    For each match, we check whether the logged-in participant has predicted.

    Context:
        today_date: Today's date.
        open_matches: Matches that are not locked and not completed.
        locked_matches: Matches that are locked but not yet completed.
        completed_matches: Matches that are completed.
        current_participant: The logged-in participant (or None).
    """
    now = timezone.now()
    today_date = now.date()
    current_participant = get_current_participant(request)

    matches_today = Match.objects.filter(
        match_date=today_date
    ).order_by('kickoff_datetime')

    open_matches = []
    locked_matches = []
    completed_matches = []

    for match in matches_today:
        match.has_predicted = False
        if current_participant:
            match.has_predicted = Prediction.objects.filter(
                participant=current_participant, match=match
            ).exists()

        if match.status == 'completed':
            completed_matches.append(match)
        elif match.is_locked:
            locked_matches.append(match)
        else:
            open_matches.append(match)

    context = {
        'today_date': today_date,
        'open_matches': open_matches,
        'locked_matches': locked_matches,
        'completed_matches': completed_matches,
        'current_participant': current_participant,
    }
    return render(request, 'predictor/today.html', context)


def matches(request):
    """Render all matches page.

    For each match, indicates whether the logged-in participant has predicted.

    Context:
        matches: All matches ordered by kickoff.
        current_participant: The logged-in participant (or None).
    """
    current_participant = get_current_participant(request)
    all_matches = Match.objects.all().order_by('kickoff_datetime')

    for match in all_matches:
        match.has_predicted = False
        if current_participant:
            match.has_predicted = Prediction.objects.filter(
                participant=current_participant, match=match
            ).exists()

    context = {
        'matches': all_matches,
        'current_participant': current_participant,
    }
    return render(request, 'predictor/matches.html', context)


def schedule(request):
    """Render the schedule page with matches grouped by date.

    Uses itertools.groupby to group matches by match_date.

    Context:
        grouped_matches: List of (date, [matches]) tuples.
    """
    all_matches = Match.objects.all().order_by('kickoff_datetime')
    grouped = itertools.groupby(all_matches, key=lambda m: m.match_date)
    grouped_matches = [(date, list(matches)) for date, matches in grouped]

    context = {'grouped_matches': grouped_matches}
    return render(request, 'predictor/schedule.html', context)


def leaderboard(request):
    """Render the full leaderboard page.

    Context:
        leaderboard: Full leaderboard entries with rank, points,
                     exact_predictions, matches_predicted.
    """
    board = get_leaderboard()
    context = {'leaderboard': board}
    return render(request, 'predictor/leaderboard.html', context)


def match_detail(request, match_id):
    """Render the detail page for a single match.

    Shows all predictions for the match. If the match is completed,
    highlights who got the exact score right.

    Context:
        match: The Match object.
        predictions: All predictions for this match.
        has_predicted: Whether the logged-in participant has predicted.
        current_participant: The logged-in participant (or None).
    """
    match = get_object_or_404(Match, pk=match_id)
    current_participant = get_current_participant(request)
    predictions = match.predictions.select_related('participant')

    has_predicted = False
    if current_participant:
        has_predicted = Prediction.objects.filter(
            participant=current_participant, match=match
        ).exists()

    context = {
        'match': match,
        'predictions': predictions,
        'has_predicted': has_predicted,
        'current_participant': current_participant,
    }
    return render(request, 'predictor/match_detail.html', context)


# ---------------------------------------------------------------------------
# Prediction views
# ---------------------------------------------------------------------------

def submit_prediction(request, match_id):
    """Submit a prediction for a specific match.

    - Must be logged in (session participant_id).
    - Match must not be locked.
    - If already predicted, redirect to edit.
    - Supports AJAX inline submission returning JsonResponse.

    GET: Show prediction form.
    POST: Validate and create prediction; redirect to match_detail with
          success message. If AJAX request, return JSON response.
    """
    match = get_object_or_404(Match, pk=match_id)
    current_participant = get_current_participant(request)

    if not current_participant:
        messages.warning(request, "Please log in to make predictions.")
        return redirect('predictor:login')

    if match.is_locked:
        messages.error(
            request,
            f"Predictions are locked for {match.home_team} vs {match.away_team}."
        )
        return redirect('predictor:match_detail', match_id=match.id)

    # Check for existing prediction
    existing = Prediction.objects.filter(
        participant=current_participant, match=match
    ).first()
    if existing:
        messages.info(request, "You already predicted this match. Editing instead.")
        return redirect('predictor:edit_prediction', match_id=match.id)

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == 'POST':
        form = InlinePredictionForm(request.POST) if is_ajax else PredictionForm(request.POST)
        if form.is_valid():
            prediction = Prediction.objects.create(
                participant=current_participant,
                match=match,
                home_score=form.cleaned_data['home_score'],
                away_score=form.cleaned_data['away_score'],
            )
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'home_score': prediction.home_score,
                    'away_score': prediction.away_score,
                    'message': 'Prediction submitted successfully!',
                })
            messages.success(
                request,
                f"Prediction submitted: {match.home_team} {prediction.home_score} - "
                f"{prediction.away_score} {match.away_team}"
            )
            return redirect('predictor:match_detail', match_id=match.id)
        else:
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'errors': form.errors,
                }, status=400)
            messages.error(request, "Please correct the errors below.")
    else:
        form = InlinePredictionForm() if is_ajax else PredictionForm()

    context = {
        'form': form,
        'match': match,
        'current_participant': current_participant,
    }
    return render(request, 'predictor/submit_prediction.html', context)


def edit_prediction(request, match_id):
    """Edit an existing prediction for a specific match.

    - Must be logged in (session participant_id).
    - Match must not be locked.
    - Prediction must exist.

    GET: Show form pre-filled with current prediction values.
    POST: Validate and update prediction; redirect with success message.
    """
    match = get_object_or_404(Match, pk=match_id)
    current_participant = get_current_participant(request)

    if not current_participant:
        messages.warning(request, "Please log in to edit predictions.")
        return redirect('predictor:login')

    if match.is_locked:
        messages.error(
            request,
            f"Predictions are locked for {match.home_team} vs {match.away_team}."
        )
        return redirect('predictor:match_detail', match_id=match.id)

    prediction = get_object_or_404(
        Prediction, participant=current_participant, match=match
    )

    if request.method == 'POST':
        form = PredictionForm(request.POST)
        if form.is_valid():
            prediction.home_score = form.cleaned_data['home_score']
            prediction.away_score = form.cleaned_data['away_score']
            prediction.save()
            messages.success(
                request,
                f"Prediction updated: {match.home_team} {prediction.home_score} - "
                f"{prediction.away_score} {match.away_team}"
            )
            return redirect('predictor:match_detail', match_id=match.id)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PredictionForm(
            initial={
                'home_score': prediction.home_score,
                'away_score': prediction.away_score,
            }
        )

    context = {
        'form': form,
        'match': match,
        'prediction': prediction,
        'current_participant': current_participant,
    }
    return render(request, 'predictor/edit_prediction.html', context)


# ---------------------------------------------------------------------------
# API views
# ---------------------------------------------------------------------------

def countdown_api(request):
    """Return JSON with next match info and seconds remaining.

    Returns:
        JSON object with keys: match (string or None), home_team, away_team,
        kickoff (ISO format), seconds_remaining (int), venue.
    """
    now = timezone.now()
    next_match = (
        Match.objects.filter(kickoff_datetime__gt=now)
        .order_by('kickoff_datetime')
        .first()
    )

    if next_match:
        delta = next_match.kickoff_datetime - now
        return JsonResponse({
            'match': str(next_match),
            'home_team': next_match.home_team,
            'away_team': next_match.away_team,
            'kickoff': next_match.kickoff_datetime.isoformat(),
            'seconds_remaining': max(0, int(delta.total_seconds())),
            'venue': next_match.venue,
        })

    return JsonResponse({
        'match': None,
        'home_team': None,
        'away_team': None,
        'kickoff': None,
        'seconds_remaining': 0,
        'venue': None,
    })

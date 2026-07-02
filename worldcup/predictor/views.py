"""Views for the FIFA World Cup 2026 Family Prediction League."""

import itertools

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import InlinePredictionForm, ParticipantLoginForm, PredictionForm
from .models import Match, Participant, Prediction, KnockoutMatch


def get_leaderboard():
    """Calculate full leaderboard data.

    Returns a list of dicts sorted by points (desc), then exact_predictions (desc),
    each containing: participant, points, exact_predictions, matches_predicted, rank.
    Excludes admin participants.
    """
    participants = Participant.objects.filter(is_active=True, is_admin=False)
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

def login_view(request, admin=False):
    """Handle participant login via name + secret_code.

    GET: Display login form with name dropdown and secret code field.
         Stores the 'next' parameter in the form for post-login redirect.
    POST: Validate credentials; on success store participant_id in session
          and redirect to the original page (or home). On failure, show error.
    """
    # Store the 'next' redirect URL from query params or referer
    next_url = request.GET.get('next') or request.META.get('HTTP_REFERER', '')
    # Only keep internal paths
    if next_url and not next_url.startswith('/'):
        next_url = ''

    if request.method == 'POST':
        form = ParticipantLoginForm(request.POST, admin=admin)
        # Also read next from hidden field
        next_url = request.POST.get('next', '')
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
                # Redirect to original page or home
                if next_url:
                    return redirect(next_url)
                return redirect('predictor:home')
            except Participant.DoesNotExist:
                messages.error(
                    request,
                    "Invalid name or secret code. Please try again."
                )
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ParticipantLoginForm(admin=admin)

    return render(request, 'predictor/login.html', {
        'form': form,
        'next_url': next_url,
    })


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

    from datetime import timedelta
    next_24h = now + timedelta(hours=24)

    next_matches = (
        Match.objects.filter(
            kickoff_datetime__gt=now,
            kickoff_datetime__lte=next_24h
        )
        .order_by('kickoff_datetime')
    )

    # Participant count
    participant_count = Participant.objects.filter(is_active=True, is_admin=False).count()

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

    match_count = Match.objects.count()
    total_predictions = Prediction.objects.count()

    context = {
        'next_match': next_match,
        'next_matches': next_matches,
        'participant_count': participant_count,
        'top5': top5,
        'upcoming_matches': upcoming_matches,
        'recent_matches': recent_matches,
        'current_participant': current_participant,
        'match_count': match_count,
        'total_predictions': total_predictions,
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
    from django.db.models import Case, When, Value, IntegerField

    predictions = (
        match.predictions
        .select_related("participant")
        .annotate(
            exact_first=Case(
                When(
                    home_score=match.home_score,
                    away_score=match.away_score,
                    then=Value(0),
                ),
                default=Value(1),
                output_field=IntegerField(),
            )
        )
        .order_by("exact_first", "submitted_at")
    )

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
        from django.urls import reverse
        login_url = reverse('predictor:login')
        return redirect(f'{login_url}?next={request.path}')

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
        from django.urls import reverse
        login_url = reverse('predictor:login')
        return redirect(f'{login_url}?next={request.path}')

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


# ---------------------------------------------------------------------------
# Admin Dashboard view
# ---------------------------------------------------------------------------

def admin_dashboard(request):
    """Custom admin dashboard for managing matches, results, and knockout bracket."""
    # Check if user is admin participant
    from django.contrib import messages
    participant_id = request.session.get('participant_id')
    is_admin = False
    if participant_id:
        try:
            participant = Participant.objects.get(pk=participant_id, is_admin=True, is_active=True)
            is_admin = True
        except Participant.DoesNotExist:
            pass

    if not is_admin:
        from django.contrib import messages
        messages.error(request, "You don't have admin access.")
        return redirect('predictor:home')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'set_result':
            match_id = request.POST.get('match_id')
            home_score = request.POST.get('home_score')
            away_score = request.POST.get('away_score')
            try:
                match = Match.objects.get(pk=match_id)
                match.home_score = int(home_score)
                match.away_score = int(away_score)
                match.status = 'completed'
                match.save()
                messages.success(request, f"Result set: {match.home_team} {home_score} - {away_score} {match.away_team}")
            except (Match.DoesNotExist, ValueError, TypeError) as e:
                messages.error(request, f"Error setting result: {e}")

        elif action == 'update_knockout':
            ko_id = request.POST.get('ko_id')
            home_team = request.POST.get('home_team', '')
            away_team = request.POST.get('away_team', '')
            home_score = request.POST.get('home_score')
            away_score = request.POST.get('away_score')
            home_score_p = request.POST.get('home_score_p')
            away_score_p = request.POST.get('away_score_p')
            try:
                ko = KnockoutMatch.objects.get(pk=ko_id)
                ko.home_team = home_team
                ko.away_team = away_team

                if ko.match:
                    ko.match.home_team = home_team
                    ko.match.away_team = away_team
                    if home_score and away_score:
                        ko.match.home_score = int(home_score)
                        ko.match.away_score = int(away_score)
                        ko.match.status = 'completed'
                    ko.match.save()
                if home_score and away_score:
                    ko.home_score = int(home_score)
                    ko.away_score = int(away_score)
                    ko.is_completed = True
                if home_score_p and away_score_p:
                    ko.home_score_p = int(home_score_p)
                    ko.away_score_p = int(away_score_p)
                    
                ko.save()
                messages.success(request, f"Knockout match updated: {ko}")
            except (KnockoutMatch.DoesNotExist, ValueError, TypeError) as e:
                messages.error(request, f"Error updating knockout: {e}")
                import traceback; traceback.print_exc();

        elif action == 'create_match':
            home_team = request.POST.get('home_team')
            away_team = request.POST.get('away_team')
            match_date = request.POST.get('match_date')
            kickoff = request.POST.get('kickoff_datetime')
            group = request.POST.get('group_stage', '')
            stage = request.POST.get('stage', 'group')
            venue = request.POST.get('venue', '')
            try:
                from datetime import datetime
                match = Match.objects.create(
                    home_team=home_team,
                    away_team=away_team,
                    match_date=match_date,
                    kickoff_datetime=kickoff,
                    group_stage=group,
                    stage=stage,
                    venue=venue,
                )
                messages.success(request, f"Match created: {match}")
            except Exception as e:
                messages.error(request, f"Error creating match: {e}")

        elif action == 'delete_match':
            match_id = request.POST.get('match_id')
            try:
                match = Match.objects.get(pk=match_id)
                match.delete()
                messages.success(request, "Match deleted successfully.")
            except Match.DoesNotExist:
                messages.error(request, "Match not found.")

        elif action == 'init_knockout':
            # Initialize knockout bracket slots
            stages = [
                ('r32', 16),  # 16 matches in R32
                ('r16', 8),
                ('qf', 4),
                ('sf', 2),
                ('3rd', 1),
                ('final', 1),
            ]
            count = 0
            for stage_code, num_matches in stages:
                for pos in range(1, num_matches + 1):
                    ko, created = KnockoutMatch.objects.get_or_create(
                        stage=stage_code,
                        position=pos,
                    )
                    if created:
                        count += 1
            messages.success(request, f"Knockout bracket initialized with {count} slots.")

        return redirect('predictor:admin_dashboard')

    # GET - show dashboard
    from django.db.models import Count, Q
    all_matches = Match.objects.all().order_by('kickoff_datetime')
    upcoming = Match.objects.filter(status='upcoming').count()
    live = Match.objects.filter(status='live').count()
    completed = Match.objects.filter(status='completed').count()
    total_predictions = Prediction.objects.count()

    # Knockout bracket data
    knockout_matches = KnockoutMatch.objects.all().order_by('stage', 'position')

    # Available teams for dropdowns
    available_teams = sorted(set(
        list(Match.objects.values_list('home_team', flat=True)) +
        list(Match.objects.values_list('away_team', flat=True))
    ))

    context = {
        'all_matches': all_matches,
        'upcoming_count': upcoming,
        'live_count': live,
        'completed_count': completed,
        'total_predictions': total_predictions,
        'knockout_matches': knockout_matches,
        'available_teams': available_teams,
        'current_participant': Participant.objects.get(pk=participant_id) if participant_id else None,
    }
    return render(request, 'predictor/admin_dashboard.html', context)


def bracket(request):
    """Render the knockout bracket page."""
    participant_id = request.session.get('participant_id')
    current_participant = Participant.objects.get(pk=participant_id) if participant_id else None

    knockout_matches = KnockoutMatch.objects.select_related('match').all().order_by('stage', 'position')

    # Organize by stage as a list of (label, matches) pairs
    stage_labels = {
        'r32': 'Round of 32', 'r16': 'Round of 16',
        'qf': 'Quarter Finals', 'sf': 'Semi Finals',
        '3rd': '3rd Place', 'final': 'Final',
    }
    stage_order = ['r32', 'r16', 'qf', 'sf', '3rd', 'final']
    stages_dict = {}
    for km in knockout_matches:
        if km.stage not in stages_dict:
            stages_dict[km.stage] = []
        stages_dict[km.stage].append(km)

    bracket_stages = []
    for stage_key in stage_order:
        if stage_key in stages_dict:
            bracket_stages.append({
                'key': stage_key,
                'label': stage_labels.get(stage_key, stage_key),
                'matches': stages_dict[stage_key],
            })

    context = {
        'bracket_stages': bracket_stages,
        'current_participant': current_participant,
    }
    return render(request, 'predictor/bracket.html', context)

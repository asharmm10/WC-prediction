from django.utils import timezone

from .models import Match, Participant, Prediction


def predictor_context(request):
    """
    Context processor that adds global prediction league data to all templates.
    """
    participant_count = Participant.objects.filter(is_active=True).count()

    upcoming_matches = (
        Match.objects.filter(kickoff_datetime__gt=timezone.now())
        .order_by('kickoff_datetime')[:5]
    )

    # Calculate leaderboard
    leaderboard = _calculate_leaderboard()

    current_leader = leaderboard[0] if leaderboard else None
    top5 = leaderboard[:5]

    # Current logged-in participant (from session)
    current_participant = None
    participant_id = request.session.get('participant_id')
    if participant_id:
        try:
            current_participant = Participant.objects.get(
                pk=participant_id, is_active=True
            )
        except Participant.DoesNotExist:
            pass

    # Gateway context: detect if request came through Caddy with XTransformPort
    is_behind_gateway = getattr(request, 'is_behind_gateway', False)
    xtransformport_param = ''
    if is_behind_gateway:
        port = request.GET.get('XTransformPort', '8000')
        xtransformport_param = f'XTransformPort={port}'

    return {
        'participant_count': participant_count,
        'upcoming_matches': upcoming_matches,
        'current_leader': current_leader,
        'top5': top5,
        'current_participant': current_participant,
        'is_behind_gateway': is_behind_gateway,
        'xtransformport_param': xtransformport_param,
    }


def _calculate_leaderboard():
    """
    Calculate leaderboard from predictions.
    Returns a list of dicts with 'participant', 'points', and 'exact_count'.
    """
    participants = Participant.objects.filter(is_active=True, is_admin=False)
    leaderboard = []

    for i, participant in enumerate(participants):
        predictions = participant.predictions.select_related('match')
        points = 0
        exact_predictions = 0
        matches_predicted = predictions.count()
        for pred in predictions:
            if pred.is_exact:
                points += 3
                exact_predictions += 1

        leaderboard.append({
            'participant': participant,
            'points': points,
            'exact_predictions': exact_predictions,
            'matches_predicted': matches_predicted,
            'rank': i + 1,
        })

    leaderboard.sort(key=lambda x: x['points'], reverse=True)
    return leaderboard

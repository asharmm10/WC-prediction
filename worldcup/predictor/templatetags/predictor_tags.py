from django import template

from ..models import Participant, Prediction

register = template.Library()


@register.simple_tag
def get_leaderboard():
    """
    Usage: {% get_leaderboard as leaderboard %}
    Calculates and returns leaderboard data as a list of dicts
    with 'participant', 'points', and 'exact_count'.
    """
    participants = Participant.objects.filter(is_active=True)
    leaderboard = []

    for participant in participants:
        predictions = participant.predictions.select_related('match')
        points = 0
        exact_count = 0
        for pred in predictions:
            if pred.is_exact:
                points += 3
                exact_count += 1

        leaderboard.append({
            'participant': participant,
            'points': points,
            'exact_count': exact_count,
        })

    leaderboard.sort(key=lambda x: x['points'], reverse=True)
    return leaderboard


@register.simple_tag
def get_participant_points(participant):
    """
    Usage: {% get_participant_points participant as points %}
    Returns the total points for a given participant.
    """
    if not isinstance(participant, Participant):
        return 0

    predictions = participant.predictions.select_related('match')
    points = 0
    for pred in predictions:
        points += pred.points
    return points

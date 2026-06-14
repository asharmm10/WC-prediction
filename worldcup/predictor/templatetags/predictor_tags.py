from django import template
from django.templatetags.static import static

from ..models import Participant, Prediction, get_team_logo, get_team_color

register = template.Library()


@register.simple_tag(takes_context=True)
def gw_static(context, path):
    """
    Like {% static %} but appends XTransformPort when behind the gateway.
    Usage: {% gw_static "images/teams/brazil.png" %}
    """
    url = static(path)
    xtransformport_param = context.get('xtransformport_param', '')
    if xtransformport_param:
        separator = '&' if '?' in url else '?'
        url = f"{url}{separator}{xtransformport_param}"
    return url


@register.simple_tag
def get_leaderboard():
    """
    Usage: {% get_leaderboard as leaderboard %}
    Calculates and returns leaderboard data as a list of dicts
    with 'participant', 'points', and 'exact_count'.
    """
    participants = Participant.objects.filter(is_active=True, is_admin=False)
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


@register.simple_tag
def team_logo(team_name):
    """Return the static URL for a team's logo.
    Usage: {% team_logo "Brazil" as logo_url %}
    """
    logo_path = get_team_logo(team_name)
    if logo_path:
        return static(logo_path)
    return ''


@register.simple_tag
def team_color(team_name):
    """Return the theme color for a team.
    Usage: {% team_color "Brazil" as color %}
    """
    return get_team_color(team_name)


@register.filter
def team_logo_url(team_name):
    """Filter version: {{ "Brazil"|team_logo_url }}"""
    logo_path = get_team_logo(team_name)
    if logo_path:
        return static(logo_path)
    return ''


@register.filter
def team_color_hex(team_name):
    """Filter version: {{ "Brazil"|team_color_hex }}"""
    return get_team_color(team_name)

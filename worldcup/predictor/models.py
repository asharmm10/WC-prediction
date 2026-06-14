from django.db import models
from django.utils import timezone


# Team logo mapping - maps team name to static image path
TEAM_LOGO_MAP = {
    'Argentina': 'argentina-national-team-footylogos.png',
    'Australia': 'australia-national-team-footylogos.png',
    'Algeria': 'algeria-national-team-footballlogos-org.png',
    'Austria': 'austria-national-team-footballlogos-org.png',
    'Belgium': 'belgium-national-team-footballlogos-org.png',
    'Brazil': 'brazil-national-team-footballlogos-org.png',
    'Canada': 'canada-national-team-footballlogos-org.png',
    'Colombia': 'colombia-national-team-footballlogos-org.png',
    "Cote d'Ivoire": 'cote-d-ivoire-national-team-footballlogos-org.png',
    'Croatia': 'croatia-national-team-footballlogos-org.png',
    'Curacao': 'curacao-national-team-footballlogos-org.png',
    'Czechia': 'czechia-national-team-footballlogos-org.png',
    'DR Congo': 'dr-congo-footballlogos-org.png',
    'Ecuador': 'ecuador-national-team-footballlogos-org.png',
    'Egypt': 'egypt-national-team-footballlogos-org.png',
    'England': 'england-national-team-footballlogos-org.png',
    'France': 'france-national-team-footballlogos-org.png',
    'Germany': 'germany-national-team-footballlogos-org.png',
    'Ghana': 'ghana-national-team-footylogos.png',
    'Haiti': 'haiti-national-team-footylogos.png',
    'Iran': 'iran-national-team-footballlogos-org.png',
    'Iraq': 'iraq-footballlogos-org.png',
    'Japan': 'japan-national-team-footballlogos-org.png',
    'Jordan': 'jordan-footballlogos-org.png',
    'Mexico': 'mexico-national-team-footballlogos-org.png',
    'Morocco': 'morocco-national-team-footballlogos-org.png',
    'Netherlands': 'netherlands-dutch-national-team-footballlogos-org.png',
    'New Zealand': 'new-zealand-national-team-footballlogos-org.png',
    'Norway': 'norway-national-team-footballlogos-org.png',
    'Panama': 'panama-national-team-footballlogos-org.png',
    'Paraguay': 'paraguay-national-team-footballlogos-org.png',
    'Portugal': 'portugal-national-team-footballlogos-org.png',
    'Qatar': 'qatar-national-team-footballlogos-org.png',
    'Saudi Arabia': 'saudi-arabia-national-team-footballlogos-org.png',
    'Scotland': 'scotland-national-team-footballlogos-org.png',
    'Senegal': 'senegal-national-team-footballlogos-org.png',
    'South Africa': 'south-africa-national-team-footballlogos-org.png',
    'South Korea': 'south-korea-national-team-footballlogos-org.png',
    'Spain': 'spain-national-team-footballlogos-org.png',
    'Sweden': 'sweden-national-team-footballlogos-org.png',
    'Switzerland': 'swiss-national-team-footballlogos-org.png',
    'Tunisia': 'tunisia-national-team-footballlogos-org.png',
    'Turkey': 'turkey-national-team-footballlogos-org.png',
    'Uruguay': 'uruguay-national-team-footballlogos-org.png',
    'USA': 'usa-national-team-footballlogos-org.png',
    'Uzbekistan': 'uzbekistan-national-team-footballlogos-org.png',
    'Bosnia and Herzegovina': 'bosnia-and-herzegovina-footballlogos-org.png',
    'Cabo Verde': 'cabo-verde-footballlogos-org.png',
    'Curaçao': 'curacao-national-team-footballlogos-org.png',
}

# Team theme colors for backgrounds
TEAM_COLORS = {
    'Argentina': '#75AADB',
    'Australia': '#FFD700',
    'Algeria': '#008C45',
    'Austria': '#ED2939',
    'Belgium': '#ED2939',
    'Brazil': '#009739',
    'Canada': '#FF0000',
    'Colombia': '#FCD116',
    "Cote d'Ivoire": '#F77F00',
    'Croatia': '#0D5EAF',
    'Curacao': '#002B7F',
    'Czechia': '#11457E',
    'DR Congo': '#007FFF',
    'Ecuador': '#FFD100',
    'Egypt': '#C8102E',
    'England': '#FFFFFF',
    'France': '#002395',
    'Germany': '#000000',
    'Ghana': '#FFCE00',
    'Haiti': '#00209F',
    'Iran': '#239F40',
    'Iraq': '#CE1126',
    'Japan': '#BC002D',
    'Jordan': '#CE1126',
    'Mexico': '#006341',
    'Morocco': '#C1272D',
    'Netherlands': '#FF6600',
    'New Zealand': '#000000',
    'Norway': '#BA0C2F',
    'Panama': '#005293',
    'Paraguay': '#D52B1E',
    'Portugal': '#006600',
    'Qatar': '#8A1538',
    'Saudi Arabia': '#006C35',
    'Scotland': '#003087',
    'Senegal': '#00853F',
    'South Africa': '#007749',
    'South Korea': '#CD2E3A',
    'Spain': '#AA151B',
    'Sweden': '#006AA7',
    'Switzerland': '#DA291C',
    'Tunisia': '#E70013',
    'Turkey': '#E30A17',
    'Uruguay': '#5DADE2',
    'USA': '#3C3B6E',
    'Uzbekistan': '#1EB53A',
    'Bosnia and Herzegovina': '#002395',
    'Cabo Verde': '#003893',
}


def get_team_logo(team_name):
    """Return the static path for a team's logo image."""
    filename = TEAM_LOGO_MAP.get(team_name)
    if filename:
        return f'images/teams/{filename}'
    return None


def get_team_color(team_name):
    """Return the theme color for a team."""
    return TEAM_COLORS.get(team_name, '#333333')


class Participant(models.Model):
    name = models.CharField(max_length=100, unique=True)
    secret_code = models.CharField(max_length=20, unique=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def total_points(self):
        return sum(p.points for p in self.predictions.select_related('match'))


class Match(models.Model):
    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('live', 'Live'),
        ('completed', 'Completed'),
    ]

    STAGE_CHOICES = [
        ('group', 'Group Stage'),
        ('r32', 'Round of 32'),
        ('r16', 'Round of 16'),
        ('qf', 'Quarter Finals'),
        ('sf', 'Semi Finals'),
        ('3rd', '3rd Place'),
        ('final', 'Final'),
    ]

    home_team = models.CharField(max_length=100)
    away_team = models.CharField(max_length=100)
    match_date = models.DateField()
    match_time = models.TimeField(null=True, blank=True)
    kickoff_datetime = models.DateTimeField(
        help_text="Exact kickoff time for locking predictions"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='upcoming',
    )
    home_score = models.IntegerField(null=True, blank=True)
    away_score = models.IntegerField(null=True, blank=True)
    home_flag = models.ImageField(upload_to='flags/', null=True, blank=True)
    away_flag = models.ImageField(upload_to='flags/', null=True, blank=True)
    venue = models.CharField(max_length=200, blank=True)
    group_stage = models.CharField(
        max_length=10,
        blank=True,
        help_text="Group A-H or KO for knockout",
    )
    stage = models.CharField(
        max_length=10,
        choices=STAGE_CHOICES,
        default='group',
        help_text="Tournament stage",
    )

    class Meta:
        ordering = ['kickoff_datetime']
        verbose_name_plural = 'matches'

    def __str__(self):
        return f"{self.home_team} vs {self.away_team} ({self.match_date})"

    @property
    def is_locked(self):
        return self.kickoff_datetime <= timezone.now()

    @property
    def result_str(self):
        if self.home_score is not None and self.away_score is not None:
            return f"{self.home_score} - {self.away_score}"
        return "Not played"

    @property
    def home_team_logo(self):
        return get_team_logo(self.home_team)

    @property
    def away_team_logo(self):
        return get_team_logo(self.away_team)

    @property
    def home_team_color(self):
        return get_team_color(self.home_team)

    @property
    def away_team_color(self):
        return get_team_color(self.away_team)


class Prediction(models.Model):
    participant = models.ForeignKey(
        Participant,
        on_delete=models.CASCADE,
        related_name='predictions',
    )
    match = models.ForeignKey(
        Match,
        on_delete=models.CASCADE,
        related_name='predictions',
    )
    home_score = models.IntegerField()
    away_score = models.IntegerField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('participant', 'match')
        ordering = ['match__kickoff_datetime']

    def __str__(self):
        return (
            f"{self.participant.name}: "
            f"{self.match.home_team} {self.home_score} - "
            f"{self.away_score} {self.match.away_team}"
        )

    @property
    def is_exact(self):
        if self.match.status != 'completed':
            return False
        return (
            self.home_score == self.match.home_score
            and self.away_score == self.match.away_score
        )

    @property
    def points(self):
        return 3 if self.is_exact else 0


class KnockoutMatch(models.Model):
    """Represents a slot in the knockout bracket tree."""
    STAGE_CHOICES = [
        ('r32', 'Round of 32'),
        ('r16', 'Round of 16'),
        ('qf', 'Quarter Finals'),
        ('sf', 'Semi Finals'),
        ('3rd', '3rd Place'),
        ('final', 'Final'),
    ]

    stage = models.CharField(max_length=5, choices=STAGE_CHOICES)
    position = models.PositiveIntegerField(help_text="Position within the stage (1-based)")
    home_team = models.CharField(max_length=100, blank=True)
    away_team = models.CharField(max_length=100, blank=True)
    home_score = models.IntegerField(null=True, blank=True)
    away_score = models.IntegerField(null=True, blank=True)
    match = models.OneToOneField(
        Match,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='knockout_slot',
    )
    is_completed = models.BooleanField(default=False)

    class Meta:
        ordering = ['stage', 'position']
        unique_together = ('stage', 'position')

    def __str__(self):
        return f"{self.get_stage_display()} - Match {self.position}: {self.home_team} vs {self.away_team}"

    @property
    def home_team_logo(self):
        return get_team_logo(self.home_team) if self.home_team else None

    @property
    def away_team_logo(self):
        return get_team_logo(self.away_team) if self.away_team else None

    @property
    def winner(self):
        if not self.is_completed or self.home_score is None:
            return None
        if self.home_score > self.away_score:
            return self.home_team
        elif self.away_score > self.home_score:
            return self.away_team
        return None  # Draw/penalties - handled separately

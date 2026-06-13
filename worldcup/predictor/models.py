from django.db import models
from django.utils import timezone


class Participant(models.Model):
    name = models.CharField(max_length=100, unique=True)
    secret_code = models.CharField(max_length=20, unique=True)
    is_active = models.BooleanField(default=True)
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

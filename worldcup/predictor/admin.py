import csv
import io

from django.contrib import admin, messages
from django.http import HttpResponse
from django.utils import timezone

from .models import Match, Participant, Prediction


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ('name', 'secret_code', 'is_active')
    search_fields = ('name',)
    list_filter = ('is_active',)
    readonly_fields = ('created_at',)


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = (
        'home_team',
        'away_team',
        'match_date',
        'kickoff_datetime',
        'status',
        'home_score',
        'away_score',
    )
    list_filter = ('status', 'match_date', 'group_stage')
    search_fields = ('home_team', 'away_team')
    date_hierarchy = 'match_date'
    actions = [
        'lock_predictions',
        'unlock_predictions',
        'recalculate_scores',
        'export_csv',
        'export_excel',
    ]

    @admin.action(description="Lock predictions for selected matches")
    def lock_predictions(self, request, queryset):
        updated = queryset.filter(status='upcoming').update(status='live')
        self.message_user(
            request,
            f"{updated} match(es) locked for predictions.",
            messages.SUCCESS,
        )

    @admin.action(description="Unlock predictions for selected matches")
    def unlock_predictions(self, request, queryset):
        updated = queryset.filter(status='live').update(status='upcoming')
        self.message_user(
            request,
            f"{updated} match(es) unlocked for predictions.",
            messages.SUCCESS,
        )

    @admin.action(description="Recalculate scores for selected matches")
    def recalculate_scores(self, request, queryset):
        count = 0
        for match in queryset:
            if match.status == 'completed':
                count += match.predictions.count()
        self.message_user(
            request,
            f"Score recalculation triggered for {count} prediction(s) across "
            f"{queryset.count()} match(es).",
            messages.SUCCESS,
        )

    @admin.action(description="Export predictions as CSV")
    def export_csv(self, request, queryset):
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            'Participant',
            'Match',
            'Home Team',
            'Away Team',
            'Predicted Home Score',
            'Predicted Away Score',
            'Actual Home Score',
            'Actual Away Score',
            'Points',
            'Submitted At',
        ])
        predictions = Prediction.objects.filter(
            match__in=queryset
        ).select_related('participant', 'match')
        for pred in predictions:
            writer.writerow([
                pred.participant.name,
                str(pred.match),
                pred.match.home_team,
                pred.match.away_team,
                pred.home_score,
                pred.away_score,
                pred.match.home_score if pred.match.home_score is not None else '',
                pred.match.away_score if pred.match.away_score is not None else '',
                pred.points,
                pred.submitted_at.strftime('%Y-%m-%d %H:%M:%S'),
            ])
        output.seek(0)
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = (
            f'attachment; filename=predictions_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
        return response

    @admin.action(description="Export predictions as Excel")
    def export_excel(self, request, queryset):
        try:
            from openpyxl import Workbook
        except ImportError:
            self.message_user(
                request,
                "openpyxl is not installed. Install it with: pip install openpyxl",
                messages.ERROR,
            )
            return

        wb = Workbook()
        ws = wb.active
        ws.title = "Predictions"

        headers = [
            'Participant',
            'Match',
            'Home Team',
            'Away Team',
            'Predicted Home Score',
            'Predicted Away Score',
            'Actual Home Score',
            'Actual Away Score',
            'Points',
            'Submitted At',
        ]
        ws.append(headers)

        predictions = Prediction.objects.filter(
            match__in=queryset
        ).select_related('participant', 'match')

        for pred in predictions:
            ws.append([
                pred.participant.name,
                str(pred.match),
                pred.match.home_team,
                pred.match.away_team,
                pred.home_score,
                pred.away_score,
                pred.match.home_score if pred.match.home_score is not None else '',
                pred.match.away_score if pred.match.away_score is not None else '',
                pred.points,
                pred.submitted_at.strftime('%Y-%m-%d %H:%M:%S'),
            ])

        # Auto-adjust column widths
        for column_cells in ws.columns:
            max_length = max(
                len(str(cell.value or '')) for cell in column_cells
            )
            ws.column_dimensions[column_cells[0].column_letter].width = (
                min(max_length + 2, 50)
            )

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)

        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = (
            f'attachment; filename=predictions_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        )
        return response


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = ('participant', 'match', 'home_score', 'away_score', 'submitted_at')
    list_filter = ('match__match_date',)
    search_fields = ('participant__name',)
    readonly_fields = ('submitted_at', 'updated_at')

import csv
import io

from django.contrib import admin, messages
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import path, reverse
from django.utils import timezone

from .models import Match, Participant, Prediction, KnockoutMatch


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ('name', 'secret_code', 'is_active', 'is_admin')
    search_fields = ('name',)
    list_filter = ('is_active', 'is_admin')
    readonly_fields = ('created_at',)
    list_editable = ('is_active', 'is_admin')


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = (
        'home_team',
        'away_team',
        'match_date',
        'kickoff_datetime',
        'status',
        'stage',
        'home_score',
        'away_score',
    )
    list_filter = ('status', 'match_date', 'group_stage', 'stage')
    search_fields = ('home_team', 'away_team')
    date_hierarchy = 'match_date'
    list_editable = ('status', 'home_score', 'away_score')
    actions = [
        'lock_predictions',
        'unlock_predictions',
        'mark_completed',
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

    @admin.action(description="Mark selected matches as completed")
    def mark_completed(self, request, queryset):
        updated = queryset.filter(status='live').update(status='completed')
        self.message_user(
            request,
            f"{updated} match(es) marked as completed.",
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
            'Participant', 'Match', 'Home Team', 'Away Team',
            'Predicted Home Score', 'Predicted Away Score',
            'Actual Home Score', 'Actual Away Score', 'Points', 'Submitted At',
        ]
        ws.append(headers)

        predictions = Prediction.objects.filter(
            match__in=queryset
        ).select_related('participant', 'match')

        for pred in predictions:
            ws.append([
                pred.participant.name, str(pred.match),
                pred.match.home_team, pred.match.away_team,
                pred.home_score, pred.away_score,
                pred.match.home_score if pred.match.home_score is not None else '',
                pred.match.away_score if pred.match.away_score is not None else '',
                pred.points,
                pred.submitted_at.strftime('%Y-%m-%d %H:%M:%S'),
            ])

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
    list_filter = ('match__match_date', 'match__status')
    search_fields = ('participant__name',)
    readonly_fields = ('submitted_at', 'updated_at')
    list_select_related = ('participant', 'match')


@admin.register(KnockoutMatch)
class KnockoutMatchAdmin(admin.ModelAdmin):
    list_display = ('stage', 'position', 'home_team', 'away_team', 'home_score', 'away_score', 'is_completed')
    list_filter = ('stage', 'is_completed')
    list_editable = ('home_team', 'away_team', 'home_score', 'away_score', 'is_completed')
    ordering = ('stage', 'position')

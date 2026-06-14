from django.urls import path

from . import views

app_name = 'predictor'

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('admin-login/', views.login_view, {'admin': True}, name='admin_login'),
    path('logout/', views.logout_view, name='logout'),
    path('today/', views.today, name='today'),
    path('matches/', views.matches, name='matches'),
    path('schedule/', views.schedule, name='schedule'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('match/<int:match_id>/', views.match_detail, name='match_detail'),
    path('predict/<int:match_id>/', views.submit_prediction, name='submit_prediction'),
    path('predict/<int:match_id>/edit/', views.edit_prediction, name='edit_prediction'),
    path('api/countdown/', views.countdown_api, name='countdown_api'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('bracket/', views.bracket, name='bracket'),
]

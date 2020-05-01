from django.urls import path

from . import views

urlpatterns = [
    path('short-term/', views.ShortTermInterestView.as_view()),
    path('long-term/', views.LongTermInterestView.as_view()),
    path('long-term/<int:pk>/', views.LongTermInterestItemView.as_view()),
    path('activity-stats/', views.ActivityStatsView.as_view()),

    path('papers/', views.PaperView.as_view()),
    path('papers/<int:pk>/', views.PaperItemView.as_view()),

    path('stream-graph/', views.StreamGraphView.as_view()),
    path('similarity/<int:pk>/', views.SimilarityView.as_view()),

    path('black-listed-keywords/<int:pk>/', views.UserBlacklistedKeywordItemView.as_view()),
]

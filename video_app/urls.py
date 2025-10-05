from django.urls import path
from . import views

app_name = 'video_app'

urlpatterns = [
    path('', views.landing_page, name='landing'),
    path('home/', views.home, name='home'),
    path('create-room/', views.create_room, name='create_room'),
    path('join-room/', views.join_room, name='join_room'),
    path('room/<str:room_id>/', views.room, name='room'),
    path('room/<str:room_id>/leave/', views.leave_room, name='leave_room'),
    path('api/room/<str:room_id>/participants/', views.get_participants, name='get_participants'),
]
from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing'),
    path('home/', views.home, name='home'),
    path('create-room/', views.create_room, name='create_room'),
    path('join-room/', views.join_room, name='join_room'),
    path('room/<str:room_id>/', views.room, name='room'),
    path('room/<str:room_id>/leave/', views.leave_room, name='leave_room'),
    path('api/room/<str:room_id>/participants/', views.get_participants, name='get_participants'),
    
    # Chat URLs
    path('api/room/<str:room_id>/chat/send/', views.send_message, name='send_message'),
    path('api/room/<str:room_id>/chat/messages/', views.get_messages, name='get_messages'),
    
    # Admin control URLs
    path('api/room/<str:room_id>/mute-all/', views.mute_all, name='mute_all'),
    path('api/room/<str:room_id>/remove-all/', views.remove_all, name='remove_all'),
    path('api/room/<str:room_id>/mute/<str:user_id>/', views.mute_participant, name='mute_participant'),
    path('api/room/<str:room_id>/remove/<str:user_id>/', views.remove_participant, name='remove_participant'),
]
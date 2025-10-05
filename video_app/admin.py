from django.contrib import admin

# Register your models here.


from django.contrib import admin
from .models import Room, Participant

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'id', 'created_by', 'created_at', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'created_by']

@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ['name', 'room', 'joined_at', 'is_admin']
    list_filter = ['is_admin', 'joined_at']
    search_fields = ['name', 'room__name']
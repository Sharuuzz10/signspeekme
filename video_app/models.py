from django.db import models
import uuid
import shortuuid

class Room(models.Model):
    id = models.CharField(primary_key=True, max_length=20, unique=True, default=shortuuid.uuid)
    name = models.CharField(max_length=255)
    created_by = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    max_participants = models.IntegerField(default=10)
    
    def __str__(self):
        return f"{self.name} ({self.id})"

class Participant(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='participants')
    user_id = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    joined_at = models.DateTimeField(auto_now_add=True)
    is_admin = models.BooleanField(default=False)
    video_enabled = models.BooleanField(default=True)
    audio_enabled = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['room', 'user_id']
    
    def __str__(self):
        return f"{self.name} in {self.room.name}"
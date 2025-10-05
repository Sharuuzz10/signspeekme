from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
import uuid
import random
import string
from datetime import datetime

# Simple in-memory storage
rooms = {}
participants = {}
chat_messages = {}
user_streams = {}  # Track user media streams

def landing_page(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        
        if name and email:
            # Store user info in session
            request.session['user_name'] = name
            request.session['user_email'] = email
            request.session['user_id'] = str(uuid.uuid4())
            
            messages.success(request, f'Welcome, {name}!')
            return redirect('/home/')
        else:
            messages.error(request, 'Please fill in all fields')
    
    return render(request, 'landing.html')

def home(request):
    # Check if user has session data
    if not request.session.get('user_name'):
        messages.warning(request, 'Please enter your details first')
        return redirect('/')
    
    context = {
        'user_name': request.session['user_name'],
        'user_email': request.session['user_email'],
    }
    return render(request, 'home.html', context)

def create_room(request):
    if not request.session.get('user_name'):
        return redirect('/')
    
    if request.method == 'POST':
        room_name = request.POST.get('room_name', 'New Meeting')
        user_id = request.session.get('user_id')
        user_name = request.session.get('user_name')
        
        # Generate a simple room ID (6 characters)
        room_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        
        # Store room information
        rooms[room_id] = {
            'name': room_name,
            'created_by': user_name,
            'created_by_id': user_id,
            'created_at': 'now',
            'is_active': True
        }
        
        # Add creator as participant
        participants[room_id] = [{
            'user_id': user_id,
            'name': user_name,
            'is_admin': True,
            'video_enabled': True,
            'audio_enabled': True
        }]
        
        # Initialize chat for this room
        chat_messages[room_id] = []
        
        # Initialize user streams for this room
        user_streams[room_id] = {}
        
        messages.success(request, f'Room created successfully! Room ID: {room_id}')
        return redirect(f'/room/{room_id}/')
    
    return render(request, 'create_room.html')

def join_room(request):
    if not request.session.get('user_name'):
        return redirect('/')
    
    if request.method == 'POST':
        room_id = request.POST.get('room_id', '').strip().upper()
        user_id = request.session.get('user_id')
        user_name = request.session.get('user_name')
        
        if not room_id:
            messages.error(request, 'Please enter a room ID')
            return render(request, 'join_room.html')
        
        if room_id in rooms and rooms[room_id]['is_active']:
            # Add user to participants
            if room_id not in participants:
                participants[room_id] = []
            
            # Check if user already in room
            user_exists = any(p['user_id'] == user_id for p in participants[room_id])
            
            if not user_exists:
                participants[room_id].append({
                    'user_id': user_id,
                    'name': user_name,
                    'is_admin': False,
                    'video_enabled': True,
                    'audio_enabled': True
                })
            
            # Initialize chat if not exists
            if room_id not in chat_messages:
                chat_messages[room_id] = []
            
            # Initialize user streams if not exists
            if room_id not in user_streams:
                user_streams[room_id] = {}
            
            messages.success(request, f'Joined room successfully!')
            return redirect(f'/room/{room_id}/')
        else:
            messages.error(request, 'Room not found or inactive')
    
    return render(request, 'join_room.html')

def room(request, room_id):
    if not request.session.get('user_name'):
        return redirect('/')
    
    if room_id not in rooms:
        messages.error(request, 'Room not found')
        return redirect('/home/')
    
    user_id = request.session.get('user_id')
    
    # Check if user is in participants
    user_in_room = any(
        p['user_id'] == user_id 
        for p in participants.get(room_id, [])
    )
    
    if not user_in_room:
        messages.error(request, 'You are not a participant of this room')
        return redirect('/join-room/')
    
    # Check if user is admin (room creator)
    is_admin = rooms[room_id]['created_by_id'] == user_id
    
    # Get all participants for this room
    room_participants = participants.get(room_id, [])
    
    # Get chat messages for this room
    room_chat_messages = chat_messages.get(room_id, [])
    
    context = {
        'room_id': room_id,
        'room_name': rooms[room_id]['name'],
        'room_creator_id': rooms[room_id]['created_by_id'],
        'user_name': request.session.get('user_name'),
        'user_id': user_id,
        'is_admin': is_admin,
        'participants': room_participants,
        'chat_messages': room_chat_messages[-50:],  # Last 50 messages
    }
    
    return render(request, 'room.html', context)

def leave_room(request, room_id):
    user_id = request.session.get('user_id')
    if user_id and room_id in participants:
        # Remove user from participants
        participants[room_id] = [
            p for p in participants[room_id] 
            if p['user_id'] != user_id
        ]
        
        # Remove user from streams
        if room_id in user_streams and user_id in user_streams[room_id]:
            del user_streams[room_id][user_id]
        
        # Add leave message to chat
        if room_id in chat_messages:
            leaving_user = next((p for p in participants.get(room_id, []) if p['user_id'] == user_id), None)
            if leaving_user:
                system_message = {
                    'id': str(uuid.uuid4()),
                    'user_id': 'system',
                    'user_name': 'System',
                    'message': f'{leaving_user["name"]} has left the meeting',
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'is_system': True
                }
                chat_messages[room_id].append(system_message)
        
        # If no participants left, deactivate room
        if not participants[room_id]:
            rooms[room_id]['is_active'] = False
    
    messages.success(request, 'You have left the meeting')
    return redirect('/home/')

def get_participants(request, room_id):
    if room_id in participants:
        return JsonResponse({
            'participants': participants[room_id],
            'success': True
        })
    return JsonResponse({'participants': [], 'success': False})

# Chat functionality
def send_message(request, room_id):
    if request.method == 'POST':
        user_id = request.session.get('user_id')
        user_name = request.session.get('user_name')
        message_text = request.POST.get('message', '').strip()
        
        if message_text and room_id in chat_messages:
            # Create message object
            message = {
                'id': str(uuid.uuid4()),
                'user_id': user_id,
                'user_name': user_name,
                'message': message_text,
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'is_system': False
            }
            
            # Add message to chat
            chat_messages[room_id].append(message)
            
            # Keep only last 100 messages to prevent memory issues
            if len(chat_messages[room_id]) > 100:
                chat_messages[room_id] = chat_messages[room_id][-100:]
            
            return JsonResponse({'success': True, 'message': message})
    
    return JsonResponse({'success': False})

def get_messages(request, room_id):
    if room_id in chat_messages:
        return JsonResponse({'messages': chat_messages[room_id], 'success': True})
    return JsonResponse({'messages': [], 'success': False})

# Admin control functions
def mute_participant(request, room_id, user_id):
    if room_id in participants:
        for participant in participants[room_id]:
            if participant['user_id'] == user_id:
                participant['audio_enabled'] = not participant['audio_enabled']
                
                # Add system message
                if room_id in chat_messages:
                    action = "muted" if not participant['audio_enabled'] else "unmuted"
                    system_message = {
                        'id': str(uuid.uuid4()),
                        'user_id': 'system',
                        'user_name': 'System',
                        'message': f'{participant["name"]} has been {action}',
                        'timestamp': datetime.now().strftime('%H:%M:%S'),
                        'is_system': True
                    }
                    chat_messages[room_id].append(system_message)
                break
    return JsonResponse({'success': True})

def mute_all(request, room_id):
    if room_id in participants:
        admin_user_id = rooms[room_id]['created_by_id']
        muted_users = []
        
        for participant in participants[room_id]:
            # Don't mute the admin
            if participant['user_id'] != admin_user_id:
                if participant['audio_enabled']:  # Only mute if not already muted
                    participant['audio_enabled'] = False
                    muted_users.append(participant['name'])
        
        # Add system message
        if room_id in chat_messages and muted_users:
            system_message = {
                'id': str(uuid.uuid4()),
                'user_id': 'system',
                'user_name': 'System',
                'message': f'All participants have been muted',
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'is_system': True
            }
            chat_messages[room_id].append(system_message)
            
    return JsonResponse({'success': True, 'muted_count': len(muted_users)})

def remove_participant(request, room_id, user_id):
    if room_id in participants:
        # Find user to remove
        user_to_remove = next((p for p in participants[room_id] if p['user_id'] == user_id), None)
        
        if user_to_remove:
            # Remove user from participants
            participants[room_id] = [
                p for p in participants[room_id] 
                if p['user_id'] != user_id
            ]
            
            # Remove user from streams
            if room_id in user_streams and user_id in user_streams[room_id]:
                del user_streams[room_id][user_id]
            
            # Add system message
            if room_id in chat_messages:
                system_message = {
                    'id': str(uuid.uuid4()),
                    'user_id': 'system',
                    'user_name': 'System',
                    'message': f'{user_to_remove["name"]} has been removed from the meeting',
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'is_system': True
                }
                chat_messages[room_id].append(system_message)
    
    return JsonResponse({'success': True, 'removed_user': user_to_remove['name'] if user_to_remove else None})

def remove_all(request, room_id):
    # Remove all participants except the admin
    if room_id in participants:
        admin_user_id = rooms[room_id]['created_by_id']
        removed_users = [p for p in participants[room_id] if p['user_id'] != admin_user_id]
        
        # Clear all streams except admin
        if room_id in user_streams:
            user_streams[room_id] = {admin_user_id: user_streams[room_id].get(admin_user_id)}
        
        # Remove all participants except admin
        participants[room_id] = [p for p in participants[room_id] if p['user_id'] == admin_user_id]
        
        # Add system message
        if room_id in chat_messages and removed_users:
            system_message = {
                'id': str(uuid.uuid4()),
                'user_id': 'system',
                'user_name': 'System',
                'message': 'All participants have been removed from the meeting',
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'is_system': True
            }
            chat_messages[room_id].append(system_message)
    
    return JsonResponse({'success': True, 'removed_count': len(removed_users)})

# Stream management
def update_user_stream(request, room_id):
    if request.method == 'POST':
        user_id = request.session.get('user_id')
        video_enabled = request.POST.get('video_enabled', 'true') == 'true'
        audio_enabled = request.POST.get('audio_enabled', 'true') == 'true'
        
        if room_id in participants:
            for participant in participants[room_id]:
                if participant['user_id'] == user_id:
                    participant['video_enabled'] = video_enabled
                    participant['audio_enabled'] = audio_enabled
                    break
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False})
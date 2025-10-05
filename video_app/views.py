from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
import uuid
import random
import string

# Simple in-memory storage
rooms = {}
participants = {}

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
            return redirect('/home/')  # Use direct URL instead of reverse
        else:
            messages.error(request, 'Please fill in all fields')
    
    return render(request, 'landing.html')

def home(request):
    # Check if user has session data
    if not request.session.get('user_name'):
        messages.warning(request, 'Please enter your details first')
        return redirect('/')  # Use direct URL
    
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
            'created_at': 'now',
            'is_active': True
        }
        
        # Add creator as participant
        participants[room_id] = [{
            'user_id': user_id,
            'name': user_name,
            'is_admin': True
        }]
        
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
                    'is_admin': False
                })
            
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
    
    # Check if user is in participants
    user_in_room = any(
        p['user_id'] == request.session.get('user_id') 
        for p in participants.get(room_id, [])
    )
    
    if not user_in_room:
        messages.error(request, 'You are not a participant of this room')
        return redirect('/join-room/')
    
    # Get user's admin status
    user_is_admin = any(
        p['user_id'] == request.session.get('user_id') and p['is_admin'] 
        for p in participants.get(room_id, [])
    )
    
    context = {
        'room_id': room_id,
        'room_name': rooms[room_id]['name'],
        'user_name': request.session.get('user_name'),
        'user_id': request.session.get('user_id'),
        'is_admin': user_is_admin,
        'participants': participants.get(room_id, [])
    }
    
    return render(request, 'room.html', context)

def leave_room(request, room_id):
    user_id = request.session.get('user_id')
    if user_id and room_id in participants:
        participants[room_id] = [
            p for p in participants[room_id] 
            if p['user_id'] != user_id
        ]
    
    messages.success(request, 'You have left the meeting')
    return redirect('/home/')

def get_participants(request, room_id):
    if room_id in participants:
        return JsonResponse({'participants': participants[room_id]})
    return JsonResponse({'participants': []})
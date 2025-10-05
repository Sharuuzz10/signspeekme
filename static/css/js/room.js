let localStream;
let peer;
const peers = {};
const userStreams = {};

// Initialize PeerJS
peer = new Peer(userId, {
    host: '0.peerjs.com',
    port: 443,
    path: '/',
    secure: true
});

peer.on('open', (id) => {
    console.log('My peer ID is: ' + id);
    joinRoom();
});

peer.on('call', (call) => {
    // Answer the call with our local stream
    call.answer(localStream);
    
    call.on('stream', (remoteStream) => {
        // Display the remote stream
        addVideoStream(call.peer, remoteStream, call.metadata.userName);
    });
});

// Initialize media devices
async function initMedia() {
    try {
        localStream = await navigator.mediaDevices.getUserMedia({
            video: true,
            audio: true
        });
        
        // Display local video
        addVideoStream(userId, localStream, userName + ' (You)');
        
        // Notify others in the room
        notifyJoined();
        
    } catch (error) {
        console.error('Error accessing media devices:', error);
    }
}

function addVideoStream(userId, stream, name) {
    // Remove existing video if present
    const existingVideo = document.querySelector(`[data-user-id="${userId}"]`);
    if (existingVideo) {
        existingVideo.remove();
    }
    
    const videoGrid = document.getElementById('video-grid');
    const videoContainer = document.createElement('div');
    videoContainer.className = 'video-container';
    videoContainer.setAttribute('data-user-id', userId);
    
    const videoElement = document.createElement('video');
    videoElement.className = 'video-element';
    videoElement.srcObject = stream;
    videoElement.playsInline = true;
    videoElement.autoplay = true;
    videoElement.muted = userId === peer.id;
    
    const nameLabel = document.createElement('div');
    nameLabel.className = 'participant-name';
    nameLabel.textContent = name;
    
    videoContainer.appendChild(videoElement);
    videoContainer.appendChild(nameLabel);
    videoGrid.appendChild(videoContainer);
    
    userStreams[userId] = stream;
}

function notifyJoined() {
    // In a real application, you'd use WebSockets here
    // For simplicity, we'll use polling to update participant list
    updateParticipantList();
}

function callUser(userId, userName) {
    if (userId === peer.id) return;
    
    const call = peer.call(userId, localStream, {
        metadata: { userName: userName }
    });
    
    call.on('stream', (remoteStream) => {
        addVideoStream(userId, remoteStream, userName);
    });
    
    call.on('close', () => {
        removeVideoStream(userId);
    });
    
    peers[userId] = call;
}

function removeVideoStream(userId) {
    const videoElement = document.querySelector(`[data-user-id="${userId}"]`);
    if (videoElement) {
        videoElement.remove();
    }
    delete userStreams[userId];
    updateParticipantList();
}

function updateParticipantList() {
    fetch(`/api/room/${roomId}/participants/`)
        .then(response => response.json())
        .then(data => {
            const participantsList = document.getElementById('participants-list');
            const participantCount = document.getElementById('participant-count');
            
            participantCount.textContent = data.participants.length;
            
            participantsList.innerHTML = data.participants.map(participant => `
                <div class="participant-item" data-user-id="${participant.user_id}">
                    <div class="participant-avatar">
                        ${participant.name.charAt(0).toUpperCase()}
                    </div>
                    <div class="participant-info">
                        <div class="participant-name">${participant.name}</div>
                        <div class="participant-status">
                            ${participant.is_admin ? '(Host)' : ''}
                            ${!participant.audio_enabled ? '🔇' : ''}
                            ${!participant.video_enabled ? '📹 off' : ''}
                        </div>
                    </div>
                </div>
            `).join('');
            
            // Call new participants
            data.participants.forEach(participant => {
                if (participant.user_id !== userId && !peers[participant.user_id]) {
                    callUser(participant.user_id, participant.name);
                }
            });
        });
}

// Control functions
document.getElementById('toggle-video').addEventListener('click', function() {
    const videoTrack = localStream.getVideoTracks()[0];
    if (videoTrack) {
        videoTrack.enabled = !videoTrack.enabled;
        this.style.background = videoTrack.enabled ? '#404040' : '#ea4335';
    }
});

document.getElementById('toggle-audio').addEventListener('click', function() {
    const audioTrack = localStream.getAudioTracks()[0];
    if (audioTrack) {
        audioTrack.enabled = !audioTrack.enabled;
        this.style.background = audioTrack.enabled ? '#404040' : '#ea4335';
    }
});

document.getElementById('screen-share').addEventListener('click', async function() {
    try {
        const screenStream = await navigator.mediaDevices.getDisplayMedia({
            video: true
        });
        
        // Replace video track in all peer connections
        const videoTrack = screenStream.getVideoTracks()[0];
        Object.values(peers).forEach(call => {
            const sender = call.peerConnection.getSenders().find(s => 
                s.track && s.track.kind === 'video'
            );
            if (sender) {
                sender.replaceTrack(videoTrack);
            }
        });
        
        // Update local stream
        localStream.removeTrack(localStream.getVideoTracks()[0]);
        localStream.addTrack(videoTrack);
        
        videoTrack.onended = () => {
            // Switch back to camera when screen share ends
            switchToCamera();
        };
        
    } catch (error) {
        console.error('Error sharing screen:', error);
    }
});

async function switchToCamera() {
    try {
        const cameraStream = await navigator.mediaDevices.getUserMedia({
            video: true
        });
        const cameraTrack = cameraStream.getVideoTracks()[0];
        
        Object.values(peers).forEach(call => {
            const sender = call.peerConnection.getSenders().find(s => 
                s.track && s.track.kind === 'video'
            );
            if (sender) {
                sender.replaceTrack(cameraTrack);
            }
        });
        
        localStream.removeTrack(localStream.getVideoTracks()[0]);
        localStream.addTrack(cameraTrack);
        
    } catch (error) {
        console.error('Error switching to camera:', error);
    }
}

function leaveRoom() {
    // Close all peer connections
    Object.values(peers).forEach(call => call.close());
    
    // Stop local stream
    if (localStream) {
        localStream.getTracks().forEach(track => track.stop());
    }
    
    // Redirect to home
    window.location.href = `/room/${roomId}/leave/`;
}

// Admin functions
function muteAll() {
    if (!isAdmin) return;
    
    Object.values(peers).forEach(call => {
        // In a real application, you'd send a signal to mute the remote user
        console.log('Muting:', call.peer);
    });
}

function removeAll() {
    if (!isAdmin) return;
    
    if (confirm('Remove all participants from the meeting?')) {
        Object.values(peers).forEach(call => {
            call.close();
        });
    }
}

// Initialize room
function joinRoom() {
    initMedia();
    setInterval(updateParticipantList, 5000); // Update every 5 seconds
}

// Clean up on page unload
window.addEventListener('beforeunload', leaveRoom);
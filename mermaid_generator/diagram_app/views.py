from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import uuid
from .services import mermaid_generator
from .models import ChatSession, ChatMessage, DiagramHistory
from io import BytesIO
import base64

def chat_interface(request):
    """Main chat interface with sidebar preview"""
    # Create or get session
    session_id = request.session.get('chat_session_id')
    if not session_id:
        chat_session = ChatSession.objects.create()
        session_id = str(chat_session.session_id)
        request.session['chat_session_id'] = session_id
    else:
        try:
            chat_session = ChatSession.objects.get(session_id=session_id)
        except ChatSession.DoesNotExist:
            chat_session = ChatSession.objects.create()
            session_id = str(chat_session.session_id)
            request.session['chat_session_id'] = session_id
    
    # Get chat history
    chat_history = ChatMessage.objects.filter(session=chat_session).order_by('timestamp')
    
    return render(request, 'diagram_app/chat_interface.html', {
        'session_id': session_id,
        'chat_history': chat_history
    })

@csrf_exempt
@require_http_methods(["POST"])
def send_message(request):
    """Handle chat messages with context awareness"""
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id')
        
        if not user_message:
            return JsonResponse({'error': 'Message cannot be empty'}, status=400)
        
        # Generate contextual response
        result = mermaid_generator.generate_response_with_context(session_id, user_message)
        
        if 'error' in result:
            return JsonResponse({'error': result['error']}, status=500)
        
        # Save diagram if Mermaid code was generated
        if result.get('mermaid_code'):
            session = ChatSession.objects.get(session_id=session_id)
            DiagramHistory.objects.create(
                session=session,
                user_prompt=user_message,
                mermaid_code=result['mermaid_code']
            )
        
        return JsonResponse({
            'success': True,
            'response': result['response'],
            'mermaid_code': result.get('mermaid_code'),
            'session_id': result['session_id']
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
def get_chat_history(request, session_id):
    """Get chat history for a session"""
    try:
        session = ChatSession.objects.get(session_id=session_id)
        messages = ChatMessage.objects.filter(session=session).order_by('timestamp')
        
        history = []
        for msg in messages:
            history.append({
                'type': msg.message_type,
                'content': msg.content,
                'mermaid_code': msg.mermaid_code,
                'timestamp': msg.timestamp.isoformat()
            })
        
        return JsonResponse({'history': history})
        
    except ChatSession.DoesNotExist:
        return JsonResponse({'error': 'Session not found'}, status=404)

def new_session(request):
    """Start a new chat session"""
    chat_session = ChatSession.objects.create()
    session_id = str(chat_session.session_id)
    request.session['chat_session_id'] = session_id
    
    return JsonResponse({'session_id': session_id})

def simple_editor(request):
    """Simple fullscreen editor"""
    return render(request, 'diagram_app/fullscreen_editor.html')



@csrf_exempt
@require_http_methods(["POST"])
def save_diagram_edit(request):
    """Save edited diagram"""
    try:
        data = json.loads(request.body)
        diagram_id = data.get('diagram_id')
        mermaid_code = data.get('mermaid_code')
        title = data.get('title', 'Untitled Diagram')
        
        if diagram_id:
            # Update existing diagram
            diagram = DiagramHistory.objects.get(id=diagram_id)
            diagram.mermaid_code = mermaid_code
            diagram.save()
        else:
            # Create new diagram
            diagram = DiagramHistory.objects.create(
                user_prompt=title,
                mermaid_code=mermaid_code
            )
        
        return JsonResponse({
            'success': True,
            'diagram_id': diagram.id,
            'message': 'Diagram saved successfully'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


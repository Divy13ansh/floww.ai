from django.urls import path
from . import views

app_name = 'diagram_app'

urlpatterns = [
    path('', views.chat_interface, name='chat_interface'),
    path('send-message/', views.send_message, name='send_message'),
    path('chat-history/<str:session_id>/', views.get_chat_history, name='chat_history'),
    path('new-session/', views.new_session, name='new_session'),
    path('simple-editor/', views.simple_editor, name='simple_editor'),
    # path('editor/<int:diagram_id>/', views.fullscreen_editor, name='fullscreen_editor_with_id'),
    path('save-edit/', views.save_diagram_edit, name='save_diagram_edit'),
    # Keep old URLs for backward compatibility
    # path('old/', views.home, name='home'),
    # path('generate/', views.generate_diagram, name='generate_diagram'),
    # path('diagram/<int:diagram_id>/', views.diagram_detail, name='diagram_detail'),
]

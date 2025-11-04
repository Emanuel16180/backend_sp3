# apps/chat/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import ChatMessage
from .serializers import ChatMessageSerializer

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def chat_messages_view(request, appointment_id):
    if request.method == 'GET':
        # Obtener todos los mensajes de esta cita
        messages = ChatMessage.objects.filter(appointment_id=appointment_id)
        serializer = ChatMessageSerializer(messages, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        # Crear nuevo mensaje
        serializer = ChatMessageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(
                sender=request.user,
                appointment_id=appointment_id
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
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
    """
    Endpoint para Chat Simulado (HTTP Polling).
    """
    if request.method == 'GET':
        # 1. Obtener mensajes de la cita
        queryset = ChatMessage.objects.filter(appointment_id=appointment_id)
        
        # 2. LÓGICA DE POLING: Filtrar solo los nuevos
        # El frontend enviará ?last_id=50 para pedir solo los que llegaron después
        last_id = request.query_params.get('last_id')
        
        if last_id:
            queryset = queryset.filter(id__gt=last_id)
        
        # Ordenar por antigüedad (los más viejos primero para mantener el hilo)
        queryset = queryset.order_by('timestamp')
        
        serializer = ChatMessageSerializer(queryset, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        # Guardar mensaje nuevo (Esto no cambia)
        serializer = ChatMessageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(
                sender=request.user,
                appointment_id=appointment_id
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
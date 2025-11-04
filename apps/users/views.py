# apps/users/views.py

from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import PatientProfile
from .serializers import (
    UserDetailSerializer, 
    UserProfileSerializer, 
    PatientProfileSerializer,
    PatientCompleteProfileSerializer
)

@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def user_profile_detail(request):
    user = request.user
    
    if request.method == 'GET':
        serializer = UserDetailSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    elif request.method in ['PUT', 'PATCH']:
        partial = request.method == 'PATCH'
        serializer = UserProfileSerializer(user, data=request.data, partial=partial)
        
        if serializer.is_valid():
            serializer.save()
            updated_user = UserDetailSerializer(user)
            return Response({
                'message': 'Perfil actualizado exitosamente',
                'user': updated_user.data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'POST', 'PUT', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def patient_profile_detail(request):
    user = request.user
    
    if user.user_type != 'patient':
        return Response({'error': 'Solo para pacientes'}, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        try:
            patient_profile = user.patient_profile
            serializer = PatientProfileSerializer(patient_profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except PatientProfile.DoesNotExist:
            return Response({'message': 'Perfil de paciente no encontrado'}, status=status.HTTP_404_NOT_FOUND)
    
    elif request.method == 'POST':
        if hasattr(user, 'patient_profile'):
            return Response({'error': 'Ya tienes perfil de paciente'}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = PatientProfileSerializer(data=request.data)
        if serializer.is_valid():
            patient_profile = serializer.save(user=user)
            return Response({
                'message': 'Perfil de paciente creado',
                'profile': PatientProfileSerializer(patient_profile).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method in ['PUT', 'PATCH']:
        try:
            patient_profile = user.patient_profile
        except PatientProfile.DoesNotExist:
            return Response({'error': 'Perfil no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        
        partial = request.method == 'PATCH'
        serializer = PatientProfileSerializer(patient_profile, data=request.data, partial=partial)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Perfil actualizado',
                'profile': serializer.data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def update_complete_profile(request):
    user = request.user
    
    if user.user_type != 'patient':
        return Response({'error': 'Solo para pacientes'}, status=status.HTTP_403_FORBIDDEN)
    
    partial = request.method == 'PATCH'
    serializer = PatientCompleteProfileSerializer(user, data=request.data, partial=partial)
    
    if serializer.is_valid():
        serializer.save()
        updated_user = UserDetailSerializer(user)
        return Response({
            'message': 'Perfil completo actualizado',
            'user': updated_user.data
        }, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_account(request):
    password = request.data.get('password')
    if not password or not request.user.check_password(password):
        return Response({'error': 'Contraseña incorrecta'}, status=status.HTTP_400_BAD_REQUEST)
    
    request.user.is_active = False
    request.user.save()
    
    return Response({'message': 'Cuenta desactivada'}, status=status.HTTP_200_OK)
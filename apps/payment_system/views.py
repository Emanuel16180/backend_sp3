# apps/payment_system/views.py

import stripe
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, generics
from apps.appointments.models import Appointment
from apps.appointments.serializers import AppointmentCreateSerializer
from apps.professionals.models import CarePlan
from django.shortcuts import get_object_or_404
from apps.users.models import CustomUser
from apps.clinical_history.views import IsPatient
from django_tenants.utils import tenant_context  # <-- IMPORTAR TENANT_CONTEXT
from apps.tenants.models import Clinic  # <-- IMPORTAR CLÍNICA
from apps.professionals.serializers import CarePlanSerializer
from .models import PaymentTransaction, PatientPlan
from .serializers import PaymentTransactionSerializer, PaymentConfirmationSerializer, PatientPlanSerializer
from django.utils import timezone
from decimal import Decimal
import logging

# Configurar el logger
logger = logging.getLogger(__name__)

# Configurar Stripe con la clave secreta
stripe.api_key = settings.STRIPE_SECRET_KEY

from rest_framework.decorators import api_view, permission_classes

class CreateCheckoutSessionView(APIView):
    """
    Vista para crear una sesión de pago en Stripe.
    Proceso:
    1. Valida y crea una cita preliminar en estado 'pending'
    2. Crea la sesión de pago en Stripe
    3. Retorna el sessionId para redirigir al usuario
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        data = request.data
        psychologist_id = data.get('psychologist')
        
        # 1. Validar que los datos de la cita sean correctos (horario disponible, etc.)
        # Usamos el AppointmentCreateSerializer que ya tiene toda la lógica de validación de horarios
        serializer = AppointmentCreateSerializer(data=data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        validated_data = serializer.validated_data

        # --- CORRECCIÓN PARA ELIMINAR CITAS "FANTASMA" ---
        # Antes de crear la nueva cita, buscamos y eliminamos cualquier cita "fantasma"
        # (pendiente y no pagada) que ocupe el mismo horario.
        # Esto libera el espacio si un pago anterior fue abandonado.
        citas_fantasma_eliminadas = Appointment.objects.filter(
            psychologist=validated_data['psychologist'],
            appointment_date=validated_data['appointment_date'],
            start_time=validated_data['start_time'],
            status='pending',
            is_paid=False
        ).delete()
        
        if citas_fantasma_eliminadas[0] > 0:
            logger.info(f"Eliminadas {citas_fantasma_eliminadas[0]} citas fantasma para liberar el horario")
        # --- FIN DE LA CORRECCIÓN ---

        # Ahora que el espacio está libre, creamos la nueva cita preliminar de forma segura
        appointment = serializer.save(status='pending', is_paid=False)

        # 2. Obtener el precio de la consulta del psicólogo
        psychologist = validated_data['psychologist']  # Usar los datos ya validados
        
        # Verificar que el psicólogo tenga perfil profesional
        if not hasattr(psychologist, 'professional_profile'):
            appointment.delete()  # Limpiar la cita creada
            return Response({
                'error': 'Este usuario no tiene un perfil profesional configurado.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        fee = psychologist.professional_profile.consultation_fee
        
        if not fee or fee <= 0:
            appointment.delete()  # Limpiar la cita creada
            return Response({
                'error': 'Este profesional no tiene una tarifa configurada.'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # --- CORRECCIÓN PARA REDIRECCIÓN AL FRONTEND ---
            backend_host = request.get_host()
            
            # Determinar el protocolo y host del frontend
            if 'localhost' in backend_host or '127.0.0.1' in backend_host:
                # Desarrollo local
                if ':8000' in backend_host:
                    # Puertos comunes para React: 5174, 5173, 3000
                    for frontend_port in ['5174', '5173', '3000']:
                        frontend_host = backend_host.replace(':8000', f':{frontend_port}')
                        break
                else:
                    frontend_host = f"{backend_host}:3000"
                protocol = 'http'
            else:
                # Producción - usar HTTPS
                # Obtener el dominio del tenant desde el schema_name
                tenant_domain = request.tenant.schema_name
                if tenant_domain == 'public':
                    # Si es público, usar psicoadmin.xyz
                    frontend_host = 'psicoadmin.xyz'
                else:
                    # Para tenants específicos: bienestar.psicoadmin.xyz, mindcare.psicoadmin.xyz
                    frontend_host = f"{tenant_domain}.psicoadmin.xyz"
                protocol = 'https'
            
            logger.info(f"Redirigiendo pagos desde {backend_host} hacia {protocol}://{frontend_host}")
            # --- FIN DE LA CORRECCIÓN ---
            
            # 3. Crear la sesión de pago en Stripe
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price_data': {
                            'currency': 'usd',  # Puedes cambiar a 'bob' para bolivianos
                            'product_data': {
                                'name': f'Consulta con {psychologist.get_full_name()}',
                                'description': f'Cita agendada para el {appointment.appointment_date} a las {appointment.start_time}',
                            },
                            'unit_amount': int(fee * 100),  # Stripe maneja los montos en centavos
                        },
                        'quantity': 1,
                    },
                ],
                mode='payment',
                # URLs de redirección con protocolo correcto (http local, https producción)
                success_url=f"{protocol}://{frontend_host}/payment-success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{protocol}://{frontend_host}/payment-cancel",
                # Guardamos el ID de nuestra cita para saber qué actualizar después
                metadata={
                    'appointment_id': appointment.id,
                    'patient_id': request.user.id,
                    'psychologist_id': psychologist.id,
                    'tenant_schema_name': request.tenant.schema_name  # <-- GUARDAR EL SCHEMA
                }
            )
            
            logger.info(f"Sesión de pago creada: {checkout_session.id} para cita {appointment.id}")
            
            # --- CORRECCIÓN: Devolver URL directa en lugar de solo sessionId ---
            return Response({
                'sessionId': checkout_session.id,
                'checkout_url': checkout_session.url,  # <-- URL directa para redirigir
                'appointment_id': appointment.id,
                'amount': fee,
                'currency': 'USD'
            })

        except stripe.error.StripeError as e:
            # Si Stripe falla, borramos la cita preliminar para liberar el horario
            appointment.delete()
            logger.error(f"Error de Stripe: {str(e)}")
            return Response({
                'error': f'Error del servicio de pagos: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            # Error general
            appointment.delete()
            logger.error(f"Error general en checkout: {str(e)}")
            return Response({
                'error': 'Error interno del servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StripeWebhookView(APIView):
    """
    Vista para recibir eventos de Stripe.
    Maneja la confirmación de pagos exitosos.
    """
    permission_classes = [permissions.AllowAny]

def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        event = None

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.SignatureVerificationError as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            metadata = session.get('metadata', {})
            schema_name = metadata.get('tenant_schema_name')

            if not schema_name:
                logger.warning("Webhook recibido sin schema_name.")
                return Response(status=status.HTTP_400_BAD_REQUEST)

            try:
                tenant = Clinic.objects.get(schema_name=schema_name)
                with tenant_context(tenant):

                    # --- ¡AQUÍ ESTÁ LA NUEVA LÓGICA! ---
                    appointment_id = metadata.get('appointment_id')
                    plan_id = metadata.get('plan_id')

                    # Creamos la transacción PRIMERO
                    transaction = PaymentTransaction.objects.create(
                        patient=CustomUser.objects.get(id=metadata.get('patient_id')),
                        stripe_session_id=session.id,
                        stripe_payment_intent_id=session.get('payment_intent'),
                        amount=Decimal(session.get('amount_total', 0) / 100.0),
                        currency=session.get('currency', 'usd').upper(),
                        status='completed',
                        paid_at=timezone.now()
                    )
                    logger.info(f"Transacción {transaction.id} registrada en {schema_name}")

                    if appointment_id:
                        # --- 1. Es un pago de Cita Única ---
                        appointment = Appointment.objects.get(id=appointment_id)
                        appointment.is_paid = True
                        appointment.status = 'confirmed'
                        appointment.transaction = transaction # Vinculamos la transacción
                        appointment.save()
                        logger.info(f"Pago confirmado para Cita {appointment_id}")

                    elif plan_id:
                        # --- 2. Es un pago de Plan (CU-44) ---
                        plan = CarePlan.objects.get(id=plan_id)
                        PatientPlan.objects.get_or_create(
                            transaction=transaction, # Clave única
                            defaults={
                                'patient': transaction.patient,
                                'plan': plan,
                                'total_sessions': plan.number_of_sessions,
                                'sessions_used': 0,
                                'is_active': True
                            }
                        )
                        logger.info(f"Plan {plan.id} comprado por paciente {transaction.patient.id}")

            except Exception as e:
                logger.error(f"Error procesando webhook en {schema_name}: {e}")

        # ... (tu lógica de 'checkout.session.expired' no cambia) ...

        return Response(status=status.HTTP_200_OK)


class PaymentStatusView(APIView):
    """
    Vista para verificar el estado de un pago específico
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, appointment_id):
        try:
            appointment = Appointment.objects.get(
                id=appointment_id,
                patient=request.user
            )
            
            return Response({
                'appointment_id': appointment.id,
                'is_paid': appointment.is_paid,
                'status': appointment.status,
                'appointment_date': appointment.appointment_date,
                'start_time': appointment.start_time,
                'psychologist': appointment.psychologist.get_full_name(),
                'consultation_fee': appointment.consultation_fee
            })
            
        except Appointment.DoesNotExist:
            return Response({
                'error': 'Cita no encontrada'
            }, status=status.HTTP_404_NOT_FOUND)


class GetStripePublicKeyView(APIView):
    """
    Vista para obtener la clave pública de Stripe (necesaria para el frontend)
    """
    permission_classes = [permissions.AllowAny]  # Clave pública, puede ser accesible
    
    def get(self, request):
        return Response({
            'publicKey': settings.STRIPE_PUBLISHABLE_KEY
        })

class PaymentHistoryListView(generics.ListAPIView):
    """
    Endpoint para que un paciente vea su historial de pagos.
    """
    serializer_class = PaymentTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filtra los pagos solo para el usuario autenticado."""
        return PaymentTransaction.objects.filter(
            patient=self.request.user
        ).order_by('-paid_at')

class ConfirmPaymentView(generics.GenericAPIView):
    """
    NUEVO: Endpoint para que el Frontend confirme el pago 
    después de ser redirigido por Stripe.
    """
    serializer_class = PaymentConfirmationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            logger.error(f"🚨 Error de validación en confirmación de pago: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # --- 👇 2. OBTENER DATOS VALIDADOS (PUEDE SER CITA O PLAN) 👇 ---
        validated_data = serializer.validated_data
        session = validated_data.get('stripe_session')
        appointment = validated_data.get('appointment') # Será None si es un plan
        plan = validated_data.get('plan')             # Será None si es una cita

        if not session or (not appointment and not plan):
            logger.error("🚨 Serializer no devolvió session Y (appointment o plan)")
            return Response(
                {"error": "No se pudo validar la sesión de pago (datos faltantes)."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 3. El resto de tu lógica para crear la PaymentTransaction...
        try:
            # Obtenemos el paciente desde la metadata de Stripe
            patient_id = session.metadata.get('patient_id')
            patient = CustomUser.objects.get(id=patient_id)
            
            # Creamos el registro en 'payment_transactions'
            transaction, created = PaymentTransaction.objects.update_or_create(
                stripe_session_id=session.id,
                defaults={
                    'patient': patient,
                    'stripe_payment_intent_id': session.get('payment_intent'),
                    'amount': Decimal(session.get('amount_total', 0) / 100.0),
                    'currency': session.get('currency', 'usd').upper(),
                    'status': 'completed',
                    'paid_at': timezone.now()
                    # No asignamos 'appointment' aquí directamente
                }
            )
            logger.info(f"✅ Transacción creada: {transaction.id}. Nuevo: {created}")

            # --- 👇 4. LÓGICA CONDICIONAL 👇 ---
            if appointment:
                # --- CASO 1: Es un pago de CITA ---
                transaction.appointment = appointment
                transaction.save()

                # Actualizamos la cita
                appointment.is_paid = True
                appointment.status = 'confirmed'
                appointment.save()
                logger.info(f"✅ Cita actualizada: {appointment.id}")

                # Devolvemos los datos de la cita
                appointment_data = {
                    "id": appointment.id,
                    "appointment_date": appointment.appointment_date,
                    "start_time": appointment.start_time.strftime('%H:%M'),
                    "psychologist_name": appointment.psychologist.get_full_name(),
                    "status": appointment.get_status_display(),
                }
                return Response({"appointment": appointment_data}, 
                                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
            
            elif plan:
                # --- CASO 2: Es un pago de PLAN ---
                patient_plan, plan_created = PatientPlan.objects.get_or_create(
                    transaction=transaction, # La clave única es la transacción
                    defaults={
                        'patient': patient,
                        'plan': plan,
                        'total_sessions': plan.number_of_sessions,
                        'sessions_used': 0,
                        'is_active': True
                    }
                )
                logger.info(f"✅ Plan {plan.id} comprado. Creado ahora: {plan_created}")
                # Devolvemos los datos del plan comprado
                plan_data = {
                    "id": patient_plan.id,
                    "plan_title": plan.title,
                    "sessions_remaining": patient_plan.sessions_remaining,
                    "purchased_at": patient_plan.purchased_at
                }
                return Response({"plan": plan_data},
                                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


        except Exception as e:
            logger.error(f"🚨 Error al crear la transacción o confirmar la cita/plan: {e}", exc_info=True)
            return Response(
                {"error": "Hubo un error al procesar la confirmación en el servidor."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class ListPlansForPurchaseView(generics.ListAPIView):
    """
    Endpoint para que un Paciente (GET) vea los planes
    disponibles de un psicólogo específico.
    """
    serializer_class = CarePlanSerializer
    permission_classes = [IsPatient]

    def get_queryset(self):
        psychologist_id = self.request.query_params.get('psychologist_id')
        if not psychologist_id:
            return CarePlan.objects.none()
        return CarePlan.objects.filter(
            psychologist_id=psychologist_id,
            is_active=True
        )


class PurchasePlanView(APIView):
    """
    Endpoint para que un Paciente (POST) compre un Plan
    con Stripe (similar a 'CreateCheckoutSessionView').
    """
    permission_classes = [IsPatient]

    def post(self, request, *args, **kwargs):
        plan_id = request.data.get('plan_id')
        try:
            plan = CarePlan.objects.get(id=plan_id, is_active=True)
        except CarePlan.DoesNotExist:
            return Response({"error": "Plan no encontrado o inactivo."}, status=status.HTTP_404_NOT_FOUND)

        # (Lógica de Stripe copiada de CreateCheckoutSessionView)
        try:
            backend_host = request.get_host()
            
            # Determinar el protocolo y host del frontend
            if 'localhost' in backend_host or '127.0.0.1' in backend_host:
                # Desarrollo local
                if ':8000' in backend_host:
                    frontend_host = backend_host.replace(':8000', ':5174')
                else:
                    frontend_host = f"{backend_host}:3000"
                protocol = 'http'
            else:
                # Producción - usar HTTPS
                # Obtener el dominio del tenant desde el schema_name
                tenant_domain = request.tenant.schema_name
                if tenant_domain == 'public':
                    frontend_host = 'psicoadmin.xyz'
                else:
                    frontend_host = f"{tenant_domain}.psicoadmin.xyz"
                protocol = 'https'

            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd', # O 'bob'
                        'product_data': {
                            'name': f"Plan: {plan.title}",
                            'description': f"{plan.number_of_sessions} sesiones con {plan.psychologist.get_full_name()}",
                        },
                        'unit_amount': int(plan.total_price * 100), # Stripe usa centavos
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=f"{protocol}://{frontend_host}/payment-success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{protocol}://{frontend_host}/payment-cancel",
                metadata={
                    'plan_id': plan.id, # <-- Marcamos que esto es un PLAN
                    'patient_id': request.user.id,
                    'tenant_schema_name': request.tenant.schema_name
                }
            )

            logger.info(f"Sesión de pago para PLAN {plan.id} creada: {checkout_session.id}")
            return Response({
                'sessionId': checkout_session.id,
                'checkout_url': checkout_session.url,
            })

        except Exception as e:
            logger.error(f"Error de Stripe al comprar plan: {str(e)}")
            return Response({'error': 'Error del servicio de pagos'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MyPurchasedPlansView(generics.ListAPIView):
    """
    Endpoint para que un Paciente (GET) vea los planes que ha
    comprado y cuántas sesiones le quedan.
    """
    serializer_class = PatientPlanSerializer
    permission_classes = [IsPatient]

    def get_queryset(self):
        return PatientPlan.objects.filter(
            patient=self.request.user,
            is_active=True
        )


# ============================================
# ENDPOINTS PARA FLUTTER MOBILE (Payment Intent)
# ============================================

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_payment_intent_appointment(request):
    """
    Crea Payment Intent para pagar cita desde Flutter mobile.
    Retorna client_secret para usar con flutter_stripe Payment Sheet.
    
    POST /api/payments/mobile/create-intent-appointment/
    Body: {
        "psychologist": 14,
        "appointment_date": "2025-11-25",
        "start_time": "10:00",
        "reason": "Consulta inicial"
    }
    """
    data = request.data
    
    # Validar y crear cita preliminar
    serializer = AppointmentCreateSerializer(data=data, context={'request': request})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    validated_data = serializer.validated_data
    
    # Limpiar citas fantasma
    Appointment.objects.filter(
        psychologist=validated_data['psychologist'],
        appointment_date=validated_data['appointment_date'],
        start_time=validated_data['start_time'],
        status='pending',
        is_paid=False
    ).delete()
    
    # Crear cita preliminar
    appointment = serializer.save(status='pending', is_paid=False)
    
    # Obtener tarifa
    psychologist = validated_data['psychologist']
    if not hasattr(psychologist, 'professional_profile'):
        appointment.delete()
        return Response({
            'error': 'Este usuario no tiene un perfil profesional configurado.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    fee = psychologist.professional_profile.consultation_fee
    if not fee or fee <= 0:
        appointment.delete()
        return Response({
            'error': 'Este profesional no tiene una tarifa configurada.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Obtener o crear cliente de Stripe
        patient = request.user
        if not patient.stripe_customer_id:
            customer = stripe.Customer.create(
                email=patient.email,
                name=f"{patient.first_name} {patient.last_name}"
            )
            patient.stripe_customer_id = customer.id
            patient.save()
        
        # Crear Payment Intent
        payment_intent = stripe.PaymentIntent.create(
            amount=int(fee * 100),  # Convertir a centavos
            currency='usd',
            customer=patient.stripe_customer_id,
            metadata={
                'appointment_id': appointment.id,
                'patient_id': patient.id,
                'psychologist_id': psychologist.id,
                'tenant_schema_name': request.tenant.schema_name,
                'payment_type': 'appointment'
            },
            description=f'Cita con {psychologist.get_full_name()}'
        )
        
        logger.info(f"Payment Intent creado: {payment_intent.id} para cita {appointment.id}")
        
        return Response({
            'client_secret': payment_intent.client_secret,
            'payment_intent_id': payment_intent.id,
            'appointment_id': appointment.id,
            'amount': fee,
            'currency': 'usd',
            'publishable_key': settings.STRIPE_PUBLISHABLE_KEY
        })
        
    except stripe.error.StripeError as e:
        appointment.delete()
        logger.error(f"Error de Stripe: {str(e)}")
        return Response({
            'error': f'Error del servicio de pagos: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        appointment.delete()
        logger.error(f"Error general: {str(e)}")
        return Response({
            'error': 'Error interno del servidor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_payment_intent_plan(request):
    """
    Crea Payment Intent para comprar plan desde Flutter mobile.
    
    POST /api/payments/mobile/create-intent-plan/
    Body: {
        "plan_id": 5
    }
    """
    plan_id = request.data.get('plan_id')
    
    if not plan_id:
        return Response({
            'error': 'plan_id es requerido'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        plan = CarePlan.objects.get(id=plan_id, is_active=True)
    except CarePlan.DoesNotExist:
        return Response({
            'error': 'Plan no encontrado o inactivo'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Verificar que el usuario no tenga ya este plan activo
    existing_plan = PatientPlan.objects.filter(
        patient=request.user,
        plan=plan,
        is_active=True,
        end_date__gte=timezone.now()
    ).first()
    
    if existing_plan:
        return Response({
            'error': 'Ya tienes este plan activo'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Obtener o crear cliente de Stripe
        patient = request.user
        if not patient.stripe_customer_id:
            customer = stripe.Customer.create(
                email=patient.email,
                name=f"{patient.first_name} {patient.last_name}"
            )
            patient.stripe_customer_id = customer.id
            patient.save()
        
        # Crear Payment Intent
        payment_intent = stripe.PaymentIntent.create(
            amount=int(plan.price * 100),
            currency='usd',
            customer=patient.stripe_customer_id,
            metadata={
                'plan_id': plan.id,
                'patient_id': patient.id,
                'tenant_schema_name': request.tenant.schema_name,
                'payment_type': 'plan'
            },
            description=f'Plan: {plan.name}'
        )
        
        logger.info(f"Payment Intent para plan creado: {payment_intent.id}")
        
        return Response({
            'client_secret': payment_intent.client_secret,
            'payment_intent_id': payment_intent.id,
            'plan_id': plan.id,
            'amount': plan.price,
            'currency': 'usd',
            'publishable_key': settings.STRIPE_PUBLISHABLE_KEY
        })
        
    except stripe.error.StripeError as e:
        logger.error(f"Error de Stripe: {str(e)}")
        return Response({
            'error': f'Error del servicio de pagos: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        logger.error(f"Error general: {str(e)}")
        return Response({
            'error': 'Error interno del servidor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def confirm_payment_intent(request):
    """
    Confirma que el pago fue exitoso y actualiza la cita/plan.
    Flutter llama a este endpoint después de presentPaymentSheet().
    
    POST /api/payments/mobile/confirm-payment/
    Body: {
        "payment_intent_id": "pi_xxxxx"
    }
    """
    payment_intent_id = request.data.get('payment_intent_id')
    
    if not payment_intent_id:
        return Response({
            'error': 'payment_intent_id es requerido'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Obtener Payment Intent de Stripe
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        
        if payment_intent.status != 'succeeded':
            return Response({
                'error': 'El pago no ha sido completado',
                'status': payment_intent.status
            }, status=status.HTTP_400_BAD_REQUEST)
        
        metadata = payment_intent.metadata
        payment_type = metadata.get('payment_type')
        
        # Verificar el tenant
        if metadata.get('tenant_schema_name') != request.tenant.schema_name:
            return Response({
                'error': 'Tenant incorrecto'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if payment_type == 'appointment':
            # Confirmar cita
            appointment_id = int(metadata.get('appointment_id'))
            appointment = Appointment.objects.get(id=appointment_id)
            
            if appointment.is_paid:
                return Response({
                    'message': 'Esta cita ya fue pagada',
                    'appointment_id': appointment.id
                })
            
            appointment.is_paid = True
            appointment.status = 'scheduled'
            appointment.save()
            
            # Crear registro de transacción
            PaymentTransaction.objects.create(
                user=request.user,
                appointment=appointment,
                amount=Decimal(payment_intent.amount) / 100,
                currency=payment_intent.currency.upper(),
                stripe_payment_intent_id=payment_intent.id,
                status='completed'
            )
            
            logger.info(f"Cita {appointment.id} confirmada vía mobile")
            
            return Response({
                'success': True,
                'message': 'Pago confirmado exitosamente',
                'appointment_id': appointment.id,
                'status': 'scheduled'
            })
            
        elif payment_type == 'plan':
            # Activar plan
            plan_id = int(metadata.get('plan_id'))
            plan = CarePlan.objects.get(id=plan_id)
            
            # Verificar si ya existe
            existing = PatientPlan.objects.filter(
                patient=request.user,
                plan=plan,
                stripe_payment_intent_id=payment_intent.id
            ).first()
            
            if existing:
                return Response({
                    'message': 'Este plan ya fue activado',
                    'patient_plan_id': existing.id
                })
            
            # Crear plan de paciente
            from datetime import timedelta
            patient_plan = PatientPlan.objects.create(
                patient=request.user,
                plan=plan,
                start_date=timezone.now(),
                end_date=timezone.now() + timedelta(days=plan.duration_days),
                sessions_remaining=plan.total_sessions,
                is_active=True,
                stripe_payment_intent_id=payment_intent.id
            )
            
            # Crear transacción
            PaymentTransaction.objects.create(
                user=request.user,
                patient_plan=patient_plan,
                amount=Decimal(payment_intent.amount) / 100,
                currency=payment_intent.currency.upper(),
                stripe_payment_intent_id=payment_intent.id,
                status='completed'
            )
            
            logger.info(f"Plan {plan.id} activado vía mobile para usuario {request.user.id}")
            
            return Response({
                'success': True,
                'message': 'Plan activado exitosamente',
                'patient_plan_id': patient_plan.id,
                'sessions_remaining': patient_plan.sessions_remaining
            })
        
        else:
            return Response({
                'error': 'Tipo de pago desconocido'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Appointment.DoesNotExist:
        return Response({
            'error': 'Cita no encontrada'
        }, status=status.HTTP_404_NOT_FOUND)
    except CarePlan.DoesNotExist:
        return Response({
            'error': 'Plan no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except stripe.error.StripeError as e:
        logger.error(f"Error de Stripe: {str(e)}")
        return Response({
            'error': f'Error del servicio de pagos: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        logger.error(f"Error en confirmación: {str(e)}")
        return Response({
            'error': 'Error interno del servidor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
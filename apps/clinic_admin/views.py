import csv
import io
from django.http import HttpResponse

from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q

from apps.users.models import CustomUser
from apps.users.serializers import UserDetailSerializer
from apps.professionals.models import ProfessionalProfile
from .permissions import IsClinicAdmin

from apps.payment_system.models import PaymentTransaction
from apps.payment_system.serializers import PaymentReportSerializer
from django.db.models import Sum, F, DecimalField
from decimal import Decimal

from apps.professionals.models import VerificationDocument 
from apps.professionals.serializers import VerificationDocumentSerializer
from datetime import date, timedelta

from django.http import QueryDict
from .ai_parser import parse_prompt_to_filters

from apps.tenants.models import Clinic
from .serializers import BackupConfigSerializer
import logging
logger = logging.getLogger('apps')

class UserManagementViewSet(viewsets.ModelViewSet):
    """
    Gestión de usuarios (pacientes y profesionales) para administradores de la clínica.
    CU-30: Administrar usuarios.
    Incluye acción para verificar profesionales (CU-07).
    """
    serializer_class = UserDetailSerializer
    permission_classes = [IsClinicAdmin]

    def get_queryset(self):
        qs = CustomUser.objects.all().order_by('-date_joined')
        # Filtros opcionales (búsqueda rápida por email/nombre o tipo)
        user_type = self.request.query_params.get('user_type')
        search = self.request.query_params.get('search')
        if user_type:
            qs = qs.filter(user_type=user_type)
        if search:
            qs = qs.filter(
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        return qs

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=['is_active'])

    @action(detail=True, methods=['get'], url_path='verification-documents')
    def list_verification_documents(self, request, pk=None):
        """
        NUEVO: Obtiene la lista de documentos de verificación
        subidos por un profesional.
        """
        user = self.get_object()
        if user.user_type != 'professional':
            return Response({'error': 'Este usuario no es un profesional.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            profile = user.professional_profile
            # Buscamos los documentos asociados a este perfil
            documents = profile.verification_documents.all() 
            
            # Usamos el serializer que creamos en el paso anterior
            serializer = VerificationDocumentSerializer(documents, many=True)
            
            # Devolvemos la respuesta en el formato que espera el frontend
            return Response({"results": serializer.data}) 
        
        except ProfessionalProfile.DoesNotExist:
            return Response({'error': 'Este profesional no tiene perfil.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': f'Error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='verify-profile')
    def verify_profile(self, request, pk=None):
        user = self.get_object()
        if user.user_type != 'professional':
            return Response({'error': 'Este usuario no es un profesional.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            profile = user.professional_profile
        except ProfessionalProfile.DoesNotExist:
            return Response({'error': 'Este profesional no tiene un perfil para verificar.'}, status=status.HTTP_404_NOT_FOUND)
        if getattr(profile, 'is_verified', None) is True:
            return Response({'status': 'El perfil ya estaba verificado.'}, status=status.HTTP_200_OK)
        setattr(profile, 'is_verified', True)
        profile.save(update_fields=['is_verified'])
        return Response({'status': 'Perfil profesional verificado con éxito.'})

class PaymentReportView(viewsets.ReadOnlyModelViewSet):
    """
    NUEVO: Endpoint para que el Admin genere reportes de pagos (CU-32)
    con filtros dinámicos.
    """
    serializer_class = PaymentReportSerializer
    permission_classes = [IsClinicAdmin] # Solo Admins

    def get_queryset(self):
        # Empezamos con todos los pagos completados
        queryset = PaymentTransaction.objects.filter(status='completed')

        # --- Aplicamos los Filtros Dinámicos ---
        # A. Filtro por ID de Psicólogo (El que usa tu Dropdown)
        # Aceptamos 'psychologist' o 'psychologist_id' por si acaso
        psychologist_id = self.request.query_params.get('psychologist') or self.request.query_params.get('psychologist_id')
        
        if psychologist_id:
            # ¡IMPORTANTE! Buscamos en Citas O en Planes
            queryset = queryset.filter(
                Q(appointment__psychologist_id=psychologist_id) |
                Q(patient_plan__plan__psychologist_id=psychologist_id)
            )

# --- FILTRO INTELIGENTE DE PSICÓLOGO ---
        psy_search = self.request.query_params.get('psychologist_search')
        if psy_search:
            # Dividimos "Ernesto Valverde" en ["Ernesto", "Valverde"]
            terms = psy_search.split()
            
            # Lógica: Cada palabra debe estar en el nombre O en el apellido
            # Y debe buscar tanto en Citas (appointment) como en Planes (patient_plan)
            for term in terms:
                queryset = queryset.filter(
                    # Busca en Citas
                    Q(appointment__psychologist__first_name__icontains=term) |
                    Q(appointment__psychologist__last_name__icontains=term) |
                    # O busca en Planes
                    Q(patient_plan__plan__psychologist__first_name__icontains=term) |
                    Q(patient_plan__plan__psychologist__last_name__icontains=term)
                )

        # --- FILTRO INTELIGENTE DE PACIENTE ---
        pat_search = self.request.query_params.get('patient_search')
        if pat_search:
            terms = pat_search.split()
            for term in terms:
                queryset = queryset.filter(
                    Q(patient__first_name__icontains=term) |
                    Q(patient__last_name__icontains=term)
                )

        # --- FILTROS DE FECHA ---
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        if start_date:
            queryset = queryset.filter(paid_at__gte=start_date)
        if end_date:
            try:
                # Sumamos 1 día para incluir el día final completo
                end_date_dt = date.fromisoformat(end_date) + timedelta(days=1)
                queryset = queryset.filter(paid_at__lt=end_date_dt)
            except ValueError:
                pass

        return queryset.order_by('-paid_at')

    def get_serializer_context(self):
        # Pasamos el % de ganancia de la clínica al serializer
        context = super().get_serializer_context()
        context['clinic_percentage'] = self.request.tenant.clinic_fee_percentage
        return context

    def list(self, request, *args, **kwargs):
        # Sobrescribimos 'list' para añadir el resumen de TOTALES
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        # --- Cálculo de TOTALES ---
        clinic_percentage = request.tenant.clinic_fee_percentage

        # Usamos F() y annotate para que la BD haga el cálculo
        totals = queryset.aggregate(
            total_revenue=Sum('amount'),
            total_clinic_earning=Sum(
                (F('amount') * clinic_percentage / 100),
                output_field=DecimalField()
            )
        )

        total_psychologist_earning = (totals['total_revenue'] or 0) - (totals['total_clinic_earning'] or 0)

        return Response({
            'summary': {
                'total_transactions': queryset.count(),
                'total_revenue': totals['total_revenue'] or 0,
                'total_clinic_earning': totals['total_clinic_earning'] or 0,
                'total_psychologist_earning': total_psychologist_earning,
                'clinic_percentage': clinic_percentage
            },
            'transactions': serializer.data
        })

    # apps/clinic_admin/views.py
    # Dentro de: class PaymentReportView(viewsets.ReadOnlyModelViewSet):

    # ... (las funciones get_queryset, get_serializer_context, y list... no cambian) ...

    # --- 👇 INICIO DE LA NUEVA IDEA (DESCARGA CSV) 👇 ---
    @action(detail=False, methods=['get'])
    def download_csv(self, request, *args, **kwargs):
        """
        Endpoint para descargar el reporte de pagos filtrado en formato CSV.
        Acepta los mismos filtros que la vista 'list'.
        """
        queryset = self.get_queryset()
        transactions = self.get_serializer(queryset, many=True).data

        # --- Calcular Sumario (copiado de la función 'list') ---
        clinic_percentage = request.tenant.clinic_fee_percentage
        totals = queryset.aggregate(
            total_revenue=Sum('amount'),
            total_clinic_earning=Sum(
                (F('amount') * clinic_percentage / 100),
                output_field=DecimalField()
            )
        )
        total_psychologist_earning = (totals['total_revenue'] or 0) - (totals['total_clinic_earning'] or 0)
        # --- Fin del Sumario ---

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="reporte_pagos_{date.today()}.csv"'

        writer = csv.writer(response)

        # Escribir Resumen
        writer.writerow(['Resumen del Reporte'])
        writer.writerow(['Ingresos Totales', totals['total_revenue'] or 0])
        writer.writerow(['Ganancia Clínica', totals['total_clinic_earning'] or 0])
        writer.writerow(['Ganancia Psicólogos', total_psychologist_earning])
        writer.writerow(['Porcentaje Clínica', f"{clinic_percentage}%"])
        writer.writerow([]) # Línea en blanco

        # Escribir Cabeceras de Transacciones
        writer.writerow([
            'Fecha de Pago', 
            'Paciente', 
            'Psicólogo', 
            'Monto Total', 
            'Ganancia Clínica', 
            'Ganancia Psicólogo'
        ])

        # Escribir Datos de Transacciones
        for t in transactions:
            writer.writerow([
                t['paid_at'],
                t['patient_name'],
                t['psychologist_name'],
                t['amount'],
                t['clinic_earning'],
                t['psychologist_earning']
            ])

        return response

    @action(detail=False, methods=['get'])
    def download_pdf(self, request, *args, **kwargs):
        """
        Endpoint para descargar el reporte de pagos filtrado en formato PDF.
        Acepta los mismos filtros que la vista 'list'.
        """
        queryset = self.get_queryset()
        transactions = self.get_serializer(queryset, many=True).data

        # --- Calcular Sumario (copiado de la función 'list') ---
        clinic_percentage = request.tenant.clinic_fee_percentage
        totals = queryset.aggregate(
            total_revenue=Sum('amount'),
            total_clinic_earning=Sum(
                (F('amount') * clinic_percentage / 100),
                output_field=DecimalField()
            )
        )
        total_psychologist_earning = (totals['total_revenue'] or 0) - (totals['total_clinic_earning'] or 0)
        # --- Fin del Sumario ---

        # Configuración del PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=inch/2, leftMargin=inch/2, topMargin=inch/2, bottomMargin=inch/2)
        elements = []
        
        # 👇 AQUÍ ESTÁ LA CORRECCIÓN: Inicializar 'styles'
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='small', parent=styles['Normal'], fontSize=8, leading=10))

        # Título
        elements.append(Paragraph(f"Reporte de Pagos - {request.tenant.name}", styles['Heading1']))
        elements.append(Paragraph(f"Generado el: {date.today()}", styles['Normal']))
        elements.append(Spacer(1, 0.25*inch))

        # Resumen
        elements.append(Paragraph("Resumen de Totales", styles['Heading3']))
        summary_data = [
            ['Ingresos Totales:', f"{totals['total_revenue'] or 0} USD"],
            [f'Ganancia Clínica ({clinic_percentage}%):', f"{totals['total_clinic_earning'] or 0} USD"],
            ['Ganancia Psicólogos:', f"{total_psychologist_earning} USD"],
        ]
        summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 0.25*inch))

        # Cabeceras de Transacciones
        elements.append(Paragraph("Transacciones Detalladas", styles['Heading3']))
        table_data = [[
            'Fecha de Pago', 
            'Paciente', 
            'Psicólogo', 
            'Monto', 
            'G. Clínica', 
            'G. Psicólogo'
        ]]

        # Datos de Transacciones
        for t in transactions:
            table_data.append([
                Paragraph(t['paid_at'], styles['small']),
                Paragraph(t['patient_name'], styles['small']),
                Paragraph(t['psychologist_name'], styles['small']),
                f"{t['amount']} {t['currency']}",
                f"{t['clinic_earning']}",
                f"{t['psychologist_earning']}"
            ])

        # Crear Tabla de Transacciones
        trans_table = Table(table_data, colWidths=[1.5*inch, 2.5*inch, 2.5*inch, 1*inch, 1*inch, 1*inch])
        trans_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#00008B')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.aliceblue, colors.white]),
        ]))
        elements.append(trans_table)

        doc.build(elements)

        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="reporte_pagos_{date.today()}.pdf"'
        return response

    @action(detail=False, methods=['post'])
    def generate_smart_report(self, request):
        """
        POST /api/admin/reports/payments/generate_smart_report/
        Body: { "prompt": "Dame los pagos de Ana Torres de la semana pasada en pdf" }
        """
        prompt = request.data.get('prompt')
        if not prompt:
            return Response({'error': 'Escribe qué reporte necesitas.'}, status=400)

        # 1. Preguntar a la IA
        logger.info(f"🧠 Analizando prompt: {prompt}")
        ai_filters = parse_prompt_to_filters(prompt)
        
        if not ai_filters:
            return Response({'error': 'No entendí la consulta. Intenta ser más específico.'}, status=400)

        logger.info(f"✅ Filtros generados: {ai_filters}")

        # 2. Inyectar los filtros en la Request
        # (Hacemos esto para reutilizar la lógica de download_pdf/csv sin duplicar código)
        new_params = request.GET.copy()
        new_params.update(ai_filters)
        request._request.GET = new_params 

        # 3. Generar el archivo
        report_type = ai_filters.get('report_type', 'pdf').lower()

        if report_type == 'csv':
            return self.download_csv(request)
        else:
            return self.download_pdf(request)

class BackupConfigView(generics.RetrieveUpdateAPIView):
    """
    Endpoint para que un Admin de clínica vea (GET) y 
    actualice (PUT/PATCH) la configuración de backups automáticos.
    """
    serializer_class = BackupConfigSerializer
    permission_classes = [IsClinicAdmin]

    def get_object(self):
        # El "objeto" que estamos editando es la propia
        # clínica (tenant) a la que el admin está conectado.
        return self.request.tenant

    def perform_update(self, serializer):
        # Guardamos el cambio
        serializer.save()
        
        # Registramos en el log de auditoría
        logger.info(
            f"Admin '{self.request.user.email}' actualizó la config de backup a "
            f"'{serializer.validated_data.get('backup_schedule')}'"
        )
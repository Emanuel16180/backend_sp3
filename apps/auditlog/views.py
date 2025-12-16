# apps/auditlog/views.py
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.http import HttpResponse
from django.utils import timezone
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from io import BytesIO
from .models import LogEntry
from .serializers import LogEntrySerializer
from apps.clinic_admin.permissions import IsClinicAdmin

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para que los administradores de la clínica
    vean los registros de la bitácora.
    """
    serializer_class = LogEntrySerializer
    permission_classes = [permissions.IsAuthenticated, IsClinicAdmin]

    def get_queryset(self):
        queryset = LogEntry.objects.all().order_by('-timestamp')

        # --- Lógica de filtrado en el servidor ---
        level = self.request.query_params.get('level')
        search = self.request.query_params.get('search')

        if level:
            queryset = queryset.filter(level__iexact=level)

        if search:
            queryset = queryset.filter(
                Q(action__icontains=search) |
                Q(user__email__icontains=search) |
                Q(ip_address__icontains=search)
            )

        return queryset

    @action(detail=False, methods=['get'], url_path='export-pdf')
    def export_pdf(self, request):
        """
        Exportar bitácora filtrada a PDF
        """
        # Aplicar los mismos filtros que en get_queryset
        queryset = self.get_queryset()
        
        # Crear el PDF en memoria
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        
        # Contenedor para los elementos del PDF
        elements = []
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1e3a8a'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        # Título
        tenant_name = request.tenant.name if hasattr(request, 'tenant') else 'Sistema'
        title = Paragraph(f'Reporte de Bitácora - {tenant_name}', title_style)
        elements.append(title)
        
        # Fecha de generación
        fecha = Paragraph(
            f'Fecha de generación: {timezone.now().strftime("%d/%m/%Y %H:%M:%S")}',
            styles['Normal']
        )
        elements.append(fecha)
        elements.append(Spacer(1, 20))
        
        # Filtros aplicados
        filters_applied = []
        if request.query_params.get('level'):
            filters_applied.append(f"Nivel: {request.query_params.get('level')}")
        if request.query_params.get('search'):
            filters_applied.append(f"Búsqueda: {request.query_params.get('search')}")
        
        if filters_applied:
            filters_text = Paragraph(
                f'<b>Filtros aplicados:</b> {", ".join(filters_applied)}',
                styles['Normal']
            )
            elements.append(filters_text)
            elements.append(Spacer(1, 20))
        
        # Tabla de registros
        data = [['Fecha/Hora', 'Usuario', 'Acción', 'Nivel', 'IP']]
        
        for log in queryset[:500]:  # Limitar a 500 registros
            user_email = log.user.email if log.user else 'Sistema'
            timestamp = log.timestamp.strftime('%d/%m/%Y %H:%M')
            action = log.action[:50] + '...' if len(log.action) > 50 else log.action
            
            data.append([
                timestamp,
                user_email[:30],
                action,
                log.level,
                log.ip_address or 'N/A'
            ])
        
        # Crear tabla
        table = Table(data, colWidths=[1.8*inch, 1.8*inch, 2.2*inch, 0.8*inch, 1.2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        
        elements.append(table)
        
        # Pie de página con total de registros
        elements.append(Spacer(1, 20))
        total_text = Paragraph(
            f'<b>Total de registros en este reporte:</b> {len(data) - 1}',
            styles['Normal']
        )
        elements.append(total_text)
        
        # Generar PDF
        doc.build(elements)
        
        # Preparar respuesta
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        filename = f'bitacora_{timezone.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response

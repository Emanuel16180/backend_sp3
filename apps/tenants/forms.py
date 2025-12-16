# apps/tenants/forms.py

from django.contrib.auth.forms import AuthenticationForm

class PublicAdminAuthenticationForm(AuthenticationForm):
    """
    Formulario de autenticación para el admin público que usa 'email' en lugar de 'username'.
    """
    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        # Cambiamos la etiqueta del campo 'username' para que pida el email
        self.fields['username'].label = 'Email'
        self.fields['username'].help_text = 'Ingrese su dirección de correo electrónico'
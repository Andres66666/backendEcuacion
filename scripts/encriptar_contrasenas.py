from django.contrib.auth.hashers import make_password
from users.models import Usuario

# Cifra la contraseña del usuario 'andy'
usuario = Usuario.objects.get(nombre='Andres Benito')
usuario.password = make_password('Andres1234*')  # Reemplaza '1234' con la contraseña actual en texto plano
usuario.save()

""" Paso 1 """
""" python manage.py shell    """

""" Paso 2 """
""" exec(open('scripts/encriptar_contrasenas.py').read()) """
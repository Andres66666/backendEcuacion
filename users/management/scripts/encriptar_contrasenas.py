from django.contrib.auth.hashers import make_password
from users.models import Usuarios

# Cifra la contraseña del usuario 'andy'
usuario = Usuarios.objects.get(nombre_usuario='Andres Benito')
usuario.password = make_password('Andres1234*')  # Reemplaza '1234' con la contraseña actual en texto plano
usuario.save()

""" Paso 1 """
""" python manage.py shell    """

""" Paso 2 """
""" exec(open('scripts/encriptar_contrasenas.py').read()) """
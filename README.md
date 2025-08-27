<h1 align="center">🏗Backend Ecuacion </h1>

<table align="center" style="width: 100%; text-align: center; border-collapse: collapse; border: 1px solid blue; border-radius: 15px; background-color: #f4f4f9; box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1); padding: 20px;">
  <tr>
    <td style="border: none; padding: 0; padding-right: 20px;">
      <h1 style="font-size: 100px; margin: 0; color: #e53e3e; font-family: 'Arial', sans-serif; text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);">Django</h1>
    </td>
    <td style="border: none; padding: 0;">
      <img src="https://www.opengis.ch/wp-content/uploads/2020/04/django-python-logo.png" alt="Django Logo" width="100" style="transition: transform 0.3s ease-in-out;" onmouseover="this.style.transform='scale(1.1)'" onmouseout="this.style.transform='scale(1)'">
    </td>
  </tr>
</table>
R de prueba 
---

## 🛠 Instalaciones realizadas

---

### 1️⃣ Crear la carpeta del proyecto
```bash
mkdir BackendBarraca
cd BackendBarraca
```

### 2️⃣ Instalación de virtualenv
```bash
pip install virtualenv
```
### 3️⃣ Actualización de pip
```bash
python.exe -m pip install --upgrade pip
```
### 4️⃣ Creación de un entorno virtual
```bash
virtualenv venv
```
### 5️⃣ Activación del entorno virtual
```bash
./venv/Scripts/activate
```
### 6️⃣ Instalación de Django
```bash
pip install django
```
### 7️⃣ Instalación de Django REST Framework
```bash
pip install djangorestframework
pip install drf-spectacular
```
### 8️⃣ Instalación de Django REST Framework Simple JWT
```bash
pip install djangorestframework-simplejwt
```
### 9️⃣ Instalación de Django CORS Headers
```bash
pip install django-cors-headers
```
### 🔟 Instalación de psycopg2 (adaptador de PostgreSQL)
```bash
pip install psycopg2
```
### 1️⃣1️⃣ Creación de un nuevo proyecto Django `BackendBarraca`
```bash
django-admin startproject main .
```
### 1️⃣2️⃣ Creación de una nueva aplicación Django `BackendBarraca`
```bash
django-admin startapp users

```
### 1️⃣3️⃣ Creación de archivos en la aplicación `users`
```bash
# Ejemplo (venv) PS E:\BarracaSantaCruz\BackendBarraca> New-Item users/urls.py -ItemType File
# Crear el archivo serializers.py
New-Item users/serializers.py -ItemType File

# Crear el archivo urls.py
New-Item users/urls.py -ItemType File
```
---
### 🚀 Comandos útiles
---
### ▶️ Levantar el servidor de desarrollo
```bash
python manage.py runserver
```
### 🧩 Crear un nuevo modelo y migrarlos a la BD
```bash
python manage.py makemigrations
python manage.py migrate
```
### 🔧 Crear un superusuario
```bash
python manage.py createsuperuser
```
### 📦 Construcción de producción
```bash
python manage.py collectstatic
```
---
### 📦 Configuración de Prettier en .vscode
---

```bash
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode", // Recomendado para Django
  "editor.formatOnSaveMode": "file",
  "files.autoSave": "off",
  "[python]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```
### Instala las dependencias necesarias
```bash
pip install --save-dev black
```
###
```bash
```
## 🗄️ Base de Datos PostgreSQL
<table align="center" style="width: 100%; text-align: center; border-collapse: collapse; border: 1px solid blue; border-radius: 15px; background-color: #f4f4f9; box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1); padding: 20px;">
  <tr>
    <td style="border: none; padding: 0; padding-right: 20px;">
      <h1 style="font-size: 100px; margin: 0; color: #e53e3e; font-family: 'Arial', sans-serif; text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);">Base de Datos PostgreSQL</h1>
    </td>
    <td style="border: none; padding: 0;">
      <img src="https://upload.wikimedia.org/wikipedia/commons/2/29/Postgresql_elephant.svg" alt="PostgreSQL Logo" width="100" style="transition: transform 0.3s ease-in-out;" onmouseover="this.style.transform='scale(1.1)'" onmouseout="this.style.transform='scale(1)'">
    </td>
  </tr>
</table>
### Base de Datos Local
Para la implementación local en Django, puedes configurar tu base de datos PostgreSQL de la siguiente manera:

```bash
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'freemarket',
        'USER': 'postgres',
        'PASSWORD': 'Contraseña',
        'HOST': 'localhost',
        'PORT': '5433',
    }
}
```
### Base de Datos en el servidor
implementacion Servidor en Django
```bash
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'freemarket'),  # Valor por defecto si no existe la variable
        'USER': os.getenv('DB_USER', 'freemarket_user'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'E56Q9mldBA52Gh47RYBRlrZubgEoREJB'),
        'HOST': os.getenv('DB_HOST', 'dpg-cvmkk7umcj7s738tjtog-a.oregon-postgres.render.com'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}
```

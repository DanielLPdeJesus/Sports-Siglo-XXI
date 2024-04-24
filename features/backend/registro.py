import json
import pyrebase
import os
from flask import Blueprint, redirect, render_template, request, flash
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import base64



config = {
    "apiKey": "AIzaSyDZ3HF7aQ5GchQAy9wu6Jn3293e-UpGi3M",
    "authDomain": "seguridadinfo-308ce.firebaseapp.com",
    "databaseURL": "https://seguridadinfo-308ce-default-rtdb.firebaseio.com",
    "projectId": "seguridadinfo-308ce",
    "storageBucket": "seguridadinfo-308ce.appspot.com",
    "messagingSenderId": "388981953527",
    "appId": "1:388981953527:web:acf31898d798614a7814f2"
}

app = Blueprint('registro', __name__, url_prefix='/')

firebase = pyrebase.initialize_app(config)
auth = firebase.auth()
db = firebase.database()

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes

@app.route('/registrarme', methods=['POST'])
def registrarme():
    name = request.form['name']
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    number = request.form['number']

    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    password_encrypted = private_key.public_key().encrypt(
        password.encode('utf-8'),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

  
    password_encrypted_base64 = base64.b64encode(password_encrypted).decode('utf-8')

    

    try:
        user = auth.create_user_with_email_and_password(email, password)
        auth.send_email_verification(user['idToken'])
        datos = {
            "name": name,
            "username": username,
            "email": email,
            "number": number,
            'password': password_encrypted_base64  # Almacena la contraseña encriptada en la base de datos
        }
        db.child('users').child(user['localId']).set(datos)
        flash('¡Registro exitoso! Se ha enviado un correo de verificación a tu dirección de correo electrónico.', 'success')
        print('Registro exitoso. Correo de verificación enviado.')
        return redirect('/login')
    except Exception as e:
        print(str(e))
        flash('Error durante el registro. Por favor, inténtalo de nuevo.', 'danger')
        print('error durante el registro')
        return redirect('/registro')


@app.route('/pagos', methods=['POST'])
def pagos():
    campos_cifrados = {
        "numero": request.form['numero'],
        "fecha": request.form['fecha'],
        "cvv": request.form['cvv']
    }

    datos_planos = {
        "nombre": request.form['nombre'],
        "banco": request.form['banco']
    }

    clave_aes = os.urandom(16)
    iv_aes = b'miivultrasecreta'

    cipher = Cipher(algorithms.AES(clave_aes), modes.GCM(iv_aes), backend=default_backend())
    encryptor = cipher.encryptor()
    
    campos_cifrados_json = json.dumps(campos_cifrados).encode('utf-8')
    campos_cifrados_aes = encryptor.update(campos_cifrados_json) + encryptor.finalize()
    
    tag_aes = encryptor.tag

    campos_cifrados_base64 = base64.b64encode(campos_cifrados_aes).decode('utf-8')
    tag_base64 = base64.b64encode(tag_aes).decode('utf-8')

    datos_cifrados = {
        "campos_cifrados": campos_cifrados_base64,
        "tag_aes": tag_base64
    }

    datos_cifrados.update(datos_planos)

    db.child('pagos').push(datos_cifrados)
    print(datos_cifrados)
    print(datos_planos)
    print(campos_cifrados)
    return redirect('/producto')

@app.route('/regis', methods=['POST'])
def regis():
   
    nombre = request.form['nombre']
    correo = request.form['correo']
    telefono = request.form['telefono']
    asunto = request.form['asunto']
    mensaje_original = request.form['mensaje']

    keys_data = db.child('keys').get().val()
    if keys_data:
        public_key_base64 = keys_data.get('publicKey', '')
        private_key_base64 = keys_data.get('privateKey', '')

        # Decodificar las claves desde base64
        public_key_pem = base64.b64decode(public_key_base64)
        private_key_pem = base64.b64decode(private_key_base64)

        # Cargar las claves utilizando cryptography
        public_key = serialization.load_pem_public_key(public_key_pem, backend=default_backend())
        private_key = serialization.load_pem_private_key(private_key_pem, password=None, backend=default_backend())

    mensaje_cifrado = public_key.encrypt(
        mensaje_original.encode('utf-8'),
        padding.OAEP(
           mgf=padding.MGF1(algorithm=hashes.SHA256()),
             algorithm=hashes.SHA256(),
            label=None
        )
    )

    # Codifica el mensaje cifrado en base64 para almacenarlo en la base de datos
    mensaje_cifrado_base64 = base64.b64encode(mensaje_cifrado).decode('utf-8')

    # Almacena los datos cifrados en Firebase
    datos = {
        "nombre": nombre,
        "correo": correo,
        "telefono": telefono,
        "asunto": asunto,
        "mensaje": mensaje_cifrado_base64
    }

    db.child('contac').push(datos)  

    
    return redirect('/contacto')

@app.route('/datosencri')
def datosencri():
    # Obtener datos de Firebase
    contac_data = db.child('contac').get().val()

    # Convertir datos a una lista de diccionarios
    datos = []
    for key, value in contac_data.items():
        datos.append(value)

    # Obtener la clave privada desde Firebase
    keys_data = db.child('keys').get().val()
    if keys_data:
        private_key_base64 = keys_data.get('privateKey', '')

        # Decodificar la clave privada desde base64
        private_key_pem = base64.b64decode(private_key_base64)

        # Cargar la clave privada utilizando cryptography
        private_key = serialization.load_pem_private_key(private_key_pem, password=None, backend=default_backend())

        # Tu lógica adicional aquí...

        print(datos)
        # Renderizar la plantilla HTML con los datos
        return render_template('/datoscontac.html', datos=datos)
    else:
        # Manejar caso en el que no se encontró la clave privada
        return "Error: Clave privada no encontrada en Firebase."

@app.route('/datos')
def datos():
    # Obtener datos de Firebase
    contac_data = db.child('contac').get().val()

    # Convertir datos a una lista de diccionarios
    datos = []

    # Obtener las claves desde Firebase
    keys_data = db.child('keys').get().val()
    
    if keys_data:
        public_key_base64 = keys_data.get('publicKey', '')
        private_key_base64 = keys_data.get('privateKey', '')

        # Decodificar las claves desde base64
        public_key_pem = base64.b64decode(public_key_base64)
        private_key_pem = base64.b64decode(private_key_base64)

        # Cargar las claves utilizando cryptography
        public_key = serialization.load_pem_public_key(public_key_pem, backend=default_backend())
        private_key = serialization.load_pem_private_key(private_key_pem, password=None, backend=default_backend())

        for key, value in contac_data.items():
            try:
                mensaje_cifrado_base64 = value.get('mensaje', '')  
                mensaje_cifrado = base64.b64decode(mensaje_cifrado_base64)  

                mensaje_desencriptado = private_key.decrypt(
                    mensaje_cifrado,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                ).decode('utf-8')

                value['mensaje'] = mensaje_desencriptado

            except ValueError as e:
                # Manejo del error específico de desencriptación
                print("Error en la desencriptación. Posible causa: clave incorrecta.")
                value['mensaje'] = "Error en la desencriptación hubo un cambio de administrador. Mensaje no disponible."
            except Exception as e:
                print(f"Ocurrió un error inesperado: {e}")
                value['mensaje'] = "Error inesperado. Mensaje no disponible."

            datos.append(value)

    return render_template('/datoscontac2.html', datos=datos)

###############################################################################################
def generar_claves():
    # Genera un par de claves RSA
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    # Obtiene la clave pública
    public_key = private_key.public_key()

    # Convierte las claves a formato PEM y luego a cadena base64
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    private_key_base64 = base64.b64encode(private_pem).decode("utf-8")
    public_key_base64 = base64.b64encode(public_pem).decode("utf-8")

    return public_key_base64, private_key_base64

def guardar_claves_en_firebase(public_key, private_key):
    # Guarda las claves en la base de datos de Firebase
    ref = db.child("keys")
    ref.update({
        "publicKey": public_key,
        "privateKey": private_key
    })



@app.route('/llaves12', methods=['GET', 'POST'])
def llaves():
    if request.method == 'POST':
        public_key, private_key = generar_claves()
        guardar_claves_en_firebase(public_key, private_key)
        return render_template('generar_llave.html')
    
    return render_template('generar_llave.html')

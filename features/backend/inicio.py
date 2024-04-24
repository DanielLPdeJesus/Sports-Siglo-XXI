import pyrebase
from flask import Blueprint, request, session, redirect, render_template,url_for, flash
app = Blueprint('sesion', __name__, url_prefix='/sesion')

# Configuración de Firebase
config = {
    "apiKey": "AIzaSyDZ3HF7aQ5GchQAy9wu6Jn3293e-UpGi3M",
    "authDomain": "seguridadinfo-308ce.firebaseapp.com",
    "databaseURL": "https://seguridadinfo-308ce-default-rtdb.firebaseio.com",
    "projectId": "seguridadinfo-308ce",
    "storageBucket": "seguridadinfo-308ce.appspot.com",
    "messagingSenderId": "388981953527",
    "appId": "1:388981953527:web:acf31898d798614a7814f2"
}

firebase = pyrebase.initialize_app(config)
auth = firebase.auth()

@app.route('/iniciar', methods=['GET', 'POST'])
def iniciar_sesion():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            user = auth.sign_in_with_email_and_password(email, password)

            # Verifica si el correo electrónico ha sido verificado
            if auth.get_account_info(user['idToken'])['users'][0]['emailVerified']:
                # Permitir acceso solo si el correo está verificado
                if email == 'daniel@gmail.com' and password == '123456':
                    session['usuario2'] = email
                    return redirect('/generar_llave')
                else:
                    session['usuario'] = email
                    return redirect('/home2')
            else:
                flash('¡Verifica tu correo electrónico antes de iniciar sesión!')
                print('verifica tu correo antes de iniciar sesion')
                return redirect('/login')
        except Exception as e:
            print(str(e))
            flash('Error durante el inicio de sesión. Por favor, verifica tus credenciales y vuelve a intentarlo.', 'danger')
            print('error durnate el inicio de sesion')
            return redirect('/login')

    return render_template('login.html')

@app.route('/registrarse', methods=['POST'])
def registrarse():
    email = request.form['email']
    password = request.form['password']

    try:
        auth.create_user_with_email_and_password(email, password)
        # Nuevo usuario registrado correctamente
        return redirect('/login')  
    except Exception as e:
        
        print(str(e)) 
        return redirect('/registro') 
    


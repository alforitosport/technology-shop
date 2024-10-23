from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from werkzeug.security import generate_password_hash, check_password_hash  # Para manejar contraseñas seguras

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'tu_clave_secreta'  # Cambia a una clave secreta y segura
db = SQLAlchemy(app)

# Modelo de Usuario
class Usuario(db.Model):
    __tablename__ = 'usuario'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return f'<Usuario {self.nombre}>'

# Modelo de Compra
class Compra(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    numero_tarjeta = db.Column(db.String(16), nullable=False)
    fecha_expiracion = db.Column(db.String(5), nullable=False)
    cvv = db.Column(db.String(3), nullable=False)

    def __repr__(self):
        return f'<Compra {self.nombre}>'

# Crear la base de datos
with app.app_context():
    db.create_all()

@app.route('/', methods=['GET', 'POST'])
def home():
    # Verificar si el usuario ya está autenticado
    if 'usuario_id' in session:
        # Si ya está autenticado, redirigir a la página de bienvenida
        usuario = Usuario.query.get(session['usuario_id'])  # Obtener el usuario actual
        return redirect(url_for('welcome', nombre=usuario.nombre))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        usuario = Usuario.query.filter_by(email=email).first()  # Busca solo por email
        if usuario and usuario.password == password:  # Comprueba la contraseña
            session['usuario_id'] = usuario.id  # Almacena el ID del usuario en la sesión
            return redirect(url_for('welcome', nombre=usuario.nombre))  # Redirigir a la página de bienvenida
        else:
            return "Credenciales inválidas"  # Mensaje de error si las credenciales son incorrectas
    
    return render_template('home.html')  # Esto se ejecuta para el método GET

@app.route('/welcome')
def welcome():
    usuario_id = session.get('usuario_id')  # Obtiene el ID del usuario de la sesión
    if usuario_id:
        usuario = Usuario.query.get(usuario_id)  # Busca el usuario en la base de datos
        return render_template('welcome.html', nombre=usuario.nombre)  # Pasa el nombre a la plantilla
    return redirect(url_for('home'))  # Redirigir al home si no hay usuario en sesión

@app.route('/payment', methods=['GET', 'POST'])
def payment():
    if request.method == 'POST':
        # Aquí puedes manejar la lógica de pago con los datos del formulario
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        country = request.form['country']
        card_number = request.form['card_number']
        exp_date = request.form['exp_date']
        cvv = request.form['cvv']
        # Lógica adicional para procesar el pago
        return redirect(url_for('success'))  # Redirigir a una página de éxito

    return render_template('payment.html')

@app.route('/success')
def success():
    return "Payment was successful!"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        usuario = Usuario.query.filter_by(email=email).first()  # Cambiado a solo filtrar por email
        if usuario and check_password_hash(usuario.password, password):  # Comprobar el hash de la contraseña
            session['usuario_id'] = usuario.id  # Guardar el ID del usuario en la sesión
            return redirect(url_for('welcome', nombre=usuario.nombre))
        else:
            flash("Credenciales inválidas")  # Usar flash para mensajes de error
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        password = request.form.get('password')
        if Usuario.query.filter_by(email=email).first():
            flash("El correo electrónico ya está en uso. Por favor, elige otro.")  # Usar flash para mensajes
            return redirect(url_for('register'))
        nuevo_usuario = Usuario(nombre=nombre, email=email, password=generate_password_hash(password))  # Hashear la contraseña
        db.session.add(nuevo_usuario)
        db.session.commit()
        flash("Registro exitoso. Puedes iniciar sesión.")  # Mensaje de éxito
        return redirect(url_for('home'))
    return render_template('register.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('usuario_id', None)  # Eliminar el ID del usuario de la sesión
    return redirect(url_for('home'))  # Redirigir a la página de inicio

@app.route('/borrar_cuenta', methods=['POST'])
def borrar_cuenta():
    usuario_id = session.get('usuario_id')  # Obtener el ID del usuario de la sesión
    if usuario_id:
        usuario = Usuario.query.get(usuario_id)  # Obtener el usuario de la base de datos
        if usuario:
            db.session.delete(usuario)  # Eliminar el usuario
            db.session.commit()  # Guardar los cambios en la base de datos
            session.pop('usuario_id', None)  # Eliminar el ID del usuario de la sesión
            flash("Cuenta eliminada exitosamente.")  # Mensaje de éxito
            return redirect(url_for('home'))  # Redirigir a la página de inicio
    flash("No se pudo borrar la cuenta.")  # Mensaje de error
    return redirect(url_for('home')), 400  # Manejar el error si no se encuentra el usuario

@app.route('/usuarios', methods=['GET'])
def listar_usuarios():
    search_query = request.args.get('search')  # Obtener la consulta de búsqueda desde el formulario

    if search_query:
        # Verificar si la búsqueda es numérica para buscar por ID
        if search_query.isdigit():
            usuarios = Usuario.query.filter(Usuario.id == int(search_query)).all()
        else:
            # Buscar usuarios por nombre o email
            usuarios = Usuario.query.filter(
                or_(
                    Usuario.nombre.ilike(f'%{search_query}%'),
                    Usuario.email.ilike(f'%{search_query}%')
                )
            ).all()
    else:
        # Si no se proporciona búsqueda, mostrar todos los usuarios
        usuarios = Usuario.query.all()

    return render_template('usuarios.html', usuarios=usuarios)

# Ruta para el formulario de compra
@app.route('/comprar', methods=['GET', 'POST'])
def comprar():
    if request.method == 'POST':
        nombre = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        numero_tarjeta = request.form.get('card_number')
        fecha_expiracion = request.form.get('exp_date')
        cvv = request.form.get('cvv')

        nueva_compra = Compra(
            nombre=nombre, 
            email=email, 
            password=password, 
            numero_tarjeta=numero_tarjeta, 
            fecha_expiracion=fecha_expiracion, 
            cvv=cvv
        )

        db.session.add(nueva_compra)
        db.session.commit()

        flash("Compra realizada con éxito")
        return redirect(url_for('home'))
    
    return render_template('compra.html')


if __name__ == '__main__':
    app.run(debug=True)

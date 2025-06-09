from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your_secret_key' # Zmień na bezpieczny klucz
    app.config['TEMPLATES_AUTO_RELOAD'] = True # Dodaj tę linię

    from .routes import main_blueprint
    app.register_blueprint(main_blueprint)

    return app

if __name__ == '__main__':
    # To jest do uruchamiania deweloperskiego bezpośrednio
    # W Dockerze użyjemy Gunicorn lub innego serwera WSGI
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
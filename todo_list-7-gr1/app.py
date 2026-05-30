from flask import Flask
import secrets
from db.init import close_db_init, init_db_command_init, seed_db_command_init
from api.routes import api
from web.routes import web

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_urlsafe(16)
app.register_blueprint(api, url_prefix="/api")
app.register_blueprint(web)

close_db_init(app)
init_db_command_init(app)
seed_db_command_init(app)

if __name__ == "__main__":
    app.run(debug=True)
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
import os

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')  # Deployment
app.config['SECRET_KEY'] = '62f768c1bee1ef382d720ad6'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)

from Attendance import routes


# For PostgreSQL
def enable_foreign_keys(connection):
    connection.cursor().execute("SET CONSTRAINTS ALL IMMEDIATE")

# # --------*******For SQLite***********----------
# # To enable Foreign Key
# from sqlalchemy import event
# from sqlalchemy.engine import Engine
#
#
# @event.listens_for(Engine, "connect")
# def enable_foreign_keys(conn, branch):
#     conn.execute('PRAGMA foreign_keys=ON')
# # --------******************----------

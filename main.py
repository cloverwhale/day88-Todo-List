from flask import Flask, render_template, flash, url_for, request, jsonify
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import redirect
from forms import LoginForm, RegisterForm

import os

app = Flask(__name__)

# Heroku workaround
db_uri = os.getenv("DATABASE_URL", "sqlite:///todolist.db")
if db_uri.startswith("postgres://"):
    db_uri = db_uri.replace("postgres://", "postgresql://", 1)

# Database support
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# User session related
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
login_manager = LoginManager()
login_manager.init_app(app)

# Forms and template
Bootstrap(app)


# Database
class User(UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), unique=True, nullable=False)
    email = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    lists = relationship("TodoList", back_populates="owner")


class TodoList(db.Model):
    __tablename__ = "todo_list"
    list_id = db.Column(db.Integer, primary_key=True)
    list_title = db.Column(db.String(250))
    owner_id = db.Column(db.Integer, ForeignKey('user.id'))
    owner = relationship("User", back_populates="lists")
    tasks = relationship("Task", back_populates="parent_list")


# TODO: implement tag and due_date
class Task(db.Model):
    __tablename__ = "task"
    task_id = db.Column(db.Integer, primary_key=True)
    list_id = db.Column(db.Integer, ForeignKey('todo_list.list_id'))
    task_name = db.Column(db.String(250))
    due_date = db.Column(db.DateTime(250))
    tag = db.Column(db.String(250))
    is_completed = db.Column(db.Boolean(250))
    parent_list = relationship("TodoList", back_populates="tasks")

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


db.create_all()


# User session ------------------------------------------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


# API ---------------------------------------------------------------------
@app.route("/save", methods=["POST"])
@login_required
def save():
    current_todo_lists = TodoList.query.filter_by(owner_id=current_user.id).all()
    if len(current_todo_lists) == 5:
        flash('You have reached the maximum of 5 todo lists.')
        return '', 400
    else:
        list_data = request.json
        new_list = TodoList(
            list_title=list_data["list_title"],
            owner_id=list_data["list_owner"],
        )
        db.session.add(new_list)
        db.session.flush()
        task_list = list_data["tasks"]
        for i in range(len(task_list)):
            task = Task(
                list_id=new_list.list_id,
                task_name=task_list[i].get("task_name"),
                is_completed=task_list[i].get("completed"),
            )
            db.session.add(task)
        db.session.commit()
        return '', 204


@app.route("/update", methods=["PATCH"])
@login_required
def update():
    input_list_data = request.json
    input_list_id = int(input_list_data["list_id"])
    list_to_update = TodoList.query.filter_by(list_id=input_list_id).first()

    not_found = {"not_found": f"List id '{input_list_id}' not found."}

    if list_to_update is None:
        return jsonify(error=not_found), 404
    else:
        list_to_update.list_title = input_list_data["list_title"]
        tasks_to_empty = Task.query.filter_by(list_id=list_to_update.list_id).all()
        for task in tasks_to_empty:
            db.session.delete(task)

        task_list = input_list_data["tasks"]

        for i in range(len(task_list)):
            task = Task(
                list_id=list_to_update.list_id,
                task_name=task_list[i].get("task_name"),
                is_completed=task_list[i].get("completed"),
            )
            db.session.add(task)
        db.session.commit()
        return '', 204


@app.route("/delete", methods=["DELETE"])
@login_required
def delete():
    input_list_id = int(request.json["list_id"])
    list_to_delete = TodoList.query.filter_by(list_id=input_list_id).first()
    not_found = {"not_found": f"List id '{input_list_id}' not found."}

    if list_to_delete is None:
        return jsonify(error=not_found), 404
    else:
        tasks_to_delete = Task.query.filter_by(list_id=list_to_delete.list_id).all()
        for task in tasks_to_delete:
            db.session.delete(task)
        db.session.delete(list_to_delete)
        db.session.commit()
        return '', 204


# UI ---------------------------------------------------------------------
@app.route("/")
def list_index():
    all_lists = []
    if current_user.is_authenticated:
        todo_lists = TodoList.query.filter_by(owner_id=current_user.id).all()
        for item in todo_lists:
            db_tasks = Task.query.filter_by(list_id=item.list_id).all()
            tasks_details = [task.to_dict() for task in db_tasks]
            list_item = dict()
            list_item["list_id"] = item.list_id
            list_item["list_title"] = item.list_title
            list_item["tasks"] = tasks_details
            all_lists.append(list_item)
    return render_template("index.html", todo_lists=all_lists)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    register_form = RegisterForm()
    if register_form.validate_on_submit():
        salted_pass = generate_password_hash(
            password=register_form.password.data, method='pbkdf2:sha256', salt_length=8
        )
        user_to_add = User(
            email=register_form.email.data,
            name=register_form.name.data,
            password=salted_pass
        )
        try:
            db.session.add(user_to_add)
            db.session.commit()
            login_user(user_to_add)
        except IntegrityError:
            flash('User already exists, Please try with another email or name.')
            return redirect(url_for('register'))
        return redirect(url_for("list_index"))
    return render_template("register.html", form=register_form)


@app.route("/login", methods=["GET", "POST"])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        request_email = login_form.email.data
        request_password = login_form.password.data
        get_user = User.query.filter_by(email=request_email).first()
        if not get_user:
            flash('User not found or password incorrect.')
            return redirect(url_for('login'))
        elif not check_password_hash(get_user.password, request_password):
            flash('User not found or password incorrect.')
            return redirect(url_for('login'))
        else:
            login_user(get_user)
        return redirect(url_for("list_index"))
    return render_template("login.html", form=login_form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("list_index"))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5301, debug=True)

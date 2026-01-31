from flask import Flask, render_template
from dotenv import dotenv_values
import os

from flaskr.auth import auth_bp, close_auth_db

bed_data = [
	"dummy data that makes it 1-indexed",
	{
		"temperature": -5,
		"humidity": 0
	},
	{
		"temperature": 5,
		"humidity": 10
	},
	{
		"temperature": 15,
		"humidity": 20
	},
	{
		"temperature": 25,
		"humidity": 30
	}
	]

def create_app():
	app = Flask(__name__, instance_relative_config=True)
	
	env_vars = dotenv_values()
	plotPath = env_vars["PLOT_DB_PATH"]
	authPath = env_vars["AUTH_DB_PATH"]

	app.config.from_mapping(
        SECRET_KEY=env_vars["SECRET_KEY"],
        PLOT_DB=plotPath,
		AUTH_DB=os.path.join(app.instance_path, authPath),
        PORT=env_vars["PORT"]
	)

	# ensure the instance folder exists
	os.makedirs(app.instance_path, exist_ok=True)
	
	app.register_blueprint(auth_bp, url_prefix="/auth")
	app.teardown_appcontext(close_auth_db)

	@app.route('/')
	def index():
		return render_template("index.html", current_data=current_data)

	return app




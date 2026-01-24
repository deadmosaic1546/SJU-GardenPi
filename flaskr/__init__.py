from flask import Flask, render_template

app = Flask(__name__)

current_data = {
	"temperature": 0,
	"humidity": 0
}

@app.route('/')
def index():
    return render_template("index.html", current_data=current_data)

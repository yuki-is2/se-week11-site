from flask import Flask, render_template
from database import init_db
from routes.clothing import clothing_bp
import config

app = Flask(__name__)
app.secret_key = "ootd-dev-secret-key"  # セッション用（本番では.envに移す）
app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH

# Blueprintを登録
app.register_blueprint(clothing_bp)

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
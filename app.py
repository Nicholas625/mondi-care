from flask import Flask, render_template, request, redirect, url_for, jsonify, session, make_response
import os
import numpy as np
from datetime import datetime
from werkzeug.utils import secure_filename
from functools import wraps
import random
import tensorflow as tf

from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input

# Import database
from database import db

app = Flask(__name__)
app.secret_key = "mondicare_secret_key_2026"

# ================= SET RANDOM SEEDS ================= #
random.seed(42)
np.random.seed(42)
tf.random.set_seed(42)

# ================= LOGIN DECORATOR ================= #
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ================= CONFIGURATION ================= #
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ================= LOAD TRAINED MODEL ================= #
model = None

# Try SavedModel format first (most compatible)
savedmodel_path = "models/mondicare_savedmodel"
if os.path.exists(savedmodel_path):
    try:
        model = tf.saved_model.load(savedmodel_path)
        print("✅ Model loaded successfully from SavedModel format!")
    except Exception as e:
        print(f"❌ Could not load SavedModel: {e}")
        model = None

# Fall back to .keras format if SavedModel not found
if model is None:
    from tensorflow.keras.models import load_model
    keras_paths = ["models/mondicare_final.keras", "models/new_mondicare.keras"]
    for path in keras_paths:
        if os.path.exists(path):
            try:
                model = load_model(path, compile=False)
                print(f"✅ Model loaded successfully from {path}")
                break
            except Exception as e:
                print(f"❌ Could not load from {path}: {e}")

if model is None:
    print("❌ ERROR: No model found! Please check your models folder.")
else:
    print("✅ Model is ready for predictions!")

# Class names
class_names = ['Early_Blight', 'Healthy', 'Late_Blight']

# ================= PESTICIDE RECOMMENDATIONS ================= #
PESTICIDE_RECOMMENDATIONS = {
    "Early_Blight": {
        "chemicals": ["Mancozeb", "Chlorothalonil", "Azoxystrobin"],
        "application": "Apply every 7-10 days. Remove infected leaves first.",
        "organic": "Copper spray or Bacillus subtilis",
        "safety": "Wear protective gear. Don't spray before rain."
    },
    "Late_Blight": {
        "chemicals": ["Ridomil Gold", "Copper-based fungicides", "Metalaxyl"],
        "application": "Apply immediately after detection. Repeat every 5-7 days.",
        "organic": "Copper hydroxide + Neem oil",
        "safety": "Very contagious! Destroy severely infected plants."
    },
    "Healthy": {
        "chemicals": ["No chemicals needed"],
        "application": "Preventive spraying every 2 weeks recommended",
        "organic": "Compost tea, Neem spray for prevention",
        "safety": "Maintain proper spacing and crop rotation"
    }
}

# ================= ROUTES ================= #
@app.route("/")
def index():
    return render_template("welcome.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if 'user_id' in session:
        return redirect(url_for("dashboard"))
    
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        user = db.get_user_by_username(username)
        
        if user:
            if password:
                session['user'] = user['username']
                session['user_id'] = user['id']
                session['login_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                db.update_last_login(user['id'])
                return redirect(url_for("dashboard"))
            else:
                return render_template("login.html", error="Invalid password")
        else:
            user_id = db.create_user(username, f"{username}@example.com", password or "password")
            if user_id:
                session['user'] = username
                session['user_id'] = user_id
                return redirect(url_for("dashboard"))
            else:
                return render_template("login.html", error="Login failed")
    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if 'user_id' in session:
        return redirect(url_for("dashboard"))
    
    if request.method == "POST":
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if username and username.strip():
            user_id = db.create_user(username, email, password)
            if user_id:
                session['user'] = username
                session['user_id'] = user_id
                return redirect(url_for("dashboard"))
            else:
                return render_template("signup.html", error="Username already exists")
        else:
            return render_template("signup.html", error="Please enter a username")
    return render_template("signup.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

# ================= PREDICTION ================= #
@app.route("/predict", methods=["POST"])
def predict():
    if model is None:
        return render_template("dashboard.html", prediction="ERROR: Model not loaded. Please check your model file.")

    if "image" not in request.files:
        return redirect(url_for("dashboard"))

    file = request.files["image"]
    if file.filename == "":
        return redirect(url_for("dashboard"))

    if not allowed_file(file.filename):
        return render_template("dashboard.html", prediction="Invalid file type. Please upload PNG, JPG, or JPEG.")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = secure_filename(f"{timestamp}_{file.filename}")
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    try:
        img = image.load_img(filepath, target_size=(224, 224))
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = preprocess_input(img_array)

        # Make prediction
        predictions = model.predict(img_array, verbose=0)
        if hasattr(predictions, 'numpy'):
            predictions = predictions.numpy()
        
        class_index = np.argmax(predictions[0])
        result = class_names[class_index]
        confidence = float(predictions[0][class_index]) * 100

        recommendation = PESTICIDE_RECOMMENDATIONS.get(result, PESTICIDE_RECOMMENDATIONS["Healthy"])
        
        if 'user_id' in session:
            db.save_prediction(
                session['user_id'],
                filepath,
                result,
                confidence,
                recommendation['chemicals'],
                recommendation['application'],
                recommendation['safety']
            )
            session['last_prediction'] = {
                'disease': result,
                'chemicals': recommendation['chemicals'],
                'confidence': confidence
            }

        return render_template(
            "result.html",
            prediction=result,
            confidence=round(confidence, 2),
            recommendation=recommendation,
            image_path=filepath,
            is_logged_in='user_id' in session
        )

    except Exception as e:
        print("ERROR:", e)
        return render_template("dashboard.html", prediction=f"Error: {str(e)}")

# ================= PREMIUM FEATURES ================= #
@app.route("/shop_locator")
@login_required
def shop_locator():
    last_prediction = session.get('last_prediction')
    if not last_prediction:
        return redirect(url_for("dashboard"))
    return render_template("shop_locator.html", prediction=last_prediction)

@app.route("/get_shops")
@login_required
def get_shops():
    shops = db.get_all_shops()
    shops_list = []
    for shop in shops:
        if shop['type'] == 'physical':
            shops_list.append({
                'id': shop['id'],
                'name': shop['name'],
                'type': shop['type'],
                'address': shop['address'],
                'phone': shop['phone'],
                'whatsapp': shop['whatsapp'],
                'products': shop['products'].split(', ') if shop['products'] else [],
                'hours': shop['hours']
            })
        else:
            shops_list.append({
                'id': shop['id'],
                'name': shop['name'],
                'type': shop['type'],
                'website': shop['website'],
                'delivery': shop['delivery_info'],
                'delivery_fee': 'Varies',
                'products': shop['products'].split(', ') if shop['products'] else [],
                'payment': shop['payment_info']
            })
    response = make_response(jsonify(shops_list))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

@app.route("/officers")
@login_required
def officers_page():
    return render_template("officers.html")

@app.route("/get_officers")
@login_required
def get_officers():
    officers = db.get_all_officers()
    officers_list = []
    for officer in officers:
        officers_list.append({
            'id': officer['id'],
            'name': officer['name'],
            'title': officer['title'],
            'district': officer['district'],
            'region': officer['region'],
            'phone': officer['phone'],
            'whatsapp': officer['whatsapp'],
            'whatsapp_link': f"https://wa.me/{officer['whatsapp']}",
            'email': officer['email'],
            'expertise': officer['expertise'],
            'available': officer['available'],
            'languages': officer['languages'].split(', ') if officer['languages'] else [],
            'office_location': officer['office_location'],
            'years_experience': officer['years_experience']
        })
    response = make_response(jsonify(officers_list))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

@app.route("/connect_officer/<int:officer_id>", methods=["POST"])
@login_required
def connect_officer(officer_id):
    officer = db.get_officer_by_id(officer_id)
    if officer:
        data = request.get_json()
        print(f"📧 Connection request from {data.get('name')} to {officer['name']}")
        print(f"📝 Message: {data.get('message')}")
        return jsonify({
            "status": "success",
            "message": f"✓ Request sent to {officer['name']}! They will contact you within 24 hours.",
            "officer": dict(officer)
        })
    return jsonify({"status": "error", "message": "Officer not found"})

@app.route("/history")
@login_required
def history():
    predictions = db.get_user_predictions(session['user_id'])
    return render_template("history.html", predictions=predictions)

# ================= RUN APPLICATION ================= #
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
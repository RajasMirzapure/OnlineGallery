from flask import Flask, render_template, request, redirect, url_for, flash
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader

# Load environment variables from .env for local testing (Render ignores this file)
load_dotenv()

# --- DATABASE CONFIGURATION ---
# Heroku/Render will provide DATABASE_URL. 
# We fetch it and convert the old 'postgres://' scheme to 'postgresql://' 
# as required by recent SQLAlchemy versions.
db_url = os.environ.get("DATABASE_URL")
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# Initialize Flask app
app = Flask(__name__)

# Configure CORS: Allows Vercel frontend to talk to this Render backend
# NOTE: Set to "*" for now, but update this to your final Vercel domain later!
CORS(app, resources={r"/*": {"origins": "*"}})

# Flask Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key_for_testing') # Get secret key from environment
app.config['SQLALCHEMY_DATABASE_URI'] = db_url or 'sqlite:///media.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False 

db = SQLAlchemy(app)

# Cloudinary Configuration (Reads directly from environment variables)
cloudinary.config(
  cloud_name = os.getenv("YOUR_CLOUD_NAME"),
  api_key = os.getenv("YOUR_API_KEY"),
  api_secret = os.getenv("YOUR_API_SECRET"),
  secure = True
)


class Media(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # The Column function takes the type directly as its first argument
    file_url = db.Column(db.String(200), nullable=False)
    media_type = db.Column(db.String(10), nullable=False)

with app.app_context():
    # This creates tables locally. We will run this manually on Render/Koyeb later.
    db.create_all()

# --- ROUTES ---

@app.route("/")
def home():
    # Note: This route might be redundant if Vercel handles all front-end routing
    return render_template("front.html") 

@app.route("/image")
def img():
    return render_template("image.html") 

@app.route("/image/see")
def view_img():
    # Ensure this query works with PostgreSQL.
    all_images = Media.query.filter_by(media_type='image').all()
    return render_template('see.html', all_images=all_images)


@app.route("/image/add", methods=['GET','POST'])
def upload_img():
    if request.method == 'POST':
        file_to_upload = request.files.get('file')

        if file_to_upload and file_to_upload.content_type.startswith('image/'):
            # The actual image upload to Cloudinary
            upload_result = cloudinary.uploader.upload(file_to_upload, resource_type='image')
            secure_url = upload_result['secure_url']

            new_image = Media(file_url=secure_url, media_type='image')
            db.session.add(new_image)
            db.session.commit()
            return redirect(url_for('view_img'))
        else:
            flash("Upload failed. Please select a valid image file.")
            return redirect(url_for('upload_img'))
            
    return render_template("add_img.html") 


@app.route("/video")
def vid():
    return render_template("vid.html")

if __name__ == '__main__':
    app.run(debug=True, port=5001)


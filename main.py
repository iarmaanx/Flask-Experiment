import os
import json
from flask import Flask, request, jsonify, session, redirect, url_for, render_template, send_from_directory

app = Flask(__name__)

# Secret key for session encryption (make sure to keep it secure)
app.secret_key = 'your_secret_key_here'

# Set the upload folder to be directly inside the current directory
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Path to the JSON file where user data is stored
USER_DATA_FILE = 'user_data.json'

def load_user_data():
    """Load user data from user_data.json."""
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r') as file:
            return json.load(file)
    return {}

def save_user_data(data):
    """Save user data to user_data.json."""
    with open(USER_DATA_FILE, 'w') as file:
        json.dump(data, file, indent=4)

def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    if 'username' in session:
        username = session['username']
        profile_image = session.get('profile_image', None)
        return render_template('home.html', username=username, profile_image=profile_image)
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        session['username'] = username  # Store username in session
        return redirect(url_for('home'))  # Redirect to the home page
    return render_template('login.html')  # Render login page

@app.route('/upload_image', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({"message": "No file part"}), 400
    
    file = request.files['image']
    
    if file.filename == '':
        return jsonify({"message": "No selected file"}), 400
    
    if file and allowed_file(file.filename):
        filename = file.filename
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)  # Save the image to the upload folder
        
        # Load existing user data from JSON file
        user_data = load_user_data()
        username = session['username']
        
        # Save the profile image path for the current user
        if username not in user_data:
            user_data[username] = {}
        user_data[username]['profile_image'] = f'uploads/{filename}'
        
        # Save updated user data back to the JSON file
        save_user_data(user_data)
        
        session['profile_image'] = f'uploads/{filename}'  # Save the relative path for rendering
        
        return jsonify({"message": f"Image successfully uploaded to {filepath}"}), 200
    else:
        return jsonify({"message": "Invalid file type. Allowed types are: png, jpg, jpeg, gif, bmp."}), 400

@app.route('/remove_image', methods=['POST'])
def remove_image():
    profile_image = session.get('profile_image', None)
    
    if profile_image:
        # Extract the filename from the session data
        filename = profile_image.split('/')[-1]
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        # Try to remove the file
        try:
            if os.path.exists(filepath):
                os.remove(filepath)  # Delete the file from the server
                
                # Load user data from the JSON file
                user_data = load_user_data()
                username = session['username']
                
                # Remove the profile image entry from user data
                if username in user_data and 'profile_image' in user_data[username]:
                    del user_data[username]['profile_image']
                
                # Save updated user data back to the JSON file
                save_user_data(user_data)
                
                # Remove profile image from session
                session.pop('profile_image', None)
                
                return jsonify({"message": f"File {filename} successfully removed."}), 200
            else:
                return jsonify({"message": "File not found."}), 404
        except Exception as e:
            return jsonify({"message": f"Error removing file: {str(e)}"}), 500
    else:
        return jsonify({"message": "No file associated with this user."}), 400

@app.route('/logout')
def logout():
    session.pop('username', None)  # Remove the username from the session
    session.pop('profile_image', None)  # Remove the profile image from the session
    return redirect(url_for('login'))  # Redirect to the login page

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)

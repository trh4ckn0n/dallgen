import os
from flask import Flask, render_template, request, redirect, url_for, session
import openai
from dotenv import load_dotenv
from db import init_db, insert_image, get_history, delete_image, reset_db

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change_this_secret")
openai.api_key = os.getenv("OPENAI_API_KEY")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

@app.route('/', methods=['GET', 'POST'])
def index():
    image_urls = []
    if request.method == 'POST':
        prompt = request.form['prompt']
        n = int(request.form.get('n', 3))
        style = request.form.get('style', '')
        size = request.form.get('size', '1024x1024')
        full_prompt = f"{prompt}, style {style}" if style else prompt

        try:
            response = openai.Image.create(
                prompt=full_prompt,
                n=n,
                size=size,
                model="dall-e-3"
            )
            for item in response['data']:
                url = item['url']
                insert_image(full_prompt, url)
                image_urls.append(url)
        except Exception as e:
            image_urls.append(f"Erreur : {str(e)}")

    return render_template('index.html', image_urls=image_urls)

# Admin login
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form['password'] == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect('/admin')
        return "Mot de passe incorrect"
    return render_template('admin_login.html')

# Admin dashboard
@app.route('/admin')
def admin():
    if not session.get('admin'):
        return redirect('/admin/login')
    try:
        history = get_history()
    except Exception as e:
        history = []
        error = f"⚠️ Erreur : {str(e)} — la base semble ne pas être initialisée."
        return render_template('admin.html', history=history, error=error)
    return render_template('admin.html', history=history)

# Supprimer une image
@app.route('/admin/delete/<int:image_id>', methods=['POST'])
def admin_delete(image_id):
    if not session.get('admin'):
        return redirect('/admin/login')
    delete_image(image_id)
    return redirect('/admin')

# Réinitialiser la base
@app.route('/admin/reset', methods=['POST'])
def admin_reset():
    if not session.get('admin'):
        return redirect('/admin/login')
    reset_db()
    return "Base de données réinitialisée"

@app.route('/admin/initdb', methods=['POST'])
def admin_initdb():
    if not session.get('admin'):
        return redirect('/admin/login')
    init_db()
    return redirect('/admin')
    
if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0")

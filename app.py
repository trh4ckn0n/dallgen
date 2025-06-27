import os
import logging
from flask import Flask, render_template, request, redirect, url_for, session, flash
import openai
from dotenv import load_dotenv
from db import init_db, insert_image, get_history, delete_image, reset_db

load_dotenv()

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change_this_secret")

openai.api_key = os.getenv("OPENAI_API_KEY")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

VALID_SIZES = ["256x256", "512x512", "1024x1024"]

@app.route('/files')
def list_files():
    files = os.listdir('/opt/render/project/src/')
    return "<br>".join(files)

@app.route('/', methods=['GET', 'POST'])
def index():
    image_urls = []
    if request.method == 'POST':
        prompt = request.form.get('prompt', '').strip()
        n = request.form.get('n', '3')
        style = request.form.get('style', '').strip()
        size = request.form.get('size', '1024x1024')

        # Validation des entrées
        if not prompt:
            flash("Le prompt ne peut pas être vide.", "error")
            return render_template('index.html', image_urls=[])

        try:
            n = int(n)
            if n < 1 or n > 5:
                flash("Le nombre d’images doit être entre 1 et 5.", "error")
                return render_template('index.html', image_urls=[])
        except ValueError:
            flash("Le nombre d’images doit être un entier.", "error")
            return render_template('index.html', image_urls=[])

        if size not in VALID_SIZES:
            flash(f"Taille invalide : {size}.", "error")
            return render_template('index.html', image_urls=[])

        full_prompt = f"{prompt}, style {style}" if style else prompt
        app.logger.info(f"Prompt complet: {full_prompt}, n={n}, size={size}")

        try:
            response = openai.Image.create(
                prompt=full_prompt,
                n=n,
                size=size,
                # model="dall-e-3"  # Optionnel : commenter si erreur
            )
            for item in response['data']:
                url = item['url']
                insert_image(full_prompt, url)
                image_urls.append(url)

            if not image_urls:
                flash("Aucune image générée, réessayez avec un autre prompt.", "error")

        except openai.error.OpenAIError as e:
            flash(f"Erreur lors de la génération : {e}", "error")
            app.logger.error(f"Erreur OpenAI Image.create : {e}")
        except Exception as e:
            flash(f"Erreur interne : {e}", "error")
            app.logger.error(f"Erreur interne : {e}")

        return render_template('index.html', image_urls=image_urls)

    # GET
    return render_template('index.html', image_urls=[])

# Admin login
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form['password'] == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect('/admin')
        flash("Mot de passe incorrect", "error")
        return render_template('admin_login.html')
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
    flash("Base de données réinitialisée.", "info")
    return redirect('/admin')

@app.route('/admin/initdb', methods=['POST'])
def admin_initdb():
    if not session.get('admin'):
        return redirect('/admin/login')
    init_db()
    flash("Base de données initialisée.", "info")
    return redirect('/admin')

if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0")

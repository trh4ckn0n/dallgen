import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
import openai
from dotenv import load_dotenv
from db import init_db, insert_image, get_history, delete_image, reset_db

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change_this_secret")
openai.api_key = os.getenv("OPENAI_API_KEY")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")


@app.route('/files')
def list_files():
    files = os.listdir('/opt/render/project/src/')
    return "<br>".join(files)


@app.route('/', methods=['GET', 'POST'])
def index():
    image_urls = []
    if request.method == 'POST':
        prompt = request.form['prompt']
        n = int(request.form.get('n', 3))
        style = request.form.get('style', '').strip()
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
            error_msg = f"Erreur lors de la génération : {str(e)}"
            flash(error_msg, 'error')
            return render_template('index.html', image_urls=[])

        return render_template('index.html', image_urls=image_urls)

    # GET : afficher page vide sans images
    return render_template('index.html', image_urls=[])


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form['password'] == ADMIN_PASSWORD:
            session['admin'] = True
            flash("Connexion réussie", "success")
            return redirect(url_for('admin'))
        flash("Mot de passe incorrect", "error")
    return render_template('admin_login.html')


def admin_required(f):
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin'):
            flash("Veuillez vous connecter en admin", "error")
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)

    return decorated


@app.route('/admin')
@admin_required
def admin():
    try:
        history = get_history()
        error = None
    except Exception as e:
        history = []
        error = f"⚠️ Erreur : {str(e)} — la base semble ne pas être initialisée."
    return render_template('admin.html', history=history, error=error)


@app.route('/admin/delete/<int:image_id>', methods=['POST'])
@admin_required
def admin_delete(image_id):
    try:
        delete_image(image_id)
        flash(f"Image {image_id} supprimée", "success")
    except Exception as e:
        flash(f"Erreur lors de la suppression : {str(e)}", "error")
    return redirect(url_for('admin'))


@app.route('/admin/reset', methods=['POST'])
@admin_required
def admin_reset():
    try:
        reset_db()
        flash("Base de données réinitialisée avec succès", "success")
    except Exception as e:
        flash(f"Erreur lors de la réinitialisation : {str(e)}", "error")
    return redirect(url_for('admin'))


@app.route('/admin/initdb', methods=['POST'])
@admin_required
def admin_initdb():
    try:
        init_db()
        flash("Base de données initialisée avec succès", "success")
    except Exception as e:
        flash(f"Erreur lors de l'initialisation : {str(e)}", "error")
    return redirect(url_for('admin'))


if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0")

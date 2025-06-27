from flask import Flask, render_template, request, redirect, url_for, session
import openai, os
from dotenv import load_dotenv
from db import init_db, insert_image, get_history

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
admin_password = os.getenv("ADMIN_PASSWORD")

app = Flask(__name__)
app.secret_key = "supersecret"  # change for prod

init_db()

@app.route('/', methods=['GET', 'POST'])
def index():
    image_urls = []
    if request.method == 'POST':
        prompt = request.form['prompt']
        style = request.form['style']
        size = request.form['size']
        n_images = int(request.form['n_images'])

        full_prompt = f"{prompt}, style {style}, signé style by trhacknon"

        try:
            response = openai.Image.create(
                prompt=full_prompt,
                n=n_images,
                size=size,
                model="dall-e-3"
            )
            for data in response['data']:
                url = data['url']
                image_urls.append(url)
                insert_image(full_prompt, url)
        except Exception as e:
            image_urls.append(f"Erreur : {str(e)}")

    return render_template('index.html', image_urls=image_urls)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    history = get_history()
    return render_template('admin.html', history=history)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['password'] == admin_password:
            session['logged_in'] = True
            return redirect(url_for('admin'))
    return '''
        <form method="post" style="text-align:center; margin-top:100px;">
            <input type="password" name="password" placeholder="Mot de passe admin">
            <button type="submit">Connexion</button>
        </form>
    '''

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0")

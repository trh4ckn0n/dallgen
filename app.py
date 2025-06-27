from flask import Flask, render_template, request, redirect, url_for, session
import openai
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
admin_password = os.getenv("ADMIN_PASSWORD")

app = Flask(__name__)
app.secret_key = "supersecret"  # change me for production

history = []  # in-memory history (can be written to file/db)

@app.route('/', methods=['GET', 'POST'])
def index():
    image_url = None
    if request.method == 'POST':
        prompt = request.form['prompt']
        size = request.form['size']
        style = request.form['style']
        full_prompt = f"{prompt}, style {style}, signé style by trhacknon"
        try:
            response = openai.Image.create(
                prompt=full_prompt,
                n=1,
                size=size,
                model="dall-e-3"
            )
            image_url = response['data'][0]['url']
            history.append({
                'prompt': full_prompt,
                'image_url': image_url,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        except Exception as e:
            image_url = f"Erreur : {str(e)}"
    return render_template('index.html', image_url=image_url)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    return render_template('admin.html', history=history)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        pwd = request.form['password']
        if pwd == admin_password:
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

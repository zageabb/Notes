from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'images')
app.secret_key = 'replace-with-secure-secret'

db = SQLAlchemy(app)

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(200))

    def __repr__(self):
        return f"<Note {self.title!r}>"

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    notes = Note.query.all()
    return render_template('index.html', notes=notes)

@app.route('/add', methods=['GET', 'POST'])
def add_note():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        image_file = request.files.get('image')
        filename = None
        if image_file and image_file.filename:
            filename = secure_filename(image_file.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(path)
        note = Note(title=title, content=content, image=filename)
        db.session.add(note)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add_note.html')

@app.route('/note/<int:note_id>', methods=['GET', 'POST'])
def note_detail(note_id):
    note = Note.query.get_or_404(note_id)
    if request.method == 'POST':
        note.title = request.form['title']
        note.content = request.form['content']
        image_file = request.files.get('image')
        if image_file and image_file.filename:
            filename = secure_filename(image_file.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(path)
            note.image = filename
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('note.html', note=note)

@app.route('/delete/<int:note_id>', methods=['POST'])
def delete_note(note_id):
    note = Note.query.get_or_404(note_id)
    if note.image:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], note.image)
        if os.path.exists(image_path):
            os.remove(image_path)
    db.session.delete(note)
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5001, debug=True)

from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os
from werkzeug.utils import secure_filename
import requests

app = Flask(__name__)

# Configuration for file uploads
UPLOAD_FOLDER = 'static/images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Initialize the SQLite database
def init_db():
    conn = sqlite3.connect('books.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS books (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    author TEXT,
                    image TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS words (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_id INTEGER,
                    word TEXT,
                    meaning TEXT,
                    page_number INTEGER,
                    line_number INTEGER,
                    word_position INTEGER,
                    FOREIGN KEY(book_id) REFERENCES books(id)
                )''')
    conn.commit()
    conn.close()

# Check if the uploaded file is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Fetch the meaning of a word using an API (example: Dictionary API)
def get_word_meaning(word):
    api_url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    response = requests.get(api_url)
    if response.status_code == 200:
        data = response.json()
        meaning = data[0]['meanings'][0]['definitions'][0]['definition']
        return meaning
    else:
        return "Meaning not found."

@app.route('/')
def index():
    conn = sqlite3.connect('books.db')
    c = conn.cursor()
    c.execute('SELECT * FROM books')
    books = c.fetchall()
    conn.close()
    return render_template('index.html', books=books)

@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        file = request.files['image']

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            conn = sqlite3.connect('books.db')
            c = conn.cursor()
            c.execute('INSERT INTO books (title, author, image) VALUES (?, ?, ?)', (title, author, image_path))
            conn.commit()
            conn.close()
            return redirect(url_for('index'))
        else:
            return "Invalid file format. Only images are allowed."

    return render_template('add_book.html')

@app.route('/book/<int:book_id>', methods=['GET', 'POST'])
def book_details(book_id):
    conn = sqlite3.connect('books.db')
    c = conn.cursor()
    c.execute('SELECT * FROM books WHERE id = ?', (book_id,))
    book = c.fetchone()

    c.execute('SELECT * FROM words WHERE book_id = ?', (book_id,))
    words = c.fetchall()
    conn.close()

    if request.method == 'POST':
        if 'search_word' in request.form:
            search_word = request.form['search_word']
            conn = sqlite3.connect('books.db')
            c = conn.cursor()
            c.execute('SELECT * FROM words WHERE book_id = ? AND word = ?', (book_id, search_word))
            searched_words = c.fetchall()
            conn.close()
            return render_template('book_details.html', book=book, words=searched_words)

        elif 'search_page' in request.form:
            search_page = request.form['search_page']
            conn = sqlite3.connect('books.db')
            c = conn.cursor()
            c.execute('SELECT * FROM words WHERE book_id = ? AND page_number = ?', (book_id, search_page))
            searched_words = c.fetchall()
            conn.close()
            return render_template('book_details.html', book=book, words=searched_words)

        else:
            word = request.form['word']
            page_number = request.form['page_number']
            line_number = request.form['line_number']
            word_position = request.form['word_position']

            meaning = get_word_meaning(word)

            conn = sqlite3.connect('books.db')
            c = conn.cursor()
            c.execute('INSERT INTO words (book_id, word, meaning, page_number, line_number, word_position) VALUES (?, ?, ?, ?, ?, ?)',
                      (book_id, word, meaning, page_number, line_number, word_position))
            conn.commit()
            conn.close()

            return redirect(url_for('book_details', book_id=book_id))

    return render_template('book_details.html', book=book, words=words)

@app.route('/edit_word/<int:word_id>', methods=['GET', 'POST'])
def edit_word(word_id):
    conn = sqlite3.connect('books.db')
    c = conn.cursor()
    c.execute('SELECT * FROM words WHERE id = ?', (word_id,))
    word = c.fetchone()
    conn.close()

    if request.method == 'POST':
        new_word = request.form['word']
        new_meaning = request.form['meaning']

        conn = sqlite3.connect('books.db')
        c = conn.cursor()
        c.execute('UPDATE words SET word = ?, meaning = ? WHERE id = ?', (new_word, new_meaning, word_id))
        conn.commit()
        conn.close()

        return redirect(url_for('book_details', book_id=word[1]))

    return render_template('edit_word.html', word=word)

if __name__ == '__main__':
    init_db()
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)

import docx
import re
from collections import OrderedDict
from flask import Flask, render_template, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import SubmitField, FileField, TextAreaField, StringField, IntegerField
from wtforms.validators import DataRequired
from werkzeug.utils import secure_filename


def distance(a, b):
    "Calculates the Levenshtein distance between a and b."
    n, m = len(a), len(b)
    if n > m:
        # Make sure n <= m, to use O(min(n, m)) space
        a, b = b, a
        n, m = m, n

    # Keep current and previous row, not entire matrix
    current_row = range(n + 1)
    for i in range(1, m + 1):
        previous_row, current_row = current_row, [i] + [0] * n
        for j in range(1, n + 1):
            add, delete, change = previous_row[j] + 1, \
                current_row[j - 1] + 1, previous_row[j - 1]
            if a[j - 1] != b[i - 1]:
                change += 1
            current_row[j] = min(add, delete, change)

    return current_row[n]


words = set()

app = Flask(__name__)

app.config['SECRET_KEY'] = 'a really really really really long secret key'


class AddWordsForm(FlaskForm):
    text = TextAreaField("Текст: ")
    file = FileField('Добавить из файла')
    submit = SubmitField("Добавить")


class FindDistanceForm(FlaskForm):
    word = StringField("Слово: ", validators=[DataRequired()])
    max_distance = IntegerField(
        "Максимальное расстояние: ", validators=[DataRequired()])
    submit = SubmitField('Найти')


@app.route('/words/', methods=['get', 'post'])
def add_words():
    form = AddWordsForm()
    if form.validate_on_submit():
        if form.text.data:
            text = form.text.data
            word_list = set(re.sub("[.,?!'\";:-]+", "", text).lower().split())
            words.update(word_list)
        if form.file.data:
            filename = secure_filename(form.file.data.filename)
            form.file.data.save('uploads/' + filename)
            doc = docx.Document('uploads/' + filename)
            text = ''
            for paragraph in doc.paragraphs:
                text = ' '.join([paragraph.text, text])
                word_list = set(
                    re.sub("[.,?!'\";:-]+", "", text).lower().split())
                words.update(word_list)
        return redirect(url_for('add_words'))
    return render_template('add_words.html', form=form)


@app.route('/distance/', methods=['get', 'post'])
def find_distance():
    form = FindDistanceForm()
    result = {}
    if form.validate_on_submit():
        cur_word = form.word.data
        max_dist = form.max_distance.data
        for word in words:
            dist = distance(cur_word, word)
            if dist <= max_dist:
                if dist not in result.keys():
                    result[dist] = [word]
                else:
                    result[dist].append(word)
        return render_template('show_distance.html', word=cur_word, words=OrderedDict(sorted(result.items())))
    return render_template('find_distance.html', form=form)


@app.route('/help/')
def help():
    return render_template('help.html')


@app.route('/')
def index():
    return redirect(url_for('help'))


if __name__ == '__main__':
    app.run()

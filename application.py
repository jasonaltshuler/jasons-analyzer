import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session, redirect, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError

from helpers import apology, short, thesaurus, decode
import magic

# Told about "Counter" from a friend https://docs.python.org/2/library/collections.html
from collections import Counter

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["short"] = short

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":

        if not request.files["thefile"]:
            if not request.form.get("thetext"):
                text = "No type entered or file uploaded"
            else:
                rawtext = request.form.get("thetext")
                text = rawtext.replace('\n', ' ').replace('\r', '')

        else:
            if request.form.get("thetext"):
                text = "Please upload a file OR enter text (not both)"
            else:
                file = request.files["thefile"]
                if file.filename.endswith('.docx'):

                    # This is all from http://etienned.github.io/posts/extract-text-from-word-docx-simply/
                    try:
                        from xml.etree.cElementTree import XML
                    except ImportError:
                        from xml.etree.ElementTree import XML
                    import zipfile


                    """
                    Module that extract text from MS XML Word document (.docx).
                    (Inspired by python-docx <https://github.com/mikemaccana/python-docx>)
                    """

                    WORD_NAMESPACE = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
                    PARA = WORD_NAMESPACE + 'p'
                    TEXT = WORD_NAMESPACE + 't'


                    def get_docx_text(path):
                        """
                        Take the path of a docx file as argument, return the text in unicode.
                        """
                        document = zipfile.ZipFile(path)
                        xml_content = document.read('word/document.xml')
                        document.close()
                        tree = XML(xml_content)

                        paragraphs = []
                        for paragraph in tree.getiterator(PARA):
                            texts = [node.text
                                     for node in paragraph.getiterator(TEXT)
                                     if node.text]
                            if texts:
                                paragraphs.append(''.join(texts))

                        return '\n\n'.join(paragraphs)

                    file = request.files["thefile"]
                    rawtext = get_docx_text(file)
                    text = rawtext.replace('\n', ' ').replace('\r', '')

        punctuation = []
        period=0
        semicolon=0
        colon=0
        dash=0
        mdash=0
        comma=0
        exclamation=0
        question=0
        slash=0
        parenthesis=0
        quotation=0

        for character in text:
            if character ==".":
                period +=1
            elif character ==";":
                semicolon +=1
            elif character ==":":
                colon +=1
            elif character =="-":
                dash +=1
            elif character =="—":
                mdash +=1
            elif character ==",":
                comma +=1
            elif character =="!":
                exclamation +=1
            elif character =="?":
                question +=1
            elif character =="/":
                slash +=1
            elif character =="(":
                parenthesis +=1
            elif character =='“':
                quotation +=1

        punctuation.append({'Mark': ".", 'Count': period})
        text = text.replace('.', ' ')
        punctuation.append({'Mark': ";", 'Count': semicolon})
        text = text.replace(';', ' ')
        punctuation.append({'Mark': ":", 'Count': colon})
        text = text.replace(':', ' ')
        punctuation.append({'Mark': "-", 'Count': dash})
        text = text.replace('-', '')
        punctuation.append({'Mark': "—", 'Count': mdash})
        text = text.replace('—', '')
        punctuation.append({'Mark': ",", 'Count': comma})
        text = text.replace(',', ' ')
        punctuation.append({'Mark': "!", 'Count': exclamation})
        text = text.replace('!', ' ')
        punctuation.append({'Mark': "?", 'Count': question})
        text = text.replace('?', ' ')
        punctuation.append({'Mark': "/", 'Count': slash})
        text = text.replace('/', '')
        punctuation.append({'Mark': "( )", 'Count': parenthesis})
        text = text.replace('(', ' ')
        text = text.replace(')', ' ')
        punctuation.append({'Mark': '" "', 'Count': quotation})
        text = text.replace('“', ' ')
        text = text.replace('”', ' ')


        # Got this from here https://www.geeksforgeeks.org/ways-sort-list-dictionaries-values-python-using-itemgetter/
        # and https://www.geeksforgeeks.org/python-removing-dictionary-from-list-of-dictionaries/
        from operator import itemgetter
        punctuationsorted = sorted(punctuation, key=itemgetter('Count'), reverse = True)
        punctuationrefined = [i for i in punctuationsorted if not (i['Count'] == 0)]

        nocase = text.lower()
        allWords = nocase.split()
        words=len(allWords)

        # From https://docs.python.org/2/library/collections.html
        import re
        # Read text file with 100 most common English words from wikipedia
        commons = open('commonwords.txt').read().split()

        # Load text file with 1000 most common English words from https://1000mostcommonwords.com/1000-most-common-english-words/
        morecommons = open('morewords.txt').read().split()

        cnt = Counter()
        for word in (allWords):
            cnt[word] += 1
        counted = cnt


        keys=counted.keys()
        key_array=[]

        for key in keys:
            key_array.append(key)

        for i in range(0, len(key_array)):
            # Check if word in the sample is in 100 word database
            for common in commons:
                if key_array[i] == common:
                    del counted[key_array[i]]
                    continue
            # Check if word in the sample is in 1000 word database
            for morecommon in morecommons:
                if key_array[i] == morecommon:
                    del counted[key_array[i]]
            # Check if word is "I", for some reason wasn't being caught in the other for loops
            if key_array[i] == "i":
                    del counted[key_array[i]]


        number = request.form.get("quantity")
        number = int(number)

        most=counted.most_common(number)

        favorites=[]
        favoritewords=[]

        for i in range(0, len(most)):
            if most[i][1] >= 3:
                favorites.append({'Word': most[i][0].upper(), 'Count': most[i][1]})
                favoritewords.append(most[i][0].upper())

        session['favoritewords'] = favoritewords

        return render_template("after.html", text=text, words=words, favorites=favorites, punctuationrefined=punctuationrefined)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("index.html")

@app.route("/synonyms", methods=["GET"])
def synonyms():
    if not session.get('favoritewords', None):
        return redirect(url_for('home'))
    else:
        theword = request.args.get('word')
        synonyms = thesaurus(theword)
        if synonyms == None:
            return render_template("synonyms.html", theword=theword, noun_synonyms="", adjective_synonyms="", verb_synonyms="", adverb_synonyms="")
        else:
            if 'noun' in synonyms:
                noun_synonyms = synonyms["noun"]["syn"]
            else:
                noun_synonyms = ""
            if 'adjective' in synonyms:
                adjective_synonyms = synonyms["adjective"]["syn"]
            else:
                adjective_synonyms = ""
            if 'verb' in synonyms:
                verb_synonyms = synonyms["verb"]["syn"]
            else:
                verb_synonyms = ""
            if 'adverb' in synonyms:
                adverb_synonyms = synonyms["adverb"]["syn"]
            else:
                adverb_synonyms = ""
            return render_template("synonyms.html", theword=theword, noun_synonyms=noun_synonyms, adjective_synonyms=adjective_synonyms, verb_synonyms=verb_synonyms, adverb_synonyms=adverb_synonyms)

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

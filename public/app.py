
from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from unicodedata import normalize
from helpers import apology, login_required, lookup, usd
from random import randint, sample
from http.server import BaseHTTPRequestHandler
from cowpy import cow


app = Flask(__name__)

nums = []
# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

db = SQL("sqlite:///quizlee.db")

app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

db.execute("""
CREATE TABLE IF NOT EXISTS 'users'(
    'id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    'username' TEXT NOT NULL,
    'score' INTEGER NOT NULL DEFAULT 0,
    'hash' TEXT NOT NULL
)""")

@app.route("/",methods=["GET", "POST"])
def index():

    try:
        users = db.execute("SELECT * FROM users where id = ?", session["user_id"])
        user = users[0]
        return render_template("index.html", user=user)
    except:
        return render_template("index.html")



@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":

        username = request.form.get("username")
        password =  request.form.get("password")
        confirmation = request.form.get("confirmation")


        if not username:
            return apology("must provide username", "/register")

        if not password:
            return apology("must provide password", "/register")

        if confirmation != password:
            return apology("passwords diferentes","/register")

        hashed_password = generate_password_hash(password)
        try:
            user_id = db.execute("INSERT INTO users (username,score, hash) VALUES ( ?, ?, ?)", username, 0,hashed_password)
        except (ValueError):
            return print("User not disponible", "/register")
        session["user_id"] = user_id

        return redirect("/")
    else:
        return render_template("register.html")




@app.route("/login", methods=["GET", "POST"])
def login():
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("username errado", "/login")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("password errado", "/login")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("Conta inexistente", "/login")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/scores", methods=["GET", "POST"])
def scores():

    render_template("scores.html", score='')

    rows = db.execute("SELECT * FROM users ORDER BY score DESC LIMIT 10")
    score = []
    pos = 0
    for row in rows:
        pos += 1
        player = row

        player["position"] = pos

        score.append(player)
    return render_template("scores.html", score=score)

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@login_required
@app.route("/play", methods=["GET", "POST"])
def play():

    maximo = db.execute("SELECT id FROM questions")

    if request.method == "GET":

        num = randint(1,len(maximo))
        nums.append(num)

        cont = 1

        users = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        user = users[0]

        questions = db.execute("SELECT * FROM questions WHERE id = ?", num )
        question = questions[0]

        rows = db.execute("SELECT * FROM respostas WHERE id_question = ? ", question["id"])
        respostas = []

        for row in rows:
            resposta = row

            respostas.append(resposta)

        return render_template("/play.html", question=question, respostas=respostas, cont=cont, user=user, nums=nums)

    elif request.method == "POST":

        cont = int(request.form.get("cont"))
        numero = request.form.get("nums")

        nums.append(numero)

        b1 = request.form.get("1")
        b2 = request.form.get("2")
        b3 = request.form.get("3")

        if b1 != None:
            option = int(b1)

        if b2 != None:
            option = int(b2)

        if b3 != None:
            option = int(b3)

        users = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        user = users[0]

        if int(option) > 0:
            user["score"] += 1
            db.execute("UPDATE users SET score = ? WHERE id = ?", user["score"], user["id"])

        #tipo = type(id_question)
        #return apology(f"{id_question} e {tipo}", "index.html")

        if cont < 5:

            while True:

                num = randint(1,len(maximo))

                if num in nums:
                    num = randint(1,len(maximo))

                else:
                    nums.append(num)

                    questions = db.execute("SELECT * FROM questions WHERE id = ?", num)
                    question = questions[0]

                    rows = db.execute("SELECT * FROM respostas WHERE id_question = ? ", question["id"])
                    respostas = []

                    for row in rows:
                        resposta = row

                        respostas.append(resposta)

                    cont += 1

                    return render_template("/play.html", question=question, respostas=respostas, cont=cont, user=user, nums=nums)
        else:
            return redirect("/")




def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type','text/plain')
        self.end_headers()
        message = cow.Cowacter().milk('Hello from Python from a Serverless Function!')
        self.wfile.write(message.encode())
        return

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

    

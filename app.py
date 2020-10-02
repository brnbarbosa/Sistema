from cs50 import SQL
import sqlite3
from datetime import datetime, date

from flask import Flask, flash, jsonify, redirect, render_template, request, session, g, current_app
from flask_session import Session


from tempfile import mkdtemp

from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

# side script for support
from helper import login_required, day, prazo_medio, factor, lqd

app = Flask(__name__)

# ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.route('/')
@login_required
def index():
    return render_template('index.html')

# ----- OPERATION ------ #
@app.route('/sacados', methods=['GET', 'POST'])
@login_required
def sacados():

    # connect database
    con = sqlite3.connect('brn.db')
    con.row_factory = sqlite3.Row

    # create cursor
    cur = con.cursor()

    # GET
    if request.method == 'GET':
        # select all 'sacados'
        cur.execute('SELECT * FROM sacados')

        rows = cur.fetchall()

        return render_template('sacados.html', rows=rows)

    # POST
    else:
        nm = request.form.get('nome')
        cp = request.form.get('cep')
        end = request.form.get('endereco')
        cnpj = request.form.get('cnpj')

         # insert new 'sacado' to db
        cur.execute("INSERT INTO sacados (nome, cep, endereço, cnpj) VALUES (?,?,?,?)",(nm, cp, end, cnpj) )
            
        con.commit()    

        return redirect('/sacados')

@app.route('/clientes', methods=['GET', 'POST'])
@login_required
def clientes():

    # connect database
    con = sqlite3.connect('brn.db')
    con.row_factory = sqlite3.Row

    # create cursor
    cur = con.cursor()

    # GET
    if request.method == 'GET':
        # select all 'sacados'
        cur.execute('SELECT * FROM clientes')

        rows = cur.fetchall()

        return render_template('clientes.html', rows=rows)

    # POST
    else:
        nm = request.form.get('nome')
        cp = request.form.get('cep')
        end = request.form.get('endereco')
        cnpj = request.form.get('cnpj')

         # insert new 'sacado' to db
        cur.execute("INSERT INTO clientes (nome, cep, endereço, cnpj) VALUES (?,?,?,?)",(nm, cp, end, cnpj) )
            
        con.commit()    

        return redirect('/clientes')

@app.route('/operacao', methods=['GET', 'POST'])
@login_required
def operacao():

    # connect database
    con = sqlite3.connect('brn.db')
    con.row_factory = sqlite3.Row

    # create a cursor
    cur = con.cursor()

    # query cliente table to list all clientes
    cliente = cur.execute('SELECT nome FROM clientes')
    cliente = cur.fetchall()

    # query sacados table to list all sacados
    sacado = cur.execute('SELECT nome FROM sacados')
    sacado = cur.fetchall()

    borderos = cur.execute('SELECT * FROM borderos') 
    borderos = cur.fetchall()

    # GET
    if request.method == 'GET':
        return render_template('operacao.html', sacado=sacado, cliente=cliente, bordero=borderos)
    
    # POST
    else:

        # get all user inputs
        # name of cliente
        nm_cliente = request.form.get('cliente')

        # name of sacado
        nm_sacado = request.form.get('sacado')

        # titulo number
        titulo = request.form.get('titulo')

        # valor
        valor = float(request.form.get('valor'))
        
        # vencimento and calculating total days between today and vencimento date
        venc = datetime.strptime(request.form.get('vencimento'), '%Y-%m-%d')
        vencimento = date(venc.year, venc.month, venc.day)
        dias = day(vencimento)

        # tipo (cheque or duplicata)
        tipo = request.form.get('tipo')

        # taxa float value
        taxa = float(request.form.get('tx'))

        # fator TODO juros compostos <<<<<_____________________-----------------------------------_______>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>!!!!!!!!!!!!!!!!!!!!!!!!!!
        fator = factor(taxa, dias)

        # liquido of operation
        liquido = float(lqd(fator, valor))
 
        # insert all that information in a support table
        cur.execute('INSERT INTO borderos (cliente, sacado, titulo, valor, vencimento, dt_negoc, tipo, taxa, fator, liquido, prazo) VALUES (?,?,?,?,?,?,?,?,?,?,?)', 
                    (nm_cliente, nm_sacado, titulo, valor, request.form.get('vencimento'), date.today(), tipo, taxa, fator, liquido, dias))

        con.commit()

        return render_template('operacao.html', sacado=sacado, cliente=cliente, bordero=borderos)
        
@app.route('/table', methods=['GET'])
@login_required
def table():

    # connect database
    con = sqlite3.connect('brn.db')
    con.row_factory = sqlite3.Row

    # create a cursor
    cur = con.cursor()

    borderos = cur.execute('SELECT * FROM borderos') 
    borderos = cur.fetchall()

    return render_template('/table.html', borderos=borderos)


@app.route('/bordero', methods=['GET', 'POST'])
@login_required
def bordero():

    # connect database
    con = sqlite3.connect('brn.db')
    con.row_factory = sqlite3.Row

    # create a cursor
    cur = con.cursor()

    borderos = cur.execute('SELECT * FROM borderos') 
    borderos = cur.fetchall()

    total = cur.execute('SELECT SUM(valor) FROM borderos')
    total = cur.fetchall()

    n_titulos = cur.execute('SELECT COUNT(*) FROM borderos')
    n_titulos = cur.fetchall()
    
    dias = cur.execute('SELECT SUM(prazo) FROM borderos')
    dias = cur.fetchall()

    p_medio = prazo_medio(n_titulos[0]["COUNT(*)"], dias[0]["SUM(prazo)"])

    if request.method == 'GET':
        return render_template('/bordero.html', borderos=borderos, total=total, n_titulos=n_titulos, p_medio=p_medio)
    else:
        return render_template('/bordero.html', borderos=borderos, total=total, n_titulos=n_titulos, p_medio=p_medio)
    


@app.route('/relatorios', methods=['GET', 'POST'])
@login_required
def relatorios():
    return redirect('/')


# ----- FIRST PAGE ------ #
@app.route('/login', methods=['GET', 'POST'])
def login():

    # connect database
    con = sqlite3.connect('brn.db')
    con.row_factory = sqlite3.Row

    # create cursor
    cur = con.cursor()
    
    # login user
    # GET
    if request.method == 'GET':
        return render_template('login.html')

    # POST
    else:

        # forget any user_id
        session.clear()

        # blank user and password
        if not request.form.get('user'):
            return render_template('login.html')
        
        elif not request.form.get('password'):
            return render_template('login.html')

        usr = request.form.get('user')

        # query db for users
        cur.execute('SELECT * FROM usuario WHERE nome= ?', (usr,))

        rows = cur.fetchall()
        # ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return render_template('login.html')
        
        # remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # redirect user to home page
        return redirect("/")

@app.route('/register', methods=['GET', 'POST'])
def register():

    # connect database
    con = sqlite3.connect('brn.db')
    con.row_factory = sqlite3.Row

    # create cursor
    cur = con.cursor()

    # register user
    # GET
    if request.method == 'GET':
        return render_template('register.html')

    # POST
    else:

        # try to get user and password
        try:
            user = request.form.get('user')
            psswd = generate_password_hash(request.form.get('password'))

            # connect to db    
            with sqlite3.connect("brn.db") as con:
                cur = con.cursor()

                # insert new user to db
                cur.execute("INSERT INTO usuario (nome, hash) VALUES (?,?)",(user, psswd) )
            
                con.commit()

        except:
            con.rollback()

        finally:
            # return to login
            return redirect('/login')
        
        # close connection
        con.close()

@app.route("/logout")
def logout():

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect("/")



        
    
            


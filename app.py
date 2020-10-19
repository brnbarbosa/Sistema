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

def getApp():
    return app

# ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['TESTING'] = False

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
    # connect database
    con = sqlite3.connect('brn.db')
    con.row_factory = sqlite3.Row

    # create cursor
    cur = con.cursor()

    ttlos = cur.execute('SELECT * FROM titulo')
    ttlos = cur.fetchall()

    for row in ttlos:
        if row['status'] == 'Em Aberto' and datetime.strptime(row['vencimento'], '%Y-%m-%d').date() < date.today():
            cur.execute("UPDATE titulo SET status = 'Vencido' WHERE vencimento = ?", (row['vencimento'],))
            con.commit()


    con.close()

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
        rows = cur.execute('SELECT * FROM sacados ORDER BY nome')

        rows = cur.fetchall()

        return render_template('sacados.html', rows=rows)

    # POST
    else:
        nm = request.form.get('nome').upper()
        cp = request.form.get('cep')
        end = request.form.get('endereco').upper()
        cnpj = request.form.get('cnpj')

        nm_testing = cur.execute('SELECT * FROM sacados WHERE nome = ?', (nm,))
        nm_testing = cur.fetchone()

        if nm_testing == None:
             # insert new 'sacado' to db
            cur.execute("INSERT INTO sacados (nome, cep, endereço, cnpj) VALUES (?,?,?,?)",(nm, cp, end, cnpj) )
            con.commit() 
        else:
            cur.execute('UPDATE sacados SET cep=:c, endereço=:e, cnpj=:j WHERE nome=:n;', {'c':cp, 'e':end, 'j':cnpj, 'n':nm,})
            con.commit() 
                       

        return redirect('/sacados')

@app.route('/atualizar', methods=['GET', 'POST'])
@login_required
def atualizar():
    # connect database
    con = sqlite3.connect('brn.db')
    con.row_factory = sqlite3.Row

    # create cursor
    cur = con.cursor()

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
        cur.execute('SELECT * FROM clientes ORDER BY nome')

        rows = cur.fetchall()

        return render_template('clientes.html', rows=rows)

    # POST
    else:

        inputs = {
            'nm': request.form.get('nome').upper(),
            'cp': request.form.get('cep'),
            'end': request.form.get('endereco').upper(),
            'cnpj': request.form.get('cnpj'),
            'taxa': request.form.get('tx')
        }
        

         # insert new 'sacado' to db
        cur.execute("INSERT INTO clientes (nome, cep, endereço, cnpj, taxa) VALUES (?,?,?,?,?)", (inputs['nm'], inputs['cp'], inputs['end'], inputs['cnpj'], inputs['taxa']) )
            
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
    cliente = cur.execute('SELECT nome FROM clientes ORDER BY nome')
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
        nm_cliente = request.form.get('cliente').upper()

        # name of sacado
        nm_sacado = request.form.get('sacado').upper()

        checkSacado = cur.execute('SELECT id FROM sacados WHERE nome = ?;', (nm_sacado,))
        checkSacado = cur.fetchone()

        if checkSacado == None:
            # insert new 'sacado' to db
            cur.execute("INSERT INTO sacados (nome, cep, endereço, cnpj) VALUES (?,?,?,?)",(nm_sacado, 'Inserir', 'Inserir', 'Inserir') )
            con.commit()

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
        taxa = cur.execute('SELECT taxa FROM clientes WHERE nome = ?', (nm_cliente,))
        taxa = cur.fetchall()

        # factor
        fator = factor(taxa[0]['taxa'], dias, valor)

        # liquido of operation
        liquido = float(lqd(fator, valor))
 
        # insert all that information in a support table
        cur.execute('INSERT INTO borderos (cliente, sacado, titulo, valor, vencimento, dt_negoc, tipo, taxa, fator, liquido, prazo) VALUES (?,?,?,?,?,?,?,?,?,?,?)', 
                    (nm_cliente, nm_sacado, titulo, valor, request.form.get('vencimento'), date.today(), tipo, taxa[0]['taxa'], fator, liquido, dias))

        con.commit()

        return render_template('operacao.html', sacado=sacado, cliente=cliente, bordero=borderos)

@app.route('/cancelar', methods=['GET', 'POST'])
@login_required
def cancelar():

    # connect database
    con = sqlite3.connect('brn.db')
    con.row_factory = sqlite3.Row

    # create a cursor
    cur = con.cursor()

    # cancela a operação
    cur.execute('DELETE FROM borderos')
    con.commit()

    return redirect('/')

        
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

    fator = cur.execute('SELECT SUM(fator) FROM borderos')
    fator = cur.fetchall()

    li = cur.execute('SELECT SUM(liquido) FROM borderos')
    li = cur.fetchall()

    # insert all data in Titulos
    for row in borderos:
        cId = cur.execute('SELECT id FROM clientes WHERE nome = (SELECT cliente FROM borderos WHERE cliente = ?)', (row['cliente'],))
        cId = cur. fetchall()

        sId = cur.execute('SELECT id FROM sacados WHERE nome = (SELECT sacado FROM borderos WHERE sacado = ?)', (row['sacado'],))
        sId = cur.fetchall()

        cur.execute("INSERT INTO titulo (cliente_id, sacado_id, titulo, vencimento, valor, dt_negoc, tipo, status, nm_sac) VALUES (?,?,?,?,?,?,?,?,?)",
                    (cId[0]['id'], sId[0]['id'], row['titulo'], row['vencimento'], row['valor'], row['dt_negoc'], row['tipo'], "Em Aberto", row['sacado']))

        con.commit()

    if request.method == 'GET':
        return render_template('/bordero.html', borderos=borderos, total=total, n_titulos=n_titulos, p_medio=p_medio, fator=fator, li=li)
    else:
        return render_template('/bordero.html', borderos=borderos, total=total, n_titulos=n_titulos, p_medio=p_medio, fator=fator, li=li)

@app.route('/encerrar', methods=['POST'])
@login_required
def encerrar():

    # connect database
    con = sqlite3.connect('brn.db')
    con.row_factory = sqlite3.Row

    # create a cursor
    cur = con.cursor()

    cur.execute('DELETE FROM borderos')

    con.commit()
    con.close()
    
    return redirect('/')



@app.route('/relatorios', methods=['GET', 'POST'])
@login_required
def relatorios():
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

    # query títulos table 
    tit = cur.execute('SELECT * FROM titulo')
    tit = cur.fetchall()

    # GET
    if request.method == "GET":
        return render_template('/relatorios.html', cliente=cliente, sacado=sacado, titulo=tit)

    # POST
    else:

        inputs = {
                "cliente_id": None,
                "sacado_id": None,
                "tipo": "'" + request.form.get('tipo') + "'",
                "status": "'" + request.form.get('status') + "'",
                "titulo": "'" + request.form.get('titulo') + "'",
                "vencimento": request.form.get('vencimento')
        }

        # get all user inputs
        nm_cli = request.form.get('cliente')
        if nm_cli != None:
            nm_cli = nm_cli.upper()
            cID = cur.execute('SELECT id FROM clientes WHERE nome = ?', (nm_cli,))
            cID = cur.fetchall()
            inputs['cliente_id'] = cID[0]['id']

        nm_sac = request.form.get('sacado')
        if nm_sac != None:
            nm_sac = nm_sac.upper()
            sID = cur.execute('SELECT id FROM sacados WHERE nome = ?', (nm_sac,))
            sID = cur.fetchall()
            inputs['sacado_id'] = sID[0]['id']


        sql = 'SELECT * FROM titulo'
        where =[]

        for key in inputs:
            if inputs[key] != None and inputs[key] != "''" and inputs[key] != '':
                where.append(f'{key} = {inputs[key]}')
                
        if where:
            sql = '{} WHERE {}'.format(sql, ' AND '.join(where,))

        titulos = cur.execute(sql)
        titulos = cur.fetchall()
                
        return render_template('/relatorios.html', cliente=cliente, sacado=sacado, titulo=titulos)

@app.route('/baixa', methods=['GET', 'POST'])
@login_required
def baixa():

     # connect database
    con = sqlite3.connect('brn.db')
    con.row_factory = sqlite3.Row

    # create a cursor
    cur = con.cursor()

    
    # query cliente table to list all clientes
    cliente = cur.execute('SELECT nome FROM clientes')
    cliente = cur.fetchall()

    # query títulos table 
    titlo = cur.execute('SELECT * FROM titulo WHERE status != "Quitado" ORDER BY vencimento')
    titlo = cur.fetchall()

    if request.method == 'GET':
        return render_template('baixa.html', cliente=cliente, titulo=titlo)

    else:

        # get user inputs
        inputs = {
            "cliente_id": None,
            "titulo": request.form.get('titulo'),
            "dt_baixa": request.form.get('dt_baixa')
        }

        nm_cli = request.form.get('cliente').upper()
        if nm_cli != None:
            cID = cur.execute('SELECT id FROM clientes WHERE nome = ?', (nm_cli,))
            cID = cur.fetchall()
            inputs['cliente_id'] = cID[0]['id']

        cur.execute("UPDATE titulo SET dt_baixa=:dt, status='Quitado' WHERE cliente_id=:idC AND titulo=:tit;", {'dt':inputs['dt_baixa'], 'idC':inputs['cliente_id'], 'tit':inputs['titulo']})
        con.commit()

        titlo = cur.execute('SELECT * FROM titulo WHERE status != "Quitado" ORDER BY vencimento')
        titlo = cur.fetchall()

        return render_template('baixa.html', cliente=cliente, titulo=titlo)

@app.route('/adiantamentos', methods=['GET', 'POST'])
@login_required
def adiantamentos():
    # connect database
    con = sqlite3.connect('brn.db')
    con.row_factory = sqlite3.Row

    # create a cursor
    cur = con.cursor()

    # query cliente table to list all clientes
    cliente = cur.execute('SELECT nome FROM clientes')
    cliente = cur.fetchall()

    # query adiantamentos table
    ad = cur.execute('SELECT * FROM adiantamentos')
    ad = cur.fetchall()

    if request.method == "GET":
        return render_template('adiantamentos.html', cliente=cliente, adiantamento=ad)

    else:

        # get user inputs
        inputs = {
            "cliente_id": None,
            "valor": request.form.get('valor')
        }

        nm_cli = request.form.get('cliente').upper()
        if nm_cli != None:
            cID = cur.execute('SELECT id FROM clientes WHERE nome = ?', (nm_cli,))
            cID = cur.fetchall()
            inputs['cliente_id'] = cID[0]['id']

        cur.execute('INSERT INTO adiantamentos (cliente_id, data, valor) VALUES (?,?,?)', (inputs['cliente_id'], date.today(), inputs['valor']))
        con.commit()

        # query adiantamentos table
        ad = cur.execute('SELECT * FROM adiantamentos')
        ad = cur.fetchall()

        return render_template('adiantamentos.html', cliente=cliente, adiantamento=ad)

@app.route('/quitacao', methods=['GET', 'POST'])
@login_required
def quitacao():

     # connect database
    con = sqlite3.connect('brn.db')
    con.row_factory = sqlite3.Row

    # create a cursor
    cur = con.cursor()

    
    # query cliente table to list all clientes
    cliente = cur.execute('SELECT nome FROM clientes')
    cliente = cur.fetchall()

    # query adiantamentos table
    ad = cur.execute('SELECT * FROM adiantamentos')
    ad = cur.fetchall()

    if request.method == 'GET':
        return render_template('quitacao.html', cliente=cliente, adiantamento=ad)

    else:

        # get user inputs
        inputs = {
            "cliente_id": None,
            "valor": request.form.get('valor')
        }

        nm_cli = request.form.get('cliente').upper()
        if nm_cli != None:
            cID = cur.execute('SELECT id FROM clientes WHERE nome = ?', (nm_cli,))
            cID = cur.fetchall()
            inputs['cliente_id'] = cID[0]['id']

        cur.execute("DELETE FROM adiantamentos WHERE cliente_id=:idC AND valor=:vl", {'idC':inputs['cliente_id'], 'vl':inputs['valor']})
        con.commit()

        # query adiantamentos table
        ad = cur.execute('SELECT * FROM adiantamentos')
        ad = cur.fetchall()

        return render_template('quitacao.html', cliente=cliente, adiantamento=ad)

@app.route('/balanco', methods=['GET', 'POST'])
@login_required
def balanco():

     # connect database
    con = sqlite3.connect('brn.db')
    con.row_factory = sqlite3.Row

    # create a cursor
    cur = con.cursor()

    # query cheques and em aberto
    cheques = cur.execute('SELECT SUM(valor) FROM titulo WHERE tipo = "cheque" AND status = "Em Aberto";')
    cheques = cur.fetchall()

    # query duplicatas and em aberto
    duplicatas = cur.execute('SELECT SUM(valor) FROM titulo WHERE tipo = "duplicata" AND status = "Em Aberto";')
    duplicatas = cur.fetchall()

    # query adiantamentos
    adiantamentos = cur.execute('SELECT SUM(valor) FROM adiantamentos;')
    adiantamentos = cur.fetchall()

    saldo = 0.00

    if request.method == 'GET':
        return render_template('balanco.html', cheques=cheques, duplicatas=duplicatas, adiantamentos=adiantamentos, saldo=saldo)

    else:

        # get user inputs
        saldo = float(request.form.get('saldo'))
        total = 0.00

        if cheques[0]['SUM(valor)'] != None and duplicatas[0]['SUM(valor)'] != None and adiantamentos[0]['SUM(valor)'] != None:
            total = saldo + cheques[0]['SUM(valor)'] + duplicatas[0]['SUM(valor)'] + adiantamentos[0]['SUM(valor)']
        elif cheques[0]['SUM(valor)'] == None:
            total = saldo + duplicatas[0]['SUM(valor)'] + adiantamentos[0]['SUM(valor)']
        elif duplicatas[0]['SUM(valor)'] == None:
            total = saldo + cheques[0]['SUM(valor)'] + adiantamentos[0]['SUM(valor)']
        elif adiantamentos[0]['SUM(valor)'] == None:
            total = saldo + cheques[0]['SUM(valor)'] + duplicatas[0]['SUM(valor)']
        else:
            total = saldo


        return render_template('balanco.html', cheques=cheques, duplicatas=duplicatas, adiantamentos=adiantamentos, saldo=saldo, total=total)



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



        
    
            


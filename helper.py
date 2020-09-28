from flask import redirect, render_template, request, session
from functools import wraps

from datetime import date

def login_required(f):
    # decorator to check login
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def dias(vencimento):
    return (date.today() - vencimento)

def prazo_medio(n_titulos, dias):
    return (dias / n_titulos)

def fator(taxa, dias):
    return ((taxa/30) * dias)

def liquido(fator, valor):
    return (valor * fator)
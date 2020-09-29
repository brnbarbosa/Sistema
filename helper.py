from flask import redirect, render_template, request, session
from functools import wraps

from datetime import datetime, date

def login_required(f):
    # decorator to check login
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def prazo_medio(n_titulos, dias):
    return (dias / n_titulos)

def lqd(vencimento, taxa, valor):
    dias = (vencimento - date.today()).days
    fator = ((taxa/30) * dias)/100
    liquido = valor - (fator * valor)
    return float(liquido)
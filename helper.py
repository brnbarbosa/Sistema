from flask import redirect, render_template, request, session
from functools import wraps

from datetime import datetime, date

import math

def login_required(f):
    # decorator to check login
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def day(vencimento):
    # TODO IMPLEMENTAR DIAS DA SEMANA
    return ((vencimento - date.today()).days + 1)

def prazo_medio(n_titulos, dias):
    return (dias / n_titulos)

def factor(taxa, dias, valor):
    expo = dias / 30
    base = (taxa / 100) + 1
    factor = (valor * pow(base, expo)) - valor
    return factor

def lqd(fator, valor):
    liquido = valor - fator
    return float(liquido)
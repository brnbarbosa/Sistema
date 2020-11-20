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

def day(vencimento, dt_negoc):
    if vencimento.weekday() == 5:
        return ((vencimento - dt_negoc).days + 3)
    elif vencimento.weekday() == 6:
        return ((vencimento - dt_negoc).days + 2)
    else:
        return ((vencimento - dt_negoc).days + 1)

def prazo_medio(n_titulos, dias):
    return (dias / n_titulos)

def factor(taxa, dias, valor):
    expo = math.floor((dias / 30)*100)/100
    base = (taxa / 100) + 1
    factor = (valor * pow(base, expo)) - valor
    return factor

def lqd(fator, valor):
    liquido = valor - fator
    return float(liquido)
import time

from celery_app import celery_app

@celery_app.task
def calcular_soma(a:int, b:int):
    time.sleep(3)
    return a + b

@celery_app.task
def calcular_fatorial(n):
    time.sleep(3)
    resultado = 1
    for i in range(n, 0, -1):
        resultado *= i
    return resultado
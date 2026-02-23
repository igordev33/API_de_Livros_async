from celery import Celery
import time
import os

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")

celery_app = Celery("celery_worker", broker=f"redis://{REDIS_HOST}:{REDIS_PORT}/0", backend=f"redis://{REDIS_HOST}:{REDIS_PORT}/0")

@celery_app.task
def calcular_soma(a:int, b:int):
    time.sleep(3)
    return a + b

@celery_app.task
def calcular_fatorial(n):
    time.sleep(3)
    if n == 0:
        return 1
    resultado = 1
    for i in range(n, 0, -1):
        resultado *= i
    return resultado
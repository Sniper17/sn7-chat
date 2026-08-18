# Configuração limpa do Baguncinha.
# Não existe wrapper de handle_message aqui. Os comandos pertencem ao novo Worker.
import os

timeout = int(os.getenv("GUNICORN_TIMEOUT", "240"))
graceful_timeout = 30
workers = 1

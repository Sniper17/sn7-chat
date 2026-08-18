# Baguncinha — v4 private async commands

- Mantém !cmds, !cmdp e !cmda locais.
- Comandos enviados ao Worker usam job assíncrono.
- O painel consulta o resultado até ~190s, permitindo o Render acordar sem travar o Gunicorn.
- Comandos privados continuam privados e não são publicados na Kick.

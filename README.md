# SN7 Chat v3.1 — privado isolado

Interface de testes do SN7 Chat/Baguncinha.

## Regra de isolamento

O painel envia todos os comandos com a origem explícita:

- `source=private`
- `channel=private`
- `delivery=private_only`
- `reply_only=true`

Também envia os mesmos valores nos headers `X-Command-*`.

Isso permite que o novo SN7 Kick Worker execute os mesmos comandos da live sem publicar a resposta do painel privado no Kick e sem importar mensagens da live para este painel.

### Importante para o Worker

O Worker precisa respeitar `source=private`/`delivery=private_only`: quando a origem for `private`, ele deve retornar a resposta HTTP para o painel, mas **não enviar a resposta para o chat da Kick** e não inserir a mensagem no fluxo de eventos públicos da live.

A lógica dos comandos continua centralizada no Worker. O painel não cria uma segunda implementação dos comandos.

## Render

Start command:

`gunicorn app:app`

Variáveis esperadas:

- `WORKER_COMMAND_URL`
- `WORKER_COMMAND_KEY`
- `BROADCASTER_USER_ID`
- opcional: `REQUEST_TIMEOUT` (padrão 180)
- opcional: `COMMAND_SOURCE` (padrão `private`)

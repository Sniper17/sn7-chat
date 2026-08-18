# SN7 Chat + SN7 Core — v4.0

Esta atualização conecta o Baguncinha diretamente ao SN7 Core.

## Funcionamento

- `!placos` (ou o comando de moeda salvo no painel) consulta o SN7 Core.
- `!rank`, `!ranking` e `!top` consultam o ranking do SN7 Core.
- Comandos personalizados salvos no painel do Core podem ser testados no chat privado.
- `!cmds` e `!cmdp` mostram os comandos cadastrados no Core quando ele estiver acessível.
- Outros comandos continuam passando pelo Kick Worker.
- O painel continua enviando os comandos como privados.

## Render

Mantenha as variáveis existentes:

- WORKER_COMMAND_URL
- WORKER_COMMAND_KEY
- BROADCASTER_USER_ID
- COMMAND_SOURCE

Adicione/confirme:

- SN7_CORE_URL = endereço público do serviço SN7 Core
- SN7_CORE_TIMEOUT = 10

O código usa `https://sn7-core.onrender.com` como padrão apenas se `SN7_CORE_URL` não existir. Se o seu serviço no Render tiver outro endereço, use o endereço real em `SN7_CORE_URL`.

`BROADCASTER_USER_ID` deve ser o ID do canal usado no SN7 Core.

## Instalação

Substitua `app.py` pelo arquivo deste pacote e coloque `core_client.py` na mesma pasta. O `requirements.txt` já está incluído.

# SN7 Chat V3.9 — wake direto

Correção específica do chat privado.

O Twitch/Kick continua normal e não é alterado.

No chat privado:
- `!wake` agora acorda diretamente Kick, RedSec e Warzone;
- `!bf <arma>` acorda o RedSec antes de consultar `/classe`;
- `!classe <arma>` e `!meta <tipo>` acordam o Warzone antes de consultar `/meta`;
- se houver erro após o wake, o chat tenta uma segunda vez.

A API Central fica somente como fallback do `!wake`, não como dependência
obrigatória para Warzone/RedSec.

Kick continua sendo chamado diretamente.

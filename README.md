# SN7 Chat V3.7

Correção do histórico.

O print mostrou que `/ultimabriga` e `/ultimobanco` não existem no deployment
atual da API Kick, então o chat não deve depender dessas rotas.

Agora:
- `!briga @usuario` salva a resposta da última briga no próprio chat.
- `!ultimabriga` recupera essa última briga.
- `!bancores` / `!resultado` salva o último resultado do banco.
- `!ultimobanco` recupera esse último resultado.

Os comandos usam somente rotas Kick que já estavam funcionando.

Observação: o cache fica na memória do processo do chat. Se o serviço do
Render reiniciar, o histórico recente é perdido e começa vazio novamente.

# SN7 Chat V3.6 — serviços diretos

Correção principal: os comandos do chat não passam mais pelas rotas
`/kick/<rota>`, `/warzone/<rota>` e `/redsec/<rota>` da API Central.

O chat chama diretamente:
- Kick: https://kick-duelo-api.onrender.com
- Warzone: https://warzone-api-qbn9.onrender.com
- RedSec: https://redsec-loadout-api.onrender.com

A Central continua sendo usada para:
- `!wake`
- `!health`

Isso evita que uma rota ausente no proxy central faça o chat exibir a página
HTML/SVG 404 do Render.

Também há proteção para não exibir HTML de erro cru no chat.

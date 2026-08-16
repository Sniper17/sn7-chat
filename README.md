# SN7 Chat V3.13 — health corrigido

`!health` não depende mais da rota `/health` da API Central.

Agora consulta diretamente os três serviços:
- Kick
- RedSec
- Warzone

E retorna um resumo simples de disponibilidade.

Exemplo:
`🩺 HEALTH • kick 🟢 • redsec 🟢 • warzone 🟢 • 3/3 online`

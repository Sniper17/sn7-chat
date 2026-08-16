# SN7 Chat V3 — Completo

Chat particular conectado à API Central.

## Kick / eventos
- `!rank` -> `/kick/ranking`
- `!placos` ou `!pontos` -> `/kick/pontos`
- `!bandido` -> `/kick/bandido`, pistola por padrão
- `!bandido fuzil` -> equipamento informado
- `!policia` -> `/kick/policia`, pistola por padrão
- `!policia fuzil` -> equipamento informado
- `!c4banco 1000` -> `/kick/c4banco`
- `!bancores` ou `!resultado` -> `/kick/resultado`
- `!briga @usuario` -> `/kick/briga`

## Jogos
- `!bf svd` -> RedSec `/classe?arma=svd`
- `!classe c9` -> Warzone `/meta?tipo=c9`
- `!meta ar` -> Warzone `/meta?tipo=ar`

## Infra
- `!wake` -> acorda/verifica Kick, Warzone e RedSec
- `!health` -> saúde da central

IMPORTANTE:
A V3 usa `SN7Fps` como usuário padrão no chat particular porque o chat
ainda não tem autenticação/login. Quando quisermos permitir outros usuários,
adicionaremos identidade/login.

# SN7 Chat — Baguncinha (privado)

Versão 3.3 — painel privado de testes dos comandos do Worker.

## Listas de comandos

- `!cmds` → somente comandos públicos.
- `!cmdp` → somente comandos personalizados.
- `!cmda` → somente comandos de ADM, disponível no painel privado.

As listas são resolvidas localmente pelo painel e não dependem da identificação de uma live.

## ADM

`!addplaco`, `!addpoints`, `!setplaco`, `!setpoints`, `!faliu`, `!add cmd`, `!edit cmd`, `!del cmd`

`!c4banco`, `!policia` e `!bandido` não entram nas listas. Esses comandos pertencem ao fluxo de ações e são anunciados quando necessário.

## Isolamento

O painel envia os testes ao Worker com `source=private`, `channel=private`, `delivery=private_only` e `reply_only=true`, para que as respostas permaneçam no painel e não sejam publicadas na live.

## Interface

- Tela inicial sem o título “Baguncinha” no centro.
- Instruções diretas para `!cmda`, `!cmds` e `!cmdp`.
- Campo de mensagem com alinhamento vertical centralizado.
- Mantido o tratamento de teclado móvel com `visualViewport`.

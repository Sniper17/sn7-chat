# SN7 Chat V3.10

Ajuste do Warzone no chat privado.

- `!bf` continua funcionando diretamente no RedSec.
- `!classe`/`!meta` tentam Warzone direto, com retry.
- Se o Warzone direto falhar, o chat tenta `/warzone/meta` pela API Central.
- `!wake` agora mostra `x/3`, pois são três serviços principais; o fallback
  da Central não é contado como quarto serviço.

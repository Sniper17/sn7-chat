# SN7 Chat V3.8

Correção do Warzone e RedSec.

O V3.7 chamou diretamente:
- Warzone `/meta`
- RedSec `/classe`

O print mostrou que esses caminhos estão retornando 404 HTML quando chamados
diretamente pelo chat.

V3.8 volta a usar a API Central para essas duas integrações, nos caminhos que
já foram validados no projeto:
- `/warzone/meta?tipo=...`
- `/redsec/classe?arma=...`

Kick continua sendo chamado diretamente pela `kick-duelo-api`.

Também há proteção para qualquer resposta HTML/SVG de erro não aparecer como
código no chat.

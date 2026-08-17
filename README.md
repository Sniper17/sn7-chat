# SN7 Chat V3.14 — !batalha

Adicionado o comando privado:

`!batalha @jogador`

Ele chama diretamente a API Kick:
`/duelo?jogador1=SN7Fps&jogador2=<alvo>`

A API Kick continua responsável por aplicar o resultado do duelo e atualizar
os pontos/V-D usados no ranking. O chat apenas exibe a resposta.

Há wake + retry para lidar com cold start do Render.

No StreamElements, a sintaxe correta para a Twitch é:
`$(customapi https://kick-duelo-api.onrender.com/duelo?jogador1=$(sender)&jogador2=$(queryescape ${1:}))`

A documentação atual do StreamElements confirma que `${1:}` é válido dentro
de `$(queryescape)` e que `$(customapi)` faz GET com timeout de 15 segundos.

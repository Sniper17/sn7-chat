# SN7 Chat v2.1

Interface de chat restaurada e melhorada para celular.

- Caixa de mensagem fixa e separada do histórico.
- Ajuste automático para teclado virtual usando Visual Viewport.
- Área de mensagens com espaço reservado para não ficar atrás do compositor.
- Enter envia; Shift+Enter quebra linha.
- Não usa autofocus, evitando abrir o teclado sozinho.
- Mantém `/chat`, `/health` e os comandos do SN7 Chat.

Start command no Render: `gunicorn app:app`

def post_worker_init(worker):
    import app as chat_app

    original = chat_app.handle_message

    aliases = {
        "!placo": "!placos",
        "!ponto": "!placos",
        "!pontos": "!placos",
        "!ranking": "!rank",
        "!top": "!rank",
    }

    def handle_message_with_aliases(msg):
        raw = str(msg or "").strip()
        low = raw.lower()

        # Preserve the existing behavior, only normalizing aliases.
        if low in aliases:
            return original(aliases[low])

        return original(msg)

    chat_app.handle_message = handle_message_with_aliases

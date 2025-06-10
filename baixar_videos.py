import asyncio
from telethon.sync import TelegramClient
from telethon.tl.types import MessageMediaDocument
import os

# Substitua pelas suas credenciais
api_id = 25632854     # <-- seu API ID
api_hash = 'e66d7cff5c25af82bd9fe827a90ebe41'  # <-- seu API HASH
phone_number = '+5515991843604'  # Com o DDD

# Nome da sessão (será criada automaticamente)
client = TelegramClient('minha_sessao', api_id, api_hash)

def limpar_nome(nome):
    # Remove caracteres inválidos no Windows/Linux
    return "".join(c for c in nome if c.isalnum() or c in (' ', '.', '_', '-')).rstrip()

async def baixar_video(message, pasta, nome_canal):
    if message.video or isinstance(message.media, MessageMediaDocument):
        # Tenta usar o nome original do arquivo, se existir
        if message.file and message.file.name:
            filename = limpar_nome(message.file.name)
        else:
            filename = f"{nome_canal}_video_{message.id}.mp4"
        
        path = os.path.join(pasta, filename)
        
        if os.path.exists(path):  # Evita downloads duplicados
            print(f"Já existe: {filename}")
            return

        print(f"Baixando: {filename}")
        with open(path, 'wb') as f:
            async for chunk in client.iter_download(message.media, chunk_size= 8 * 1024 * 1024):
                f.write(chunk)

async def main():
    await client.start(phone_number)

    print("Listando seus canais e grupos...\n")
    canais = []
    async for dialog in client.iter_dialogs():
        if dialog.is_channel:
            canais.append(dialog)

    for idx, canal in enumerate(canais):
        print(f"[{idx}] {canal.name} (ID: {canal.id})")

    escolha = int(input("\nDigite o número do canal desejado: "))
    canal_escolhido = canais[escolha]
    nome_canal = limpar_nome(canal_escolhido.name)
    print(f"\nSelecionado: {nome_canal}")

    pasta = 'videos'
    os.makedirs(pasta, exist_ok=True)

    print("\nBuscando mensagens...\n")
    mensagens = []
    async for message in client.iter_messages(canal_escolhido.id, limit=1000):
        if message.video or isinstance(message.media, MessageMediaDocument):
            mensagens.append(message)

    print(f"\nTotal de vídeos encontrados: {len(mensagens)}")

    # Controla paralelismo (máx 5 ao mesmo tempo)
    sem = asyncio.Semaphore(10)

    async def baixar_com_limite(msg):
        async with sem:
            try:
                # Reatualiza a mensagem para evitar erro de referência expirada
                msg_atualizada = await client.get_messages(msg.chat_id, ids=msg.id)
                await baixar_video(msg_atualizada, pasta, nome_canal)
            except Exception as e:
                print(f"❌ Erro ao baixar mensagem {msg.id}: {e}")

    await asyncio.gather(*[baixar_com_limite(m) for m in mensagens])

    print("\n✅ Todos os vídeos foram baixados.")

with client:
    client.loop.run_until_complete(main())

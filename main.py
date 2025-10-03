#!/usr/bin/env python3
"""
Bot do Telegram - Assistente Financeiro (Versão SEGURA)
Usa variáveis de ambiente para proteger credenciais
"""

import requests
import json
import time
import logging
import os
from datetime import datetime, timedelta
from salvar_gasto import salvar_gasto

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Token do bot (usando variável de ambiente)
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN não configurado! Configure a variável de ambiente BOT_TOKEN.")

# URL base da API do Telegram
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Estados da conversa
user_states = {}

# Categorias disponíveis (mesmas do Excel)
CATEGORIAS = [
    "Moradia", "Alimentação", "Empréstimo", "Investimento", "Cartão de crédito",
    "Transporte", "Serviços", "Lazer", "Saúde", "Educação", "Outros"
]

def send_message(chat_id, text, reply_markup=None):
    """Envia mensagem para o chat"""
    url = f"{BASE_URL}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text
    }
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    
    try:
        response = requests.post(url, json=data, timeout=10)
        result = response.json()
        if result.get('ok'):
            logger.info(f"✅ Mensagem enviada: {text}")
            return True
        else:
            logger.error(f"❌ Erro ao enviar: {result}")
            return False
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        return False

def get_updates(offset=None):
    """Obtém atualizações do bot"""
    url = f"{BASE_URL}/getUpdates"
    params = {"timeout": 30}
    if offset:
        params["offset"] = offset
    
    try:
        response = requests.get(url, params=params, timeout=35)
        result = response.json()
        if result.get('ok'):
            return result
        else:
            logger.error(f"❌ API Error: {result}")
            return None
    except Exception as e:
        logger.error(f"❌ Erro ao obter updates: {e}")
        return None

def handle_start(chat_id, user_id):
    """Inicia conversa para registrar gasto"""
    logger.info(f"🚀 Iniciando conversa para usuário {user_id}")
    user_states[user_id] = {"state": "descricao"}
    send_message(chat_id, "💰 Vamos registrar um gasto!\n\nO que você comprou?")
    return "descricao"

def handle_descricao(chat_id, user_id, text):
    """Recebe descrição do gasto"""
    logger.info(f"📝 Descrição: {text}")
    user_states[user_id]["descricao"] = text
    user_states[user_id]["state"] = "valor"
    send_message(chat_id, "💵 Quanto você gastou? (ex: 300,00)")
    return "valor"

def handle_valor(chat_id, user_id, text):
    """Recebe valor do gasto"""
    logger.info(f"💵 Valor: {text}")
    user_states[user_id]["valor"] = text
    user_states[user_id]["state"] = "data"
    
    reply_markup = {
        "keyboard": [["Hoje", "Ontem", "Data personalizada"]],
        "one_time_keyboard": True
    }
    send_message(chat_id, "📅 Quando foi?", reply_markup)
    return "data"

def handle_data(chat_id, user_id, text):
    """Recebe data do gasto"""
    logger.info(f"📅 Data: {text}")
    
    # Processar data
    if text == "Hoje":
        data = datetime.today().strftime("%d/%m/%Y")
    elif text == "Ontem":
        data = (datetime.today() - timedelta(days=1)).strftime("%d/%m/%Y")
    elif text == "Data personalizada":
        user_states[user_id]["state"] = "data_custom"
        send_message(chat_id, "📝 Digite a data no formato DD/MM/AAAA:")
        return "data_custom"
    else:
        # Assumir que é data personalizada
        data = text
    
    # Salvar data e ir para categoria
    user_states[user_id]["data"] = data
    user_states[user_id]["state"] = "categoria"
    
    # Criar teclado com categorias
    categorias_teclado = []
    for i in range(0, len(CATEGORIAS), 2):
        linha = [CATEGORIAS[i]]
        if i + 1 < len(CATEGORIAS):
            linha.append(CATEGORIAS[i + 1])
        categorias_teclado.append(linha)
    
    reply_markup = {
        "keyboard": categorias_teclado,
        "one_time_keyboard": True
    }
    send_message(chat_id, "📂 Escolha a categoria:", reply_markup)
    return "categoria"

def handle_categoria(chat_id, user_id, text):
    """Recebe categoria e salva gasto"""
    logger.info(f"📂 Categoria: {text}")
    user_states[user_id]["categoria"] = text
    
    try:
        logger.info("💾 Salvando gasto no Google Sheets...")
        salvar_gasto(
            user_states[user_id]["valor"],
            user_states[user_id]["descricao"],
            user_states[user_id]["data"],
            user_states[user_id]["categoria"]
        )
        
        send_message(chat_id, 
            f"✅ Gasto registrado com sucesso!\n\n"
            f"📝 Item: {user_states[user_id]['descricao']}\n"
            f"💵 Valor: R$ {user_states[user_id]['valor']}\n"
            f"📅 Data: {user_states[user_id]['data']}\n"
            f"📂 Categoria: {user_states[user_id]['categoria']}"
        )
        logger.info("✅ Gasto salvo com sucesso!")
        
    except Exception as e:
        logger.error(f"❌ Erro ao salvar: {e}")
        send_message(chat_id, f"❌ Erro ao salvar gasto: {str(e)}")
    
    # Limpar estado do usuário
    if user_id in user_states:
        del user_states[user_id]
    
    return "end"

def handle_help(chat_id):
    """Mostra ajuda"""
    help_text = """🤖 Assistente Financeiro Bot

Comandos:
/gasto - Registrar um novo gasto
/help - Mostrar esta ajuda

Fluxo:
1. /gasto → Digite o item
2. Digite o valor (ex: 300,00)
3. Escolha a data
4. Escolha a categoria

Categorias:
Moradia, Alimentação, Empréstimo, Investimento, Cartão de crédito, Transporte, Serviços, Lazer, Saúde, Educação, Outros
    """
    send_message(chat_id, help_text)

def process_message(update):
    """Processa mensagem recebida"""
    try:
        message = update.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        user_id = message.get("from", {}).get("id")
        text = message.get("text", "")
        
        logger.info(f"📨 Processando: user={user_id}, text='{text}'")
        
        if not chat_id or not text:
            return
        
        # Comandos
        if text.startswith("/"):
            if text == "/start" or text == "/gasto":
                handle_start(chat_id, user_id)
            elif text == "/help":
                handle_help(chat_id)
            elif text == "/cancel":
                if user_id in user_states:
                    del user_states[user_id]
                send_message(chat_id, "❌ Operação cancelada.")
            return
        
        # Estados da conversa
        if user_id in user_states:
            state = user_states[user_id].get("state")
            logger.info(f"🔄 Estado: {state}")
            
            if state == "descricao":
                handle_descricao(chat_id, user_id, text)
            elif state == "valor":
                handle_valor(chat_id, user_id, text)
            elif state == "data":
                handle_data(chat_id, user_id, text)
            elif state == "data_custom":
                # Processar data personalizada
                user_states[user_id]["data"] = text
                user_states[user_id]["state"] = "categoria"
                
                # Criar teclado com categorias
                categorias_teclado = []
                for i in range(0, len(CATEGORIAS), 2):
                    linha = [CATEGORIAS[i]]
                    if i + 1 < len(CATEGORIAS):
                        linha.append(CATEGORIAS[i + 1])
                    categorias_teclado.append(linha)
                
                reply_markup = {
                    "keyboard": categorias_teclado,
                    "one_time_keyboard": True
                }
                send_message(chat_id, "📂 Escolha a categoria:", reply_markup)
            elif state == "categoria":
                handle_categoria(chat_id, user_id, text)
        
    except Exception as e:
        logger.error(f"❌ Erro ao processar mensagem: {e}")

def main():
    """Função principal"""
    if BOT_TOKEN == "SEU_TOKEN_DO_BOT_AQUI":
        print("❌ ERRO: Configure a variável de ambiente BOT_TOKEN")
        return
    
    print("🤖 Bot SEGURO iniciado! Pressione Ctrl+C para parar.")
    print("📱 Envie /gasto para começar")
    print("🔍 Logs ativados")
    
    offset = None
    
    try:
        while True:
            updates = get_updates(offset)
            
            if updates and updates.get("ok"):
                for update in updates.get("result", []):
                    offset = update.get("update_id", 0) + 1
                    process_message(update)
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Bot parado pelo usuário")
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == '__main__':
    main()

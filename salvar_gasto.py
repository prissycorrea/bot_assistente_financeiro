import re, unicodedata
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread.utils import rowcol_to_a1
import os
import json

# === AUTH SEGURO (usando variáveis de ambiente) ===
scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]

# Buscar credenciais das variáveis de ambiente
credenciais_json = os.getenv('GOOGLE_CREDENTIALS')
if not credenciais_json:
    raise ValueError("GOOGLE_CREDENTIALS não configurado! Configure a variável de ambiente GOOGLE_CREDENTIALS.")

# Converter string JSON para dict
credenciais_dict = json.loads(credenciais_json)
creds = ServiceAccountCredentials.from_json_keyfile_dict(credenciais_dict, scope)

client = gspread.authorize(creds)

# ID da planilha (usando variável de ambiente)
SHEET_ID = os.getenv('SHEET_ID', "1FhOzraDArNXpfyTwBG9hoR2LuF2lEg5g84AhjiDWXaQ")
spreadsheet = client.open_by_key(SHEET_ID)

# ---- helpers ----
def _norm(s: str) -> str:
    s = unicodedata.normalize("NFD", str(s))
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    return s.strip().lower()

def _find_header_row(ws):
    # procura de 8 a 25 por "nome da divida"
    for r in range(8, 26):
        row = [_norm(x) for x in ws.row_values(r)]
        if any("nome da divida" in c for c in row):
            return r
    # fallback no 13 se não achar
    return 13

def _map_cols(ws, header_row):
    # Mapear colunas fixas conforme solicitado
    cols = {}
    cols["descricao"] = 16  # Coluna P
    cols["data"] = 17       # Coluna Q  
    cols["categoria"] = 18  # Coluna R
    cols["valor"] = 19      # Coluna S
    
    return cols

def _next_free_row(ws, header_row, col_ref, min_start=14):
    start = max(min_start, header_row + 1)
    col_vals = ws.col_values(col_ref)
    last = len(col_vals)
    return max(start, last + 1)

def _parse_valor(txt):
    t = re.sub(r"[^\d,.-]", "", str(txt))
    if "," in t and "." in t:  # 1.234,56
        t = t.replace(".", "").replace(",", ".")
    elif "," in t:
        t = t.replace(",", ".")
    return float(t)

# ---- função principal ----
def salvar_gasto(valor, descricao, data_str, categoria):
    # 1) aba por data
    data_obj = datetime.strptime(data_str, "%d/%m/%Y")
    aba = data_obj.strftime("%m-%Y")
    
    try:
        ws = spreadsheet.worksheet(aba)
    except gspread.WorksheetNotFound:
        # Listar abas disponíveis para ajudar o usuário
        abas_disponiveis = [ws.title for ws in spreadsheet.worksheets()]
        raise RuntimeError(f"Aba '{aba}' não encontrada! Abas disponíveis: {abas_disponiveis}")

    # 2) header + colunas
    header = _find_header_row(ws)
    cols = _map_cols(ws, header)
    
    # 3) próxima linha vazia (usando VALOR como referência)
    row = _next_free_row(ws, header, cols["valor"], min_start=14)

    # 4) normaliza valor
    val = _parse_valor(valor) if not isinstance(valor, (int, float)) else float(valor)

    # 5) batch update - salvar nas colunas corretas
    updates = [
        {"range": f"{aba}!{rowcol_to_a1(row, cols['descricao'])}", "values": [[descricao]]},      # Coluna P
        {"range": f"{aba}!{rowcol_to_a1(row, cols['data'])}",      "values": [[data_str]]},       # Coluna Q
        {"range": f"{aba}!{rowcol_to_a1(row, cols['categoria'])}", "values": [[categoria]]},      # Coluna R
        {"range": f"{aba}!{rowcol_to_a1(row, cols['valor'])}",     "values": [[f"R$ {val:.2f}".replace(".", ",")]]}, # Coluna S
    ]
    
    # Atualizar todos os campos como texto
    if updates:
        body = {"valueInputOption": "USER_ENTERED", "data": updates}
        spreadsheet.values_batch_update(body)

    print(f"✅ {descricao} | R$ {val:.2f} | {data_str} | {categoria} -> {aba} L{row}")

# === exemplo de uso ===
# salvar_gasto("300,00", "Teste final", "25/10/2025", "Pago")

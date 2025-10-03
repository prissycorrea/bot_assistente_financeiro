# 🤖 Assistente Financeiro Bot

Bot do Telegram para registrar gastos em planilha Google Sheets.

## 🚀 Deploy

### Railway (Recomendado)

1. **Fork este repositório**
2. **Acesse [railway.app](https://railway.app)**
3. **Conecte com GitHub**
4. **Selecione seu repositório**
5. **Configure as variáveis de ambiente:**
   - `BOT_TOKEN`: Token do seu bot (obtenha no @BotFather)
   - `SHEET_ID`: ID da sua planilha Google Sheets
   - `GOOGLE_CREDENTIALS`: Credenciais JSON do Google (veja env_example.txt)

### GitHub Actions

1. **Configure os secrets no GitHub:**
   - Vá em Settings → Secrets and variables → Actions
   - Adicione: `BOT_TOKEN`, `SHEET_ID`, `GOOGLE_CREDENTIALS`

2. **O workflow já está configurado** (veja .github/workflows/deploy.yml)

## 📋 Configuração

### 1. Criar Bot no Telegram
1. Fale com [@BotFather](https://t.me/BotFather)
2. Use `/newbot`
3. Escolha um nome e username
4. Copie o token

### 2. Configurar Google Sheets
1. Crie uma planilha no Google Sheets
2. Compartilhe com o email do service account
3. Copie o ID da planilha (da URL)

### 3. Configurar Service Account
1. Acesse [Google Cloud Console](https://console.cloud.google.com)
2. Crie um projeto
3. Ative a Google Sheets API
4. Crie uma service account
5. Baixe o JSON de credenciais

## 🔧 Uso

Envie `/start` ou `/gasto` para o bot e siga as instruções:

1. **Descrição**: O que você comprou
2. **Valor**: Quanto gastou (ex: 300,00)
3. **Data**: Quando foi (Hoje, Ontem, ou data personalizada)
4. **Categoria**: Escolha uma categoria

## 📁 Estrutura

- `bot_assistente_financeiro.py` - Bot principal
- `salvar_gasto.py` - Função para salvar gastos
- `requirements.txt` - Dependências Python
- `runtime.txt` - Versão do Python
- `env_example.txt` - Exemplo de variáveis de ambiente

## 🛡️ Segurança

- ✅ Credenciais em variáveis de ambiente
- ✅ Sem tokens hardcoded
- ✅ .gitignore configurado
- ✅ Secrets do GitHub

## 📝 Categorias

- Moradia
- Alimentação  
- Empréstimo
- Investimento
- Cartão de crédito
- Transporte
- Serviços
- Lazer
- Saúde
- Educação
- Outros
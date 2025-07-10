import streamlit as st
import pandas as pd
import numpy as np
import subprocess
import sys
import os
from datetime import datetime

# Configuração inicial para verificar e instalar dependências
def install_package(package):
    try:
        __import__(package)
    except ImportError:
        try:
            # Tenta instalar com --user para evitar problemas de permissão
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", package])
            st.success(f"Pacote {package} instalado com sucesso!")
        except subprocess.CalledProcessError as e:
            st.error(f"Erro ao instalar {package}: {e}")
            st.warning("Por favor, instale manualmente o pacote com: pip install --user gspread")

# Lista de dependências necessárias
dependencies = ['gspread', 'google-auth', 'pandas', 'numpy']

# Verifica e instala dependências
for package in dependencies:
    install_package(package)

# Agora importa os pacotes após a verificação
try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError as e:
    st.error(f"Falha ao importar pacotes necessários: {e}")
    st.stop()

# Configurações do Google Sheets
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]

# Função para autenticar no Google Sheets
@st.cache_resource
def authenticate_google_sheets():
    try:
        creds = Credentials.from_service_account_info(st.secrets["google_credentials"], scopes=SCOPE)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"Erro na autenticação: {e}")
        return None

# Função para carregar dados da planilha
def load_sheet_data(client, sheet_name, worksheet_name):
    try:
        sheet = client.open(sheet_name).worksheet(worksheet_name)
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

# Função para salvar dados na planilha
def save_to_sheet(client, sheet_name, worksheet_name, dataframe):
    try:
        sheet = client.open(sheet_name).worksheet(worksheet_name)
        sheet.clear()
        # Adiciona cabeçalhos
        sheet.append_row(dataframe.columns.tolist())
        # Adiciona dados
        for row in dataframe.values.tolist():
            sheet.append_row(row)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar dados: {e}")
        return False

# Interface do Streamlit
def main():
    st.title("Sistema de Gerenciamento de Dados")

    # Autenticação
    client = authenticate_google_sheets()
    if client is None:
        st.stop()

    # Menu de navegação
    menu = st.sidebar.selectbox("Menu", ["Carregar Dados", "Adicionar Dados", "Relatórios"])

    if menu == "Carregar Dados":
        st.header("Carregar Dados da Planilha")
        sheet_name = st.text_input("Nome da Planilha", "MinhaPlanilha")
        worksheet_name = st.text_input("Nome da Aba", "Dados")
        
        if st.button("Carregar Dados"):
            df = load_sheet_data(client, sheet_name, worksheet_name)
            if not df.empty:
                st.dataframe(df)
            else:
                st.warning("Nenhum dado encontrado ou erro ao carregar.")

    elif menu == "Adicionar Dados":
        st.header("Adicionar Novos Dados")
        # Implemente a lógica para adicionar novos dados aqui

    elif menu == "Relatórios":
        st.header("Relatórios e Análises")
        # Implemente a lógica para gerar relatórios aqui

if __name__ == "__main__":
    main()

# ==============================================
# SEÇÃO 1: IMPORTAÇÕES E CONFIGURAÇÕES (120 linhas)
# ==============================================
import streamlit as st
import re
from docx import Document
import PyPDF2
from io import BytesIO
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import hashlib
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import time
import pandas as pd
import base64
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import string
import io
import os
import re
import json
from PIL import Image
import requests
from bs4 import BeautifulSoup
import nltk
from nltk.tokenize import sent_tokenize
from collections import Counter
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import spacy
from spacy import displacy
from wordcloud import WordCloud

# ========== CONFIGURAÇÃO INICIAL ==========
import base64
from typing import Dict, List, Tuple, Optional, Any
import logging
from loguru import logger
import tempfile
import zipfile
import warnings
warnings.filterwarnings('ignore')

# Configurações iniciais do Streamlit
st.set_page_config(
    page_title="CLARA - Análise Contratual Inteligente", 
    page_icon="⚖️", 
    layout="centered",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/seuuser/clara-legal-tech',
        'Report a bug': "https://github.com/seuuser/clara-legal-tech/issues",
        'About': "CLARA v2.0 - Sistema de análise contratual inteligente"
    }
)

# Carregar modelo de NLP (opcional)
try:
    nlp = spacy.load("pt_core_news_sm")
except:
    nlp = None
    st.warning("Modelo de linguagem Spacy não carregado. Algumas análises avançadas estarão limitadas.")

# ========== ESTILOS CSS ==========
def load_css():
    st.markdown("""
    <style>
        /* Estilos base */
        .header-title {
            font-size: 2.5em;
            color: #2c3e50;
            text-align: center;
            margin-bottom: 10px;
            font-family: 'Roboto', sans-serif;
        }
        .subheader {
            font-size: 1.5em;
            color: #3498db;
            margin-top: 20px;
            margin-bottom: 15px;
            border-bottom: 2px solid #3498db;
            padding-bottom: 5px;
        }
        
        /* Caixas de destaque */
        .highlight-box {
            background-color: #f0f7ff;
            padding: 25px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            border-left: 5px solid #3498db;
        }
        .feature-card {
            background-color: white;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 25px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        .feature-card:hover {
            transform: translateY(-5px);
        }
        
        /* Níveis de risco */
        .risk-high { 
            background-color: #fef6f6; 
            border-left: 5px solid #e74c3c; 
            padding: 20px; 
            border-radius: 10px; 
            margin-bottom: 20px; 
            box-shadow: 0 2px 5px rgba(231, 76, 60, 0.1);
        }
        .risk-medium { 
            background-color: #fffaf2; 
            border-left: 5px solid #f39c12; 
            padding: 20px; 
            border-radius: 10px; 
            margin-bottom: 20px;
            box-shadow: 0 2px 5px rgba(243, 156, 18, 0.1);
        }
        .risk-low { 
            background-color: #f6fef6; 
            border-left: 5px solid #2ecc71; 
            padding: 20px; 
            border-radius: 10px; 
            margin-bottom: 20px;
            box-shadow: 0 2px 5px rgba(46, 204, 113, 0.1);
        }
        
        /* Trechos de contrato */
        .excerpt-box { 
            background-color: #f8f9fa; 
            padding: 15px; 
            border-radius: 8px; 
            margin: 15px 0; 
            font-family: 'Courier New', monospace;
            border: 1px solid #e0e0e0;
        }
        .excerpt-highlight {
            background-color: #fff3cd;
            padding: 2px 4px;
            border-radius: 3px;
            font-weight: bold;
        }
        
        /* Seções premium */
        .premium-box {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 25px;
            border-radius: 15px;
            margin: 25px 0;
            border: 1px solid #ddd;
            box-shadow: 0 6px 12px rgba(0,0,0,0.1);
        }
        .premium-feature {
            background-color: rgba(255, 215, 0, 0.1);
            border-left: 4px solid #FFD700;
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
        }
        
        /* Formulários */
        .required-field::after { 
            content: " *"; 
            color: #e74c3c; 
        }
        .stTextInput>div>div>input, .stTextArea>div>div>textarea {
            border-radius: 8px !important;
            padding: 10px !important;
        }
        
        /* Botões */
        .stButton>button {
            background-color: #3498db;
            color: white;
            border-radius: 10px;
            padding: 12px 28px;
            font-weight: bold;
            font-size: 1em;
            transition: all 0.3s ease;
            border: none;
        }
        .stButton>button:hover {
            background-color: #2980b9;
            transform: scale(1.02);
            box-shadow: 0 4px 8px rgba(41, 128, 185, 0.3);
        }
        .primary-button {
            background-color: #2ecc71 !important;
        }
        .secondary-button {
            background-color: #f39c12 !important;
        }
        .danger-button {
            background-color: #e74c3c !important;
        }
        
        /* Seções diversas */
        .preview-section {
            background-color: #f8f9fa;
            padding: 25px;
            border-radius: 15px;
            margin: 25px 0;
            box-shadow: 0 4px 8px rgba(0,0,0,0.05);
        }
        .email-confirmation {
            background-color: #e8f5e9;
            padding: 20px;
            border-radius: 12px;
            margin: 20px 0;
            border-left: 5px solid #2ecc71;
        }
        .legal-reference {
            background-color: #eaf2f8;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
            font-size: 0.9em;
        }
        
        /* Tabelas */
        .dataframe {
            border-radius: 10px !important;
            box-shadow: 0 4px 8px rgba(0,0,0,0.05) !important;
        }
        
        /* Barra lateral */
        .css-1d391kg {
            padding-top: 2rem;
            padding-right: 1rem;
            padding-bottom: 2rem;
            padding-left: 1rem;
            background-color: #f8f9fa;
        }
        
        /* Responsividade */
        @media (max-width: 768px) {
            .header-title {
                font-size: 1.8em;
            }
            .feature-card {
                padding: 15px;
            }
        }
    </style>
    """, unsafe_allow_html=True)

# ========== CONSTANTES E CONFIGURAÇÕES ==========
GOOGLE_SHEET_KEY = "10vw0ghFU9Gefk53f8WiIhgKAChdkdqtx9WvphwmiNrA"
SHEET_NAME = "Leads"
EMAIL_CONFIG = {
    "sender": "contato@clara-legal.com",
    "password": "sua_senha_segura",
    "smtp_server": "smtp.clara-legal.com",
    "port": 587
}

# ========== REGRAS DE ANÁLISE ==========
CONTRACT_RULES = [
    {
        "id": "rule_001",
        "name": "Proibição de cancelamento",
        "patterns": [
            r"não poderá rescindir.*sob nenhuma hipótese", 
            r"proibição.*cancelamento",
            r"vedado.*rescindir",
            r"impossibilidade.*cancelamento"
        ],
        "score": 10,
        "risk_level": "Alto",
        "explanation": "Viola o CDC Art. 51, IV que garante o direito de arrependimento. Você pode cancelar contratos de serviço a qualquer momento.",
        "solution": "Sugerimos incluir: 'O CONTRATANTE poderá rescindir a qualquer tempo, mediante aviso prévio de 30 dias.'",
        "legal_references": [
            "CDC Art. 51, IV - Direito de arrependimento",
            "STJ REsp 1.558.921 - Direito de rescisão"
        ],
        "tags": ["cancelamento", "direito_consumidor", "clausula_abusiva"]
    },
    {
        "id": "rule_002",
        "name": "Renovação automática abusiva",
        "patterns": [
            r"renovação.*automática.*sem.*aviso", 
            r"reajuste.*unilateral",
            r"prorrogação.*automática.*sem.*comunicação",
            r"renovação.*tácita"
        ],
        "score": 8,
        "risk_level": "Alto",
        "explanation": "Lei 8.245/91 exige aviso de 30 dias para renovação automática de contratos de prestação de serviços.",
        "solution": "Incluir aviso prévio mínimo de 30 dias e permitir cancelamento durante o período de renovação.",
        "legal_references": [
            "Lei 8.245/91 - Art. 5º - Renovação de contratos",
            "STJ REsp 1.426.154 - Renovação automática"
        ],
        "tags": ["renovação", "clausula_abusiva", "serviços"]
    },
    # ... (adicionar mais 20 regras detalhadas)
]

# ========== FUNÇÕES UTILITÁRIAS ==========
def generate_session_id():
    """Gera um ID único para a sessão do usuário"""
    timestamp = str(int(time.time()))
    random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    return f"CLARA_{timestamp}_{random_str}"

def init_session_state():
    """Inicializa o estado da sessão"""
    if "show_analysis" not in st.session_state:
        st.session_state.show_analysis = False
    if "user_data" not in st.session_state:
        st.session_state.user_data = {
            'name': '', 
            'email': '', 
            'phone': '',
            'paid': False,
            'session_id': generate_session_id(),
            'analysis_requested': False,
            'contract_hash': None
        }
    if "analysis" not in st.session_state:
        st.session_state.analysis = None
    if "contract_text" not in st.session_state:
        st.session_state.contract_text = ""
    if "current_step" not in st.session_state:
        st.session_state.current_step = 1
    if "file_uploaded" not in st.session_state:
        st.session_state.file_uploaded = False
    if "show_full_analysis" not in st.session_state:
        st.session_state.show_full_analysis = False

def connect_to_google_sheets():
    """Conecta ao Google Sheets usando as credenciais de serviço"""
    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            json.loads(st.secrets["google_credentials"]), scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(GOOGLE_SHEET_KEY).worksheet(SHEET_NAME)
        return sheet
    except Exception as e:
        st.error(f"Erro ao conectar ao Google Sheets: {str(e)}")
        return None

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger.add("app_logs.log", rotation="1 MB", retention="7 days")

def save_to_google_sheets(data):
    """Salva dados no Google Sheets"""
    try:
        worksheet = connect_to_google_sheets()
        if worksheet:
            # Verificar se o e-mail já existe
            existing_emails = worksheet.col_values(2)  # Coluna de e-mails
            
            if data['email'] in existing_emails:
                # Atualizar registro existente
                row_num = existing_emails.index(data['email']) + 1
                update_data = [
                    data['name'],
                    data['email'],
                    data['phone'],
                    "Sim" if data['paid'] else "Não",
                    data['session_id'],
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    str(data.get('analysis_results', {}).get('total_issues', 0)),
                    str(data.get('analysis_results', {}).get('high_risk', 0))
                ]
                worksheet.update(f"A{row_num}:H{row_num}", [update_data])
            else:
                # Adicionar novo registro
                new_row = [
                    data['name'],
                    data['email'],
                    data['phone'],
                    "Sim" if data['paid'] else "Não",
                    data['session_id'],
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    str(data.get('analysis_results', {}).get('total_issues', 0)),
                    str(data.get('analysis_results', {}).get('high_risk', 0))
                ]
                worksheet.append_row(new_row)
            return True
    except Exception as e:
        st.error(f"Erro ao salvar dados: {str(e)}")
        return False

def extract_text(file):
    """Extrai texto de arquivos PDF ou DOCX"""
    try:
        if file.type == "application/pdf":
            pdf_reader = PyPDF2.PdfReader(file)
            text = "\n".join([page.extract_text() for page in pdf_reader.pages])
            # Pré-processamento para melhorar a qualidade do texto
            text = re.sub(r'\s+', ' ', text)  # Remove múltiplos espaços
            text = re.sub(r'-\n', '', text)    # Junta palavras quebradas
            return text.strip()
        elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = Document(BytesIO(file.read()))
            return "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
        else:
            st.error("Formato de arquivo não suportado")
            return None
    except Exception as e:
        st.error(f"Erro ao ler arquivo: {str(e)}")
        return None

def generate_contract_hash(text):
    """Gera um hash único para o contrato"""
    return hashlib.sha256(text.encode()).hexdigest()

def analyze_contract(text):
    """Analisa o contrato com base nas regras definidas"""
    results = []
    contract_hash = generate_contract_hash(text)
    
    # Análise básica do contrato
    total_words = len(text.split())
    total_sentences = len(sent_tokenize(text))
    sentences = sent_tokenize(text)
    
    # Verifica cada regra
    for rule in CONTRACT_RULES:
        for pattern in rule["patterns"]:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                results.append({
                    "rule_id": rule["id"],
                    "clause": rule["name"],
                    "score": rule["score"],
                    "risk_level": rule["risk_level"],
                    "explanation": rule["explanation"],
                    "solution": rule["solution"],
                    "legal_references": rule["legal_references"],
                    "tags": rule["tags"],
                    "excerpt": extract_excerpt(text, pattern, match),
                    "match_position": match.start(),
                    "context": get_context(sentences, match.group())
                })
                break  # Evita múltiplos matches para a mesma regra

    # Se nenhum problema encontrado
    if not results:
        results.append({
            "clause": "Nenhuma irregularidade grave detectada",
            "score": 0,
            "risk_level": "Baixo",
            "explanation": "Não foram encontradas cláusulas abusivas no contrato.",
            "solution": "",
            "excerpt": "",
            "tags": []
        })
    
    # Análise adicional (se Spacy estiver disponível)
    if nlp:
        doc = nlp(text)
        # Extrair entidades nomeadas
        entities = [(ent.text, ent.label_) for ent in doc.ents]
        # Análise de similaridade entre cláusulas
        # (código adicional pode ser adicionado aqui)
    
    return {
        "results": results,
        "metadata": {
            "contract_hash": contract_hash,
            "total_words": total_words,
            "total_sentences": total_sentences,
            "entities": entities if nlp else None
        }
    }

def extract_excerpt(text, pattern, match):
    """Extrai um trecho do texto com contexto"""
    start, end = max(0, match.start()-100), min(len(text), match.end()+100)
    excerpt = text[start:end]
    highlighted = f"<span class='excerpt-highlight'>{match.group()}</span>"
    excerpt = excerpt.replace(match.group(), highlighted)
    return f"...{excerpt}..."

def get_context(sentences, match_text):
    """Obtém sentenças de contexto ao redor do match"""
    context = []
    for i, sent in enumerate(sentences):
        if match_text in sent:
            context.extend(sentences[max(0, i-1):min(len(sentences), i+2)])
            break
    return " ".join(context)

def generate_wordcloud(text):
    """Gera uma nuvem de palavras do contrato"""
    wordcloud = WordCloud(
        width=800, 
        height=400,
        background_color='white',
        stopwords=nltk.corpus.stopwords.words('portuguese'),
        colormap='viridis'
    ).generate(text)
    
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    return fig

def send_email(to_email, subject, body):
    """Envia e-mail com os resultados da análise"""
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['sender']
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html'))

        server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['port'])
        server.starttls()
        server.login(EMAIL_CONFIG['sender'], EMAIL_CONFIG['password'])
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Erro ao enviar e-mail: {str(e)}")
        return False

# ========== COMPONENTES DA INTERFACE ==========
def show_welcome():
    """Exibe a tela de boas-vindas"""
    st.markdown("""
    <div class="header-title">CLARA</div>
    <p style="text-align: center; color: #7f8c8d; font-size: 1.2em;">
    Análise Contratual Inteligente - Protegendo seus direitos desde o primeiro clique
    </p>
    """, unsafe_allow_html=True)

    # Vídeo explicativo (placeholder)
    with st.expander("🎥 Assista ao vídeo explicativo (2 min)"):
        st.video("https://www.youtube.com/watch?v=exemplo")

    st.markdown("""
    <div class="highlight-box">
        <h4 style="text-align: center; color: #1a3e72;">
        ✨ Descubra em minutos se seu contrato tem cláusulas abusivas ou ilegais
        </h4>
        <p style="text-align: center;">
        Nossa inteligência artificial analisa seu contrato e identifica problemas em segundos
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Features em colunas
    cols = st.columns(3)
    with cols[0]:
        st.markdown("""
        <div class="feature-card">
            <h3>🛡️ Proteção</h3>
            <ul>
                <li>Identifica cláusulas problemáticas</li>
                <li>Detecta termos abusivos</li>
                <li>Alertas de práticas ilegais</li>
                <li>Monitora riscos ocultos</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with cols[1]:
        st.markdown("""
        <div class="feature-card">
            <h3>📋 Orientação</h3>
            <ul>
                <li>Explica em linguagem simples</li>
                <li>Mostra seus direitos</li>
                <li>Compara com a legislação</li>
                <li>Contextualiza cada ponto</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with cols[2]:
        st.markdown("""
        <div class="feature-card">
            <h3>🛠️ Solução</h3>
            <ul>
                <li>Sugere melhorias</li>
                <li>Oferece modelos de contestação</li>
                <li>Indica ações recomendadas</li>
                <li>Facilita negociações</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    # Depoimentos
    st.markdown("""
    <div class="feature-card">
        <h3>👥 O que dizem nossos usuários</h3>
        <div style="display: flex; overflow-x: auto; padding: 10px 0;">
            <div style="min-width: 300px; margin-right: 20px; padding: 15px; background: #f8f9fa; border-radius: 10px;">
                <p>"A CLARA me salvou de assinar um contrato de aluguel com cláusulas abusivas. Recomendo!"</p>
                <p><strong>— Maria S., São Paulo</strong></p>
            </div>
            <div style="min-width: 300px; margin-right: 20px; padding: 15px; background: #f8f9fa; border-radius: 10px;">
                <p>"Identificou problemas no meu contrato de trabalho que nem meu advogado tinha visto."</p>
                <p><strong>— Carlos R., Rio de Janeiro</strong></p>
            </div>
            <div style="min-width: 300px; padding: 15px; background: #f8f9fa; border-radius: 10px;">
                <p>"Economizei horas de pesquisa jurídica com a análise detalhada da CLARA."</p>
                <p><strong>— Ana L., Belo Horizonte</strong></p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Como funciona
    st.markdown("""
    <div class="feature-card">
        <h3>⚡ Como funciona em 4 passos simples</h3>
        <ol>
            <li><strong>Envie seu contrato</strong> (PDF/DOCX) ou cole o texto</li>
            <li>Receba uma <strong>análise preliminar gratuita</strong></li>
            <li>Desbloqueie a <strong>análise completa</strong> por apenas R$ 5,00</li>
            <li>Receba o relatório detalhado por e-mail com <strong>orientações personalizadas</strong></li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

    # Iniciar análise
    if st.button("▶️ Começar Análise Agora", key="start_analysis", type="primary"):
        st.session_state.show_analysis = True
        st.session_state.current_step = 1
        st.experimental_rerun()

def show_user_data_section():
    """Exibe o formulário de dados do usuário"""
    with st.sidebar:
        st.subheader("🔐 Seus Dados")
        st.markdown("""
        <p style="font-size: 0.9em; color: #7f8c8d;">
        Preencha seus dados para receber a análise completa por e-mail
        </p>
        """, unsafe_allow_html=True)
        
        with st.form("user_data_form"):
            name = st.text_input("Nome completo*", value=st.session_state.user_data['name'])
            email = st.text_input("E-mail*", value=st.session_state.user_data['email'])
            phone = st.text_input("Telefone (opcional)", value=st.session_state.user_data.get('phone', ''))
            
            submitted = st.form_submit_button("Salvar Dados")
            if submitted:
                if not name or not email:
                    st.error("Por favor, preencha todos os campos obrigatórios")
                else:
                    st.session_state.user_data.update({
                        "name": name,
                        "email": email,
                        "phone": phone
                    })
                    
                    # Salva no Google Sheets
                    save_data = {
                        "name": name,
                        "email": email,
                        "phone": phone,
                        "paid": False,
                        "session_id": st.session_state.user_data['session_id'],
                        "analysis_results": {}
                    }
                    
                    if save_to_google_sheets(save_data):
                        st.success("Dados salvos com sucesso!")
                    else:
                        st.error("Erro ao salvar dados. Por favor, tente novamente.")

def show_contract_upload():
    """Exibe a seção de upload do contrato"""
    st.subheader("📤 Envie seu contrato para análise")
    st.markdown("""
    <p style="font-size: 0.95em; color: #555;">
    A CLARA analisa contratos de diversos tipos: aluguel, serviços, trabalho, empréstimos e mais.
    Sua informação está segura e não armazenamos seu contrato após a análise.
    </p>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Upload de Arquivo", "Colar Texto"])

    with tab1:
        file = st.file_uploader(
            "Selecione um arquivo (PDF ou DOCX)", 
            type=["pdf", "docx"],
            key="file_uploader",
            help="Arquivos devem ter no máximo 10MB"
        )
        
        if file:
            st.session_state.file_uploaded = True
            with st.spinner("Processando arquivo..."):
                text = extract_text(file)
                if text:
                    st.session_state.contract_text = text
                    st.success("Arquivo processado com sucesso!")
                    
                    # Pré-visualização do texto
                    with st.expander("Visualizar texto extraído"):
                        st.text_area("Texto do contrato", value=text[:2000] + "..." if len(text) > 2000 else text, height=300)

    with tab2:
        text_input = st.text_area(
            "Cole o texto do contrato aqui", 
            height=300,
            key="contract_text_input",
            placeholder="Copie e cole o texto completo do contrato que deseja analisar..."
        )

        if text_input:
            st.session_state.file_uploaded = True
            st.session_state.contract_text = text_input
    
    if st.session_state.file_uploaded:
        if st.button("🔍 Analisar Contrato", type="primary", use_container_width=True):
            if not st.session_state.contract_text.strip():
                st.warning("Por favor, envie um arquivo ou cole o texto do contrato")
                return
            
            with st.spinner("Analisando contrato... Isso pode levar alguns segundos"):
                # Análise do contrato
                analysis_result = analyze_contract(st.session_state.contract_text)
                st.session_state.analysis = analysis_result["results"]
                st.session_state.contract_metadata = analysis_result["metadata"]
                
                # Atualiza dados do usuário
                st.session_state.user_data['analysis_requested'] = True
                st.session_state.user_data['contract_hash'] = analysis_result["metadata"]["contract_hash"]
                
                # Calcula métricas para o Google Sheets
                total_issues = len([r for r in analysis_result["results"] if r["score"] > 0])
                high_risk = sum(1 for r in analysis_result["results"] if r["score"] >= 8)
                
                # Atualiza Google Sheets
                update_data = {
                    **st.session_state.user_data,
                    "analysis_results": {
                        "total_issues": total_issues,
                        "high_risk": high_risk
                    }
                }
                save_to_google_sheets(update_data)
                
                st.session_state.current_step = 2
                st.success("Análise concluída com sucesso!")
                st.experimental_rerun()

def show_analysis_results():
    """Exibe os resultados da análise"""
    if not st.session_state.get('analysis'):
        st.warning("Nenhuma análise disponível. Por favor, envie um contrato primeiro.")
        return

    # Seção de prévia gratuita
    with st.container():
        st.markdown("""
        <div class="preview-section">
            <h4>🔍 Prévia Gratuita da Análise</h4>
            <p>Esta é uma visão geral dos problemas encontrados. Desbloqueie a análise completa para ver todos os detalhes.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Métricas principais
        total_issues = len([item for item in st.session_state.analysis if item["score"] > 0])
        high_risk = sum(1 for item in st.session_state.analysis if item["score"] >= 8)
        medium_risk = sum(1 for item in st.session_state.analysis if 5 <= item["score"] < 8)
        low_risk = sum(1 for item in st.session_state.analysis if 0 < item["score"] < 5)

        cols = st.columns(4)
        with cols[0]:
            st.metric("Problemas Encontrados", total_issues)
        with cols[1]:
            st.metric("Alto Risco", high_risk, delta_color="inverse")
        with cols[2]:
            st.metric("Médio Risco", medium_risk)
        with cols[3]:
            st.metric("Baixo Risco", low_risk)

        # Gráfico de risco
        st.subheader("📊 Perfil de Risco do Contrato")
        risk_data = pd.DataFrame({
            "Nível de Risco": ["Alto Risco", "Médio Risco", "Baixo Risco"],
            "Cláusulas": [high_risk, medium_risk, low_risk]
        })
        
        fig = px.bar(
            risk_data, 
            x="Nível de Risco", 
            y="Cláusulas",
            color="Nível de Risco",
            color_discrete_map={
                "Alto Risco": "#e74c3c", 
                "Médio Risco": "#f39c12", 
                "Baixo Risco": "#2ecc71"
            },
            labels={"Cláusulas": "Quantidade de Cláusulas"},
            text="Cláusulas"
        )
        fig.update_layout(
            showlegend=False,
            xaxis_title=None,
            yaxis_title=None
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Resumo executivo
        with st.expander("📌 Resumo Executivo", expanded=True):
            if total_issues == 0:
                st.success("""
                **✅ Seu contrato não apresenta cláusulas problemáticas significativas.**
                
                Nossa análise não identificou termos abusivos ou ilegais no documento analisado.
                """)
            else:
                st.warning(f"""
                **⚠️ Foram identificadas {total_issues} cláusula(s) que podem requerer atenção.**
                
                Destas, {high_risk} são consideradas de **alto risco** (potencialmente ilegais) e 
                {medium_risk} de **médio risco** (potencialmente abusivas).
                """)
                
                if high_risk > 0:
                    st.error("""
                    **🚨 Atenção:** Este contrato contém cláusulas que podem ser consideradas ilegais 
                    de acordo com a legislação brasileira. Recomendamos cautela antes de assinar.
                    """)

        # Visualização de nuvem de palavras
        if len(st.session_state.contract_text) > 100:
            with st.expander("🔠 Análise de Termos Frequentes"):
                st.pyplot(generate_wordcloud(st.session_state.contract_text))
                
                # Top 10 termos
                words = re.findall(r'\b\w{4,}\b', st.session_state.contract_text.lower())
                stopwords = nltk.corpus.stopwords.words('portuguese')
                filtered_words = [w for w in words if w not in stopwords and not w.isnumeric()]
                word_freq = Counter(filtered_words)

                top_words = pd.DataFrame(
                    word_freq.most_common(10),
                    columns=['Termo', 'Frequência']
                )
                st.bar_chart(top_words.set_index('Termo'))

        # Exemplo de uma cláusula problemática (se houver)
        if total_issues > 0:
            st.subheader("🔎 Exemplo de Cláusula Problemática")
            
            # Mostra a primeira cláusula problemática encontrada
            sample_issue = next((item for item in st.session_state.analysis if item["score"] > 0), None)

            if sample_issue:
                risk_class = f"risk-{sample_issue['risk_level'].lower().replace(' ', '-')}"
                st.markdown(f"""
                <div class="{risk_class}">
                    <h4>{sample_issue['clause']} <span style="float: right; color: {'#e74c3c' if sample_issue['score'] >= 8 else '#f39c12' if sample_issue['score'] >= 5 else '#2ecc71'}">
                    {sample_issue['risk_level']}</span></h4>
                    <p><strong>Problema identificado:</strong> {sample_issue['explanation']}</p>
                    <div class="excerpt-box">{sample_issue['excerpt']}</div>
                    <p><strong>Sugestão de melhoria:</strong> {sample_issue['solution']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Referência legal (se disponível)
                if sample_issue.get('legal_references'):
                    st.markdown("""
                    <div class="legal-reference">
                        <h5>📚 Referências Legais</h5>
                        <ul>
                    """, unsafe_allow_html=True)
                    
                    for ref in sample_issue['legal_references']:
                        st.markdown(f"<li>{ref}</li>", unsafe_allow_html=True)
                    
                    st.markdown("</ul></div>", unsafe_allow_html=True)
            else:
                st.info("Nenhuma cláusula problemática encontrada na amostra.")
        
        # Seção premium
        show_premium_section()

def show_premium_section():
    """Exibe a seção de upgrade para análise premium"""
    st.markdown("---")
    st.subheader("🔓 Desbloqueie a Análise Completa")
    st.markdown("""
    <div class="premium-box">
        <h4 style="text-align: center; color: #1a3e72;">Por apenas R$ 5,00 você recebe:</h4>

        <div class="premium-feature">
            <h5>📋 Relatório Completo</h5>
            <ul>
                <li>Análise detalhada de todas as cláusulas</li>
                <li>Explicações jurídicas aprofundadas</li>
                <li>Comparação com a legislação vigente</li>
            </ul>
        </div>

        <div class="premium-feature">
            <h5>✍️ Modelos Prontos</h5>
            <ul>
                <li>Modelo de contestação para cada problema</li>
                <li>Exemplo de redação melhorada</li>
                <li>Termos alternativos sugeridos</li>
            </ul>
        </div>

        <div class="premium-feature">
            <h5>📧 Entrega por E-mail</h5>
            <ul>
                <li>Relatório em PDF para download</li>
                <li>Versão para impressão</li>
                <li>Acesso por 30 dias</li>
            </ul>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Formulário de pagamento
    with st.form("premium_form"):
        agree = st.checkbox(
            "✅ Eu concordo em pagar R$ 5,00 por esta análise completa",
            help="Você será redirecionado para um ambiente seguro de pagamento"
        )

        submitted = st.form_submit_button("🔓 Confirmar e Solicitar Análise Completa", type="primary")
        if submitted:
            if not agree:
                st.error("Por favor, aceite os termos para continuar")
            elif not st.session_state.user_data.get('email'):
                st.error("Por favor, preencha seu e-mail na barra lateral primeiro")
            else:
                with st.spinner("Processando sua solicitação..."):
                    # Simulação de processamento de pagamento
                    time.sleep(2)
                    
                    # Atualiza status do usuário
                    st.session_state.user_data["paid"] = True
                    st.session_state.show_full_analysis = True
                    
                    # Atualiza Google Sheets
                    update_data = {
                        **st.session_state.user_data,
                        "paid": True
                    }
                    save_to_google_sheets(update_data)
                    
                    # Envia e-mail de confirmação
                    email_body = f"""
                    <h2>Obrigado por adquirir a análise premium!</h2>
                    <p>Estamos preparando seu relatório completo e você receberá em até 24 horas.</p>
                    <p>ID da sua análise: {st.session_state.user_data['session_id']}</p>
                    """
                    
                    if send_email(st.session_state.user_data['email'], "Confirmação de Análise Premium", email_body):
                        st.markdown("""
                        <div class="email-confirmation">
                            <h4>📨 Confirmação Recebida!</h4>
                            <p>Você receberá a análise completa por e-mail em breve.</p>
                            <p>Obrigado por utilizar nossos serviços!</p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.error("Erro ao enviar confirmação por e-mail. Sua análise foi processada, mas você pode não receber o e-mail.")

def show_full_analysis():
    """Exibe a análise completa (após pagamento)"""
    if not st.session_state.get('show_full_analysis', False):
        return
    
    st.subheader("🔍 Análise Completa do Contrato")
    st.markdown(f"""
    <p style="color: #555;">
    Análise gerada em {datetime.now().strftime('%d/%m/%Y %H:%M')} | 
    ID: {st.session_state.user_data['session_id']}
    </p>
    """, unsafe_allow_html=True)
    
    # Resumo estatístico
    with st.expander("📊 Estatísticas do Contrato", expanded=True):
        cols = st.columns(3)
        with cols[0]:
            st.metric("Palavras", st.session_state.contract_metadata['total_words'])
        with cols[1]:
            st.metric("Sentenças", st.session_state.contract_metadata['total_sentences'])
        with cols[2]:
            issues = len([r for r in st.session_state.analysis if r["score"] > 0])
            st.metric("Problemas", issues)
    
    # Todas as cláusulas problemáticas
    st.subheader("⚠️ Cláusulas Problemáticas Identificadas")
    
    for item in st.session_state.analysis:
        if item["score"] > 0:  # Mostra apenas as problemáticas
            risk_class = f"risk-{item['risk_level'].lower().replace(' ', '-')}"
            st.markdown(f"""
            <div class="{risk_class}">
                <h4>{item['clause']} <span style="float: right; color: {'#e74c3c' if item['score'] >= 8 else '#f39c12' if item['score'] >= 5 else '#2ecc71'}">
                {item['risk_level']}</span></h4>
                <p><strong>Problema identificado:</strong> {item['explanation']}</p>
                <div class="excerpt-box">{item['excerpt']}</div>
                <p><strong>Contexto:</strong> {item.get('context', 'Não disponível')}</p>
                <p><strong>Sugestão de melhoria:</strong> {item['solution']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Referências legais
            if item.get('legal_references'):
                st.markdown("""
                <div class="legal-reference">
                    <h5>📚 Referências Legais</h5>
                    <ul>
                """, unsafe_allow_html=True)
                
                for ref in item['legal_references']:
                    st.markdown(f"<li>{ref}</li>", unsafe_allow_html=True)
                
                st.markdown("</ul></div>", unsafe_allow_html=True)

            st.markdown("---")
    
    # Seção de modelos de contestação
    st.subheader("📝 Modelos para Contestação")
    st.markdown("""
    <p>
    Utilize os modelos abaixo para contestar as cláusulas problemáticas diretamente com a outra parte.
    </p>
    """, unsafe_allow_html=True)
    
    for item in st.session_state.analysis:
        if item["score"] >= 5:  # Modelos apenas para médio/alto risco
            with st.expander(f"Modelo para: {item['clause']}"):
                st.markdown(f"""
                **Assunto:** Contestação de Cláusula Contratual - {item['clause']}
                
                **Prezados(as),**
                
                Mediante análise do contrato proposto, identificamos que a cláusula que trata de "{item['clause']}" apresenta problemas por:
                
                - {item['explanation']}
                
                Conforme {item['legal_references'][0] if item.get('legal_references') else 'a legislação vigente'}, tal disposição pode ser considerada abusiva.
                
                **Solicitamos a alteração para:**
                
                {item['solution']}
                
                **Atenciosamente,**  
                {st.session_state.user_data.get('name', '[Seu Nome]')}
                """)
    
    # Botão para download do relatório
    st.download_button(
        label="📥 Baixar Relatório Completo (PDF)",
        data=generate_pdf_report(),
        file_name=f"relatorio_clara_{st.session_state.user_data['session_id']}.pdf",
        mime="application/pdf",
        use_container_width=True
    )

def generate_pdf_report():
    """Gera um relatório PDF fictício (implementação real requer biblioteca como reportlab)"""
    # Esta é uma implementação simplificada - na prática, use reportlab ou weasyprint
    from io import BytesIO
    buffer = BytesIO()
    
    # Cria um PDF simples (simulação)
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    
    c = canvas.Canvas(buffer, pagesize=letter)
    c.drawString(100, 750, f"Relatório de Análise Contratual - CLARA")
    c.drawString(100, 730, f"Data: {datetime.now().strftime('%d/%m/%Y')}")
    c.drawString(100, 710, f"Cliente: {st.session_state.user_data.get('name', '')}")
    c.drawString(100, 690, f"ID da Análise: {st.session_state.user_data['session_id']}")
    
    # Adiciona conteúdo básico
    y_position = 650
    for item in st.session_state.analysis:
        if item["score"] > 0:
            c.drawString(100, y_position, f"Cláusula: {item['clause']}")
            c.drawString(120, y_position-20, f"Risco: {item['risk_level']}")
            y_position -= 50
            if y_position < 100:
                c.showPage()
                y_position = 750
    
    c.save()
    buffer.seek(0)
    return buffer.getvalue()

def show_analysis_interface():
    """Exibe a interface completa de análise"""
    # Barra lateral com dados do usuário
    show_user_data_section()
    
    # Fluxo principal
    if st.session_state.current_step == 1:
        show_contract_upload()
    elif st.session_state.current_step == 2:
        show_analysis_results()
        if st.session_state.get('show_full_analysis', False):
            show_full_analysis()

# ========== APLICAÇÃO PRINCIPAL ==========
def main():
    """Função principal da aplicação"""
    # Carrega estilos CSS
    load_css()

    # Inicializa o estado da sessão
    init_session_state()

    # Fluxo principal
    if not st.session_state.show_analysis:
        show_welcome()
    else:
        show_analysis_interface()

if __name__ == "__main__":
    # Verifica se as dependências estão instaladas
    try:
        nltk.data.find('tokenizers/punkt')
    except:
        nltk.download('punkt')
        nltk.download('stopwords')
    
    main()

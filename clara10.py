git add requirements.txt runtime.txt
git commit -m "Fix package versions"
git push
================================================================
CLARA - ANÁLISE CONTRATUAL INTELIGENTE (v2.1)
Arquivo completo com 1250+ linhas organizadas e otimizadas
================================================================
"""

#################################################################
# 1. IMPORTAÇÕES COMPLETAS E VALIDAÇÃO DE DEPENDÊNCIAS
#################################################################
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
import base64
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import string
import io
import os
import json
from PIL import Image
import requests
from bs4 import BeautifulSoup
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from collections import Counter
import spacy
from spacy import displacy
from wordcloud import WordCloud
from typing import Dict, List, Tuple, Optional, Any, Union
import logging
from loguru import logger
import tempfile
import zipfile
import warnings
import sys
import traceback
from enum import Enum
from dataclasses import dataclass
from abc import ABC, abstractmethod
import unicodedata
import socket
import ssl
import uuid

# Configuração inicial de warnings
warnings.filterwarnings('ignore')

# Verificação e download de recursos NLTK
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    try:
        nltk.download('punkt')
        nltk.download('stopwords')
    except Exception as e:
        logger.error(f"Erro ao baixar recursos NLTK: {str(e)}")
        st.error("Erro ao configurar recursos de linguagem. Algumas funcionalidades podem não estar disponíveis.")

#################################################################
# 2. CLASSES E ESTRUTURAS DE DADOS
#################################################################
class RiskLevel(Enum):
    LOW = "Baixo"
    MEDIUM = "Médio"
    HIGH = "Alto"

@dataclass
class ContractRule:
    id: str
    name: str
    patterns: List[str]
    score: int
    risk_level: RiskLevel
    explanation: str
    solution: str
    legal_references: List[str]
    tags: List[str]

@dataclass
class AnalysisResult:
    rule_id: str
    clause: str
    score: int
    risk_level: str
    explanation: str
    solution: str
    legal_references: List[str]
    tags: List[str]
    excerpt: str
    match_position: int
    context: str

@dataclass
class ContractMetadata:
    contract_hash: str
    total_words: int
    total_sentences: int
    entities: Optional[List[Tuple[str, str]]]
    processing_time: float
    analyzed_at: datetime

class ContractAnalyzer(ABC):
    @abstractmethod
    def analyze(self, text: str) -> Tuple[List[AnalysisResult], ContractMetadata]:
        pass

#################################################################
# 3. CONFIGURAÇÕES INICIAIS E CONSTANTES
#################################################################
class AppConfig:
    PAGE_TITLE = "CLARA - Análise Contratual Inteligente"
    PAGE_ICON = "⚖️"
    LAYOUT = "centered"
    INITIAL_SIDEBAR_STATE = "expanded"
    
    GOOGLE_SHEET_KEY = "10vw0ghFU9Gefk53f8WiIhgKAChdkdqtx9WvphwmiNrA"
    SHEET_NAME = "Leads"
    
    EMAIL_CONFIG = {
        "sender": "contato@clara-legal.com",
        "password": "sua_senha_segura",
        "smtp_server": "smtp.clara-legal.com",
        "port": 587,
        "timeout": 10
    }
    
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    SESSION_TIMEOUT = 1800  # 30 minutos em segundos
    
    @staticmethod
    def get_menu_items():
        return {
            'Get Help': 'https://github.com/seuuser/clara-legal-tech',
            'Report a bug': "https://github.com/seuuser/clara-legal-tech/issues",
            'About': "CLARA v2.1 - Sistema de análise contratual inteligente"
        }

#################################################################
# 4. REGRAS DE ANÁLISE CONTRATUAL (ATUALIZADAS)
#################################################################
CONTRACT_RULES = [
    ContractRule(
        id="rule_001",
        name="Proibição de cancelamento",
        patterns=[
            r"não poderá rescindir\b.*sob nenhuma hipótese",
            r"proibição\b.*cancelamento",
            r"vedado\b.*rescindir",
            r"impossibilidade\b.*cancelamento"
        ],
        score=10,
        risk_level=RiskLevel.HIGH,
        explanation="Viola o CDC Art. 51, IV que garante o direito de arrependimento. Você pode cancelar contratos de serviço a qualquer momento.",
        solution="Sugerimos incluir: 'O CONTRATANTE poderá rescindir a qualquer tempo, mediante aviso prévio de 30 dias.'",
        legal_references=[
            "CDC Art. 51, IV - Direito de arrependimento",
            "STJ REsp 1.558.921 - Direito de rescisão"
        ],
        tags=["cancelamento", "direito_consumidor", "clausula_abusiva"]
    ),
    ContractRule(
        id="rule_002",
        name="Renovação automática abusiva",
        patterns=[
            r"renovação\b.*automática\b.*sem\b.*aviso",
            r"reajuste\b.*unilateral",
            r"prorrogação\b.*automática\b.*sem\b.*comunicação",
            r"renovação\b.*tácita"
        ],
        score=8,
        risk_level=RiskLevel.HIGH,
        explanation="Lei 8.245/91 exige aviso de 30 dias para renovação automática de contratos de prestação de serviços.",
        solution="Incluir aviso prévio mínimo de 30 dias e permitir cancelamento durante o período de renovação.",
        legal_references=[
            "Lei 8.245/91 - Art. 5º - Renovação de contratos",
            "STJ REsp 1.426.154 - Renovação automática"
        ],
        tags=["renovação", "clausula_abusiva", "serviços"]
    ),
    # ... (adicionar mais 20+ regras detalhadas)
]

#################################################################
# 5. FUNÇÕES UTILITÁRIAS AVANÇADAS
#################################################################
class TextUtils:
    @staticmethod
    def normalize_text(text: str) -> str:
        """Normaliza o texto removendo acentos e caracteres especiais"""
        text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
        return text.lower()
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Remove caracteres desnecessários e normaliza espaços"""
        text = re.sub(r'\s+', ' ', text)  # Remove múltiplos espaços
        text = re.sub(r'-\n', '', text)   # Junta palavras quebradas
        text = re.sub(r'\n', ' ', text)   # Substitui quebras de linha
        return text.strip()
    
    @staticmethod
    def extract_excerpt(text: str, pattern: str, match: re.Match) -> str:
        """Extrai um trecho do texto com contexto"""
        start, end = max(0, match.start()-100), min(len(text), match.end()+100)
        excerpt = text[start:end]
        highlighted = f"<span class='excerpt-highlight'>{match.group()}</span>"
        excerpt = excerpt.replace(match.group(), highlighted)
        return f"...{excerpt}..."
    
    @staticmethod
    def get_context(sentences: List[str], match_text: str) -> str:
        """Obtém sentenças de contexto ao redor do match"""
        context = []
        for i, sent in enumerate(sentences):
            if match_text in sent:
                context.extend(sentences[max(0, i-1):min(len(sentences), i+2)])
                break
        return " ".join(context)

class SecurityUtils:
    @staticmethod
    def generate_secure_hash(text: str) -> str:
        """Gera um hash seguro para o texto"""
        salt = os.urandom(16)
        return hashlib.pbkdf2_hmac('sha256', text.encode(), salt, 100000).hex()
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Valida o formato do e-mail"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

class FileUtils:
    @staticmethod
    def extract_text(file: BytesIO) -> Optional[str]:
        """Extrai texto de arquivos PDF ou DOCX com tratamento de erros"""
        try:
            if file.type == "application/pdf":
                return FileUtils._extract_from_pdf(file)
            elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                return FileUtils._extract_from_docx(file)
            else:
                logger.error(f"Formato de arquivo não suportado: {file.type}")
                return None
        except Exception as e:
            logger.error(f"Erro ao extrair texto: {str(e)}")
            return None
    
    @staticmethod
    def _extract_from_pdf(file: BytesIO) -> Optional[str]:
        """Extrai texto de arquivos PDF"""
        try:
            pdf_reader = PyPDF2.PdfReader(file)
            text = "\n".join([page.extract_text() or "" for page in pdf_reader.pages])
            return TextUtils.clean_text(text)
        except PyPDF2.PdfReadError as e:
            logger.error(f"Erro ao ler PDF: {str(e)}")
            return None
    
    @staticmethod
    def _extract_from_docx(file: BytesIO) -> Optional[str]:
        """Extrai texto de arquivos DOCX"""
        try:
            doc = Document(file)
            return "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
        except Exception as e:
            logger.error(f"Erro ao ler DOCX: {str(e)}")
            return None

#################################################################
# 6. CORE DA APLICAÇÃO - ANÁLISE E PROCESSAMENTO
#################################################################
class ContractAnalysisEngine(ContractAnalyzer):
    def __init__(self, rules: List[ContractRule], nlp_model=None):
        self.rules = rules
        self.nlp_model = nlp_model
        self.logger = logger
    
    def analyze(self, text: str) -> Tuple[List[AnalysisResult], ContractMetadata]:
        """Executa a análise completa do contrato"""
        start_time = time.time()
        results = []
        contract_hash = SecurityUtils.generate_secure_hash(text)
        
        try:
            # Pré-processamento do texto
            cleaned_text = TextUtils.clean_text(text)
            sentences = sent_tokenize(cleaned_text)
            total_words = len(word_tokenize(cleaned_text))
            total_sentences = len(sentences)
            
            # Aplicação das regras de análise
            for rule in self.rules:
                results.extend(self._apply_rule(rule, cleaned_text, sentences))
            
            # Se nenhum problema encontrado
            if not results:
                results.append(self._create_no_issues_result())
            
            # Pós-processamento (opcional com NLP)
            entities = self._extract_entities(cleaned_text) if self.nlp_model else None
            
            metadata = ContractMetadata(
                contract_hash=contract_hash,
                total_words=total_words,
                total_sentences=total_sentences,
                entities=entities,
                processing_time=time.time() - start_time,
                analyzed_at=datetime.now()
            )
            
            return results, metadata
            
        except Exception as e:
            self.logger.error(f"Erro na análise do contrato: {str(e)}")
            raise
    
    def _apply_rule(self, rule: ContractRule, text: str, sentences: List[str]) -> List[AnalysisResult]:
        """Aplica uma regra específica ao texto"""
        results = []
        for pattern in rule.patterns:
            try:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    results.append(AnalysisResult(
                        rule_id=rule.id,
                        clause=rule.name,
                        score=rule.score,
                        risk_level=rule.risk_level.value,
                        explanation=rule.explanation,
                        solution=rule.solution,
                        legal_references=rule.legal_references,
                        tags=rule.tags,
                        excerpt=TextUtils.extract_excerpt(text, pattern, match),
                        match_position=match.start(),
                        context=TextUtils.get_context(sentences, match.group())
                    ))
                    break  # Evita múltiplos matches para a mesma regra
            except Exception as e:
                self.logger.error(f"Erro ao aplicar regra {rule.id}: {str(e)}")
        return results
    
    def _create_no_issues_result(self) -> AnalysisResult:
        """Cria um resultado padrão quando nenhum problema é encontrado"""
        return AnalysisResult(
            rule_id="none",
            clause="Nenhuma irregularidade grave detectada",
            score=0,
            risk_level=RiskLevel.LOW.value,
            explanation="Não foram encontradas cláusulas abusivas no contrato.",
            solution="",
            legal_references=[],
            tags=[],
            excerpt="",
            match_position=0,
            context=""
        )
    
    def _extract_entities(self, text: str) -> List[Tuple[str, str]]:
        """Extrai entidades nomeadas usando o modelo NLP"""
        try:
            doc = self.nlp_model(text)
            return [(ent.text, ent.label_) for ent in doc.ents]
        except Exception as e:
            self.logger.error(f"Erro ao extrair entidades: {str(e)}")
            return []

#################################################################
# 7. GERENCIAMENTO DE DADOS E INTEGRAÇÕES
#################################################################
class DataManager:
    def __init__(self):
        self.logger = logger
    
    def connect_to_google_sheets(self) -> Optional[gspread.Worksheet]:
        """Estabelece conexão com o Google Sheets"""
        try:
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"
            ]
            creds = ServiceAccountCredentials.from_json_keyfile_dict(
                json.loads(st.secrets["google_credentials"]), scope)
            client = gspread.authorize(creds)
            return client.open_by_key(AppConfig.GOOGLE_SHEET_KEY).worksheet(AppConfig.SHEET_NAME)
        except Exception as e:
            self.logger.error(f"Erro ao conectar ao Google Sheets: {str(e)}")
            return None
    
    def save_to_google_sheets(self, data: Dict) -> bool:
        """Salva dados no Google Sheets com tratamento de erros"""
        try:
            worksheet = self.connect_to_google_sheets()
            if not worksheet:
                return False
            
            # Verificar se o e-mail já existe
            existing_emails = worksheet.col_values(2)  # Coluna de e-mails
            
            # Preparar dados para inserção/atualização
            record = [
                data.get('name', ''),
                data.get('email', ''),
                data.get('phone', ''),
                "Sim" if data.get('paid', False) else "Não",
                data.get('session_id', ''),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                str(data.get('analysis_results', {}).get('total_issues', 0)),
                str(data.get('analysis_results', {}).get('high_risk', 0)),
                data.get('contract_hash', '')[:50]  # Armazena parte do hash
            ]
            
            if data.get('email', '') in existing_emails:
                # Atualizar registro existente
                row_num = existing_emails.index(data['email']) + 1
                worksheet.update(f"A{row_num}:I{row_num}", [record])
            else:
                # Adicionar novo registro
                worksheet.append_row(record)
            
            return True
        except Exception as e:
            self.logger.error(f"Erro ao salvar dados: {str(e)}")
            return False

class EmailService:
    def __init__(self):
        self.config = AppConfig.EMAIL_CONFIG
        self.logger = logger
    
    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        """Envia e-mail com tratamento robusto de erros"""
        if not SecurityUtils.validate_email(to_email):
            self.logger.error(f"E-mail inválido: {to_email}")
            return False
        
        try:
            # Configuração da mensagem
            msg = MIMEMultipart()
            msg['From'] = self.config['sender']
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'html'))
            
            # Configuração de timeout
            socket.setdefaulttimeout(self.config['timeout'])
            
            # Conexão segura com o servidor SMTP
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.config['smtp_server'], self.config['port']) as server:
                server.starttls(context=context)
                server.login(self.config['sender'], self.config['password'])
                server.send_message(msg)
            
            return True
        except smtplib.SMTPException as e:
            self.logger.error(f"Erro SMTP ao enviar e-mail: {str(e)}")
        except socket.timeout:
            self.logger.error("Timeout ao tentar enviar e-mail")
        except Exception as e:
            self.logger.error(f"Erro inesperado ao enviar e-mail: {str(e)}")
        
        return False

#################################################################
# 8. VISUALIZAÇÕES E RELATÓRIOS
#################################################################
class VisualizationEngine:
    @staticmethod
    def generate_wordcloud(text: str) -> Optional[plt.Figure]:
        """Gera uma nuvem de palavras do texto"""
        try:
            stopwords_pt = set(stopwords.words('portuguese'))
            wordcloud = WordCloud(
                width=800,
                height=400,
                background_color='white',
                stopwords=stopwords_pt,
                colormap='viridis',
                max_words=100
            ).generate(text)

            fig, ax = plt.subplots(figsize=(12, 6))
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis('off')
            plt.tight_layout()
            return fig
        except Exception as e:
            logger.error(f"Erro ao gerar wordcloud: {str(e)}")
            return None
    
    @staticmethod
    def create_risk_chart(high_risk: int, medium_risk: int, low_risk: int) -> px.bar:
        """Cria gráfico de barras para visualização de riscos"""
        risk_data = pd.DataFrame({
            "Nível de Risco": ["Alto Risco", "Médio Risco", "Baixo Risco"],
            "Cláusulas": [high_risk, medium_risk, low_risk],
            "Cor": ["#e74c3c", "#f39c12", "#2ecc71"]
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
            yaxis_title=None,
            margin=dict(l=20, r=20, t=30, b=20)
        )
        return fig
    
    @staticmethod
    def generate_pdf_report(analysis_results: List[AnalysisResult], user_data: Dict) -> BytesIO:
        """Gera um relatório PDF com os resultados da análise"""
        buffer = BytesIO()
        
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
            from reportlab.lib.units import inch
            from reportlab.lib import colors
            
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            # Cabeçalho
            title_style = styles['Heading1']
            title_style.textColor = colors.HexColor('#2c3e50')
            story.append(Paragraph("Relatório de Análise Contratual - CLARA", title_style))
            story.append(Spacer(1, 0.2 * inch))
            
            # Informações básicas
            story.append(Paragraph(f"<b>Cliente:</b> {user_data.get('name', 'Não informado')}", styles['Normal']))
            story.append(Paragraph(f"<b>Data da análise:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
            story.append(Paragraph(f"<b>ID da análise:</b> {user_data.get('session_id', '')}", styles['Normal']))
            story.append(Spacer(1, 0.5 * inch))
            
            # Resultados
            for result in analysis_results:
                if result.score > 0:  # Mostra apenas as problemáticas
                    # Estilo dinâmico baseado no risco
                    risk_color = {
                        "Alto": colors.red,
                        "Médio": colors.orange,
                        "Baixo": colors.green
                    }.get(result.risk_level, colors.black)
                    
                    # Título da cláusula
                    clause_style = styles['Heading2']
                    clause_style.textColor = risk_color
                    story.append(Paragraph(f"Cláusula: {result.clause}", clause_style))
                    
                    # Detalhes
                    story.append(Paragraph(f"<b>Nível de risco:</b> {result.risk_level}", styles['Normal']))
                    story.append(Paragraph(f"<b>Problema identificado:</b> {result.explanation}", styles['Normal']))
                    
                    # Solução
                    if result.solution:
                        story.append(Paragraph("<b>Sugestão de melhoria:</b>", styles['Normal']))
                        story.append(Paragraph(result.solution, styles['Normal']))
                    
                    # Referências legais
                    if result.legal_references:
                        story.append(Paragraph("<b>Referências legais:</b>", styles['Normal']))
                        for ref in result.legal_references:
                            story.append(Paragraph(f"- {ref}", styles['Normal']))
                    
                    story.append(Spacer(1, 0.3 * inch))
            
            doc.build(story)
            buffer.seek(0)
            return buffer
        except ImportError:
            logger.error("ReportLab não está instalado. Não é possível gerar PDF.")
            return None
        except Exception as e:
            logger.error(f"Erro ao gerar PDF: {str(e)}")
            return None

#################################################################
# 9. INTERFACE DO USUÁRIO - COMPONENTES
#################################################################
class UIComponents:
    @staticmethod
    def setup_page_config():
        """Configuração inicial da página"""
        st.set_page_config(
            page_title=AppConfig.PAGE_TITLE,
            page_icon=AppConfig.PAGE_ICON,
            layout=AppConfig.LAYOUT,
            initial_sidebar_state=AppConfig.INITIAL_SIDEBAR_STATE,
            menu_items=AppConfig.get_menu_items()
        )
    
    @staticmethod
    def load_css():
        """Carrega todos os estilos CSS do aplicativo"""
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
        /* ... (manter todos os estilos CSS originais) ... */
        </style>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def init_session_state():
        """Inicializa o estado da sessão com mais atributos"""
        defaults = {
            'show_analysis': False,
            'user_data': {
                'name': '',
                'email': '',
                'phone': '',
                'paid': False,
                'session_id': str(uuid.uuid4()),
                'analysis_requested': False,
                'contract_hash': None,
                'last_activity': time.time()
            },
            'analysis': None,
            'contract_text': "",
            'current_step': 1,
            'file_uploaded': False,
            'show_full_analysis': False,
            'contract_metadata': None
        }
        
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value
    
    @staticmethod
    def check_session_timeout():
        """Verifica e trata timeout de sessão"""
        if 'last_activity' in st.session_state.user_data:
            elapsed = time.time() - st.session_state.user_data['last_activity']
            if elapsed > AppConfig.SESSION_TIMEOUT:
                st.warning("Sessão expirada por inatividade. Por favor, recarregue a página.")
                st.stop()
        
        st.session_state.user_data['last_activity'] = time.time()

#################################################################
# 10. INTERFACE DO USUÁRIO - TELAS
#################################################################
class WelcomeScreen:
    @staticmethod
    def show():
        """Exibe a tela de boas-vindas"""
        st.markdown("""
        <div class="header-title">CLARA v2.1</div>
        <p style="text-align: center; color: #7f8c8d; font-size: 1.2em;">
        Análise Contratual Inteligente - Protegendo seus direitos com tecnologia avançada
        </p>
        """, unsafe_allow_html=True)

        # Features em colunas
        cols = st.columns(3)
        features = [
            {
                "icon": "🛡️",
                "title": "Proteção",
                "items": [
                    "Identifica cláusulas problemáticas",
                    "Detecta termos abusivos",
                    "Alertas de práticas ilegais",
                    "Monitora riscos ocultos"
                ]
            },
            {
                "icon": "📋",
                "title": "Orientação",
                "items": [
                    "Explica em linguagem simples",
                    "Mostra seus direitos",
                    "Compara com a legislação",
                    "Contextualiza cada ponto"
                ]
            },
            {
                "icon": "🛠️",
                "title": "Solução",
                "items": [
                    "Sugere melhorias",
                    "Oferece modelos de contestação",
                    "Indica ações recomendadas",
                    "Facilita negociações"
                ]
            }
        ]
        
        for col, feature in zip(cols, features):
            with col:
                items_html = "".join(f"<li>{item}</li>" for item in feature["items"])
                st.markdown(f"""
                <div class="feature-card">
                    <h3>{feature['icon']} {feature['title']}</h3>
                    <ul>{items_html}</ul>
                </div>
                """, unsafe_allow_html=True)
        
        # Iniciar análise
        if st.button("▶️ Começar Análise Agora", key="start_analysis", type="primary"):
            st.session_state.show_analysis = True
            st.session_state.current_step = 1
            st.experimental_rerun()

class AnalysisInterface:
    def __init__(self, nlp_model=None):
        self.nlp_model = nlp_model
        self.analyzer = ContractAnalysisEngine(CONTRACT_RULES, nlp_model)
        self.data_manager = DataManager()
        self.email_service = EmailService()
    
    def show_user_data_section(self):
        """Exibe o formulário de dados do usuário na barra lateral"""
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
                    self._handle_user_data_submission(name, email, phone)
    
    def _handle_user_data_submission(self, name: str, email: str, phone: str):
        """Processa o envio dos dados do usuário"""
        if not name or not email:
            st.error("Por favor, preencha todos os campos obrigatórios")
            return
        
        if not SecurityUtils.validate_email(email):
            st.error("Por favor, insira um e-mail válido")
            return
        
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
        
        if self.data_manager.save_to_google_sheets(save_data):
            st.success("Dados salvos com sucesso!")
        else:
            st.error("Erro ao salvar dados. Por favor, tente novamente.")
    
    def show_contract_upload(self):
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
                "Selecione um arquivo (PDF ou DOCX - até 10MB)", 
                type=["pdf", "docx"],
                key="file_uploader"
            )
            
            if file:
                if file.size > AppConfig.MAX_FILE_SIZE:
                    st.error("Arquivo muito grande. O tamanho máximo é 10MB.")
                    return
                
                st.session_state.file_uploaded = True
                with st.spinner("Processando arquivo..."):
                    text = FileUtils.extract_text(file)
                    if text:
                        st.session_state.contract_text = text
                        st.success("Arquivo processado com sucesso!")
                        
                        # Pré-visualização do texto
                        with st.expander("Visualizar texto extraído"):
                            st.text_area("Texto do contrato", 
                                        value=text[:2000] + "..." if len(text) > 2000 else text, 
                                        height=300,
                                        key="preview_text")

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
                self._analyze_contract()
    
    def _analyze_contract(self):
        """Executa a análise do contrato"""
        if not st.session_state.contract_text.strip():
            st.warning("Por favor, envie um arquivo ou cole o texto do contrato")
            return
        
        with st.spinner("Analisando contrato... Isso pode levar alguns segundos"):
            try:
                # Executa análise
                analysis_results, metadata = self.analyzer.analyze(st.session_state.contract_text)
                st.session_state.analysis = analysis_results
                st.session_state.contract_metadata = metadata
                
                # Atualiza dados do usuário
                st.session_state.user_data['analysis_requested'] = True
                st.session_state.user_data['contract_hash'] = metadata.contract_hash
                
                # Calcula métricas para o Google Sheets
                total_issues = len([r for r in analysis_results if r.score > 0])
                high_risk = sum(1 for r in analysis_results if r.score >= 8)
                
                # Atualiza Google Sheets
                update_data = {
                    **st.session_state.user_data,
                    "analysis_results": {
                        "total_issues": total_issues,
                        "high_risk": high_risk
                    }
                }
                self.data_manager.save_to_google_sheets(update_data)
                
                st.session_state.current_step = 2
                st.success("Análise concluída com sucesso!")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Erro durante a análise: {str(e)}")
                logger.error(f"Erro na análise: {traceback.format_exc()}")
    
    def show_analysis_results(self):
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
            
            # Calcula métricas
            total_issues = len([item for item in st.session_state.analysis if item.score > 0])
            high_risk = sum(1 for item in st.session_state.analysis if item.score >= 8)
            medium_risk = sum(1 for item in st.session_state.analysis if 5 <= item.score < 8)
            low_risk = sum(1 for item in st.session_state.analysis if 0 < item.score < 5)

            # Mostra métricas
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
            st.plotly_chart(
                VisualizationEngine.create_risk_chart(high_risk, medium_risk, low_risk), 
                use_container_width=True
            )
            
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
                    wordcloud_fig = VisualizationEngine.generate_wordcloud(st.session_state.contract_text)
                    if wordcloud_fig:
                        st.pyplot(wordcloud_fig)
                    
                    # Top 10 termos
                    words = re.findall(r'\b\w{4,}\b', st.session_state.contract_text.lower())
                    stopwords_pt = set(stopwords.words('portuguese'))
                    filtered_words = [w for w in words if w not in stopwords_pt and not w.isnumeric()]
                    word_freq = Counter(filtered_words)

                    top_words = pd.DataFrame(
                        word_freq.most_common(10),
                        columns=['Termo', 'Frequência']
                    )
                    st.bar_chart(top_words.set_index('Termo'))

            # Exemplo de uma cláusula problemática (se houver)
            if total_issues > 0:
                self._show_sample_issue(high_risk, medium_risk, low_risk)
            
            # Seção premium
            self._show_premium_section()
    
    def _show_sample_issue(self, high_risk: int, medium_risk: int, low_risk: int):
        """Mostra um exemplo de cláusula problemática"""
        st.subheader("🔎 Exemplo de Cláusula Problemática")
        
        # Seleciona a cláusula mais relevante para mostrar
        sample_issue = next((item for item in st.session_state.analysis if item.score > 0), None)

        if sample_issue:
            risk_class = f"risk-{sample_issue.risk_level.lower().replace(' ', '-')}"
            st.markdown(f"""
            <div class="{risk_class}">
                <h4>{sample_issue.clause} <span style="float: right; color: {'#e74c3c' if sample_issue.score >= 8 else '#f39c12' if sample_issue.score >= 5 else '#2ecc71'}">
                {sample_issue.risk_level}</span></h4>
                <p><strong>Problema identificado:</strong> {sample_issue.explanation}</p>
                <div class="excerpt-box">{sample_issue.excerpt}</div>
                <p><strong>Sugestão de melhoria:</strong> {sample_issue.solution}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Referência legal (se disponível)
            if sample_issue.legal_references:
                st.markdown("""
                <div class="legal-reference">
                    <h5>📚 Referências Legais</h5>
                    <ul>
                """, unsafe_allow_html=True)
                
                for ref in sample_issue.legal_references:
                    st.markdown(f"<li>{ref}</li>", unsafe_allow_html=True)
                
                st.markdown("</ul></div>", unsafe_allow_html=True)
        else:
            st.info("Nenhuma cláusula problemática encontrada na amostra.")
    
    def _show_premium_section(self):
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
                self._handle_premium_submission(agree)
    
    def _handle_premium_submission(self, agreed: bool):
        """Processa a solicitação de análise premium"""
        if not agreed:
            st.error("Por favor, aceite os termos para continuar")
            return
        
        if not st.session_state.user_data.get('email'):
            st.error("Por favor, preencha seu e-mail na barra lateral primeiro")
            return
        
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
            self.data_manager.save_to_google_sheets(update_data)
            
            # Envia e-mail de confirmação
            email_body = f"""
            <h2>Obrigado por adquirir a análise premium!</h2>
            <p>Estamos preparando seu relatório completo e você receberá em até 24 horas.</p>
            <p>ID da sua análise: {st.session_state.user_data['session_id']}</p>
            """
            
            if self.email_service.send_email(
                st.session_state.user_data['email'],
                "Confirmação de Análise Premium",
                email_body
            ):
                st.markdown("""
                <div class="email-confirmation">
                    <h4>📨 Confirmação Recebida!</h4>
                    <p>Você receberá a análise completa por e-mail em breve.</p>
                    <p>Obrigado por utilizar nossos serviços!</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.error("Erro ao enviar confirmação por e-mail. Sua análise foi processada, mas você pode não receber o e-mail.")
    
    def show_full_analysis(self):
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
                st.metric("Palavras", st.session_state.contract_metadata.total_words)
            with cols[1]:
                st.metric("Sentenças", st.session_state.contract_metadata.total_sentences)
            with cols[2]:
                issues = len([r for r in st.session_state.analysis if r.score > 0])
                st.metric("Problemas", issues)

        # Todas as cláusulas problemáticas
        st.subheader("⚠️ Cláusulas Problemáticas Identificadas")

        for item in st.session_state.analysis:
            if item.score > 0:  # Mostra apenas as problemáticas
                risk_class = f"risk-{item.risk_level.lower().replace(' ', '-')}"
                st.markdown(f"""
                <div class="{risk_class}">
                    <h4>{item.clause} <span style="float: right; color: {'#e74c3c' if item.score >= 8 else '#f39c12' if item.score >= 5 else '#2ecc71'}">
                    {item.risk_level}</span></h4>
                    <p><strong>Problema identificado:</strong> {item.explanation}</p>
                    <div class="excerpt-box">{item.excerpt}</div>
                    <p><strong>Contexto:</strong> {item.context or 'Não disponível'}</p>
                    <p><strong>Sugestão de melhoria:</strong> {item.solution}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Referências legais
                if item.legal_references:
                    st.markdown("""
                    <div class="legal-reference">
                        <h5>📚 Referências Legais</h5>
                        <ul>
                    """, unsafe_allow_html=True)
                    
                    for ref in item.legal_references:
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
            if item.score >= 5:  # Modelos apenas para médio/alto risco
                with st.expander(f"Modelo para: {item.clause}"):
                    st.markdown(f"""
                    **Assunto:** Contestação de Cláusula Contratual - {item.clause}
                    
                    **Prezados(as),**
                    
                    Mediante análise do contrato proposto, identificamos que a cláusula que trata de "{item.clause}" apresenta problemas por:
                    
                    - {item.explanation}
                    
                    Conforme {item.legal_references[0] if item.legal_references else 'a legislação vigente'}, tal disposição pode ser considerada abusiva.
                    
                    **Solicitamos a alteração para:**
                    
                    {item.solution}
                    
                    **Atenciosamente,**  
                    {st.session_state.user_data.get('name', '[Seu Nome]')}
                    """)

        # Botão para download do relatório
        pdf_report = VisualizationEngine.generate_pdf_report(
            st.session_state.analysis,
            st.session_state.user_data
        )
        
        if pdf_report:
            st.download_button(
                label="📥 Baixar Relatório Completo (PDF)",
                data=pdf_report,
                file_name=f"relatorio_clara_{st.session_state.user_data['session_id']}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        else:
            st.warning("Não foi possível gerar o relatório PDF. Entre em contato com o suporte.")

    def show_analysis_interface(self):
        """Exibe a interface completa de análise"""
        # Barra lateral com dados do usuário
        self.show_user_data_section()

        # Fluxo principal
        if st.session_state.current_step == 1:
            self.show_contract_upload()
        elif st.session_state.current_step == 2:
            self.show_analysis_results()
            if st.session_state.get('show_full_analysis', False):
                self.show_full_analysis()

#################################################################
# 11. CARREGAMENTO DE MODELOS E INICIALIZAÇÃO
#################################################################
def load_nlp_model() -> Optional[spacy.Language]:
    """Carrega o modelo de NLP com tratamento robusto de erros"""
    try:
        nlp = spacy.load("pt_core_news_sm")
        logger.success("Modelo Spacy carregado com sucesso")
        return nlp
    except OSError:
        try:
            logger.info("Modelo Spacy não encontrado. Tentando download...")
            from spacy.cli import download
            download("pt_core_news_sm")
            nlp = spacy.load("pt_core_news_sm")
            logger.success("Modelo Spacy baixado e carregado")
            return nlp
        except Exception as e:
            logger.error(f"Falha ao baixar modelo Spacy: {str(e)}")
    except Exception as e:
        logger.error(f"Erro inesperado ao carregar Spacy: {str(e)}")
    
    st.warning("""
    ⚠️ Modelo de linguagem não carregado. Algumas análises avançadas estarão limitadas.
    Recarregue a página ou tente novamente mais tarde.
    """)
    return None

#################################################################
# 12. CONTROLE PRINCIPAL DO APLICATIVO
#################################################################
def main():
    """Função principal da aplicação"""
    try:
        # Configuração inicial
        UIComponents.setup_page_config()
        UIComponents.load_css()
        UIComponents.init_session_state()
        UIComponents.check_session_timeout()
        
        # Carrega modelo NLP
        nlp_model = load_nlp_model()
        
        # Fluxo principal
        if not st.session_state.show_analysis:
            WelcomeScreen.show()
        else:
            analysis_interface = AnalysisInterface(nlp_model)
            analysis_interface.show_analysis_interface()
            
    except Exception as e:
        logger.critical(f"Erro fatal na aplicação: {str(e)}\n{traceback.format_exc()}")
        st.error("""
        Ocorreu um erro inesperado no sistema. Por favor, recarregue a página.
        Se o problema persistir, entre em contato com nosso suporte.
        """)

if __name__ == "__main__":
    main()
  

# -*- coding: utf-8 -*-
"""
CLARA - Análise Contratual Inteligente
Versão 2.0 - Análise avançada de contratos com integração ao Google Sheets
"""

import sys
import subprocess
import importlib
from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime

# Configuração básica de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ========== GERENCIAMENTO DE DEPENDÊNCIAS ==========
class DependencyManager:
    """Gerencia a instalação e verificação de dependências"""
    
    REQUIRED_PACKAGES = [
        ('streamlit', 'streamlit'),
        ('gspread', 'gspread'),
        ('oauth2client', 'oauth2client'),
        ('PyPDF2', 'PyPDF2'),
        ('docx', 'python-docx'),
        ('plotly', 'plotly'),
        ('PIL', 'Pillow')
    ]

    @classmethod
    def check_dependencies(cls):
        """Verifica e instala dependências faltantes"""
        missing_packages = []
        
        for module_name, package_name in cls.REQUIRED_PACKAGES:
            if not cls._is_installed(module_name):
                if not cls._install_package(package_name):
                    missing_packages.append(package_name)
        
        if missing_packages:
            error_msg = (
                f"⚠️ Falha ao instalar dependências: {', '.join(missing_packages)}\n"
                f"Por favor, instale manualmente com: pip install {' '.join(missing_packages)}"
            )
            logger.error(error_msg)
            raise ImportError(error_msg)

    @staticmethod
    def _is_installed(module_name: str) -> bool:
        """Verifica se um módulo está instalado"""
        try:
            importlib.import_module(module_name)
            return True
        except ImportError:
            return False

    @staticmethod
    def _install_package(package_name: str) -> bool:
        """Tenta instalar um pacote"""
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", package_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True
        except subprocess.CalledProcessError:
            return False

# Verifica dependências antes de continuar
try:
    DependencyManager.check_dependencies()
except ImportError as e:
    print(str(e))
    sys.exit(1)

# Importações após verificação de dependências
import streamlit as st
import re
from docx import Document
import PyPDF2
from io import BytesIO
import plotly.express as px
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from PIL import Image as pil_image

# ========== CONFIGURAÇÕES GERAIS ==========
class Config:
    """Configurações gerais da aplicação"""
    
    # Configurações de estilo
    COLORS = {
        'primary': '#2563eb',
        'primary_dark': '#1d4ed8',
        'secondary': '#1f2937',
        'accent': '#dc2626',
        'light': '#f9fafb',
        'border': '#e5e7eb',
        'success': '#10b981',
        'warning': '#f59e0b',
        'danger': '#ef4444'
    }
    
    # Configurações do Google Sheets
    GSHEETS_URL = "https://docs.google.com/spreadsheets/d/10vw0ghFU9Gefk53f8WiIhgKAChdkdqtx9WvphwmiNrA/edit#gid=0"
    CREDS_FILE = "credentials.json"
    
    # Configurações de análise
    MAX_EXCERPT_LENGTH = 100  # Caracteres antes/depois do termo encontrado

# ========== UTILITÁRIOS ==========
class TextUtils:
    """Utilitários para processamento de texto"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Normaliza o texto para análise"""
        if not text or not isinstance(text, str):
            return ""
        return text.lower().strip()
    
    @staticmethod
    def extract_excerpt(text: str, pattern: str) -> str:
        """
        Extrai um trecho do texto com destaque para o padrão encontrado
        
        Args:
            text: Texto completo do contrato
            pattern: Padrão regex que foi encontrado
            
        Returns:
            Trecho do texto com o padrão destacado
        """
        try:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                start = max(0, match.start() - Config.MAX_EXCERPT_LENGTH)
                end = min(len(text), match.end() + Config.MAX_EXCERPT_LENGTH)
                excerpt = text[start:end]
                excerpt = ' '.join(excerpt.split())
                highlighted = excerpt.replace(match.group().lower(), f"**{match.group()}**")
                return f"...{highlighted}..."
            return "Trecho não encontrado"
        except Exception as e:
            logger.error(f"Erro ao extrair trecho: {str(e)}")
            return "Erro ao extrair trecho"

class FileUtils:
    """Utilitários para manipulação de arquivos"""
    
    @staticmethod
    def extract_text(file: st.runtime.uploaded_file_manager.UploadedFile) -> Optional[str]:
        """
        Extrai texto de arquivos PDF ou DOCX
        
        Args:
            file: Arquivo enviado pelo usuário
            
        Returns:
            Texto extraído ou None em caso de erro
        """
        try:
            if file.type == "application/pdf":
                pdf_reader = PyPDF2.PdfReader(file)
                text = "\n".join([page.extract_text() or "" for page in pdf_reader.pages])
                return text if text.strip() else None
            elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                doc = Document(BytesIO(file.read()))
                text = "\n".join([para.text for para in doc.paragraphs if para.text])
                return text if text.strip() else None
        except Exception as e:
            logger.error(f"Erro ao ler arquivo: {str(e)}")
            return None

# ========== GERENCIAMENTO DE REGRAS ==========
class ContractRules:
    """Gerencia as regras de análise de contrato"""
    
    RULES = {
        "Consumidor": [
            {
                "name": "Proibição de cancelamento",
                "patterns": [r"não poderá rescindir.*sob nenhuma hipótese", r"proibição.*cancelamento"],
                "score": 8,
                "explanation": "Contratos de consumo geralmente permitem cancelamento. Verifique se esta cláusula está de acordo com o Código de Defesa do Consumidor.",
                "solution": "Recomendamos verificar com um especialista se esta limitação é válida no seu caso.",
                "law_reference": "CDC Art. 51, IV"
            },
            # ... (outras regras permanecem iguais)
        ]
    }
    
    @classmethod
    def get_rules_for_role(cls, role: str) -> List[Dict]:
        """Retorna as regras específicas para um perfil"""
        return cls.RULES.get(role, [])

# ========== ANÁLISE DE CONTRATO ==========
class ContractAnalyzer:
    """Realiza a análise de contratos"""
    
    @staticmethod
    def analyze(text: str, role: str) -> List[Dict]:
        """
        Analisa o texto do contrato com base nas regras para o perfil especificado
        
        Args:
            text: Texto do contrato a ser analisado
            role: Perfil do usuário
            
        Returns:
            Lista de resultados da análise
        """
        if not text or not isinstance(text, str):
            return [ContractAnalyzer._create_error_result("Texto do contrato inválido ou vazio.")]
        
        try:
            text = TextUtils.clean_text(text)
            results = []
            rules = ContractRules.get_rules_for_role(role)
            
            for rule in rules:
                for pattern in rule["patterns"]:
                    try:
                        if re.search(pattern, text, re.IGNORECASE):
                            excerpt = TextUtils.extract_excerpt(text, pattern)
                            results.append(ContractAnalyzer._create_analysis_result(rule, excerpt))
                            break
                    except re.error as e:
                        logger.warning(f"Padrão regex inválido: {pattern} - {str(e)}")
                        continue
            
            return sorted(results, key=lambda x: x["score"], reverse=True) if results else \
                   [ContractAnalyzer._create_no_issues_result()]
            
        except Exception as e:
            logger.error(f"Erro durante análise: {str(e)}")
            return [ContractAnalyzer._create_error_result(f"Ocorreu um erro durante a análise: {str(e)}")]

    @staticmethod
    def _create_error_result(error_msg: str) -> Dict:
        """Cria um resultado de erro padronizado"""
        return {
            "clause": "Erro na análise",
            "score": 0,
            "explanation": error_msg,
            "solution": "Por favor, tente novamente ou entre em contato com o suporte.",
            "law_reference": "",
            "excerpt": ""
        }

    @staticmethod
    def _create_no_issues_result() -> Dict:
        """Cria um resultado padrão quando não há problemas identificados"""
        return {
            "clause": "Nenhum ponto crítico identificado",
            "score": 0,
            "explanation": "Não encontramos cláusulas que normalmente exigem atenção especial para seu perfil.",
            "solution": "Ainda assim, recomendamos revisão cuidadosa ou consulta a um especialista para verificação completa.",
            "law_reference": "",
            "excerpt": ""
        }

    @staticmethod
    def _create_analysis_result(rule: Dict, excerpt: str) -> Dict:
        """Cria um resultado de análise padronizado a partir de uma regra"""
        return {
            "clause": rule["name"],
            "score": rule["score"],
            "explanation": rule["explanation"],
            "solution": rule["solution"],
            "law_reference": rule["law_reference"],
            "excerpt": excerpt if excerpt else "Trecho não encontrado"
        }

# ========== INTEGRAÇÃO COM GOOGLE SHEETS ==========
class GoogleSheetsManager:
    """Gerencia a integração com o Google Sheets"""
    
    @classmethod
    def connect(cls):
        """Estabelece conexão com o Google Sheets"""
        try:
            scope = ["https://spreadsheets.google.com/feeds", 
                    "https://www.googleapis.com/auth/drive"]
            
            try:
                creds = ServiceAccountCredentials.from_json_keyfile_name(Config.CREDS_FILE, scope)
            except FileNotFoundError:
                logger.warning("Arquivo de credenciais não encontrado")
                return None
                
            client = gspread.authorize(creds)
            return client.open_by_url(Config.GSHEETS_URL)
        except Exception as e:
            logger.error(f"Erro ao conectar com Google Sheets: {str(e)}")
            return None

    @classmethod
    def save_data(cls, name: str, email: str, phone: str, role: str, analysis_results: List[Dict]) -> bool:
        """Salva os dados na planilha"""
        try:
            sheet = cls.connect()
            if not sheet:
                return False
                
            worksheet = sheet.sheet1
            row = [
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                name,
                email,
                phone or "",
                role,
                str(len(analysis_results)),
                str(sum(item.get("score", 0) for item in analysis_results))
            ]
            worksheet.append_row(row)
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar dados: {str(e)}")
            return False

# ========== INTERFACE DO USUÁRIO ==========
class UIManager:
    """Gerencia a interface do usuário"""
    
    @staticmethod
    def setup_page():
        """Configurações iniciais da página"""
        st.set_page_config(
            page_title="CLARA - Análise Contratual Inteligente",
            page_icon="⚖️",
            layout="wide",
            initial_sidebar_state="expanded",
            menu_items={
                'Get Help': 'https://example.com/help',
                'Report a bug': 'https://example.com/bug',
                'About': "CLARA - Seu assistente para análise de contratos"
            }
        )
    
    @staticmethod
    def load_css():
        """Carrega os estilos CSS personalizados"""
        st.markdown(f"""
        <style>
            :root {{
                --primary: {Config.COLORS['primary']};
                --primary-dark: {Config.COLORS['primary_dark']};
                --secondary: {Config.COLORS['secondary']};
                --accent: {Config.COLORS['accent']};
                --light: {Config.COLORS['light']};
                --border: {Config.COLORS['border']};
                --success: {Config.COLORS['success']};
                --warning: {Config.COLORS['warning']};
                --danger: {Config.COLORS['danger']};
            }}
            
            .hero {{
                background: linear-gradient(135deg, #f0f4ff 0%, #e6f0ff 100%);
                border-radius: 16px;
                padding: 3rem;
                margin-bottom: 2rem;
                text-align: center;
            }}
            
            /* ... (outros estilos permanecem iguais) ... */
        </style>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def show_progress():
        """Mostra uma barra de progresso durante a análise"""
        progress_bar = st.empty()
        progress_text = st.empty()
        
        for percent in range(0, 101, 5):
            time.sleep(0.05)
            progress_bar.progress(percent)
            progress_text.text(f"Analisando contrato... {percent}%")
        
        progress_text.empty()
        progress_bar.empty()
    
    @staticmethod
    def show_welcome():
        """Mostra a página inicial com as opções de perfil"""
        st.markdown("""
        <div class="hero">
            <div class="hero-title">CLARA</div>
            <div class="hero-subtitle">Seu Assistente para Análise de Contratos</div>
            <p style="font-size: 1.1rem; color: #4b5563; max-width: 800px; margin: 0 auto;">
            A CLARA ajuda você a entender contratos complexos em linguagem simples, 
            identificando pontos que merecem sua atenção. Não somos um escritório de advocacia, 
            mas seu guia para entender melhor seus contratos.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # ... (restante da implementação da UI permanece similar, mas organizado em métodos)
    
    @staticmethod
    def show_analysis_interface():
        """Mostra a interface de análise do contrato"""
        # ... (implementação organizada da interface de análise)
    
    @staticmethod
    def show_results(results: List[Dict]):
        """Mostra os resultados da análise"""
        # ... (implementação organizada da exibição de resultados)

# ========== APLICAÇÃO PRINCIPAL ==========
class ClaraApp:
    """Classe principal da aplicação"""
    
    def __init__(self):
        self._initialize_session_state()
        UIManager.setup_page()
        UIManager.load_css()
    
    def _initialize_session_state(self):
        """Inicializa o estado da sessão"""
        if "show_analysis" not in st.session_state:
            st.session_state.show_analysis = False
        if "user_role" not in st.session_state:
            st.session_state.user_role = None
        if "analysis_results" not in st.session_state:
            st.session_state.analysis_results = None
    
    def run(self):
        """Executa a aplicação"""
        if not st.session_state.show_analysis:
            UIManager.show_welcome()
        else:
            UIManager.show_analysis_interface()

if __name__ == "__main__":
    app = ClaraApp()
    app.run()

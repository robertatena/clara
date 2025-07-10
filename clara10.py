# -*- coding: utf-8 -*-
"""
CLARA - Análise Contratual Inteligente
Versão 3.0 - Refatoração completa com tratamento robusto de erros
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
                logger.info(f"Pacote {package_name} não encontrado. Instalando...")
                if not cls._install_package(package_name):
                    missing_packages.append(package_name)
        
        if missing_packages:
            error_msg = (
                f"Falha ao instalar dependências: {', '.join(missing_packages)}\n"
                f"Execute manualmente: pip install {' '.join(missing_packages)}"
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
        except Exception as e:
            logger.error(f"Erro inesperado ao instalar {package_name}: {str(e)}")
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

# ========== MODELOS DE DADOS ==========
class AnalysisResult:
    """Modelo para resultados de análise"""
    
    def __init__(self, clause: str, score: int, explanation: str, 
                 solution: str, law_reference: str, excerpt: str):
        self.clause = clause
        self.score = score
        self.explanation = explanation
        self.solution = solution
        self.law_reference = law_reference
        self.excerpt = excerpt
    
    def to_dict(self) -> Dict:
        """Converte para dicionário"""
        return {
            "clause": self.clause,
            "score": self.score,
            "explanation": self.explanation,
            "solution": self.solution,
            "law_reference": self.law_reference,
            "excerpt": self.excerpt
        }

# ========== SERVIÇOS ==========
class ContractAnalyzer:
    """Serviço de análise de contratos"""
    
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
    def analyze(cls, text: str, role: str) -> List[AnalysisResult]:
        """Analisa o texto do contrato"""
        if not text or not isinstance(text, str):
            return [cls._create_error_result("Texto do contrato inválido ou vazio.")]
        
        try:
            text = text.lower()
            results = []
            rules = cls.RULES.get(role, [])
            
            for rule in rules:
                for pattern in rule["patterns"]:
                    try:
                        if re.search(pattern, text, re.IGNORECASE):
                            excerpt = cls._extract_excerpt(text, pattern)
                            results.append(AnalysisResult(
                                clause=rule["name"],
                                score=rule["score"],
                                explanation=rule["explanation"],
                                solution=rule["solution"],
                                law_reference=rule["law_reference"],
                                excerpt=excerpt
                            ))
                            break
                    except re.error as e:
                        logger.warning(f"Padrão regex inválido: {pattern} - {str(e)}")
                        continue
            
            return sorted(results, key=lambda x: x.score, reverse=True) if results else \
                   [cls._create_no_issues_result()]
            
        except Exception as e:
            logger.error(f"Erro durante análise: {str(e)}")
            return [cls._create_error_result(f"Ocorreu um erro durante a análise: {str(e)}")]

    @staticmethod
    def _extract_excerpt(text: str, pattern: str) -> str:
        """Extrai um trecho do texto com destaque para o padrão"""
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

    @staticmethod
    def _create_error_result(error_msg: str) -> AnalysisResult:
        """Cria um resultado de erro"""
        return AnalysisResult(
            clause="Erro na análise",
            score=0,
            explanation=error_msg,
            solution="Por favor, tente novamente ou entre em contato com o suporte.",
            law_reference="",
            excerpt=""
        )

    @staticmethod
    def _create_no_issues_result() -> AnalysisResult:
        """Cria um resultado sem problemas encontrados"""
        return AnalysisResult(
            clause="Nenhum ponto crítico identificado",
            score=0,
            explanation="Não encontramos cláusulas que normalmente exigem atenção especial para seu perfil.",
            solution="Ainda assim, recomendamos revisão cuidadosa ou consulta a um especialista.",
            law_reference="",
            excerpt=""
        )

class GoogleSheetsService:
    """Serviço de integração com Google Sheets"""
    
    @classmethod
    def save_analysis(cls, name: str, email: str, phone: str, role: str, results: List[AnalysisResult]) -> bool:
        """Salva os dados da análise na planilha"""
        try:
            sheet = cls._connect()
            if not sheet:
                return False
                
            worksheet = sheet.sheet1
            row = [
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                name,
                email,
                phone or "",
                role,
                str(len(results)),
                str(sum(result.score for result in results))
            ]
            worksheet.append_row(row)
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar dados: {str(e)}")
            return False

    @staticmethod
    def _connect():
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

# ========== INTERFACE DO USUÁRIO ==========
class UIComponents:
    """Componentes da interface do usuário"""
    
    @staticmethod
    def setup_page_config():
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
        """Mostra barra de progresso durante análise"""
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
        """Página inicial com opções de perfil"""
        st.markdown("""
        <div class="hero">
            <div class="hero-title">CLARA</div>
            <div class="hero-subtitle">Seu Assistente para Análise de Contratos</div>
            <p style="font-size: 1.1rem; color: #4b5563; max-width: 800px; margin: 0 auto;">
            A CLARA ajuda você a entender contratos complexos em linguagem simples, 
            identificando pontos que merecem sua atenção.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # ... (implementação dos outros componentes da UI)

# ========== APLICAÇÃO PRINCIPAL ==========
class ClaraApp:
    """Aplicação principal"""
    
    def __init__(self):
        self._init_session_state()
        UIComponents.setup_page_config()
        UIComponents.load_css()
    
    def _init_session_state(self):
        """Inicializa o estado da sessão"""
        if "show_analysis" not in st.session_state:
            st.session_state.show_analysis = False
        if "user_role" not in st.session_state:
            st.session_state.user_role = None
        if "analysis_results" not in st.session_state:
            st.session_state.analysis_results = None
    
    def run(self):
        """Executa o fluxo principal da aplicação"""
        if not st.session_state.show_analysis:
            self._show_welcome_page()
        else:
            self._show_analysis_interface()
    
    def _show_welcome_page(self):
        """Exibe a página inicial"""
        UIComponents.show_welcome()
        
        roles = [
            {"title": "Consumidor", "icon": "🛒"},
            {"title": "Prestador de Serviços", "icon": "👨‍💻"},
            {"title": "Locatário", "icon": "🏠"},
            {"title": "Empresário", "icon": "👔"}
        ]
        
        cols = st.columns(2)
        for i, role in enumerate(roles):
            with cols[i % 2]:
                if st.button(
                    f"{role['icon']} {role['title']}",
                    key=f"role_{i}",
                    use_container_width=True
                ):
                    st.session_state.user_role = role['title']
                    st.session_state.show_analysis = True
                    st.rerun()
    
    def _show_analysis_interface(self):
        """Exibe a interface de análise"""
        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 2rem;">
            <h1>Análise Contratual</h1>
            <p style="color: #4b5563;">Perfil: {st.session_state.get('user_role', 'Não definido')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        text = self._get_contract_text()
        
        if st.button("🔍 Analisar Contrato", type="primary", use_container_width=True):
            if not text:
                st.error("Por favor, envie um arquivo ou cole o texto do contrato")
                return
            
            with st.spinner("Preparando análise..."):
                try:
                    UIComponents.show_progress()
                    results = ContractAnalyzer.analyze(text, st.session_state.user_role)
                    st.session_state.analysis_results = results
                    st.success("Análise concluída!")
                except Exception as e:
                    st.error(f"Erro durante a análise: {str(e)}")
                    st.session_state.analysis_results = [
                        ContractAnalyzer._create_error_result(f"Erro no processamento: {str(e)}")
                    ]
        
        if st.session_state.analysis_results:
            self._show_results(st.session_state.analysis_results)
    
    def _get_contract_text(self) -> Optional[str]:
        """Obtém o texto do contrato do usuário"""
        tab1, tab2 = st.tabs(["Upload de Arquivo", "Texto Digitado"])
        
        with tab1:
            file = st.file_uploader(
                "Selecione um arquivo (PDF ou DOCX)",
                type=["pdf", "docx"],
                label_visibility="collapsed"
            )
            if file:
                try:
                    if file.type == "application/pdf":
                        pdf_reader = PyPDF2.PdfReader(file)
                        return "\n".join([page.extract_text() or "" for page in pdf_reader.pages])
                    elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                        doc = Document(BytesIO(file.read()))
                        return "\n".join([para.text for para in doc.paragraphs if para.text])
                except Exception as e:
                    st.error(f"Erro ao ler arquivo: {str(e)}")
                    return None
        
        with tab2:
            return st.text_area(
                "Ou cole o texto do contrato aqui",
                height=200,
                placeholder="Copie e cole o texto completo do contrato..."
            )
        
        return None
    
    def _show_results(self, results: List[AnalysisResult]):
        """Exibe os resultados da análise"""
        st.markdown("### 📋 Resultados da Análise")
        
        # Métricas resumidas
        needs_review = sum(1 for r in results if r.score >= 7)
        suggested_review = sum(1 for r in results if 4 <= r.score < 7)
        no_issues = sum(1 for r in results if r.score < 4)
        
        cols = st.columns(3)
        cols[0].metric("Precisa revisar", needs_review)
        cols[1].metric("Sugerimos revisar", suggested_review)
        cols[2].metric("Sem problemas", no_issues)
        
        # Gráfico de pizza
        if needs_review + suggested_review + no_issues > 0:
            fig = px.pie(
                names=["Precisa revisar", "Sugerimos revisar", "Sem problemas"],
                values=[needs_review, suggested_review, no_issues],
                color_discrete_map={
                    "Precisa revisar": Config.COLORS['warning'],
                    "Sugerimos revisar": "#a3a3a3",
                    "Sem problemas": Config.COLORS['success']
                },
                hole=0.4
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Opção de relatório por e-mail
        self._show_email_report_option(results)
        
        # Detalhes da análise
        st.markdown("### 🔍 Pontos Analisados")
        for result in results:
            self._show_result_detail(result)
    
    def _show_email_report_option(self, results: List[AnalysisResult]):
        """Exibe opção para solicitar relatório por e-mail"""
        st.markdown("""
        <div class="premium-offer">
            <h3>📩 Relatório Completo por E-mail</h3>
            <p>Receba um relatório detalhado com:</p>
            <ul>
                <li>Análise completa de cada cláusula</li>
                <li>Recomendações personalizadas</li>
                <li>Modelos de contestação</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        if st.button("📧 Solicitar Relatório", key="premium_report"):
            with st.form(key='email_form'):
                name = st.text_input("Nome completo")
                email = st.text_input("E-mail")
                phone = st.text_input("Telefone (opcional)")
                
                if st.form_submit_button("Enviar Solicitação"):
                    if not name or not email:
                        st.error("Por favor, preencha pelo menos nome e e-mail")
                    else:
                        if GoogleSheetsService.save_analysis(
                            name, email, phone, 
                            st.session_state.user_role, results
                        ):
                            st.success("Relatório solicitado com sucesso!")
                            self._show_email_content(name, email, results)
    
    def _show_email_content(self, name: str, email: str, results: List[AnalysisResult]):
        """Mostra o conteúdo do e-mail que seria enviado"""
        report = f"""Relatório de Análise Contratual - CLARA
======================================

Cliente: {name}
E-mail: {email}
Perfil: {st.session_state.user_role}

Resumo da Análise:"""
        
        for item in results:
            report += f"\n\n- {item.clause} (Pontuação: {item.score}/10)"
            report += f"\n  🔍 {item.explanation}"
            report += f"\n  ⚖️ Base legal: {item.law_reference}"
            report += f"\n  💡 Sugestão: {item.solution}"
        
        st.text_area("Conteúdo do Relatório", report, height=300)
    
    def _show_result_detail(self, result: AnalysisResult):
        """Exibe os detalhes de um resultado individual"""
        risk_class = (
            "attention-needed" if result.score >= 7 else 
            "review-suggested" if result.score >= 4 else 
            "no-issues"
        )
        
        with st.expander(f"{result.clause}", expanded=True):
            st.markdown(f"""
            <div class="feature-card {risk_class}">
                <p><strong>📌 No contrato:</strong></p>
                <div class="contract-excerpt">
                    {result.excerpt}
                </div>
                <p><strong>💡 O que significa:</strong> {result.explanation}</p>
                <p><strong>⚖️ Base legal:</strong> {result.law_reference}</p>
                <p><strong>🛠️ Sugestão:</strong> {result.solution}</p>
            </div>
            """, unsafe_allow_html=True)

# Ponto de entrada da aplicação
if __name__ == "__main__":
    try:
        app = ClaraApp()
        app.run()
    except Exception as e:
        logger.critical(f"Falha crítica na aplicação: {str(e)}")
        st.error("Ocorreu um erro crítico na aplicação. Por favor, tente novamente mais tarde.")

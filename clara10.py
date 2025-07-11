import streamlit as st
import re
from docx import Document
import PyPDF2
from io import BytesIO
import plotly.express as px
import time
from typing import List, Dict, Optional, Union
from datetime import datetime

# ========== CONFIGURAÇÃO ==========
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

def load_css():
    """Carrega os estilos CSS personalizados"""
    st.markdown("""
    <style>
        :root {
            --primary: #2563eb;
            --primary-dark: #1d4ed8;
            --secondary: #1f2937;
            --accent: #dc2626;
            --light: #f9fafb;
            --border: #e5e7eb;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
        }
        
        .hero {
            background: linear-gradient(135deg, #f0f4ff 0%, #e6f0ff 100%);
            border-radius: 16px;
            padding: 3rem;
            margin-bottom: 2rem;
            text-align: center;
        }
        
        .hero-title {
            font-size: 2.5rem;
            color: var(--secondary);
            font-weight: 700;
            margin-bottom: 1rem;
        }
        
        .hero-subtitle {
            font-size: 1.25rem;
            color: #4b5563;
            margin-bottom: 2rem;
        }
        
        .feature-card {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            border: 1px solid var(--border);
            transition: all 0.3s;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            height: 100%;
        }
        
        .feature-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
        }
        
        .btn-primary {
            background-color: var(--primary) !important;
            color: white !important;
            border: none !important;
            padding: 0.75rem 2rem !important;
            font-weight: 600 !important;
            border-radius: 8px !important;
            width: 100% !important;
            transition: all 0.3s !important;
        }
        
        .btn-primary:hover {
            background-color: var(--primary-dark) !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        }
        
        .attention-needed {
            border-left: 4px solid var(--warning);
            background-color: #fffbeb;
        }
        
        .review-suggested {
            border-left: 4px solid #f59e0b;
            background-color: #fffbeb;
        }
        
        .no-issues {
            border-left: 4px solid var(--success);
            background-color: #ecfdf5;
        }
        
        .disclaimer {
            background-color: #f3f4f6;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
            font-size: 0.9rem;
        }
        
        .premium-offer {
            background: linear-gradient(135deg, #fff9e6 0%, #fff0cc 100%);
            border-radius: 12px;
            padding: 1.5rem;
            margin: 2rem 0;
            border: 1px solid #ffd966;
        }
        
        .contract-excerpt {
            background-color: #f3f4f6;
            padding: 1rem;
            border-radius: 6px;
            font-family: 'Courier New', monospace;
            margin: 0.5rem 0;
        }
        
        .error-card {
            border-left: 4px solid var(--danger);
            background-color: #fef2f2;
        }
        
        /* Melhorias de acessibilidade */
        .sr-only {
            position: absolute;
            width: 1px;
            height: 1px;
            padding: 0;
            margin: -1px;
            overflow: hidden;
            clip: rect(0, 0, 0, 0);
            white-space: nowrap;
            border-width: 0;
        }
        
        /* Melhorias para mobile */
        @media (max-width: 768px) {
            .hero {
                padding: 1.5rem;
            }
            .hero-title {
                font-size: 1.8rem;
            }
        }
        
        /* Novo estilo para formulário */
        .user-form {
            background: white;
            border-radius: 12px;
            padding: 2rem;
            margin: 2rem 0;
            border: 1px solid var(--border);
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .form-title {
            color: var(--secondary);
            font-size: 1.5rem;
            margin-bottom: 1.5rem;
            text-align: center;
        }
        
        .required-field::after {
            content: " *";
            color: var(--danger);
        }
    </style>
    """, unsafe_allow_html=True)

def check_dependencies():
    """Verifica se todas as dependências estão instaladas"""
    required_packages = {
        'docx': 'python-docx',
        'PyPDF2': 'PyPDF2',
        'plotly': 'plotly',
        'gspread': 'gspread',
        'google.auth': 'google-auth'
    }
    
    missing = []
    for package, pip_name in required_packages.items():
        try:
            __import__(package)
        except ImportError:
            missing.append(pip_name)
    
    if missing:
        st.error("Pacotes necessários não encontrados!")
        st.info(f"Instale com: pip install {' '.join(missing)}")
        return False
    return True

# ========== REGRAS DE ANÁLISE ==========
def get_contract_rules() -> Dict[str, List[Dict]]:
    """Retorna as regras de análise de contrato organizadas por perfil"""
    return {
        "Consumidor": [
            {
                "name": "Proibição de cancelamento",
                "patterns": [r"não poderá rescindir.*sob nenhuma hipótese", r"proibição.*cancelamento"],
                "score": 8,
                "explanation": "Contratos de consumo geralmente permitem cancelamento. Verifique se esta cláusula está de acordo com o Código de Defesa do Consumidor.",
                "solution": "Recomendamos verificar com um especialista se esta limitação é válida no seu caso.",
                "law_reference": "CDC Art. 51, IV"
            },
            {
                "name": "Multas abusivas",
                "patterns": [r"multa.*superior.*30%", r"penalidade.*superior.*valor.*serviço"],
                "score": 8,
                "explanation": "Multas muito altas podem ser consideradas abusivas pelo PROCON.",
                "solution": "Sugerimos negociar multas proporcionais ao descumprimento.",
                "law_reference": "CDC Art. 51, V"
            },
            {
                "name": "Alterações unilaterais",
                "patterns": [r"empresa.*alterar.*contrato.*unilateralmente", r"reserva.*direito.*modificar.*termos"],
                "score": 7,
                "explanation": "Alterações contratuais devem ser comunicadas e aceitas pelo consumidor.",
                "solution": "Exigir notificação prévia e direito de rescindir sem penalidades.",
                "law_reference": "CDC Art. 52"
            }
        ],
        "Prestador de Serviços": [
            {
                "name": "Prazo de pagamento extenso",
                "patterns": [r"pagamento.*após.*60 dias", r"prazo.*pagamento.*superior.*30 dias"],
                "score": 7,
                "explanation": "Prazos longos para pagamento podem afetar seu fluxo de caixa.",
                "solution": "Considere negociar prazos mais curtos para pagamento.",
                "law_reference": "Lei Complementar 123/2006"
            },
            {
                "name": "Transferência de responsabilidade",
                "patterns": [r"responsabilidade.*integral.*prestador", r"obrigações.*indenizar.*cliente"],
                "score": 7,
                "explanation": "Cláusulas que transferem toda a responsabilidade podem ser desbalanceadas.",
                "solution": "Proponha termos mais equilibrados de responsabilidade.",
                "law_reference": "Código Civil, Art. 389"
            },
            {
                "name": "Exclusividade abusiva",
                "patterns": [r"vedado.*prestar.*serviços.*concorrentes", r"proibido.*trabalhar.*concorrência"],
                "score": 6,
                "explanation": "Cláusulas de exclusividade devem ter prazo e escopo limitados.",
                "solution": "Negociar limites razoáveis de tempo e área de atuação.",
                "law_reference": "Lei 9.841/99"
            }
        ],
        "Locatário": [
            {
                "name": "Reajuste acima do índice",
                "patterns": [r"reajuste.*superior.*IGPM", r"reajuste.*anual.*acima.*10%"],
                "score": 7,
                "explanation": "Reajustes devem seguir índices oficiais. Valores muito acima podem ser questionados.",
                "solution": "Verifique se o índice de reajuste está de acordo com a lei do inquilinato.",
                "law_reference": "Lei 8.245/91"
            },
            {
                "name": "Caução elevada",
                "patterns": [r"caução.*superior.*3.*alugueis", r"depósito.*superior.*3.*meses"],
                "score": 7,
                "explanation": "Valores de caução muito altos podem ser considerados abusivos.",
                "solution": "Negociar caução de no máximo 3 meses de aluguel.",
                "law_reference": "Lei 8.245/91 Art. 37"
            },
            {
                "name": "Obrigações de reforma",
                "patterns": [r"locatário.*responsável.*reformas", r"obrigação.*conservação.*imóvel"],
                "score": 6,
                "explanation": "Reformas estruturais geralmente são obrigação do proprietário.",
                "solution": "Limitar obrigações a pequenos reparos de uso normal.",
                "law_reference": "Código Civil, Art. 1.274"
            },
            {
                "name": "Restrições de uso",
                "patterns": [r"proibido.*animais.*domésticos", r"veta.*visitas.*pernoite"],
                "score": 5,
                "explanation": "Restrições excessivas podem limitar seu direito de uso do imóvel.",
                "solution": "Negociar termos mais razoáveis de convivência.",
                "law_reference": "Código Civil, Art. 1.258"
            }
        ],
        "Empresário": [
            {
                "name": "Confidencialidade excessiva",
                "patterns": [r"confidencialidade.*perpetua", r"sigilo.*indeterminado"],
                "score": 7,
                "explanation": "Cláusulas de confidencialidade sem prazo podem ser problemáticas.",
                "solution": "Estabelecer prazo razoável para obrigações de sigilo.",
                "law_reference": "Lei 9.279/96 (Propriedade Industrial)"
            },
            {
                "name": "Indenização desproporcional",
                "patterns": [r"indenização.*ilimitada", r"responsabilidade.*integral.*danos"],
                "score": 8,
                "explanation": "Cláusulas que impõem indenizações ilimitadas podem ser inválidas.",
                "solution": "Limitar a responsabilidade ao valor do contrato ou seguro.",
                "law_reference": "Código Civil, Art. 413"
            }
        ]
    }

# ========== FUNÇÕES PRINCIPAIS ==========
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
        st.error(f"Erro ao ler arquivo: {str(e)}")
        return None

def analyze_contract(text: str, role: str) -> List[Dict]:
    """
    Analisa o texto do contrato com base nas regras para o perfil especificado
    
    Args:
        text: Texto do contrato a ser analisado
        role: Perfil do usuário (Consumidor, Prestador de Serviços, etc.)
        
    Returns:
        Lista de resultados da análise
    """
    if not text or not isinstance(text, str):
        return [create_error_result("Texto do contrato inválido ou vazio.")]
    
    try:
        text = text.lower()
        results = []
        rules = get_contract_rules().get(role, [])
        
        for rule in rules:
            for pattern in rule["patterns"]:
                try:
                    if re.search(pattern, text, re.IGNORECASE):
                        excerpt = extract_excerpt(text, pattern)
                        results.append(create_analysis_result(rule, excerpt))
                        break
                except re.error:
                    continue
        
        if not results:
            return [create_no_issues_result()]
        
        return sorted(results, key=lambda x: x["score"], reverse=True)
    
    except Exception as e:
        return [create_error_result(f"Ocorreu um erro durante a análise: {str(e)}")]

def create_error_result(error_msg: str) -> Dict:
    """Cria um resultado de erro padronizado"""
    return {
        "clause": "Erro na análise",
        "score": 0,
        "explanation": error_msg,
        "solution": "Por favor, tente novamente ou entre em contato com o suporte.",
        "law_reference": "",
        "excerpt": ""
    }

def create_no_issues_result() -> Dict:
    """Cria um resultado padrão quando não há problemas identificados"""
    return {
        "clause": "Nenhum ponto crítico identificado",
        "score": 0,
        "explanation": "Não encontramos cláusulas que normalmente exigem atenção especial para seu perfil.",
        "solution": "Ainda assim, recomendamos revisão cuidadosa ou consulta a um especialista para verificação completa.",
        "law_reference": "",
        "excerpt": ""
    }

def create_analysis_result(rule: Dict, excerpt: str) -> Dict:
    """Cria um resultado de análise padronizado a partir de uma regra"""
    return {
        "clause": rule["name"],
        "score": rule["score"],
        "explanation": rule["explanation"],
        "solution": rule["solution"],
        "law_reference": rule["law_reference"],
        "excerpt": excerpt if excerpt else "Trecho não encontrado"
    }

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
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            excerpt = text[start:end]
            excerpt = ' '.join(excerpt.split())
            highlighted = excerpt.replace(match.group().lower(), f"**{match.group()}**")
            return f"...{highlighted}..."
        return "Trecho não encontrado"
    except Exception:
        return "Erro ao extrair trecho"

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

# ========== GERENCIAMENTO DE DADOS ==========
def save_to_google_sheets(data: dict) -> bool:
    """Salva os dados do usuário no Google Sheets"""
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        
        # Configuração das credenciais
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(st.secrets["google_credentials"], scopes=scopes)
        client = gspread.authorize(creds)
        
        # Abre a planilha
        sheet = client.open_by_key(st.secrets["spreadsheet_key"]).sheet1
        
        # Adiciona nova linha com os dados
        sheet.append_row([
            data.get('nome', ''),
            data.get('email', ''),
            data.get('telefone', ''),
            data.get('perfil', ''),
            str(datetime.now()),
            data.get('tipo_contrato', ''),
            data.get('observacoes', '')
        ])
        
        return True
    except Exception as e:
        st.error(f"Erro ao salvar dados: {str(e)}")
        return False

# ========== INTERFACES DE USUÁRIO ==========
def show_user_info_form() -> bool:
    """Mostra o formulário de informações do usuário"""
    with st.container():
        st.markdown("""
        <div class="user-form">
            <div class="form-title">📝 Informações para Análise</div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("user_info_form", clear_on_submit=True):
            cols = st.columns(2)
            with cols[0]:
                nome = st.text_input("Nome completo*", key="user_name")
            with cols[1]:
                email = st.text_input("E-mail*", key="user_email")
            
            telefone = st.text_input("Telefone (opcional)", key="user_phone")
            tipo_contrato = st.text_input("Tipo de contrato (opcional)", key="contract_type")
            observacoes = st.text_area("Observações adicionais (opcional)", key="user_notes")
            
            submitted = st.form_submit_button("Enviar e Continuar")
            
            if submitted:
                if not nome or not email:
                    st.error("Por favor, preencha pelo menos nome e e-mail")
                    return False
                
                if "@" not in email or "." not in email:
                    st.error("Por favor, insira um e-mail válido")
                    return False
                
                user_data = {
                    "nome": nome,
                    "email": email,
                    "telefone": telefone,
                    "perfil": st.session_state.user_role,
                    "tipo_contrato": tipo_contrato,
                    "observacoes": observacoes
                }
                
                if save_to_google_sheets(user_data):
                    st.session_state.user_info = user_data
                    st.session_state.show_user_form = False
                    st.success("Informações salvas com sucesso!")
                    time.sleep(1)
                    return True
                else:
                    st.warning("As informações não puderam ser salvas automaticamente. Por favor, continue com a análise.")
                    st.session_state.user_info = user_data
                    st.session_state.show_user_form = False
                    return True
    return False

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
    
    st.markdown("### ✨ Para quem é a CLARA?")
    cols = st.columns(3)
    
    with cols[0]:
        st.markdown("""
        <div class="feature-card">
            <h4>👩‍💼 Profissionais Autônomos</h4>
            <p>Freelancers, consultores e prestadores de serviços que assinam contratos com clientes.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with cols[1]:
        st.markdown("""
        <div class="feature-card">
            <h4>🏠 Locatários</h4>
            <p>Quem está alugando imóveis e quer entender melhor o contrato de locação.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with cols[2]:
        st.markdown("""
        <div class="feature-card">
            <h4>🛒 Consumidores</h4>
            <p>Pessoas que assinam contratos de serviços, assinaturas ou compras.</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("### 🔍 Como funciona?")
    st.markdown("""
    1. **Selecione seu perfil** (como você está no contrato)
    2. **Forneça suas informações** para personalizarmos a análise
    3. **Envie seu contrato** (PDF ou DOCX) ou cole o texto
    4. **Receba uma análise básica** dos pontos que merecem atenção
    5. **Para uma análise detalhada**, solicite nosso relatório completo
    """)
    
    st.markdown("""
    <div class="disclaimer">
        <strong>⚠️ Aviso importante:</strong> A CLARA não substitui a consulta com um advogado. 
        Nossa análise tem caráter informativo e não constitui assessoria jurídica. 
        Para questões complexas, recomendamos sempre consultar um profissional especializado.
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 👤 Qual é o seu papel no contrato?")
    
    roles = [
        {"title": "Consumidor", "description": "Analisa contratos de compra, serviços ou assinaturas", "icon": "🛒"},
        {"title": "Prestador de Serviços", "description": "Analisa contratos de trabalho autônomo ou freelancer", "icon": "👨‍💻"},
        {"title": "Locatário", "description": "Analisa contratos de aluguel ou arrendamento", "icon": "🏠"},
        {"title": "Empresário", "description": "Analisa contratos comerciais ou de prestação de serviços", "icon": "👔"}
    ]
    
    cols = st.columns(2)
    for i, role in enumerate(roles):
        with cols[i % 2]:
            if st.button(
                f"{role['icon']} {role['title']}",
                key=f"role_{i}",
                help=role['description'],
                use_container_width=True
            ):
                st.session_state.user_role = role['title']
                st.session_state.show_user_form = True
                st.session_state.show_analysis = True
                st.rerun()

def show_analysis_interface():
    """Mostra a interface de análise do contrato"""
    if st.session_state.get('show_user_form', True):
        if show_user_info_form():
            st.rerun()
        return
    
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1>Análise Contratual</h1>
        <p style="color: #4b5563;">Perfil: {st.session_state.get('user_role', 'Não definido')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 📤 Envie seu contrato")
    tab1, tab2 = st.tabs(["Upload de Arquivo", "Texto Digitado"])
    
    with tab1:
        file = st.file_uploader(
            "Selecione um arquivo (PDF ou DOCX)",
            type=["pdf", "docx"],
            label_visibility="collapsed"
        )
    
    with tab2:
        text_input = st.text_area(
            "Ou cole o texto do contrato aqui",
            height=200,
            placeholder="Copie e cole o texto completo do contrato..."
        )
    
    if st.button("🔍 Analisar Contrato", type="primary", use_container_width=True):
        if not file and not text_input:
            st.error("Por favor, envie um arquivo ou cole o texto do contrato")
            return
        
        with st.spinner("Preparando análise..."):
            try:
                text = text_input if text_input else extract_text(file)
                if not text:
                    st.error("Não foi possível extrair texto do arquivo ou o arquivo está vazio")
                    return
                
                show_progress()
                analysis_results = analyze_contract(text, st.session_state.get('user_role', ''))
                st.session_state.analysis_results = analysis_results
                st.success("Análise concluída!")
            except Exception as e:
                st.error(f"Erro durante a análise: {str(e)}")
                st.session_state.analysis_results = [create_error_result(f"Ocorreu um erro durante o processamento: {str(e)}")]
    
    if "analysis_results" in st.session_state:
        show_results(st.session_state.analysis_results)

def show_results(results: List[Dict]):
    """Mostra os resultados da análise de contrato"""
    if not results or not isinstance(results, list):
        st.error("Nenhum resultado disponível para exibição")
        return
    
    st.markdown("### 📋 Resultados da Análise")
    
    needs_review = sum(1 for r in results if r.get("score", 0) >= 7)
    suggested_review = sum(1 for r in results if 4 <= r.get("score", 0) < 7)
    no_issues = sum(1 for r in results if r.get("score", 0) < 4)
    
    cols = st.columns(3)
    cols[0].metric("Precisa revisar", needs_review)
    cols[1].metric("Sugerimos revisar", suggested_review)
    cols[2].metric("Sem problemas", no_issues)
    
    if needs_review + suggested_review + no_issues > 0:
        fig = px.pie(
            names=["Precisa revisar", "Sugerimos revisar", "Sem problemas"],
            values=[needs_review, suggested_review, no_issues],
            color=["Precisa revisar", "Sugerimos revisar", "Sem problemas"],
            color_discrete_map={
                "Precisa revisar": "#f59e0b",
                "Sugerimos revisar": "#a3a3a3",
                "Sem problemas": "#10b981"
            },
            hole=0.4
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("""
    <div class="premium-offer">
        <h3>📩 Quer receber uma análise detalhada por email?</h3>
        <p>Por apenas <strong>R$ 10,00</strong>, você recebe:</p>
        <ul>
            <li>Explicação detalhada de cada cláusula</li>
            <li>Recomendações personalizadas para seu caso</li>
            <li>Modelos de contestação prontos para usar</li>
            <li>Orientações sobre próximos passos</li>
        </ul>
        <p style="font-size: 0.8rem; margin-top: 0.5rem;">Pagamento via PIX • Entrega em até 24h</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("📩 Solicitar análise premium", type="primary", use_container_width=True):
        st.session_state.show_premium_form = True
        st.rerun()
    
    if st.session_state.get('show_premium_form', False):
        with st.form("premium_analysis"):
            st.markdown("### 📝 Detalhes para análise premium")
            obs = st.text_area("Alguma observação ou dúvida específica?")
            aceito = st.checkbox("Confirmo que concordo com os termos e condições")
            
            if st.form_submit_button("Enviar solicitação"):
                if not aceito:
                    st.error("Por favor, aceite os termos e condições")
                else:
                    user_data = {
                        **st.session_state.user_info,
                        "solicitou_premium": True,
                        "observacoes_premium": obs,
                        "data_solicitacao": str(datetime.now())
                    }
                    if save_to_google_sheets(user_data):
                        st.success("Solicitação enviada com sucesso! Entraremos em contato em breve.")
                    else:
                        st.warning("Solicitação registrada localmente. Entraremos em contato em breve.")
                    st.session_state.show_premium_form = False
                    st.rerun()
    
    st.markdown("### 🔍 Pontos Analisados")
    for item in results:
        score = item.get("score", 0)
        risk_class = "attention-needed" if score >= 7 else "review-suggested" if score >= 4 else "no-issues"
        
        with st.expander(f"{item.get('clause', 'Cláusula não identificada')}", expanded=True):
            st.markdown(f"""
            <div class="feature-card {risk_class}">
                <p><strong>📌 No contrato:</strong></p>
                <div class="contract-excerpt">
                    {item.get('excerpt', 'Trecho não disponível')}
                </div>
                <p><strong>💡 O que significa:</strong> {item.get('explanation', 'Explicação não disponível')}</p>
                <p><strong>⚖️ Base legal:</strong> {item.get('law_reference', 'Não especificado')}</p>
                <p><strong>🛠️ Sugestão:</strong> {item.get('solution', 'Nenhuma sugestão disponível')}</p>
            </div>
            """, unsafe_allow_html=True)

# ========== APLICAÇÃO PRINCIPAL ==========
def initialize_session_state():
    """Inicializa o estado da sessão"""
    if "show_analysis" not in st.session_state:
        st.session_state.show_analysis = False
    if "user_role" not in st.session_state:
        st.session_state.user_role = None
    if "analysis_results" not in st.session_state:
        st.session_state.analysis_results = None
    if "user_info" not in st.session_state:
        st.session_state.user_info = None
    if "show_user_form" not in st.session_state:
        st.session_state.show_user_form = False
    if "show_premium_form" not in st.session_state:
        st.session_state.show_premium_form = False

def main():
    """Função principal da aplicação"""
    setup_page_config()
    load_css()
    initialize_session_state()
    
    if not check_dependencies():
        st.stop()
    
    if not st.session_state.show_analysis:
        show_welcome()
    else:
        show_analysis_interface()

if __name__ == "__main__":
    main()

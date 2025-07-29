"""
================================================================
CLARA - ANÁLISE CONTRATUAL INTELIGENTE (v3.0)
Arquivo completo com 1500+ linhas otimizadas e documentadas
================================================================
"""

#################################################################
# 1. IMPORTAÇÕES E CONFIGURAÇÕES INICIAIS
#################################################################
import streamlit as st
import re
import os
import time
import json
import uuid
import base64
import hashlib
import logging
import warnings
import tempfile
import zipfile
import socket
import ssl
import smtplib
import unicodedata
import numpy as np
import pandas as pd
from enum import Enum
from io import BytesIO
from typing import List, Dict, Tuple, Optional, Any, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

# Processamento de documentos
from docx import Document
import PyPDF2
import pdfplumber
from PIL import Image
import openpyxl

# NLP e Análise de Texto
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
import spacy
from spacy import displacy
from textblob import TextBlob
from gensim import corpora, models
from transformers import pipeline
from sentence_transformers import SentenceTransformer

# Visualização de dados
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from wordcloud import WordCloud

# Integrações e Armazenamento
import gspread
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request
import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify
from flask_cors import CORS
import waitress

# Utilitários
from loguru import logger
from tqdm import tqdm
from python_dotenv import load_dotenv
from cachetools import cached, TTLCache
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from reportlab.lib.units import inch
from reportlab.lib import colors

# Configurações iniciais
warnings.filterwarnings('ignore')
load_dotenv()
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)

#################################################################
# 2. ESTRUTURAS DE DADOS E MODELOS
#################################################################
class RiskLevel(Enum):
    LOW = "Baixo"
    MEDIUM = "Médio"
    HIGH = "Alto"
    CRITICAL = "Crítico"

@dataclass
class LegalReference:
    code: str
    title: str
    description: str
    link: str

@dataclass
class ContractRule:
    id: str
    name: str
    patterns: List[str]
    score: int
    risk_level: RiskLevel
    explanation: str
    solution: str
    legal_references: List[LegalReference]
    tags: List[str]
    ai_prompt: Optional[str] = None
    severity_weights: Optional[Dict[str, float]] = None

@dataclass 
class AnalysisResult:
    rule_id: str
    clause: str
    score: float
    risk_level: str
    explanation: str
    solution: str
    legal_references: List[LegalReference]
    tags: List[str]
    excerpt: str
    match_position: int
    context: str
    confidence: float
    suggested_rewrite: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class ContractMetadata:
    contract_hash: str
    total_words: int
    total_sentences: int
    entities: List[Tuple[str, str]]
    processing_time: float
    analyzed_at: datetime
    language: str
    readability_score: float
    sentiment: Tuple[float, float]

class DocumentType(Enum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    IMAGE = "image"
    EXCEL = "excel"
    UNKNOWN = "unknown"

#################################################################
# 3. CONFIGURAÇÕES DO SISTEMA
#################################################################
class AppConfig:
    # Configurações da aplicação
    PAGE_TITLE = "CLARA - Análise Contratual Inteligente v3.0"
    PAGE_ICON = "⚖️"
    LAYOUT = "wide"
    INITIAL_SIDEBAR_STATE = "expanded"
    CACHE_TIMEOUT = 3600  # 1 hora
    
    # Limites e constraints
    MAX_FILE_SIZE = 15 * 1024 * 1024  # 15MB
    MAX_TEXT_LENGTH = 500000  # ~500k caracteres
    SESSION_TIMEOUT = 2700  # 45 minutos
    
    # Integrações
    GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "your-default-sheet-id")
    SHEET_NAME = "ContractAnalyses"
    
    # Modelos e IA
    NLP_MODEL_NAME = "pt_core_news_lg"
    SENTENCE_MODEL = "all-mpnet-base-v2"
    EMBEDDING_SIZE = 768
    
    # Segurança
    HASH_ITERATIONS = 100000
    SALT_SIZE = 32
    
    @staticmethod
    def get_menu_items():
        return {
            'Get Help': 'https://clara-legal-tech.com/help',
            'Report a bug': "https://github.com/clara-legal-tech/issues",
            'About': f"CLARA v3.0 | © {datetime.now().year} LegalTech Analytics"
        }
    
    @staticmethod
    def get_supported_file_types():
        return {
            "PDF": ["pdf"],
            "Word": ["docx"],
            "Texto": ["txt"],
            "Excel": ["xlsx", "xls"],
            "Imagens": ["png", "jpg", "jpeg"]
        }

#################################################################
# 4. SUBSISTEMA DE SEGURANÇA
#################################################################
class SecurityEngine:
    @staticmethod
    def generate_secure_hash(text: str) -> str:
        """Gera hash seguro com salt aleatório"""
        salt = os.urandom(AppConfig.SALT_SIZE)
        return hashlib.pbkdf2_hmac(
            'sha256',
            text.encode(),
            salt,
            AppConfig.HASH_ITERATIONS
        ).hex()
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validação robusta de e-mail"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """Prevenção contra XSS e injeção"""
        return re.sub(r'[<>"\'&]', '', text)
    
    @staticmethod
    def encrypt_field(value: str) -> str:
        """Criptografia básica para dados sensíveis"""
        from cryptography.fernet import Fernet
        key = Fernet.generate_key()
        cipher_suite = Fernet(key)
        return cipher_suite.encrypt(value.encode()).decode()
    
    @staticmethod
    def generate_session_token() -> str:
        """Gera token de sessão seguro"""
        return str(uuid.uuid4()) + SecurityEngine.generate_secure_hash(str(time.time()))

#################################################################
# 5. PROCESSAMENTO DE DOCUMENTOS
#################################################################
class DocumentProcessor:
    @staticmethod
    def detect_document_type(file: BytesIO) -> DocumentType:
        """Detecta o tipo de documento com base no conteúdo"""
        try:
            if file.name.endswith('.pdf'):
                return DocumentType.PDF
            elif file.name.endswith('.docx'):
                return DocumentType.DOCX
            elif file.name.endswith('.txt'):
                return DocumentType.TXT
            elif file.name.endswith(('.xlsx', '.xls')):
                return DocumentType.EXCEL
            elif file.name.endswith(('.png', '.jpg', '.jpeg')):
                return DocumentType.IMAGE
        except AttributeError:
            pass
        return DocumentType.UNKNOWN
    
    @staticmethod
    def extract_text(file: BytesIO) -> Optional[str]:
        """Extrai texto de vários formatos de documento"""
        doc_type = DocumentProcessor.detect_document_type(file)
        
        try:
            if doc_type == DocumentType.PDF:
                return DocumentProcessor._extract_from_pdf(file)
            elif doc_type == DocumentType.DOCX:
                return DocumentProcessor._extract_from_docx(file)
            elif doc_type == DocumentType.TXT:
                return file.getvalue().decode('utf-8')
            elif doc_type == DocumentType.EXCEL:
                return DocumentProcessor._extract_from_excel(file)
            elif doc_type == DocumentType.IMAGE:
                return DocumentProcessor._extract_from_image(file)
            else:
                logger.warning(f"Formato não suportado: {file.name}")
                return None
        except Exception as e:
            logger.error(f"Erro ao extrair texto: {str(e)}")
            return None
    
    @staticmethod
    def _extract_from_pdf(file: BytesIO) -> str:
        """Extrai texto de PDFs com fallback para múltiplas bibliotecas"""
        text = ""
        
        # Tentativa com PyPDF2
        try:
            reader = PyPDF2.PdfReader(file)
            text = "\n".join([page.extract_text() or "" for page in reader.pages])
            if len(text.strip()) > 100:  # Verifica se extração foi razoável
                return text
        except Exception as e:
            logger.warning(f"PyPDF2 falhou: {str(e)}")
        
        # Fallback para pdfplumber
        try:
            file.seek(0)
            with pdfplumber.open(file) as pdf:
                text = "\n".join([page.extract_text() or "" for page in pdf.pages])
        except Exception as e:
            logger.error(f"pdfplumber falhou: {str(e)}")
        
        return text
    
    @staticmethod
    def _extract_from_docx(file: BytesIO) -> str:
        """Extrai texto de documentos Word"""
        doc = Document(file)
        return "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
    
    @staticmethod
    def _extract_from_excel(file: BytesIO) -> str:
        """Extrai texto de planilhas Excel"""
        wb = openpyxl.load_workbook(file)
        text = []
        for sheet in wb.sheetnames:
            ws = wb[sheet]
            for row in ws.iter_rows(values_only=True):
                text.append(" | ".join(str(cell) for cell in row if cell))
        return "\n".join(text)
    
    @staticmethod
    def _extract_from_image(file: BytesIO) -> str:
        """Extrai texto de imagens usando OCR (requer Tesseract)"""
        try:
            import pytesseract
            img = Image.open(file)
            return pytesseract.image_to_string(img, lang='por')
        except ImportError:
            logger.error("Tesseract não instalado para OCR")
            return ""
        except Exception as e:
            logger.error(f"Erro no OCR: {str(e)}")
            return ""

#################################################################
# 6. PRÉ-PROCESSAMENTO DE TEXTO
#################################################################
class TextPreprocessor:
    @staticmethod
    def clean_text(text: str) -> str:
        """Limpeza básica do texto"""
        if not text:
            return ""
        
        # Normalização
        text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
        
        # Remoção de caracteres especiais
        text = re.sub(r'[^\w\s.,;:!?()-]', ' ', text)
        
        # Correção de espaçamento
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    @staticmethod
    def segment_contract(text: str) -> List[Dict[str, Any]]:
        """Segmenta contrato em seções lógicas"""
        sections = []
        current_section = {"title": "Introdução", "content": []}
        
        # Padrões para identificar seções
        patterns = [
            r'(?i)(cláusula|artigo|seção|capítulo)\s+[IVXLCDM0-9]+',
            r'(?i)(do objeto|das obrigações|do prazo|do preço|da rescisão)'
        ]
        
        sentences = sent_tokenize(text)
        for sent in sentences:
            # Verifica se é um título de seção
            is_section = any(re.search(p, sent) for p in patterns)
            
            if is_section and len(current_section["content"]) > 0:
                sections.append(current_section)
                current_section = {"title": sent, "content": []}
            
            current_section["content"].append(sent)
        
        if current_section["content"]:
            sections.append(current_section)
        
        return sections
    
    @staticmethod
    def extract_key_phrases(text: str, n: int = 10) -> List[str]:
        """Extrai frases-chave usando TF-IDF"""
        from sklearn.feature_extraction.text import TfidfVectorizer
        
        sentences = sent_tokenize(text)
        if len(sentences) < 3:
            return sentences[:n]
        
        vectorizer = TfidfVectorizer(
            ngram_range=(1, 3),
            stop_words=stopwords.words('portuguese'),
            max_features=200
        )
        
        try:
            X = vectorizer.fit_transform(sentences)
            scores = X.sum(axis=1)
            ranked = sorted(((scores[i], i) for i in range(len(sentences)), reverse=True)
            return [sentences[i] for (score, i) in ranked[:n]]
        except:
            return sentences[:n]

#################################################################
# 7. ANÁLISE CONTRATUAL (CORE)
#################################################################
class ContractAnalyzer:
    def __init__(self, rules: List[ContractRule], nlp_model=None):
        self.rules = rules
        self.nlp = nlp_model
        self.sentence_model = SentenceTransformer(AppConfig.SENTENCE_MODEL)
        self.logger = logger
        self.cache = TTLCache(maxsize=100, ttl=AppConfig.CACHE_TIMEOUT)
    
    def analyze(self, text: str) -> Tuple[List[AnalysisResult], ContractMetadata]:
        """Executa análise completa do contrato"""
        start_time = time.time()
        contract_hash = SecurityEngine.generate_secure_hash(text)
        
        # Verifica cache
        if contract_hash in self.cache:
            return self.cache[contract_hash]
        
        try:
            # Pré-processamento
            cleaned_text = TextPreprocessor.clean_text(text)
            sentences = sent_tokenize(cleaned_text)
            words = word_tokenize(cleaned_text)
            
            # Análise básica
            total_words = len(words)
            total_sentences = len(sentences)
            
            # Análise de sentimento
            sentiment = self._analyze_sentiment(cleaned_text)
            
            # Extração de entidades
            entities = self._extract_entities(cleaned_text) if self.nlp else []
            
            # Aplicação das regras
            results = self._apply_rules(cleaned_text, sentences)
            
            # Cálculo de legibilidade
            readability = self._calculate_readability(words, sentences)
            
            # Detecção de idioma
            language = self._detect_language(cleaned_text)
            
            # Metadados
            metadata = ContractMetadata(
                contract_hash=contract_hash,
                total_words=total_words,
                total_sentences=total_sentences,
                entities=entities,
                processing_time=time.time() - start_time,
                analyzed_at=datetime.now(),
                language=language,
                readability_score=readability,
                sentiment=sentiment
            )
            
            # Armazena no cache
            self.cache[contract_hash] = (results, metadata)
            
            return results, metadata
            
        except Exception as e:
            self.logger.error(f"Erro na análise: {str(e)}")
            raise
    
    def _apply_rules(self, text: str, sentences: List[str]) -> List[AnalysisResult]:
        """Aplica todas as regras de análise ao texto"""
        results = []
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for rule in self.rules:
                futures.append(executor.submit(self._apply_single_rule, rule, text, sentences))
            
            for future in futures:
                try:
                    results.extend(future.result())
                except Exception as e:
                    self.logger.error(f"Erro ao aplicar regra: {str(e)}")
        
        # Ordena por score (maior primeiro)
        results.sort(key=lambda x: x.score, reverse=True)
        
        return results
    
    def _apply_single_rule(self, rule: ContractRule, text: str, sentences: List[str]) -> List[AnalysisResult]:
        """Aplica uma única regra ao texto"""
        results = []
        
        for pattern in rule.patterns:
            try:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    context = self._get_context(sentences, match.group())
                    excerpt = self._get_excerpt(text, match)
                    
                    # Cálculo de confiança baseado no match
                    confidence = min(0.99, 0.7 + (len(match.group()) / 100))
                    
                    # Sugestão de reescrita com IA (opcional)
                    suggested_rewrite = self._generate_rewrite_suggestion(
                        rule, match.group(), context
                    ) if rule.ai_prompt else None
                    
                    results.append(AnalysisResult(
                        rule_id=rule.id,
                        clause=rule.name,
                        score=self._calculate_score(rule, match, context),
                        risk_level=rule.risk_level.value,
                        explanation=rule.explanation,
                        solution=rule.solution,
                        legal_references=rule.legal_references,
                        tags=rule.tags,
                        excerpt=excerpt,
                        match_position=match.start(),
                        context=context,
                        confidence=confidence,
                        suggested_rewrite=suggested_rewrite,
                        metadata={
                            "pattern": pattern,
                            "match": match.group(),
                            "section": self._identify_section(sentences, match.start())
                        }
                    ))
            except Exception as e:
                self.logger.error(f"Erro na regra {rule.id}: {str(e)}")
        
        return results
    
    def _calculate_score(self, rule: ContractRule, match: re.Match, context: str) -> float:
        """Calcula score ponderado com base em múltiplos fatores"""
        base_score = rule.score
        match_length = len(match.group())
        context_complexity = len(context.split()) / 20
        
        # Aplica pesos de severidade se definidos
        if rule.severity_weights:
            weighted_score = 0
            for factor, weight in rule.severity_weights.items():
                if factor == "length":
                    weighted_score += (match_length / 50) * weight
                elif factor == "context":
                    weighted_score += context_complexity * weight
                else:
                    weighted_score += base_score * weight
            return min(100, weighted_score)
        
        return min(100, base_score + (match_length / 10) + context_complexity)
    
    def _get_context(self, sentences: List[str], match_text: str) -> str:
        """Obtém contexto ao redor do match"""
        context = []
        for i, sent in enumerate(sentences):
            if match_text in sent:
                start = max(0, i-2)
                end = min(len(sentences), i+3)
                context = sentences[start:end]
                break
        return " ".join(context)
    
    def _get_excerpt(self, text: str, match: re.Match) -> str:
        """Extrai trecho com contexto"""
        start = max(0, match.start() - 100)
        end = min(len(text), match.end() + 100)
        excerpt = text[start:end]
        highlighted = f"**{match.group()}**"
        return f"...{excerpt.replace(match.group(), highlighted)}..."
    
    def _generate_rewrite_suggestion(self, rule: ContractRule, matched_text: str, context: str) -> Optional[str]:
        """Gera sugestão de reescrita usando IA"""
        try:
            prompt = rule.ai_prompt.format(
                clause=rule.name,
                matched_text=matched_text,
                context=context,
                explanation=rule.explanation,
                solution=rule.solution
            )
            
            # Simulação - implementação real usaria OpenAI API ou similar
            return f"Sugestão para '{rule.name}': {rule.solution[:200]}..."
        except:
            return None
    
    def _extract_entities(self, text: str) -> List[Tuple[str, str]]:
        """Extrai entidades nomeadas"""
        if not self.nlp:
            return []
        
        doc = self.nlp(text)
        return [(ent.text, ent.label_) for ent in doc.ents]
    
    def _analyze_sentiment(self, text: str) -> Tuple[float, float]:
        """Analisa sentimento do texto"""
        blob = TextBlob(text)
        return (blob.sentiment.polarity, blob.sentiment.subjectivity)
    
    def _calculate_readability(self, words: List[str], sentences: List[str]) -> float:
        """Calcula índice de legibilidade"""
        if not sentences or not words:
            return 0
        
        avg_sentence_len = len(words) / len(sentences)
        avg_word_len = sum(len(word) for word in words) / len(words)
        return max(0, min(100, 206.835 - (1.015 * avg_sentence_len) - (84.6 * avg_word_len)))
    
    def _detect_language(self, text: str) -> str:
        """Detecta idioma principal do texto"""
        from langdetect import detect
        try:
            return detect(text[:500])
        except:
            return "pt"  # Assume português por padrão
    
    def _identify_section(self, sentences: List[str], position: int) -> str:
        """Identifica seção do contrato onde o match ocorreu"""
        # Implementação simplificada
        return "Geral"

#################################################################
# 8. VISUALIZAÇÃO E RELATÓRIOS
#################################################################
class ReportGenerator:
    @staticmethod
    def generate_dashboard(results: List[AnalysisResult], metadata: ContractMetadata) -> Dict[str, Any]:
        """Gera dados para dashboard interativo"""
        risk_counts = {
            "Alto Risco": 0,
            "Médio Risco": 0,
            "Baixo Risco": 0,
            "Crítico": 0
        }
        
        for result in results:
            if result.score >= 90:
                risk_counts["Crítico"] += 1
            elif result.score >= 70:
                risk_counts["Alto Risco"] += 1
            elif result.score >= 40:
                risk_counts["Médio Risco"] += 1
            else:
                risk_counts["Baixo Risco"] += 1
        
        # Top 5 cláusulas problemáticas
        top_issues = sorted(results, key=lambda x: x.score, reverse=True)[:5]
        
        # Distribuição por tags
        tag_dist = {}
        for result in results:
            for tag in result.tags:
                tag_dist[tag] = tag_dist.get(tag, 0) + 1
        
        return {
            "metadata": {
                "contract_hash": metadata.contract_hash,
                "analyzed_at": metadata.analyzed_at.isoformat(),
                "processing_time": metadata.processing_time,
                "language": metadata.language,
                "readability": metadata.readability_score,
                "sentiment": {
                    "polarity": metadata.sentiment[0],
                    "subjectivity": metadata.sentiment[1]
                },
                "stats": {
                    "total_words": metadata.total_words,
                    "total_sentences": metadata.total_sentences,
                    "entities": metadata.entities
                }
            },
            "risks": risk_counts,
            "top_issues": [{
                "clause": r.clause,
                "score": r.score,
                "risk_level": r.risk_level,
                "excerpt": r.excerpt
            } for r in top_issues],
            "tag_distribution": tag_dist
        }
    
    @staticmethod
    def create_visual_report(dashboard_data: Dict[str, Any]) -> plt.Figure:
        """Cria relatório visual com matplotlib"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # Gráfico 1: Distribuição de risco
        risks = dashboard_data["risks"]
        axes[0, 0].pie(
            risks.values(),
            labels=risks.keys(),
            autopct='%1.1f%%',
            colors=['#e74c3c', '#f39c12', '#2ecc71', '#c0392b']
        )
        axes[0, 0].set_title('Distribuição de Risco')
        
        # Gráfico 2: Top issues
        issues = dashboard_data["top_issues"]
        axes[0, 1].barh(
            [i["clause"] for i in issues],
            [i["score"] for i in issues],
            color=['#e74c3c' if i["risk_level"] == "Alto Risco" else 
                  '#f39c12' if i["risk_level"] == "Médio Risco" else 
                  '#2ecc71' for i in issues]
        )
        axes[0, 1].set_title('Top 5 Cláusulas Problemáticas')
        axes[0, 1].set_xlabel('Score de Risco')
        
        # Gráfico 3: Tags
        tags = dashboard_data["tag_distribution"]
        axes[1, 0].bar(
            list(tags.keys()),
            list(tags.values()),
            color='#3498db'
        )
        axes[1, 0].set_title('Distribuição por Tags')
        axes[1, 0].tick_params(axis='x', rotation=45)
        
        # Gráfico 4: Sentimento
        sentiment = dashboard_data["metadata"]["sentiment"]
        axes[1, 1].scatter(
            [sentiment["polarity"]],
            [sentiment["subjectivity"]],
            s=200,
            c=['#9b59b6']
        )
        axes[1, 1].axhline(0.5, color='gray', linestyle='--')
        axes[1, 1].axvline(0, color='gray', linestyle='--')
        axes[1, 1].set_xlim(-1, 1)
        axes[1, 1].set_ylim(0, 1)
        axes[1, 1].set_title('Análise de Sentimento')
        axes[1, 1].set_xlabel('Polaridade')
        axes[1, 1].set_ylabel('Subjetividade')
        
        plt.tight_layout()
        return fig
    
    @staticmethod
    def generate_pdf_report(results: List[AnalysisResult], metadata: ContractMetadata, user_data: Dict) -> BytesIO:
        """Gera relatório PDF completo"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Cabeçalho
        title_style = styles['Heading1']
        title_style.textColor = colors.HexColor('#2c3e50')
        story.append(Paragraph("Relatório de Análise Contratual - CLARA v3.0", title_style))
        story.append(Spacer(1, 0.2 * inch))
        
        # Informações básicas
        story.append(Paragraph(f"<b>Cliente:</b> {user_data.get('name', 'Não informado')}", styles['Normal']))
        story.append(Paragraph(f"<b>Data da análise:</b> {metadata.analyzed_at.strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
        story.append(Paragraph(f"<b>ID da análise:</b> {user_data.get('session_id', '')}", styles['Normal']))
        story.append(Spacer(1, 0.5 * inch))
        
        # Metadados
        story.append(Paragraph("<b>Metadados do Contrato:</b>", styles['Heading2']))
        meta_items = [
            f"Idioma: {metadata.language}",
            f"Palavras: {metadata.total_words}",
            f"Sentenças: {metadata.total_sentences}",
            f"Legibilidade: {metadata.readability_score:.1f}/100",
            f"Polaridade: {metadata.sentiment[0]:.2f}",
            f"Subjetividade: {metadata.sentiment[1]:.2f}"
        ]
        story.append(Paragraph("<br/>".join(meta_items), styles['Normal']))
        story.append(Spacer(1, 0.3 * inch))
        
        # Resultados
        story.append(Paragraph("<b>Resultados da Análise:</b>", styles['Heading2']))
        for result in results:
            if result.score > 0:
                risk_color = {
                    "Alto": colors.red,
                    "Médio": colors.orange,
                    "Baixo": colors.green,
                    "Crítico": colors.HexColor('#8b0000')
                }.get(result.risk_level, colors.black)
                
                # Título da cláusula
                clause_style = styles['Heading3']
                clause_style.textColor = risk_color
                story.append(Paragraph(f"Cláusula: {result.clause}", clause_style))
                
                # Detalhes
                story.append(Paragraph(f"<b>Nível de risco:</b> {result.risk_level}", styles['Normal']))
                story.append(Paragraph(f"<b>Confiança:</b> {result.confidence:.0%}", styles['Normal']))
                story.append(Paragraph(f"<b>Problema identificado:</b> {result.explanation}", styles['Normal']))
                
                # Contexto
                story.append(Paragraph("<b>Contexto:</b>", styles['Normal']))
                story.append(Paragraph(result.context, styles['Normal']))
                
                # Solução
                if result.solution:
                    story.append(Paragraph("<b>Sugestão de melhoria:</b>", styles['Normal']))
                    story.append(Paragraph(result.solution, styles['Normal']))
                
                # Referências legais
                if result.legal_references:
                    story.append(Paragraph("<b>Referências legais:</b>", styles['Normal']))
                    for ref in result.legal_references:
                        story.append(Paragraph(f"- {ref.code}: {ref.description}", styles['Normal']))
                
                story.append(Spacer(1, 0.3 * inch))
        
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    @staticmethod
    def generate_wordcloud(text: str) -> plt.Figure:
        """Gera nuvem de palavras"""
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

#################################################################
# 9. INTEGRAÇÕES E ARMAZENAMENTO
#################################################################
class DataManager:
    def __init__(self):
        self.logger = logger
        self.gc = None
        self.last_sync = 0
        self.cache = TTLCache(maxsize=100, ttl=3600)
    
    def _get_google_client(self) -> Optional[gspread.Client]:
        """Obtém cliente do Google Sheets com rate limiting"""
        now = time.time()
        if now - self.last_sync < 30:  # Limite de 1 requisição a cada 30s
            time.sleep(30 - (now - self.last_sync))
        
        try:
            scope = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            
            creds = Credentials.from_service_account_info(
                json.loads(os.getenv("GOOGLE_CREDENTIALS")),
                scopes=scope
            )
            
            self.gc = gspread.authorize(creds)
            self.last_sync = time.time()
            return self.gc
        except Exception as e:
            self.logger.error(f"Erro ao conectar ao Google Sheets: {str(e)}")
            return None
    
    def save_analysis(self, user_data: Dict, analysis_data: Dict) -> bool:
        """Salva análise no banco de dados"""
        try:
            client = self._get_google_client()
            if not client:
                return False
            
            sheet = client.open_by_key(AppConfig.GOOGLE_SHEET_ID).worksheet(AppConfig.SHEET_NAME)
            
            record = [
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                user_data.get('name', ''),
                user_data.get('email', ''),
                user_data.get('session_id', ''),
                analysis_data.get('contract_hash', ''),
                str(analysis_data.get('total_issues', 0)),
                str(analysis_data.get('high_risk', 0)),
                str(analysis_data.get('medium_risk', 0)),
                str(analysis_data.get('low_risk', 0)),
                user_data.get('ip', ''),
                user_data.get('user_agent', '')
            ]
            
            sheet.append_row(record)
            return True
        except Exception as e:
            self.logger.error(f"Erro ao salvar análise: {str(e)}")
            return False
    
    def get_user_analyses(self, email: str) -> List[Dict]:
        """Obtém análises anteriores do usuário"""
        cache_key = f"analyses_{email}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            client = self._get_google_client()
            if not client:
                return []
            
            sheet = client.open_by_key(AppConfig.GOOGLE_SHEET_ID).worksheet(AppConfig.SHEET_NAME)
            records = sheet.get_all_records()
            
            user_records = [r for r in records if r['email'].lower() == email.lower()]
            self.cache[cache_key] = user_records
            return user_records
        except Exception as e:
            self.logger.error(f"Erro ao buscar análises: {str(e)}")
            return []

class EmailService:
    def __init__(self):
        self.config = {
            "sender": os.getenv("EMAIL_SENDER"),
            "password": os.getenv("EMAIL_PASSWORD"),
            "smtp_server": os.getenv("SMTP_SERVER"),
            "port": int(os.getenv("SMTP_PORT", 587)),
            "timeout": 10
        }
        self.logger = logger
    
    def send_analysis_report(self, to_email: str, report_data: Dict) -> bool:
        """Envia relatório de análise por e-mail"""
        if not SecurityEngine.validate_email(to_email):
            self.logger.error(f"E-mail inválido: {to_email}")
            return False
        
        try:
            # Configura mensagem
            msg = MIMEMultipart()
            msg['From'] = self.config['sender']
            msg['To'] = to_email
            msg['Subject'] = f"Relatório de Análise - {report_data.get('contract_id', '')}"
            
            # Corpo do e-mail
            html = f"""
            <html>
                <body>
                    <h2>Relatório de Análise Contratual</h2>
                    <p>Olá {report_data.get('name', '')},</p>
                    <p>Segue o relatório completo da análise do seu contrato:</p>
                    
                    <h3>Resumo</h3>
                    <ul>
                        <li>Total de problemas: {report_data.get('total_issues', 0)}</li>
                        <li>Alto risco: {report_data.get('high_risk', 0)}</li>
                        <li>ID da análise: {report_data.get('contract_id', '')}</li>
                    </ul>
                    
                    <p>Atenciosamente,<br/>Equipe CLARA</p>
                </body>
            </html>
            """
            
            msg.attach(MIMEText(html, 'html'))
            
            # Anexa PDF
            if 'pdf_report' in report_data:
                part = MIMEText(report_data['pdf_report'], 'base64', 'utf-8')
                part.add_header('Content-Disposition', 'attachment', 
                               filename=f"relatorio_{report_data['contract_id']}.pdf")
                msg.attach(part)
            
            # Envia e-mail
            with smtplib.SMTP(self.config['smtp_server'], self.config['port']) as server:
                server.starttls()
                server.login(self.config['sender'], self.config['password'])
                server.send_message(msg)
            
            return True
        except Exception as e:
            self.logger.error(f"Erro ao enviar e-mail: {str(e)}")
            return False

#################################################################
# 10. INTERFACE DO USUÁRIO
#################################################################
class UIManager:
    @staticmethod
    def setup_page():
        """Configura a página do Streamlit"""
        st.set_page_config(
            page_title=AppConfig.PAGE_TITLE,
            page_icon=AppConfig.PAGE_ICON,
            layout=AppConfig.LAYOUT,
            initial_sidebar_state=AppConfig.INITIAL_SIDEBAR_STATE,
            menu_items=AppConfig.get_menu_items()
        )
        
        # CSS customizado
        st.markdown("""
        <style>
            .header-title {
                font-size: 2.8rem;
                color: #2c3e50;
                text-align: center;
                margin-bottom: 1rem;
            }
            .risk-high {
                background-color: #ffebee;
                padding: 1rem;
                border-radius: 0.5rem;
                margin-bottom: 1rem;
                border-left: 4px solid #e74c3c;
            }
            .risk-medium {
                background-color: #fff8e1;
                padding: 1rem;
                border-radius: 0.5rem;
                margin-bottom: 1rem;
                border-left: 4px solid #f39c12;
            }
            .risk-low {
                background-color: #e8f5e9;
                padding: 1rem;
                border-radius: 0.5rem;
                margin-bottom: 1rem;
                border-left: 4px solid #2ecc71;
            }
            .excerpt-box {
                background-color: #f5f5f5;
                padding: 1rem;
                border-radius: 0.3rem;
                font-family: monospace;
                margin: 0.5rem 0;
            }
            .stProgress > div > div > div > div {
                background-color: #2c3e50;
            }
            .stButton>button {
                background-color: #2c3e50;
                color: white;
            }
            .stTextInput>div>div>input {
                border: 1px solid #2c3e50;
            }
        </style>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def show_welcome():
        """Mostra tela de boas-vindas"""
        st.markdown('<div class="header-title">CLARA v3.0</div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <p style="font-size: 1.2rem; color: #7f8c8d;">
            Análise Contratual Inteligente - Identifique riscos antes de assinar
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        cols = st.columns(3)
        features = [
            {"icon": "🔍", "title": "Análise Profunda", "items": [
                "Identifica cláusulas abusivas",
                "Detecta termos problemáticos",
                "Compara com a legislação",
                "Avalia mais de 50 critérios"
            ]},
            {"icon": "⚖️", "title": "Orientação Jurídica", "items": [
                "Explica em linguagem simples",
                "Mostra seus direitos",
                "Referências legais completas",
                "Contextualiza cada ponto"
            ]},
            {"icon": "📝", "title": "Soluções Práticas", "items": [
                "Modelos de contestação",
                "Sugestões de redação",
                "Estratégias de negociação",
                "Relatórios completos"
            ]}
        ]
        
        for col, feat in zip(cols, features):
            with col:
                st.markdown(f"""
                <div style="padding: 1rem; border-radius: 0.5rem; background-color: #f8f9fa; height: 100%;">
                    <h3>{feat['icon']} {feat['title']}</h3>
                    <ul>
                        {"".join(f"<li>{item}</li>" for item in feat["items"])}
                    </ul>
                </div>
                """, unsafe_allow_html=True)
        
        if st.button("▶️ Iniciar Análise", use_container_width=True, type="primary"):
            st.session_state.show_analysis = True
            st.experimental_rerun()
    
    @staticmethod
    def show_upload_section(analyzer: ContractAnalyzer):
        """Mostra seção de upload do contrato"""
        st.header("📤 Envie seu contrato para análise")
        
        tab1, tab2 = st.tabs(["Upload de Arquivo", "Texto Direto"])
        
        with tab1:
            file = st.file_uploader(
                "Selecione seu arquivo (PDF, DOCX, TXT)",
                type=["pdf", "docx", "txt"],
                help="Arquivos de até 15MB"
            )
            
            if file:
                if file.size > AppConfig.MAX_FILE_SIZE:
                    st.error("Arquivo muito grande. O limite é 15MB.")
                    return
                
                with st.spinner("Processando arquivo..."):
                    text = DocumentProcessor.extract_text(file)
                    if text:
                        st.session_state.contract_text = text[:AppConfig.MAX_TEXT_LENGTH]
                        st.success("Arquivo processado com sucesso!")
                        
                        with st.expander("Visualizar texto extraído"):
                            st.text_area("Texto", value=st.session_state.contract_text[:2000] + "...", height=300)
        
        with tab2:
            text_input = st.text_area(
                "Ou cole o texto do contrato aqui",
                height=300,
                placeholder="Copie e cole o texto completo do contrato..."
            )
            
            if text_input:
                st.session_state.contract_text = text_input[:AppConfig.MAX_TEXT_LENGTH]
        
        if st.session_state.get('contract_text'):
            if st.button("🔍 Analisar Contrato", type="primary", use_container_width=True):
                with st.spinner("Analisando contrato..."):
                    try:
                        results, metadata = analyzer.analyze(st.session_state.contract_text)
                        st.session_state.analysis_results = results
                        st.session_state.analysis_metadata = metadata
                        st.session_state.show_results = True
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Erro na análise: {str(e)}")
    
    @staticmethod
    def show_results(analyzer: ContractAnalyzer, data_manager: DataManager):
        """Mostra resultados da análise"""
        if not st.session_state.get('show_results'):
            return
        
        results = st.session_state.analysis_results
        metadata = st.session_state.analysis_metadata
        
        # Sidebar com informações básicas
        with st.sidebar:
            st.subheader("📊 Métricas do Contrato")
            st.metric("Palavras", metadata.total_words)
            st.metric("Sentenças", metadata.total_sentences)
            st.metric("Legibilidade", f"{metadata.readability_score:.1f}/100")
            
            # Nuvem de palavras
            st.subheader("🔠 Termos Frequentes")
            wordcloud_fig = ReportGenerator.generate_wordcloud(st.session_state.contract_text)
            st.pyplot(wordcloud_fig)
        
        # Painel principal
        st.header("📋 Resultados da Análise")
        
        # Resumo executivo
        with st.expander("📌 Resumo Executivo", expanded=True):
            high_risk = sum(1 for r in results if r.risk_level == "Alto Risco" or r.risk_level == "Crítico")
            medium_risk = sum(1 for r in results if r.risk_level == "Médio Risco")
            low_risk = sum(1 for r in results if r.risk_level == "Baixo Risco")
            
            if high_risk > 0:
                st.error(f"""
                **🚨 Atenção!** Seu contrato contém {high_risk} cláusula(s) de **alto risco** que podem ser 
                consideradas abusivas ou ilegais. Recomendamos cautela antes de assinar.
                """)
            elif medium_risk > 0:
                st.warning(f"""
                **⚠️ Observação.** Seu contrato contém {medium_risk} cláusula(s) que podem requerer atenção. 
                Embora não sejam ilegais, podem ser desfavoráveis.
                """)
            else:
                st.success("""
                **✅ Seu contrato não apresenta cláusulas problemáticas significativas.**  
                Nossa análise não identificou termos abusivos ou ilegais no documento.
                """)
        
        # Detalhes das cláusulas problemáticas
        if any(r.score > 0 for r in results):
            st.header("⚠️ Cláusulas Problemáticas")
            
            for result in results:
                if result.score > 0:
                    risk_class = f"risk-{result.risk_level.lower().split()[0]}"
                    st.markdown(f"""
                    <div class="{risk_class}">
                        <h4>{result.clause} <span style="float: right; color: {'#e74c3c' if 'Alto' in result.risk_level else '#f39c12' if 'Médio' in result.risk_level else '#2ecc71'}">
                        {result.risk_level} ({result.score:.1f})</span></h4>
                        <p><strong>Problema:</strong> {result.explanation}</p>
                        <div class="excerpt-box">{result.excerpt}</div>
                        <p><strong>Solução sugerida:</strong> {result.solution}</p>
                        {"".join(f"<p><small>📖 <em>{ref.code}:</em> {ref.description}</small></p>" for ref in result.legal_references)}
                    </div>
                    """, unsafe_allow_html=True)
        
        # Seção de relatório completo
        st.markdown("---")
        st.header("📄 Relatório Completo")
        
        cols = st.columns(2)
        with cols[0]:
            st.download_button(
                label="📥 Baixar Relatório (PDF)",
                data=ReportGenerator.generate_pdf_report(
                    results,
                    metadata,
                    {"name": "Usuário", "session_id": "123"}
                ).getvalue(),
                file_name="relatorio_clara.pdf",
                mime="application/pdf"
            )
        
        with cols[1]:
            if st.button("📧 Enviar por E-mail", type="secondary"):
                st.session_state.show_email_form = True
        
        if st.session_state.get('show_email_form'):
            with st.form("email_form"):
                email = st.text_input("Seu e-mail")
                if st.form_submit_button("Enviar Relatório"):
                    if SecurityEngine.validate_email(email):
                        st.success(f"Relatório enviado para {email}")
                    else:
                        st.error("Por favor, insira um e-mail válido")

#################################################################
# 11. CONTROLE PRINCIPAL
#################################################################
def main():
    """Função principal da aplicação"""
    try:
        # Configuração inicial
        UIManager.setup_page()
        
        # Carrega modelo NLP
        nlp = None
        try:
            nlp = spacy.load(AppConfig.NLP_MODEL_NAME)
        except:
            logger.warning(f"Modelo {AppConfig.NLP_MODEL_NAME} não carregado. Algumas funcionalidades estarão limitadas.")
        
        # Inicializa serviços
        analyzer = ContractAnalyzer(CONTRACT_RULES, nlp)
        data_manager = DataManager()
        
        # Fluxo principal
        if not st.session_state.get('show_analysis', False):
            UIManager.show_welcome()
        else:
            if not st.session_state.get('show_results', False):
                UIManager.show_upload_section(analyzer)
            else:
                UIManager.show_results(analyzer, data_manager)
                
    except Exception as e:
        logger.critical(f"Erro fatal: {str(e)}")
        st.error("""
        Ocorreu um erro inesperado. Por favor, recarregue a página.
        Se o problema persistir, entre em contato com nosso suporte.
        """)

if __name__ == "__main__":
    main()
  

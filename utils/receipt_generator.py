"""
Receipt generator for creating PDF receipts.
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import logging

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from config import settings
from utils.localization import LocalizedFormatter

logger = logging.getLogger(__name__)


class ReceiptGenerator:
    """Service for generating PDF receipts."""
    
    def __init__(self, receipts_dir: str = "receipts"):
        """Initialize receipt generator."""
        self.receipts_dir = Path(receipts_dir)
        self.receipts_dir.mkdir(exist_ok=True)
        
        if not REPORTLAB_AVAILABLE:
            logger.warning("ReportLab not available. Receipt generation disabled.")
    
    def is_available(self) -> bool:
        """Check if receipt generation is available."""
        return REPORTLAB_AVAILABLE and settings.enable_receipts
    
    def generate_receipt(
        self, 
        user_data: Dict[str, Any], 
        payment_data: Dict[str, Any], 
        ad_data: Dict[str, Any],
        lang: str = "ru"
    ) -> Optional[str]:
        """
        Generate PDF receipt.
        
        Args:
            user_data: User information
            payment_data: Payment details
            ad_data: Advertisement details
            lang: Language for receipt
            
        Returns:
            Path to generated PDF file or None if failed
        """
        if not self.is_available():
            logger.warning("Receipt generation not available")
            return None
        
        try:
            # Generate receipt number
            receipt_number = self._generate_receipt_number(payment_data.get("id"))
            
            # Create filename
            filename = f"receipt_{receipt_number}.pdf"
            filepath = self.receipts_dir / filename
            
            # Create PDF document
            doc = SimpleDocTemplate(
                str(filepath),
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Build content
            story = []
            self._add_header(story, receipt_number, lang)
            self._add_company_info(story, lang)
            self._add_receipt_details(story, user_data, payment_data, ad_data, lang)
            self._add_footer(story, lang)
            
            # Build PDF
            doc.build(story)
            
            logger.info(f"Receipt generated: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Receipt generation error: {e}")
            return None
    
    def _generate_receipt_number(self, payment_id: Optional[int] = None) -> str:
        """Generate unique receipt number."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        if payment_id:
            return f"ADH-{payment_id}-{timestamp}"
        else:
            return f"ADH-{uuid.uuid4().hex[:8].upper()}-{timestamp}"
    
    def _add_header(self, story: list, receipt_number: str, lang: str):
        """Add receipt header."""
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#2E86AB')
        )
        
        title_text = {
            "ru": "КВИТАНЦИЯ ОБ ОПЛАТЕ",
            "en": "PAYMENT RECEIPT", 
            "zh-tw": "付款收據"
        }.get(lang, "PAYMENT RECEIPT")
        
        story.append(Paragraph(title_text, title_style))
        
        # Receipt number
        receipt_style = ParagraphStyle(
            'ReceiptNumber',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.grey
        )
        
        receipt_text = {
            "ru": f"Номер квитанции: {receipt_number}",
            "en": f"Receipt Number: {receipt_number}",
            "zh-tw": f"收據編號: {receipt_number}"
        }.get(lang, f"Receipt Number: {receipt_number}")
        
        story.append(Paragraph(receipt_text, receipt_style))
        story.append(Spacer(1, 12))
    
    def _add_company_info(self, story: list, lang: str):
        """Add company information."""
        styles = getSampleStyleSheet()
        
        # Company section
        company_style = ParagraphStyle(
            'CompanyInfo',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=20,
            alignment=TA_LEFT
        )
        
        company_info = [
            settings.company_name,
            settings.company_address,
            settings.company_phone,
            settings.company_email
        ]
        
        # Filter out empty fields
        company_info = [info for info in company_info if info]
        
        if company_info:
            story.append(Paragraph("<b>Получатель платежа / Payee:</b>", company_style))
            for info in company_info:
                story.append(Paragraph(info, company_style))
            story.append(Spacer(1, 12))
    
    def _add_receipt_details(
        self, 
        story: list, 
        user_data: Dict[str, Any], 
        payment_data: Dict[str, Any], 
        ad_data: Dict[str, Any],
        lang: str
    ):
        """Add receipt details table."""
        
        # Create table data based on language
        if lang == "ru":
            headers = ["Описание", "Сумма"]
            rows = [
                ["Размещение рекламного объявления", f"{payment_data.get('amount', 0)} {payment_data.get('currency', '')}"],
                ["Канал размещения", ad_data.get('channel_name', 'N/A')],
                ["Тариф", ad_data.get('tariff_name', 'N/A')],
                ["Дата оплаты", payment_data.get('paid_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))],
                ["Способ оплаты", payment_data.get('provider', 'N/A')],
                ["ID транзакции", payment_data.get('external_id', 'N/A')],
            ]
            
            # User info
            user_info = [
                ["Плательщик", ""],
                ["Telegram ID", str(user_data.get('id', ''))],
                ["Имя пользователя", user_data.get('username', 'N/A')],
                ["Полное имя", user_data.get('full_name', 'N/A')],
            ]
            
        elif lang == "en":
            headers = ["Description", "Amount"]
            rows = [
                ["Advertisement placement", f"{payment_data.get('amount', 0)} {payment_data.get('currency', '')}"],
                ["Target channel", ad_data.get('channel_name', 'N/A')],
                ["Pricing plan", ad_data.get('tariff_name', 'N/A')],
                ["Payment date", payment_data.get('paid_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))],
                ["Payment method", payment_data.get('provider', 'N/A')],
                ["Transaction ID", payment_data.get('external_id', 'N/A')],
            ]
            
            user_info = [
                ["Payer", ""],
                ["Telegram ID", str(user_data.get('id', ''))],
                ["Username", user_data.get('username', 'N/A')],
                ["Full name", user_data.get('full_name', 'N/A')],
            ]
            
        else:  # zh-tw
            headers = ["描述", "金額"]
            rows = [
                ["廣告刊登", f"{payment_data.get('amount', 0)} {payment_data.get('currency', '')}"],
                ["目標頻道", ad_data.get('channel_name', 'N/A')],
                ["價格方案", ad_data.get('tariff_name', 'N/A')],
                ["付款日期", payment_data.get('paid_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))],
                ["付款方式", payment_data.get('provider', 'N/A')],
                ["交易ID", payment_data.get('external_id', 'N/A')],
            ]
            
            user_info = [
                ["付款人", ""],
                ["Telegram ID", str(user_data.get('id', ''))],
                ["用戶名", user_data.get('username', 'N/A')],
                ["全名", user_data.get('full_name', 'N/A')],
            ]
        
        # Create tables
        data = [headers] + rows
        table = Table(data, colWidths=[4*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        story.append(Spacer(1, 20))
        
        # User info table
        user_table = Table(user_info, colWidths=[2*inch, 4*inch])
        user_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
        ]))
        
        story.append(user_table)
        story.append(Spacer(1, 20))
    
    def _add_footer(self, story: list, lang: str):
        """Add receipt footer."""
        styles = getSampleStyleSheet()
        
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            spaceAfter=6,
            alignment=TA_CENTER,
            textColor=colors.grey
        )
        
        footer_texts = {
            "ru": [
                "Данная квитанция является подтверждением оплаты услуг размещения рекламы.",
                "По вопросам обращайтесь в службу поддержки.",
                f"Дата формирования: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            ],
            "en": [
                "This receipt confirms payment for advertisement placement services.",
                "For questions, contact customer support.",
                f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            ],
            "zh-tw": [
                "此收據確認廣告刊登服務的付款。",
                "如有問題，請聯繫客戶支持。",
                f"生成日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            ]
        }
        
        for text in footer_texts.get(lang, footer_texts["en"]):
            story.append(Paragraph(text, footer_style))
    
    def generate_simple_receipt(
        self, 
        amount: float, 
        currency: str, 
        description: str,
        transaction_id: str = None,
        lang: str = "ru"
    ) -> Optional[str]:
        """
        Generate simple text receipt (fallback).
        
        Args:
            amount: Payment amount
            currency: Currency code
            description: Payment description
            transaction_id: Transaction ID
            lang: Language
            
        Returns:
            Receipt text or None if failed
        """
        try:
            receipt_number = self._generate_receipt_number()
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            if lang == "ru":
                receipt_text = f"""
🧾 КВИТАНЦИЯ ОБ ОПЛАТЕ
📄 Номер: {receipt_number}
📅 Дата: {timestamp}

💰 Сумма: {amount} {currency}
📋 Описание: {description}
🆔 ID транзакции: {transaction_id or 'N/A'}

🏢 {settings.company_name}
📞 {settings.company_phone}
📧 {settings.company_email}

✅ Оплата подтверждена
                """.strip()
            elif lang == "en":
                receipt_text = f"""
🧾 PAYMENT RECEIPT
📄 Number: {receipt_number}
📅 Date: {timestamp}

💰 Amount: {amount} {currency}
📋 Description: {description}
🆔 Transaction ID: {transaction_id or 'N/A'}

🏢 {settings.company_name}
📞 {settings.company_phone}
📧 {settings.company_email}

✅ Payment confirmed
                """.strip()
            else:  # zh-tw
                receipt_text = f"""
🧾 付款收據
📄 編號: {receipt_number}
📅 日期: {timestamp}

💰 金額: {amount} {currency}
📋 描述: {description}
🆔 交易ID: {transaction_id or 'N/A'}

🏢 {settings.company_name}
📞 {settings.company_phone}
📧 {settings.company_email}

✅ 付款已確認
                """.strip()
            
            return receipt_text
            
        except Exception as e:
            logger.error(f"Simple receipt generation error: {e}")
            return None
    
    def cleanup_old_receipts(self, days_old: int = 30):
        """Clean up old receipt files."""
        try:
            import time
            current_time = time.time()
            
            for receipt_file in self.receipts_dir.glob("*.pdf"):
                file_age = current_time - receipt_file.stat().st_mtime
                if file_age > (days_old * 24 * 3600):
                    receipt_file.unlink()
                    logger.info(f"Cleaned up old receipt: {receipt_file}")
                    
        except Exception as e:
            logger.error(f"Receipt cleanup error: {e}")


# Global receipt generator instance
receipt_generator = ReceiptGenerator()
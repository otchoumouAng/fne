import os
import asyncio
from jinja2 import Environment, FileSystemLoader
from playwright.async_api import async_playwright
from num2words import num2words


class PDFGenerator:
    def __init__(self, template_file):
        if not template_file:
            raise ValueError("Un nom de fichier de template est requis.")

        script_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(script_dir)
        template_dir_path = os.path.join(parent_dir, 'templates')

        self.env = Environment(loader=FileSystemLoader(template_dir_path))
        self.env.filters['money'] = self.money
        self.template = self.env.get_template(template_file)

    @staticmethod
    def money(value, currency="XOF"):
        return f"{value:,.0f} {currency}".replace(",", " ")

    @staticmethod
    def currency_to_words(currency):
        mapping = {"XOF": "francs CFA", "EUR": "euros", "USD": "dollars"}
        return mapping.get(currency, currency)

    def money_to_words(self, value, currency="XOF"):
        try:
            words = num2words(value, lang="fr")
            return f"{words} {self.currency_to_words(currency)}"
        except NotImplementedError:
            return str(value)

    def render_html(self, **context):
        # Calcule les totaux si des 'details' sont présents dans le contexte
        details = context.get('details', [])
        if details:
            subtotal = 0
            taxes = {}
            for item in details:
                line_ht = item.get("quantity", 0) * item.get("unit_price", 0)
                subtotal += line_ht
                tax_rate = item.get("tax_rate", 0)
                tax_amt = round(line_ht * tax_rate / 100)
                taxes[tax_rate] = taxes.get(tax_rate, 0) + tax_amt

            total_tax = sum(taxes.values())
            grand_total = subtotal + total_tax

            # Ajoute les totaux calculés et les helpers au contexte
            context['subtotal'] = subtotal
            context['taxes'] = taxes
            context['total_tax'] = total_tax
            context['grand_total'] = grand_total
            context['grand_total_words'] = self.money_to_words(grand_total)

        return self.template.render(**context)

    async def generate_pdf(self, html_content, output_file="document.pdf"):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.set_content(html_content)
            await page.pdf(
                path=output_file,
                format="A4",
                print_background=True,
                display_header_footer=True,
                footer_template="""
                <div style="font-size:10px; width:100%; text-align:center; color:#555; padding-top:5px;">
                    Merci pour votre confiance — Page <span class="pageNumber"></span> / <span class="totalPages"></span>
                </div>
                """,
                header_template="<div></div>",
                margin={"top": "5mm", "bottom": "10mm"}
            )
            await browser.close()
        print(f"✅ Document PDF généré : {output_file}")

import os
import asyncio
from jinja2 import Environment, FileSystemLoader
from playwright.async_api import async_playwright
from num2words import num2words


class PDFGenerator:
    def __init__(self, template_file):
        if not template_file:
            raise ValueError("Un nom de fichier de template est requis.")

        # Chemin absolu vers le répertoire du script actuel (core/)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Chemin vers le répertoire parent (facturation_ci/)
        parent_dir = os.path.dirname(script_dir)
        # Chemin final vers le dossier des templates
        template_dir_path = os.path.join(parent_dir, 'templates')

        self.env = Environment(loader=FileSystemLoader(template_dir_path))
        # Ajouter des filtres personnalisés à l'environnement Jinja2
        self.env.filters['money'] = self.money
        self.template = self.env.get_template(template_file)

    @staticmethod
    def money(value, currency="XOF"):
        # Formater les montants
        return f"{value:,.0f} {currency}".replace(",", " ")

    @staticmethod
    def currency_to_words(currency):
        # Traduction des devises usuelles
        mapping = {
            "XOF": "francs CFA",
            "EUR": "euros",
            "USD": "dollars",
        }
        return mapping.get(currency, currency)

    def money_to_words(self, value, currency="XOF"):
        # Convertir un montant en toutes lettres (français)
        try:
            words = num2words(value, lang="fr")
            return f"{words} {self.currency_to_words(currency)}"
        except NotImplementedError:
            return str(value)

    def render_html(self, context_data):
        # Calcule les totaux à partir des 'details' dans le contexte
        details = context_data.get('details', [])
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
        context_data['subtotal'] = subtotal
        context_data['taxes'] = taxes
        context_data['total_tax'] = total_tax
        context_data['grand_total'] = grand_total
        context_data['grand_total_words'] = self.money_to_words(grand_total)

        html_content = self.template.render(context_data)
        return html_content

    async def generate_pdf(self, html_content, output_file="document.pdf"):
        # Générer le PDF à partir du HTML via Playwright
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

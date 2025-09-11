import asyncio,os
from jinja2 import Environment, FileSystemLoader
from playwright.async_api import async_playwright
from num2words import num2words


class InvoiceGenerator:

    def __init__(self, template_file="invoice.html"):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(script_dir)
        template_dir_path = os.path.join(parent_dir, 'templates')
        
        self.env = Environment(loader=FileSystemLoader(template_dir_path))
        self.template = self.env.get_template(template_file)
    

    @staticmethod
    def money(value, currency="XOF"):
        """Formater les montants"""
        return f"{value:,.0f} {currency}".replace(",", " ")

    @staticmethod
    def money_to_words(value, currency="XOF"):
        """Convertir un montant en toutes lettres (français)"""
        try:
            words = num2words(value, lang="fr")
            return f"{words} {InvoiceGenerator.currency_to_words(currency)}"
        except NotImplementedError:
            return str(value)

    @staticmethod
    def currency_to_words(currency):
        """Traduction des devises usuelles"""
        mapping = {
            "XOF": "francs CFA",
            "EUR": "euros",
            "USD": "dollars",
        }
        return mapping.get(currency, currency)

    @staticmethod
    def compute_totals(details):
        """Calculer sous-total, taxes et total général"""
        subtotal = 0
        taxes = {}
        for item in details:
            line_ht = item["quantity"] * item["unit_price"]
            subtotal += line_ht
            tax_amt = round(line_ht * item["tax_rate"] / 100)
            taxes[item["tax_rate"]] = taxes.get(item["tax_rate"], 0) + tax_amt

        total_tax = sum(taxes.values())
        grand_total = subtotal + total_tax
        return subtotal, taxes, total_tax, grand_total

    def render_html(self, company, client, invoice, details):
        """Rendre le template HTML avec les données"""
        subtotal, taxes, total_tax, grand_total = self.compute_totals(details)

        html_content = self.template.render(
            company=company,
            client=client,
            invoice=invoice,
            details=details,
            subtotal=subtotal,
            taxes=taxes,
            total_tax=total_tax,
            grand_total=grand_total,
            grand_total_words=self.money_to_words(grand_total, invoice.get("currency", "XOF")),
            money=self.money
        )
        return html_content

    async def generate_pdf(self, html_content, output_file="facture.pdf"):
        """Générer le PDF à partir du HTML via Playwright (version asynchrone)"""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.set_content(html_content)

            # Options avec pied de page personnalisé
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
                header_template="<div></div>",  # pas de header
                margin={"top": "5mm", "bottom": "10mm"}
            )
            await browser.close()
        print(f"✅ Facture générée : {output_file}")


# ---------------------------
# Exemple d'utilisation
# ---------------------------
async def main():
    data = {
        "header": {
            "company": {
                "name": "Altisys Group",
                "tag": "Solutions & Services • International",
                "register": "SIREN 123 456 789 • TVA FR12 345678901",
                "address": "10 Rue de l'Innovation\nAbidjan, Côte d'Ivoire",
                "contact": "contact@altisys.ci • +225 27 21 00 00 00"
            },
            "client": {
                "name": "Client Entreprise SA",
                "address": "Avenue du Commerce\nAbidjan, Côte d'Ivoire",
                "contact": "compta@client.ci • +225 27 21 11 11 11"
            },
            "invoice": {
                "number": "INV-2025-0098",
                "date": "2025-08-28",
                "currency": "XOF",
                "notes": "Paiement par virement bancaire. Merci de mentionner le numéro de facture."
            }
        },
        "details": [
            {"reference": "SVC-001", "description": "Conseil stratégique et atelier d'innovation (2 jours)", "quantity": 2, "unit_price": 350000, "tax_rate": 18},
            {"reference": "DEV-002", "description": "Développement plateforme e-commerce - phase 1", "quantity": 1, "unit_price": 1250000, "tax_rate": 18},
            {"reference": "SUP-003", "description": "Contrat de maintenance annuel (12 mois)", "quantity": 1, "unit_price": 450000, "tax_rate": 18}
        ]
    }

    generator = InvoiceGenerator()
    html = generator.render_html(
        company=data["header"]["company"],
        client=data["header"]["client"],
        invoice=data["header"]["invoice"],
        details=data["details"]
    )
    await generator.generate_pdf(html)

if __name__ == "__main__":
    asyncio.run(main())

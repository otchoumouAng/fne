from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import sync_playwright

class InvoiceGenerator:
    def __init__(self, template_dir="templates", template_file="invoice.html"):
        self.env = Environment(loader=FileSystemLoader(template_dir))
        self.template = self.env.get_template(template_file)

    @staticmethod
    def money(value, currency="XOF"):
        """Formater les montants"""
        return f"{value:,.0f} {currency}".replace(",", " ")

    @staticmethod
    def compute_totals(details):
        """Calculer sous-total, taxes et total général"""
        subtotal = 0
        taxes = {}
        for item in details:
            line_ht = item["qty"] * item["unit_price"]
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
            money=self.money
        )
        return html_content

    def generate_pdf(self, html_content, output_file="facture_.pdf"):
        """Générer le PDF à partir du HTML via Playwright"""
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_content(html_content)
            page.pdf(path=output_file, format="A4", print_background=True)
            browser.close()
        print(f"✅ Facture générée : {output_file}")


# ---------------------------
# Exemple d'utilisation
# ---------------------------

if __name__ == "__main__":
    # Données exemple
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
            {"reference": "SVC-001", "description": "Conseil stratégique et atelier d'innovation (2 jours)", "qty": 2, "unit_price": 350000, "tax_rate": 18},
            {"reference": "DEV-002", "description": "Développement plateforme e-commerce - phase 1", "qty": 1, "unit_price": 1250000, "tax_rate": 18},
            {"reference": "SUP-003", "description": "Contrat de maintenance annuel (12 mois)", "qty": 1, "unit_price": 450000, "tax_rate": 18}
        ]
    }

    generator = InvoiceGenerator()
    html = generator.render_html(
        company=data["header"]["company"],
        client=data["header"]["client"],
        invoice=data["header"]["invoice"],
        details=data["details"]
    )
    generator.generate_pdf(html)

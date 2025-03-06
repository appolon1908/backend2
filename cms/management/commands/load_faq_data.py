from django.core.management.base import BaseCommand
from cms.models import FAQs





data = [
    {
        "question": "¿Qué es la Facturación Fiscal?",
        "answer": "La Facturación Fiscal en la República Dominicana es el proceso legal de emitir comprobantes fiscales que cumplen con las normativas de la Dirección General de Impuestos Internos (**DGII**). Estos comprobantes son documentos oficiales que respaldan las transacciones comerciales y son esenciales para la contabilidad y el cumplimiento tributario."
    },
    {
        "question": "¿Qué información debe incluir un comprobante fiscal?",
        "answer": f"""
            Un comprobante fiscal válido en la República Dominicana debe incluir:
            - Nombre, dirección y **RNC** (Registro Nacional de Contribuyentes) del emisor.
            - Nombre, dirección y RNC o cédula del receptor (si aplica).
            - Tipo de Comprobante Fiscal (NCF).
            - Número de Comprobante Fiscal (NCF) único y asignado por la DGII.
            - Fecha de emisión.
            - Descripción detallada de los bienes o servicios ofrecidos.
            - Cantidades y precios unitarios.
            - Subtotal, impuestos aplicables (como el ITBIS) y monto total.
            - Condiciones de pago (si aplica).
        """
    },
    {
        "question": "Por qué es importante la facturación fiscal?",
        "answer": """
                La facturación fiscal es crucial porque:
                - Garantiza el cumplimiento de las leyes tributarias de la República Dominicana.
                - Permite a las empresas declarar ingresos, pagar impuestos y deducir gastos.
                - Aporta transparencia en las transacciones comerciales.
                - Es obligatoria para evitar sanciones por parte de la **DGII**.
        """
    },
    {
        "question": "¿Qué es un Número de Comprobante Fiscal (NCF)?",
        "answer": """
            El NCF es un código único asignado por la **DGII** que identifica cada transacción fiscalmente registrada. Existen diferentes tipos de NCF según el tipo de transacción, como crédito fiscal, consumo final, gubernamental, entre otros.
        """
    },
    {
        "question": "Qué impuestos se aplican en la República Dominicana?",
        "answer": """
            En una factura fiscal en República Dominicana se incluyen los siguientes impuestos principales:
            - **ITBIS** (Impuesto sobre Transferencia de Bienes Industrializados y Servicios): Actualmente es del 18%.
            - **ISR** (Impuesto Sobre la Renta): Aplicable según la actividad económica del contribuyente.
        """
    },
    {
        "question": "Qué sucede si no emito facturación fiscal?",
        "answer": """
            No emitir comprobantes fiscales puede resultar en multas, sanciones administrativas y problemas legales por incumplimiento de las normativas establecidas por la DGII.
        """
    },
    {
        "question": "Cómo obtengo NCF autorizados por la DGII?",
        "answer": """
            Para obtener NCF, debes:
            1. Registrarte como contribuyente ante la DGII.
            2. Solicitar la habilitación de los NCF a través del portal de la DGII.
            3. Implementar sistemas o soluciones de facturación que cumplan con los requisitos establecidos.
        """
    }
]


class Command(BaseCommand):
    help = 'Load FAQ data into the database'

    def handle(self, *args, **kwargs):
        for item in data:
            FAQs.objects.create(question=item['question'], answer=item['answer'])
        self.stdout.write(self.style.SUCCESS('Successfully loaded FAQ data')),
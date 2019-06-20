import os
from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
# import pydf


class Render:

    @staticmethod
    def render(path: str, params: dict):
        template = get_template(path)
        html = template.render(params)
        response = BytesIO()
        file = open("sales_reporting.pdf", "wb")
        # pdf = pydf.generate_pdf(html)
        file.write(pdf)
        file.close()
        if not pdf.err:
            return HttpResponse(response.getvalue(), content_type='application/pdf')
        else:
            return HttpResponse("Error Rendering PDF", status=400)

    @staticmethod
    def render_to_file(path: str, params: dict):
        template = get_template(path)
        html = template.render(params)
        file_name = "sales_reporting.pdf"
        file_path = os.path.join(os.path.abspath(os.path.dirname("__file__")), file_name)

        pdf = pydf.generate_pdf(html)

        with open(file_path, 'wb') as pdf2:
            pdf2.write(pdf)
        return [file_name, file_path]
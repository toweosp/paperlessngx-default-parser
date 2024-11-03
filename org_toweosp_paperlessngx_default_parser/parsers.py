import os

from django.conf import settings
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

from documents.parsers import DocumentParser
from documents.parsers import ParseError

from datetime import datetime

from string import Template

from pathlib import Path
from gotenberg_client import GotenbergClient
from gotenberg_client.options import PdfAFormat
from paperless.models import OutputTypeChoices



class DefaultDocumentParser(DocumentParser):
    """
    This parser can be used to archive documents of arbitrary mime types with Paperless-ngx.
    If it parses a document with known encoding the content of the file is stored in the document's content metadata and a PDF with its 
    content is generated. 
    Otherwise the content metadata is left empty and a pdf containing a note regarding the use of this parser is generated.
    """

    logging_name = "paperless.parsing.org_toweosp_paperlessngx_default_parser"

    html_note = Template(
    '''
    <HTML>
    This document was archived by a default parser for Paperless-ngx. 
    <p>
    <b>original file name:</b> $file_name<br>
    <b>mime type:</b> $mime_type<br>
    <p>
    Download original file to work with it.
    </HTML>
    ''')

    note = Template(
    '''
    This document was archived by a default parser for Paperless-ngx. 

    original file name: $file_name
    mime type: $mime_type

    Download original file to work with it.
    ''')


    def get_thumbnail(self, document_path, mime_type, file_name=None):
        img = Image.new("RGB", (500, 700), color="white")
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype(
            font=settings.THUMBNAIL_FONT_NAME,
            size=20,
            layout_engine=ImageFont.Layout.BASIC,
        )        
        thumbnail_text = self.text if self.text else self.note.substitute(mime_type = mime_type, file_name = file_name)
        draw.text((5, 5), thumbnail_text, font=font, fill="black")

        out_path = os.path.join(self.tempdir, "thumb.webp")
        img.save(out_path, format="WEBP")
        return out_path

    def parse(self, document_path, mime_type, file_name=None):
        from chardet.universaldetector import UniversalDetector
        detector = UniversalDetector()
        for line in open(document_path, 'rb'):
            detector.feed(line)
            if detector.done: break
        detector.close()


        pdf_output = self.html_note.substitute(mime_type = mime_type, file_name = file_name)
        self.text = ''
        encoding = detector.result['encoding']
        if(encoding):
            try:
                with open(document_path, 'r', encoding=encoding) as file:
                    self.text = file.read()
                    pdf_output = self.text
                    file.close()
                    # deal with postgresql not allowing NUL bytes in text fields. In this case let self.text be empty
                    # and create PDF with default note
                    if '\x00' not in self.text: 
                        pdf_output = f'<HTML><pre>{pdf_output}</pre></HTML>'
                    else:
                        self.text = ''
                        pdf_output = self.html_note.substitute(mime_type = mime_type, file_name = file_name)
            except Exception:
                # if there is any exception while reading the file with the guessed encoding use the
                # default values for self.text and pdf_output as already defined
                pass

        self.archive_path = self.convert_to_pdf(pdf_output)

    def convert_to_pdf(self, content: str):
        pdf_path = Path(self.tempdir) / "convert.pdf"

        with (
            GotenbergClient(
                host=settings.TIKA_GOTENBERG_ENDPOINT,
                timeout=settings.CELERY_TASK_TIME_LIMIT,
            ) as client,
            client.chromium.html_to_pdf() as route,
        ):
            # Set the output format of the resulting PDF
            if settings.OCR_OUTPUT_TYPE in {
                OutputTypeChoices.PDF_A,
                OutputTypeChoices.PDF_A2,
            }:
                route.pdf_format(PdfAFormat.A2b)
            elif settings.OCR_OUTPUT_TYPE == OutputTypeChoices.PDF_A1:
                self.log.warning(
                    "Gotenberg does not support PDF/A-1a, choosing PDF/A-2b instead",
                )
                route.pdf_format(PdfAFormat.A2b)
            elif settings.OCR_OUTPUT_TYPE == OutputTypeChoices.PDF_A3:
                route.pdf_format(PdfAFormat.A3b)

            try:
                index_file_path = Path(self.tempdir) / "index.html"
                with open(index_file_path,'x') as index_file:
                    index_file.write(content)
                    index_file.close()
                response = route.index(index_file_path).run()
                pdf_path.write_bytes(response.content)

                return pdf_path

            except Exception as err:
                raise ParseError(
                    f"Error while converting document to PDF: {err}",
                ) from err


    def get_settings(self):
        """
        This parser does not implement additional settings yet
        """
        return None

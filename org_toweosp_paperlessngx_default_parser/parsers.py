import os

from django.conf import settings
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

from documents.parsers import DocumentParser

from fpdf import FPDF
from datetime import datetime

from string import Template

from django.utils.timezone import make_aware



class DefaultDocumentParser(DocumentParser):
    """
    This parser can be used to archive documents of arbitrary mime types with Paperless-ngx.
    If it parses a document with known encoding the content of the file is stored in the document's content metadata and a PDF with its 
    content is generated. 
    Otherwise the content metadata is left empty and a pdf containing a note regarding the use of this parser is generated.
    """

    logging_name = "paperless.parsing.org_toweosp_paperlessngx_default_parser"

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
        # TODO: prüfen, ob benötigt, da immer Datum der Erzeugung der Datei, was beim Upload der aktuelle Tag ist
        self.date = make_aware(datetime.fromtimestamp(os.path.getmtime(document_path)))

        from chardet.universaldetector import UniversalDetector
        detector = UniversalDetector()
        for line in open(document_path, 'rb'):
            detector.feed(line)
            if detector.done: break
        detector.close()

        self.text=''        
        encoding = detector.result['encoding']
        if(encoding):
            try:
                with open(document_path, 'r', encoding=encoding) as file:
                    self.text = file.read()
            except Exception:
                # if there is any exception while reading the file with the guessed encoding let self.text be empty
                pass 

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=10)
        parts = self.text.split('\n') if self.text else self.note.substitute(mime_type = mime_type, file_name = file_name).split('\n')
        for p in parts:
            pdf.cell(w = 0,h = 10,txt = p, ln = 1, align = 'L')
        pdf.output(os.path.join(self.tempdir,"archived.pdf"))
        self.archive_path = os.path.join(self.tempdir, "archived.pdf")

    def get_settings(self):
        """
        This parser does not implement additional settings yet
        """
        return None

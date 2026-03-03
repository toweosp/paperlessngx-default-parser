from django.apps import AppConfig
from paperlessngx_default_parser.signals import consumer_declaration

class DefaultParserConfig(AppConfig):
    name = "paperlessngx_default_parser"

    def ready(self):
        from documents.signals import document_consumer_declaration
        document_consumer_declaration.connect(consumer_declaration)
        AppConfig.ready(self)

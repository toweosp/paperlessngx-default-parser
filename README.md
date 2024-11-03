# Default parser for Paperless-ngx 
This is a default parser which can be used by [Paperless-ngx](https://docs.paperless-ngx.com/) if there is no other suitable parser found for a given mime type.

It allows to archive documents of all mime types, which are defined in /etc/mime.types. For every document consumed by this parser, the original file gets archived and a PDF as well as a thumbnail are generated.

If a file with known encoding is parsed, the content of this file is read and stored in the document's content metadata. Furthermore a PDF showing this content is generated. Otherwise the content metadata is left empty and a PDF containing the following note is generated: 

    This document was archived by a default parser for Paperless-ngx. 

    original file name: $file_name
    mime type: $mime_type

    Download original file to work with it.

## Prerequisites
This parser requires Gotenberg to be configured for Paperless-ngx.

## Installation
These installation instructions are for docker based installation. For bare metal installations you have to do analogous steps manually, i.e. install the dependencies listed in `org_toweosp_paperlessngx_default_parser.sh` and copy/link the source folder to your installation folder.  

1. Download current release or clone repository to a _folder_ of your choice.

2. Use custom container initialization as described here: https://docs.paperless-ngx.com/advanced_usage/#custom-container-initialization
   
   Place the script `org_toweosp_paperlessngx_default_parser.sh` in the directory for your container initialization scripts and make it executable.

   This script will install the required python modules. It also contains an example to add additional mime types, see [Limitations](#limitations).

3. Bind folder `org_toweosp_paperlessngx_default_parser` to `/usr/src/paperless/src/org_toweosp_paperlessngx_default_parser` for your Paperless-ngx webserver container. For example when using docker compose:

    ```
    services:
    [...]    
        webserver:
        [...]
            volumes:
            - <folder>/org_toweosp_paperlessngx_default_parser:/usr/src/paperless/src/org_toweosp_paperlessngx_default_parser
    ```
4. Add the default parser to the `PAPERLESS_APPS` environment variable, e.g. 
   `PAPERLESS_APPS="org_toweosp_paperlessngx_default_parser.apps.DefaultParserConfig"`

> **Note on using the PAPERLESS_APPS environment variable**
>
>This is a comma separated list of apps you would like to add to Paperless-ngx. Pay attention to not include any spaces in between when >adding more than one app. So use e.g.
>
>`PAPERLESS_APPS="org_toweosp_paperlessngx_default_parser.apps.DefaultParserConfig,paperless_my.apps.SpecialConfig"`
>
>instead of
>
>`PAPERLESS_APPS="org_toweosp_paperlessngx_default_parser.apps.DefaultParserConfig, paperless_my.apps.SpecialConfig"`

## Limitations

### __Error: File type {mime-type} not supported__
Paperless-ngx uses magic numbers to identify the mime type of a file which should be consumed/archived.

On the other hand Paperless-ngx currently requires a custom parser to define a dictionary of mime-types and one default extension per mime type it supports, see also [Support for arbitrary binary files? #805](https://github.com/paperless-ngx/paperless-ngx/discussions/805#discussioncomment-11020559) for a proposal to change this behaviour.

This default parser registers itself for all mime types defined in /etc/mime.types. It uses the first file extension defined in /etc/mime for a given mime type as the default extension for this mime type - or an empty string, if there is no extension defined at all.

Since the magic numbers database and /etc/mime.types don't have to be - and in fact are not - in sync, the following situation might occur:

Paperless-ngx identifies - by using magic numbers - a mime type which is not listed in /etc/mime.types. This results in the error _File type {mime-type} not supported_ because the default parser could not register itself for this mime type.

**Solution**: Add the missing mime type to /etc/mime.types.

### __Error: Not consuming file {filepath}: Unknown file extension.__
Paperless-ngx at the moment handles files differently if they are imported via the consumption directory or via UI.

When importing a file via UI, Paperless-ngx (solely) checks the mime type of the file using _magic_ numbers and checks if there is a parser registered for this mime type.

When importing a file through the consumption directory an additional check is done at first:

Paperless-ngx collects all file extensions for the given mime type by looking at 
- /etc/mime.types and 
- the default extension a parser for this mime type declares. 

A file in the consumption directory then is only consumed if its file extension matches one of theses extensions.

For example:

Given a file test.yaml which has mime type text/plain.

Importing via UI successfully archives the document. Importing the same document via the consumption directory leads to error 
_Not consuming file /usr/src/paperless/consume/test.yaml: Unknown file extension._

**Solution**: Either import the file via UI or add the unknown file extension to the file extensions for this mime type in /etc/mime.types.

### __File extension when downloading original file__
At the moment Paperless-ngx uses a default extension per mime type when downloading an original file.

For example: files of mime type _application/octet-stream_ will get file extension _.bin_, those with mime-type _text/plain_ will get extension _.txt_ when downloaded.

**Solution**: In order to use a file with a program it originates of, you may therefore have to change the file extension of the downloaded file manually.

## __How to modify /etc/mime.types used by Paperless-ngx__
For example:
- Add missing mime types using `org_toweosp_paperlessngx_default_parser.sh` (see examples there)
- Create your own custom container initialization script to add/modify mime types.
- Use your own mime.types file and bind it to /etc/mime.types

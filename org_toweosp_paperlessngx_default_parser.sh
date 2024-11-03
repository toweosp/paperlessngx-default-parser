#!/bin/bash
pip install chardet

# Add mime.types known by magic numbers database which are missing in /etc/mime.types
# File extensions can be added using the following format:
# <mime-type designation><tab><list of extensions> where <list of extensions> is a list of extensions without dot separated by a space character
echo -e "application/x-adobe-aco" >> /etc/mime.types
echo -e "message/news\teml" >> /etc/mime.types
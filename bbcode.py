'''
Created on 2012-1-12

@author: ling0322
'''

import singleton
import re

class bbcode(singleton.singleton):
    '''
    a class convert bbcode to html
    '''
    
    def __init__(self):
        self.tags = []
        self.tags.append((re.compile(r'&'), r'&amp;'))
        self.tags.append((re.compile(r' '), r'&nbsp;'))
        self.tags.append((re.compile(r'<'), r'&lt;'))
        self.tags.append((re.compile(r'>'), r'&gt;'))
        self.tags.append((re.compile(r'\[(b|i|u|s)\](.*)\[/\1\]'), r'<\1>\2</\1>'))
        self.tags.append((re.compile(r'\[url\](.*)\[/url\]'), r'<a href="\1">\1</a>'))
        self.tags.append((re.compile(r'\[url=(.*)\](.*)\[/url\]'), r'<a href="\1">\2</a>'))
        self.tags.append((re.compile(r'\[img\](.*)\[/img\]'), r'<img src="\1" />'))
        self.tags.append((re.compile(r'\[size=([0-9]*)\](.*)\[/size\]'), r'<span style="font-size:\1px">\2</span>'))
        self.tags.append((re.compile(r'\[color=(.*)\](.*)\[/color\]'), r'<span style="color:\1;">\2</span>'))
        
    def bb2html(self, bb2code):
        html_paragraphs = []
        for paragraph in bb2code.split('\n'):
            html = paragraph
            for tag in self.tags:
                html = re.sub(tag[0], tag[1], html)
            html_paragraphs.append('<p>' + html + '</p>')
        return ''.join(html_paragraphs)
        
    
    
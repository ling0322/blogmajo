'''
Created on 2012-1-11

@author: ling0322
'''
import tornado.web
import meidodb
import bbcode
import base64
import time

class Content(tornado.web.UIModule):
    def render(self, content_type, kwargs):
        return self.render_string(content_type + '.html', **kwargs)

class BlogEntry(tornado.web.UIModule):
    
    def base64_encode(self, original_str):
        if type(original_str) == unicode:
            original_str = original_str.encode('utf-8')
       
        return base64.urlsafe_b64encode(original_str)
    
    def render(self, blog):
        bbcode_conv = bbcode.bbcode()
        blog['content'] = bbcode_conv.bb2html(blog['content'])
        blog['base64-category'] = self.base64_encode(blog['category'])
        author = meidodb.get_siteinfo('username')
        return self.render_string(
            "blogentry.html", 
            blog = blog, 
            author = author,
            date = time.strftime('%d', blog['create_time']),
            month = time.strftime('%b', blog['create_time']))

class ArchivesList(tornado.web.UIModule):
    def render(self):
        archives = meidodb.get_archives()
        l = ['<li><a href="/archive/{0}">{1} ({2})</a></li>'.format(
                archive['archive'],
                time.strftime('%B %Y', time.strptime(archive['archive'], '%Y%m')),
                archive['count'])
             for archive in archives]
        return ''.join(l)
    
class RecentPostsList(tornado.web.UIModule):
    RECENT_POSTS_PAGES = 2
    
    def render(self):
        posts = []
        for i in range(self.RECENT_POSTS_PAGES):
            posts = posts + meidodb.select_entries(i)
        
        l = ['<li><a href="/blog/{0}">{1}</a></li>'.format(
                post['id'],
                post['title'])
             for post in posts]
        return ''.join(l)
    
class CategoriesList(tornado.web.UIModule):
    def render(self):
        categories = meidodb.get_categories()
        l = ['<li><a href="/category/{0}">{1} ({2})</a></li>'.format(
                base64.urlsafe_b64encode(category['category']),
                category['category'],
                category['count'])
             for category in categories]
        return ''.join(l)

class CategoryOptions(tornado.web.UIModule):
    def render(self, default):
        
        categories = meidodb.get_categories()
        l = []
        for category in categories:
            if category['category'] == default:
                l.append('<option selected="selected">' + category['category'] + '</option>')
            else:
                l.append('<option>' + category['category'] + '</option>')
        
        return ''.join(l)
    
class LinksList(tornado.web.UIModule):
    ''' 
    the links list displayed in the index
    convert the bbcode([url] tag) to html
    '''
    def render(self):
        bbcode_func = bbcode.bbcode().bb2html
        links_str = meidodb.get_siteinfo('links', '')
        l = ['<li class="page_item">{0}</li>'.format(bbcode_func(link))
             for link in links_str.split('\n')]
        return ''.join(l)  
    
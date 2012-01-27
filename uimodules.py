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
        try:
            links_str = meidodb.get_siteinfo('links', '')
            l = ['<li class="page_item"><a href="{0}">{1}</a></li>'.format(*link.split(','))
                for link in links_str.split('\n')]
            return ''.join(l)  
        except:
            return ''

class CommentsList(tornado.web.UIModule):
    ''' 
    the links list displayed in the index
    convert the bbcode([url] tag) to html
    '''
    def render(self):
        recent_comments = meidodb.get_recent_comments(10)
        
        def _get_time_str(t):
            
            # if at the same year, just neglect year in return string
            
            if t[0] == time.gmtime()[0]:
                return time.strftime("%b %d", t)
            else:
                return time.strftime("%b %d, %Y", t)
            
        return self.render_string(
            'commentlist.html',
            _get_time_str = _get_time_str,
            recent_comments = recent_comments)
        

class Comments(tornado.web.UIModule):
    ''' comments in entry page '''

    def render(self, entry_id):
        comments = meidodb.get_comment_by_entry(entry_id)
        if 0 == len(comments):
            return '<p class="nocomments">No Comments.</p>'
        else:
            count = 1
            render_str_list = []
            for comment in comments:
                render_str_list.append(self.render_string(
                    'comment.html',
                    comment = comment,
                    time = time.strftime('%B %d, %Y at %I:%M %p', comment['comment_time']),
                    floor = count))
                count = count + 1
            entry = meidodb.get_entry(entry_id)
            h3_str = '<h3 id="comments-wrap">{0} Comments to "{1}"</h3>'.format(len(render_str_list), entry['title'])
            return h3_str + '<ol class="commentlist">' + ''.join(render_str_list) + '</ol>'


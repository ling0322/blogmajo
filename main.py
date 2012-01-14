# -*- coding: utf-8 -*-

# solve the default encoding problem
import sys 
reload(sys) 
sys.setdefaultencoding("utf-8") 


import tornado.ioloop
import tornado.web
import os
from tornado import escape
import time
import uimodules
import meidodb
import base64
import hashlib

class MeidoBaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        if meidodb.get_siteinfo('password') == None:
            return 'tempusr'
        else:
            return self.get_secure_cookie("user")
    
    def _meido_render(self, content_type, kwargs):
        ''' render a page that in the frame of blogmeido '''
        
        # get site information
        
        title = meidodb.get_siteinfo('title', '')
        description = meidodb.get_siteinfo('description', '')
        
        self.render(
            'index.html', 
            blogtitle = title, 
            description = description, 
            content_type = content_type, 
            kwargs = kwargs)

class HomePage(MeidoBaseHandler):
    def get(self):
        
        # default is page 0
        
        page = int(self.get_argument('page', '0'))
        pages_max = meidodb.pages_max()
        if page > pages_max:
            page = pages_max
        
        # if the database hasn't initialized go to siteinfo page first
        
        if None == meidodb.get_siteinfo('password'):
            self.redirect('/siteinfo')
            return
            
        bloglist = meidodb.select_entries(page)
        self._meido_render(
            content_type = 'bloglist', 
            kwargs = dict(
                blogentries = bloglist, 
                pages_max = pages_max, 
                page = page,
                category = None,
                post_date = None))

class Category(MeidoBaseHandler):
    ''' display entries of a certain category '''
    
    def get(self, request):
        
        # default is page 0
        
        page = int(self.get_argument('page', '0'))
        base64_category = request
        category = base64.urlsafe_b64decode(base64_category.encode('utf-8')).decode('utf-8')

        pages_max = meidodb.pages_max_by_category(category)
        if page > pages_max:
            page = pages_max
            
        bloglist = meidodb.select_entries_by_category(page, category)
        self._meido_render(
            content_type = 'bloglist', 
            kwargs = dict(
                blogentries = bloglist, 
                pages_max = pages_max, 
                page = page,
                category = category,
                post_date = None))

class Archive(MeidoBaseHandler):
    ''' display archive of entries in one month '''
    
    def get(self, request):
        # default is page 0
        
        page = int(self.get_argument('page', '0'))
        archive = request

        pages_max = meidodb.pages_max_by_archive(archive)
        if page > pages_max:
            page = pages_max
            
        bloglist = meidodb.select_entries_by_archive(page, archive)
        self._meido_render(
            content_type = 'bloglist',
            kwargs = dict(
                blogentries = bloglist,
                pages_max = pages_max,
                page = page,
                category = None,
                post_date = time.strftime('%B %Y', time.strptime(archive, '%Y%m'))))

        

class Blog(MeidoBaseHandler):
    ''' display a blog specified by the argument of id '''
    
    def get(self, request):
        entry = meidodb.get_entry(int(request))
        
        if entry == None:
            self.redirect(u'/message?m=这个页面貌似不存在呢TwT')
            return
            
        self._meido_render(
            content_type = 'entry', 
            kwargs = dict(entry = entry))

class Message(MeidoBaseHandler):
    ''' a page that display some messages '''
     
    def get(self):
        message = self.get_argument('m')
        self._meido_render(
            content_type = 'message', 
            kwargs = dict(message = message))        

class Login(MeidoBaseHandler):
    ''' login page '''
     
    def get(self):
        self._meido_render(
            content_type = 'login', 
            kwargs = dict())
        
        
    def post(self):
        username = self.get_argument('username')
        sha256_password = hashlib.sha256(self.get_argument('password')).hexdigest()
        if username == meidodb.get_siteinfo('username') and sha256_password == meidodb.get_siteinfo('password'):
            self.set_secure_cookie('user', 'ling0322');
            self.redirect('/')
        else:
            self.redirect('/message?m=用户名密码错了呢> <')     

class Logout(MeidoBaseHandler):
    ''' logout page '''
    
    def get(self):
        self.clear_all_cookies()
        self.redirect('/')

class Modify(MeidoBaseHandler):
    
    @tornado.web.authenticated
    def get(self):
        ''' 
        arguments of this request:
            q = 'compose' -> create a new blog
            q = 'modify' -> modify a exist blog
            id -> id of the entry to modify
        '''
        if self.get_argument('q') == 'compose':
            
            # craete a new entry
            
            self._meido_render(
                content_type = 'compose', 
                kwargs = dict(
                    header_message = 'Compose a new blog ...',
                    title = '',
                    category = '',
                    content = '',
                    post_id = -1))
        
        elif self.get_argument('q') == 'modify':
            
            # modify an exist entry
            
            entry_id = int(self.get_argument('id'))
            entry = meidodb.get_entry(entry_id)
            
            self._meido_render(
                content_type = 'compose', 
                kwargs = dict(
                    header_message = 'Modify an exist blog ...',
                    title = entry['title'],
                    category = entry['category'],
                    content = entry['content'],
                    post_id = entry_id))            
    
    @tornado.web.authenticated
    def post(self):
        ''' 
        compose or modify an entry 
        arguments:
        
        title
        category
        category-new -> if this is not null, just create a new category, or use the category data
        content
        post-id -> if post-id is -1, create a new post
        '''
        
        entry_id = int(self.get_argument('post-id'))

        entry = {}
        entry['title'] = self.get_argument('title')
        
        if self.get_argument('category-new', '') == '':
            if self.get_argument('category', '') == '':
                entry['category'] = 'Uncategorized'
            else:
                entry['category'] = self.get_argument('category')
        else:
            entry['category'] = self.get_argument('category-new')
            
        entry['content'] = self.get_argument('content')
        entry['create_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        
        # id != -1 is to modify an exist entry just remove it and create a new
        
        if entry_id != -1:
            meidodb.modify_entry(entry_id, entry)
        else:
            meidodb.create_entry(entry)
        
        self.redirect('/')

class SiteInfo(MeidoBaseHandler):
    ''' change the site info '''
    
    @tornado.web.authenticated
    def get(self):
        title = meidodb.get_siteinfo('title', '')
        description = meidodb.get_siteinfo('description', '')
        username = meidodb.get_siteinfo('username', '')
        links = meidodb.get_siteinfo('links', '')
        
        # if password exists fill the input box with '-do-not-change-'
        # or left it blank
        
        if None == meidodb.get_siteinfo('password'):
            password = ''
        else:
            password = '-do-not-change-'
        
        self._meido_render(
            content_type = 'siteinfo', 
            kwargs = dict(
                title = title,
                description = description,
                username = username,
                links = links,
                password = password))  
    
    @tornado.web.authenticated
    def post(self):
        title = self.get_argument('title', '')
        description = self.get_argument('description', '')
        username = self.get_argument('username', '')
        links = self.get_argument('links', '')
        password = self.get_argument('password', None)
        password_confirm = self.get_argument('password-confirm', None)
        
        meidodb.set_siteinfo('title', title)
        meidodb.set_siteinfo('description', description)
        meidodb.set_siteinfo('username', username)
        meidodb.set_siteinfo('links', links)
        
        if password == None or username == '':
            self.redirect('/message?m=密码和用户名不能为空呢> <')
            
        if password != '-do-not-change-':
            
            # clear cookies to re-login
            
            self.clear_all_cookies()
            
            if password == password_confirm:
                meidodb.set_siteinfo('password', hashlib.sha256(password).hexdigest())
            else:
                self.redirect('/message?m=两个密码不一样呢> <')
                
        self.redirect('/message?m=修改成功!')

class Remove(MeidoBaseHandler):
    ''' remove a post '''
    
    @tornado.web.authenticated
    def get(self):
        
        # next argument is where this page comes from

        entry_id = int(self.get_argument('id'))
        entry = meidodb.get_entry(entry_id)
        next_page = self.get_argument('next')
        
        
        self._meido_render(
            content_type = 'remove', 
            kwargs = dict(
                entry = entry,
                entry_id = entry_id,
                next = next_page))
        
    @tornado.web.authenticated
    def post(self):
        next_page = escape.url_unescape(self.get_argument('next'))
        entry_id = int(self.get_argument('id'))
        meidodb.delete_entry(entry_id)
        
        # if next page is the blog just removed, jump to /
        
        if next_page.find('/blog/') != -1:
            self.redirect('/')
        else:
            self.redirect(escape.url_unescape(next_page))
        
        

settings = {
    "ui_modules": uimodules,
    "static_path": os.path.join(os.path.dirname(__file__), "static"),
    "template_path": os.path.join(os.path.dirname(__file__), "templates"),
    "cookie_secret": "61oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=",
    "login_url": "/login",
}

application = tornado.web.Application([
    (r"/", HomePage),
    (r"/blog/([0-9]+)", Blog),
    (r"/category/(.+)", Category),
    (r"/archive/([0-9]+)", Archive),
    (r"/modify", Modify),
    (r"/message", Message),
    (r"/remove", Remove),
    (r"/login", Login),
    (r"/logout", Logout),
    (r"/siteinfo", SiteInfo),
    (r"/static/(.+)", tornado.web.StaticFileHandler, dict(path=settings['static_path'])),
], **settings)

if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
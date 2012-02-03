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
import uuid
import platform

class MeidoBaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        if meidodb.get_siteinfo('password') == None:
            return 'tempusr'
        else:
            return self.get_secure_cookie("user")
    
    def _majo_background_render(self, template_name, **kwargs):
        ''' render a background page '''

        title = meidodb.get_siteinfo('title', '')
        description = meidodb.get_siteinfo('description', '')
        
        self.render(
            'majo-background.html', 
            blogtitle = title, 
            description = description, 
            content_type = template_name,
            kwargs = kwargs)        
    
    def _meido_render(self, content_type, **kwargs):
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
            self.redirect('/blog-admin/siteinfo')
            return
            
        bloglist = meidodb.select_entries(page)
        self._meido_render(
            content_type = 'bloglist', 
            blogentries = bloglist, 
            pages_max = pages_max, 
            page = page,
            category = None,
            post_date = None)

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
            blogentries = bloglist, 
            pages_max = pages_max, 
            page = page,
            category = category,
            post_date = None)

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
            blogentries = bloglist,
            pages_max = pages_max,
            page = page,
            category = None,
            post_date = time.strftime('%B %Y', time.strptime(archive, '%Y%m')))

        

class Blog(MeidoBaseHandler):
    ''' display a blog specified by the argument of id '''
    
    def get(self, request):
        entry = meidodb.get_entry(int(request))
        
        if entry == None:
            self.redirect(u'/message?m=这个页面貌似不存在呢TwT')
            return
            
        self._meido_render(
            content_type = 'entry', 
            entry = entry)

class Message(MeidoBaseHandler):
    ''' a page that display some messages '''
     
    def get(self):
        message = self.get_argument('m')
        self._meido_render(
            content_type = 'message', 
            message = message)   

class Login(MeidoBaseHandler):
    ''' login page '''
     
    def get(self):
        
        # if login success go to the page specified by next
        
        next_url = self.get_argument('next', '/')
        self._majo_background_render(
            template_name = 'login', 
            next = next_url)
        
        
    def post(self):
        username = self.get_argument('username')
        next_url = escape.url_unescape(self.get_argument('next'))
        sha256_password = hashlib.sha256(self.get_argument('password')).hexdigest()
        if username == meidodb.get_siteinfo('username') and sha256_password == meidodb.get_siteinfo('password'):
            self.set_secure_cookie('user', 'ling0322');
            self.redirect(next_url)
        else:
            self.redirect('/message?m=用户名密码错了呢> <')     

class Logout(MeidoBaseHandler):
    ''' logout page '''
    
    def get(self):
        self.clear_all_cookies()
        self.redirect('/')

class Comment(MeidoBaseHandler):
    ''' create a new comment '''
    
    def post(self): 
        author = self.get_argument("author", None)
        email = self.get_argument("email", "")
        url = self.get_argument("url", "")
        content = self.get_argument("comment", None)
        comment_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        entry_id = self.get_argument('entry_id')

        # if this comment is commented by master, use the master's name 
        
        if self.current_user != None:
            author = meidodb.get_siteinfo('username')
       
        # check the parameters
        
        if self.current_user == None and author.upper() == meidodb.get_siteinfo('username').upper():
            self.redirect('/message?m=乃不能用UP主的名字啊 (摇头ing')
            return
        if author == None:
            self.redirect('/message?m=名字不能为空呢~')
            return
        if content == None:
            self.redirect('/message?m=评论的内容呢 (盯~~~')
            return
               
        comment = dict(
            name = author,
            email = email,
            url = url,
            content = content,
            comment_time = comment_time,
            entry_id = entry_id
            )
        
        meidodb.create_comment(comment)
        self.redirect('/blog/' + str(entry_id))
        
            
            

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
            
            self._majo_background_render(
                template_name = 'compose', 
                header_message = 'Compose a new blog ...',
                title = '',
                category = '',
                content = '',
                post_id = -1)
        
        elif self.get_argument('q') == 'modify':
            
            # modify an exist entry
            
            entry_id = int(self.get_argument('id'))
            entry = meidodb.get_entry(entry_id)
            
            self._majo_background_render(
                template_name = 'compose', 
                header_message = 'Modify an exist blog ...',
                title = entry['title'],
                category = entry['category'],
                content = entry['content'],
                post_id = entry_id)           
    
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
            
        entry['content'] = self.get_argument('entry-content')
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
        
        self._majo_background_render(
            template_name = 'siteinfo', 
            title = title,
            description = description,
            username = username,
            links = links,
            password = password)
    
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

        type = self.get_argument('type')
        id = int(self.get_argument('id'))
        if type == 'entry':
            item = meidodb.get_entry(id)
        elif type == 'comment':
            item = meidodb.get_comment_by_id(id)
            
        next_page = self.get_argument('next')
        
        
        self._majo_background_render(
            template_name = 'remove', 
            type = self.get_argument('type'),
            item = item,
            id = id,
            next = next_page)
        
    @tornado.web.authenticated
    def post(self):
        next_page = escape.url_unescape(self.get_argument('next'))
        id = int(self.get_argument('id'))
        type = self.get_argument('type')
        if type == 'entry':
            meidodb.delete_entry(id)
            meidodb.delete_comment_by_entry(id)
        elif type == 'comment':
            meidodb.delete_comment_by_id(id)
        
        # if next page is the blog just removed, jump to /
        
        if type == 'entry' and next_page.find('/blog/') != -1:
            self.redirect('/')
        else:
            self.redirect(escape.url_unescape(next_page))
        
class Dashboard(MeidoBaseHandler):
    ''' change the site info '''
    
    @tornado.web.authenticated
    def get(self):
        entries_count = meidodb.entries_count()
        categories_count = meidodb.categories_count()
        comments_count = meidodb.comments_count()
        python_version = platform.python_version()
        tornado_version = tornado.version
        self._majo_background_render(
            'background-home',
            entries_count = entries_count,
            categories_count = categories_count,
            comments_count = comments_count,
            python_version = python_version,
            tornado_version = tornado_version)

# create a random cookie secret

cookie_secret = str(uuid.uuid4())
print "cookie secret is : {0} \n".format(cookie_secret)

settings = {
    "ui_modules": uimodules,
    "static_path": os.path.join(os.path.dirname(__file__), "static"),
    "template_path": os.path.join(os.path.dirname(__file__), "templates"),
    "cookie_secret": cookie_secret,
    "login_url": "/blog-admin/login",
}

application = tornado.web.Application([
    (r"/", HomePage),
    (r"/blog/([0-9]+)", Blog),
    (r"/category/(.+)", Category),
    (r"/archive/([0-9]+)", Archive),
    (r"/blog-admin/modify", Modify),
    (r"/message", Message),
    (r"/blog-admin/remove", Remove),
    (r"/blog-admin/login", Login),
    (r"/blog-admin/logout", Logout),
    (r"/comment", Comment),
    (r"/blog-admin/home", Dashboard),
    (r"/blog-admin/siteinfo", SiteInfo),
    (r"/static/(.+)", tornado.web.StaticFileHandler, dict(path=settings['static_path'])),
], **settings)

if __name__ == "__main__":
    application.listen(3323)
    tornado.ioloop.IOLoop.instance().start()

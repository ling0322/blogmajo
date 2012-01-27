# -*- coding: utf-8 -*-

'''
Created on 2012-1-11

@author: ling0322
'''
import sqlite3
import time
import atexit



def _table_is_exist(table_name):
    ''' 
    modify a entry 
    create_time area of argument entry is never used
    '''
    
    c = conn.cursor()
    c.execute(
        """
        select * 
        from sqlite_master
        where type = 'table' and name = ? 
        """, (table_name, ))
    
    if len(c.fetchall()) == 0:
        c.close()
        return False
    else:
        c.close()
        return True

def _create_table_entry():
    c = conn.cursor()
    c.execute("""
        create table entry(
            id integer primary key asc,
            category varchar(32), 
            create_time datetime,
            title text,
            content text);""")
    conn.commit()
    c.close()

def _create_table_siteinfo():
    c = conn.cursor()
    c.execute(
        """
        create table siteinfo(
            key varchar(20) primary key asc, 
            value text);
        """)
    conn.commit()
    c.close()

def _create_table_comment():
    c = conn.cursor()
    c.execute(
        """
        create table comment(
            id integer primary key,
            entry_id integer,
            name text,
            email text,
            url text,
            content text,
            comment_time datetime);
        """)
    conn.commit()
    c.close()
    
def create_comment(comment):
    ''' insert an new comment into table '''
    
    c = conn.cursor()
    c.execute(
        """
        insert into comment(entry_id, name, email, content, comment_time, url) 
        values(?, ?, ?, ?, ?, ?)
        """, (
            comment['entry_id'],
            comment['name'],
            comment['email'],
            comment['content'],
            comment['comment_time'],
            comment['url']))
    
    conn.commit()
    c.close()    

def delete_comment_by_id(id):
    ''' remove an comment by its id '''
    
    c = conn.cursor()
    c.execute("""delete from comment where id = ?""", (id, ));
    conn.commit()
    c.close()

def delete_comment_by_entry(entry_id):
    ''' remove comments of an entry '''
    
    c = conn.cursor()
    c.execute("""delete from comment where entry_id = ?""", (entry_id, ));
    conn.commit()
    c.close()

def get_recent_comments(limit):
    ''' get an comment by its id '''
    
    c = conn.cursor()
    c.execute(
        """
        select id, entry_id, name, email, content, comment_time, url 
        from comment 
        order by id desc
        limit ?
        """, (limit, ));
    
    # if the comment didn't exist, return None 
    
    all_data = c.fetchall()
    r = [_raw_data_to_comment_dict(raw_entry) for raw_entry in all_data]
        
    conn.commit()
    c.close()
    return r

def get_comment_by_id(id):
    ''' get an comment by its id '''
    
    c = conn.cursor()
    c.execute("""select id, entry_id, name, email, content, comment_time, url from comment where id = ?""", (id, ));
    
    # if the comment didn't exist, return None 
    
    all_data = c.fetchall()
    if len(all_data) == 0:
        r = None
    else:
        r = _raw_data_to_comment_dict(all_data[0])
        
    conn.commit()
    c.close()
    return r

def get_comment_by_entry(entry_id):
    ''' get comments referring to the entry '''
    
    c = conn.cursor()
    
    c.execute(
        """
        select id, entry_id, name, email, content, comment_time, url
        from comment
        where entry_id = ?
        order by comment_time asc
        """, (entry_id, ))

    all_data = c.fetchall()
    r = [_raw_data_to_comment_dict(raw_entry) for raw_entry in all_data]
            
    conn.commit()
    c.close()
    return r

def create_entry(entry):
    ''' insert an entry (blog) into table '''
    
    c = conn.cursor()
    c.execute(
        """
        insert into entry(title, category, create_time, content) 
        values(?, ?, ?, ?)
        """, (
            entry['title'], 
            entry['category'],
            entry['create_time'],
            entry['content']))
    
    conn.commit()
    c.close()

def delete_entry(entry_id):
    ''' remove an entry '''
    
    c = conn.cursor()
    c.execute("""delete from entry where id = ?""", (entry_id, ));
    conn.commit()
    c.close()
    
def modify_entry(entry_id, entry):
    ''' 
    modify a entry
    create_time area of argument entry is never used
    '''
    
    c = conn.cursor()
    c.execute(
        """
        update entry 
        set title = ?, 
            category = ?, 
            content = ?
        where id = ?
        """, (
            entry['title'], 
            entry['category'],
            entry['content'],
            entry_id))
    
    conn.commit()
    c.close()

def _raw_data_to_entry_dict(raw_data):
    ''' convert raw data (row) return from sqlite3 call to entry (dict) '''
    
    return dict(
        id = raw_data[0],
        title = raw_data[1],
        category = raw_data[2],
        create_time = time.strptime(raw_data[3], '%Y-%m-%d %H:%M:%S'),
        content = raw_data[4])

def _raw_data_to_comment_dict(raw_data):
    ''' convert raw data (row) return from sqlite3 call to comment (dict) '''
    
    return dict(
        id = raw_data[0],
        entry_id = raw_data[1],
        name = raw_data[2],
        email = raw_data[3],
        content = raw_data[4],
        comment_time = time.strptime(raw_data[5], '%Y-%m-%d %H:%M:%S'),
        url = raw_data[6],
        )
        
    
def get_entry(entry_id):
    ''' get an entry by id '''
    
    c = conn.cursor()
    c.execute("""select id, title, category, create_time, content from entry where id = ?""", (entry_id, ));
    
    # if the entry didn't exist, return false 
    
    all_data = c.fetchall()
    if len(all_data) == 0:
        r = None
    else:
        r = _raw_data_to_entry_dict(all_data[0])
        
    conn.commit()
    c.close()
    return r

def select_entries(page):
    ''' 
    return all entries specified by page
    '''
    
    c = conn.cursor()
    c.execute(
        """
        select id, title, category, create_time, content 
        from entry 
        order by create_time desc
        limit ?
        offset ?
        """, (
            ENTRIES_PER_PAGE,
            ENTRIES_PER_PAGE * page))

    all_data = c.fetchall()
    r = [_raw_data_to_entry_dict(raw_entry) for raw_entry in all_data]
            
    conn.commit()
    c.close()
    return r

def select_entries_by_category(page, category):
    ''' 
    get entries by category and page
    page is start from 0
    '''
    
    c = conn.cursor()
    
    c.execute(
        """
        select id, title, category, create_time, content 
        from entry 
        where category = ?
        order by create_time desc
        limit ?
        offset ?
        """, (
            category,
            ENTRIES_PER_PAGE,
            ENTRIES_PER_PAGE * page))

    all_data = c.fetchall()
    r = [_raw_data_to_entry_dict(raw_entry) for raw_entry in all_data]
            
    conn.commit()
    c.close()
    return r

def select_entries_by_archive(page, date):
    '''
    select entries by date and page
    page is start from 0 and date is formated as '201201'
    '''
    
    c = conn.cursor()
    
    c.execute(
        """
        select id, title, category, create_time, content 
        from entry 
        where strftime('%Y%m', create_time) = ?
        order by create_time desc
        limit ?
        offset ?
        """, (
            date,
            ENTRIES_PER_PAGE,
            ENTRIES_PER_PAGE * page))
    
    all_data = c.fetchall()
    r = [_raw_data_to_entry_dict(raw_entry) for raw_entry in all_data]
            
    conn.commit()
    c.close()
    return r    
    
    
def get_categories():
    ''' 
    get a list of categories and the number of entries in each category 
    returns a list of dict(category, count)
    '''
    
    c = conn.cursor()
    c.execute(
        """
        select category, count(*)
        from entry
        group by category
        """);
    
    all_data = c.fetchall()
    r = [dict(category = t[0], count = t[1]) for t in all_data]
    
    conn.commit()
    c.close()
    return r     

def get_archives():
    ''' 
    get a list of archives by date and the number of entries in each archive 
    returns a list of dict(archive, count)
    '''
    
    c = conn.cursor()
    c.execute(
        """
        select strftime('%Y%m', create_time), count(*)
        from entry
        group by strftime('%Y%m', create_time)
        """);
    
    all_data = c.fetchall()
    r = [dict(archive = t[0], count = t[1]) for t in all_data]
    
    conn.commit()
    c.close()
    return r 

def pages_max():
    ''' 
    get the number of pages
    '''

    c = conn.cursor()
    
    c.execute("""select count(*) from entry""")
    
    all_data = c.fetchall()
    r = (int(all_data[0][0]) - 1) / ENTRIES_PER_PAGE
    if r < 0:
        r = 0    
    conn.commit()
    c.close()
    return r   


def pages_max_by_category(category):
    ''' 
    get the number of pages of specified category
    '''

    c = conn.cursor()
    
    c.execute(
        """
        select count(*)
        from entry
        where category = ?
        """, (category, ))
    
    all_data = c.fetchall()
    r = (int(all_data[0][0]) - 1) / ENTRIES_PER_PAGE
    if r < 0:
        r = 0
    conn.commit()
    c.close()
    return r  

def pages_max_by_archive(archive):
    ''' 
    get the number of pages of specified archive date
    '''

    c = conn.cursor()
    
    c.execute(
        """
        select count(*)
        from entry
        where strftime('%Y%m', create_time) = ?
        """, (archive, ))
    
    all_data = c.fetchall()
    r = (int(all_data[0][0]) - 1) / ENTRIES_PER_PAGE
    
    conn.commit()
    c.close()
    return r  

def get_siteinfo(info_key, default_val = None):
    ''' 
    get site information specified by info_key
    '''

    c = conn.cursor()
    
    c.execute(
        """
        select value
        from siteinfo
        where key = ?
        """, (info_key, ))
    
    all_data = c.fetchall()
    if len(all_data) > 0:
        r = all_data[0][0]
    else:
        r = default_val
    
    conn.commit()
    c.close()
    return r  

def set_siteinfo(info_key, info_value):
    ''' 
    get site information specified by info_key
    '''

    c = conn.cursor()

    if None == get_siteinfo(info_key):
        
        # if the info_key isn't exist in siteinfo we should create it first
        
        c.execute(
            """
            insert into siteinfo(key, value)
            values(?, ?)
            """, (info_key, info_value))   
    else:
        
        # if it already exists
        
        c.execute(
            """
            update siteinfo
            set value = ?
            where key = ?
            """, (info_value, info_key))          
        
    
    conn.commit()
    c.close()
    
ENTRIES_PER_PAGE = 10
conn = sqlite3.connect('entriesdb')

def _close_conn():
    print 'meidodb: database connection closed.'
    conn.close()

# close the connection before exit

atexit.register(_close_conn)

# if the tables isn't exist, create them first
if False == _table_is_exist('entry'):
    _create_table_entry()
    
if False == _table_is_exist('siteinfo'):
    _create_table_siteinfo()
    
if False == _table_is_exist('comment'):
    _create_table_comment()
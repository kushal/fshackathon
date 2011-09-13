#!/usr/bin/python

import cgi
import logging
import os
import urllib2

from django.utils import simplejson

from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

from model import Team, Vote, increment_vote

class BaseHandler(webapp.RequestHandler):
    def render(self, template_name, template_values):
        #self.response.headers['Content-Type'] = 'text/html'
        path = os.path.join(os.path.dirname(__file__), 'templates/%s.html' % template_name)
        self.response.out.write(template.render(path, template_values))
        
            
class ReceiveVote(BaseHandler):
  def post(self):
    vote = self.request.get('vote')
    increment_vote(users.get_current_user(), vote)
    self.render('vote_received', {})


class Winners(BaseHandler):
  """Fetches totals"""
  def get(self):
    #TODO(kushal): Support location filter
    all_teams = Team.all().fetch(1000)
    self.render('winners', { 'teams': all_teams })

class ListProjects(BaseHandler): 
  def get(self):  
    #TODO(kushal): Support location filter
    all_teams = Team.all().fetch(1000)
    self.render('vote', { 'teams': all_teams })

class ProjectForm(BaseHandler):
  def get(self):  
    self.render('add', { })

class AddProject(BaseHandler):    
  def post(self):  
    team = Team()
    team.name = self.request.get('name')
    team.people = self.request.get('people')
    team.location = self.request.get('location')
    team.description = self.request.get('description')
    team.url = self.request.get('url')
    team.video = self.request.get('video')
    team.screenshot = self.request.get('screenshot')
    team.votes = 0
    team.hackday = '092011'
    team.put()
    team.user = users.get_current_user()
    self.render('add_received', { })
    
application = webapp.WSGIApplication([('/', ListProjects),
                                      ('/vote', ReceiveVote),
                                      ('/add', ProjectForm),
                                      ('/doadd', AddProject),
                                      ('/winners', Winners)],
                                     debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()

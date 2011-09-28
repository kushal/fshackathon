#!/usr/bin/python

import logging
from operator import attrgetter
import os
import random
import urllib
import urllib2

from django.utils import simplejson

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

from model import Team, Votes, Comment, vote, unvote, comment

config = { 'enable_voting': False,
           'enable_commenting': True,
           'enable_team_editing': True,
           'enable_team_adding': False,
           'list_teams_randomly': True,
           'highlight_winners': True,
           'admin_domain': 'foursquare.com' }

def filter_hidden(teams):
  if (checkAdmin(users.get_current_user().email())):
    return teams
  else:
    return filter(lambda x: not x.hidden, teams)

def fetchJson(url):
  logging.info('fetching url: ' + url)
  try :
    result = urllib2.urlopen(url).read()
    logging.info('got back: ' + result)
    return simplejson.loads(result)
  except urllib2.URLError, e :
    logging.error(e)


def checkAdmin(user_email):
  return user_email.endswith(config['admin_domain'])


def shouldShowComments():
  return config['enable_commenting'] and checkAdmin(users.get_current_user().email())


def shouldEnableCommenting():
  return config['enable_commenting'] and checkAdmin(users.get_current_user().email())


class BaseHandler(webapp.RequestHandler):
  def render(self, template_name, template_values):
      path = os.path.join(os.path.dirname(__file__), 'templates/%s.html' % template_name)
      self.response.out.write(template.render(path, template_values))

  def get_user_city(self, votes):
    if votes.token is None:
        client_id = 'EPMLCP1Y1MS1U1F3QRQAGZQSLNSGGLD5T5K3OTZUB1CMSKEB'
        redirect_uri = 'http://fshackathon.appspot.com/auth'
        if (self.request.url.find('localhost') > -1):
            client_id = 'QADWWPJPWQEJCBQT3BZ0KHZVDZED2VDHZWI23ZW45PA00OXF'
            redirect_uri = 'http://localhost:8000/auth'
        self.redirect('https://foursquare.com/oauth2/authenticate?client_id=%s&response_type=code&redirect_uri=%s' %
                      (client_id, redirect_uri), False)
        return
    user = fetchJson('https://api.foursquare.com/v2/users/self?oauth_token=%s' % votes.token)
    venue = user['response']['user']['checkins']['items'][0]['venue']['id']
      # TODO: Check here now as cheater protection

    venue_to_city = {
                     '4de0117c45dd3eae8764d6ac': 'San Francisco',
                     '4c5c076c7735c9b6af0e8b72': 'New York',
                     '4b5d0df8f964a5209e5029e3': 'Tokyo',
                     '4c8a35721eafb1f780017835': 'Paris'
                 }
    return venue_to_city.get(venue)
  

class ReceiveComment(BaseHandler):
  def post(self):
    team_key = self.request.get('team_key')
    text = self.request.get('text')
    user = users.get_current_user()
    comment(user, team_key, text)
    self.redirect('/', {})

class ReceiveAnnotation(BaseHandler):
  def post(self):
    team_key = self.request.get('team_key')
    team = Team.get(team_key)
    text = self.request.get('text')
    team.annotation = text
    team.put()
    self.redirect('/', {})
    
class ReceiveHide(BaseHandler):
  def post(self):
    team_key = self.request.get('team_key')
    team = Team.get(team_key)
    hidden = self.request.get('hidden')
    if hidden == 'true':
      team.hidden = True
    else:
      team.hidden = False
    team.put()
    self.redirect('/', {})


class ReceiveVote(BaseHandler):
  # TODO: unvoting, local
  def post(self):
    team_key = self.request.get('team_key')
    undo = self.request.get('undo')
    if undo == '1':
        unvote(users.get_current_user(), team_key)
    else:
        is_local = self.request.get('local')
        # TODO: Verify local
        vote(users.get_current_user(), team_key, is_local)
    self.render('vote_received', {})


class ReceiveAuth(BaseHandler):
  def get(self):
    code = self.request.get('code')
    client_id = 'EPMLCP1Y1MS1U1F3QRQAGZQSLNSGGLD5T5K3OTZUB1CMSKEB'
    client_secret = 'EZYSGRHUEGLRULLLGEYZKSVN1PV0RKWQJL3JL2D5QWQV0XWJ'
    redirect_uri = 'http://fshackathon.appspot.com/auth'
    if (self.request.url.find('localhost') > -1):
        client_id = 'QADWWPJPWQEJCBQT3BZ0KHZVDZED2VDHZWI23ZW45PA00OXF'
        client_secret = 'EIP4CULDABQQRZCL0AKNJYISGRMD43O4XE4QC2LO1OVCFGL5'
        redirect_uri = 'http://localhost:8000/auth'
    result = fetchJson('https://foursquare.com/oauth2/access_token?client_id=%s&client_secret=%s&grant_type=authorization_code&redirect_uri=%s&code=%s' %
                       (client_id, client_secret, urllib.quote_plus(redirect_uri), code))
    token = result['access_token']
    votes = Votes.for_user(users.get_current_user())
    votes.token = token
    votes.put()
    self.redirect('listlocal', False)

class Winners(BaseHandler):
  def get(self):
    if not checkAdmin(users.get_current_user().email()):
      return self.error(403)
    #TODO(kushal): Support location filter
    all_teams = filter_hidden(Team.all().fetch(1000))
    for team in all_teams:
      team.totalvotes = team.votes + team.local_votes
    all_teams.sort(key=attrgetter('totalvotes'))
    self.render('winners', { 'teams': all_teams })

class WinnersLocal(BaseHandler):
  def get(self):
    existing = filter_hidden(Team.for_user(users.get_current_user()))
    votes = Votes.for_user(users.get_current_user())
    city = self.get_user_city(votes)
    if city is None:
        self.render('listlocal_fail', {  })
    else:
      all_teams = filter_hidden(Team.for_city(city))
      all_teams.sort(key=attrgetter('local_votes'))
      self.render('winnerslocal', { 'teams': all_teams, 'city': city, 'team': existing })


class ListProjects(BaseHandler): 
  def get(self):  
    current_user = users.get_current_user()
    votes = Votes.for_user(current_user)
    
    team_comments = {}
    user_comments = {}
      
    if shouldShowComments():
      comments = Comment.all()
      for comment in comments:
        team_key = str(comment.team.key())
        comment.author_name = comment.user.nickname().split('@', 1)[0]
        if not team_key in team_comments:
          team_comments[team_key] = []
        if comment.user == current_user:
          user_comments[team_key] = comment
        team_comments[team_key].append(comment)
            
    all_teams = filter_hidden(Team.all().fetch(1000))
    for team in all_teams:
      team.voted = (team.key() in votes.local_teams or team.key() in votes.teams)
      team_key = str(team.key())
      if shouldShowComments():
        if team_key in team_comments:
          team.comments = team_comments[team_key]
        if team_key in user_comments:
          team.user_comment = user_comments[team_key].text
    
    logout_url = users.create_logout_url("/")

    winning_teams = filter(lambda x: config['highlight_winners'] and x.annotation is not None and x.annotation != '', all_teams)
    all_teams = filter(lambda x: x not in winning_teams, all_teams)

    # Disable randomness for commenting always
    if config["list_teams_randomly"] and not shouldEnableCommenting():
      random.shuffle(all_teams)
      
    self.render('list', { 'teams': all_teams,
                          'winning_teams': winning_teams,
                          'votes': votes,
                          'team_comments': team_comments,
                          'user_comments': user_comments,
                          'highlight_winners': config['highlight_winners'],
                          'enable_voting': config['enable_voting'],
                          'enable_commenting': shouldEnableCommenting(),
                          'logout_url': logout_url })


class ListProjectsLocal(BaseHandler): 
  def get(self):
    votes = Votes.for_user(users.get_current_user())
    city = self.get_user_city(votes)
    if city is None:
        self.render('listlocal_fail', {  })
    else:
        all_teams = filter_hidden(Team.for_city(city))
        votes = Votes.for_user(users.get_current_user())
        for team in all_teams:
            team.voted = (team.key() in votes.local_teams or team.key() in votes.teams)
        self.render('listlocal', { 'city': city, 'teams': all_teams })


class ProjectForm(BaseHandler):
  def get(self):
    existing = Team.for_user(users.get_current_user())
    if config['enable_team_adding']:
      self.render('add', { 'existing': existing })
      return
    if config['enable_team_editing']:
      if existing:
        self.render('add', { 'existing': existing })
      else:
        self.render('noadd', { })


class AddProject(BaseHandler):    
  def post(self):
    if not config['enable_team_adding']:
      self.error(403)
    team = Team.for_user(users.get_current_user())
    if not team:
        team = Team()
    team.name = self.request.get('name')
    team.people = self.request.get('people')
    location = self.request.get('location')
    team.location = self.request.get('location')
    if location == 'Other':
        team.location = self.request.get('otherLocation')
    team.description = self.request.get('description')
    team.url = self.request.get('url')
    team.video = self.request.get('video')
    team.image = self.request.get('image')
    team.winner = self.request.get('winner')
    team.email = self.request.get('email')
    team.votes = 0
    team.hackday = '092011'
    team.user = users.get_current_user()
    team.put()
    self.render('add_received', { })

class TeamPage(BaseHandler):
  def get(self):
    team_key = self.request.get('team_key')
    team = Team.get(team_key)
    votes = Votes.for_user(users.get_current_user())
    team.voted = (team.key() in votes.local_teams or team.key() in votes.teams)
    self.render('team', { 'team': team })
  
    
application = webapp.WSGIApplication([('/', ListProjects),
                                      ('/listlocal', ListProjectsLocal),
                                      ('/vote', ReceiveVote),
                                      ('/docomment', ReceiveComment),
                                      ('/annotate', ReceiveAnnotation),
                                      ('/hide', ReceiveHide),
                                      ('/auth', ReceiveAuth),
                                      ('/add', ProjectForm),
                                      ('/doadd', AddProject),
                                      ('/winners', Winners),
                                      ('/winnerslocal', WinnersLocal),
                                      ('/team', TeamPage)],
                                     debug = True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()

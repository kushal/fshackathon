import logging

from google.appengine.ext import db

class Team(db.Model):
  user = db.UserProperty()
  name = db.StringProperty()
  hackday = db.StringProperty()
  location = db.StringProperty()
  people = db.StringProperty()
  description = db.TextProperty()
  url = db.StringProperty()
  video = db.StringProperty()
  image = db.StringProperty()
  winner = db.TextProperty()
  votes = db.IntegerProperty(default = 0)
  local_votes = db.IntegerProperty(default = 0)

  @staticmethod
  def for_user(user):
    q = Team.all()
    q.filter("user = ", user)
    results = q.fetch(1)
    if len(results):
        return results[0]
    return None
  
  @staticmethod
  def for_city(city):
    return Team.all().filter('location =', city).fetch(1000)


class Votes(db.Model):
  user = db.UserProperty()
  token = db.StringProperty()
  local_teams = db.ListProperty(db.Key)
  teams = db.ListProperty(db.Key)
  @staticmethod
  def for_user(user):
      votes = Votes.get_or_insert(user.email())
      votes.user = user
      return votes


class Comment(db.Model):
  user = db.UserProperty()
  team = db.ReferenceProperty(Team)
  text = db.TextProperty()
  @staticmethod
  def get_comment(user, team):
    query = db.Query(Comment)
    query.filter('user =', user).filter('team =', team)
    result = query.fetch(limit=1)
    for comment in result:
      return comment
    return None
  @staticmethod
  def get_team_comments(team):
    query = db.Query(Comment)
    return query.filter('team =', team)
  @staticmethod
  def get_user_comments(user):
    query = db.Query(Comment)
    return query.filter('user =', user)

def update_team(team_key, amount, is_local):
    team = Team.get(team_key)
    if is_local:
        team.local_votes += amount
    else:
        team.votes += amount
    team.put()


def vote(user, team_key, is_local):
    # TODO: Ideally, this would be a transaction
    # Get user's votes, make sure hasn't already voted for this.
    votes = Votes.for_user(user)
    team_key_obj = db.Key(team_key)
    if (team_key_obj in votes.teams or team_key_obj in votes.local_teams):
        return

    # If so, add to user.
    if is_local:
        votes.local_teams.append(team_key_obj)
    else:
        votes.teams.append(team_key_obj)
    votes.put()

    # Then add to team.
    db.run_in_transaction(update_team, team_key, 1, is_local)
    
    
def unvote(user, team_key):
    # TODO: Ideally, this would be a transaction
    # Get user's votes, make sure has already voted for this. If so, remove from user.
    votes = Votes.for_user(user)
    team_key_obj = db.Key(team_key)
    if team_key_obj in votes.teams:
        votes.teams.remove(team_key_obj)
        db.run_in_transaction(update_team, team_key, -1, False)
        votes.put()
    if team_key_obj in votes.local_teams:
        votes.local_teams.remove(team_key_obj)
        db.run_in_transaction(update_team, team_key, -1, True)
        votes.put()

def comment(user, team_key, text):
  team = Team.get(team_key)
  if not team:
    logging.debug('NO TEAM: ' + team_key)
    return
  comment = Comment.get_comment(user, team)
  if comment:
    comment.text = text
    comment.put()
    return
  comment = Comment(user=user, team=team, text=text)
  logging.debug('Comment stored: ' + text)
  comment.put()

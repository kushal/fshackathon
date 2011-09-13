from google.appengine.ext import db

class Team(db.Model):
  user = db.UserProperty()
  name = db.StringProperty()
  hackday = db.StringProperty()
  location = db.StringProperty()
  people = db.StringProperty()
  description = db.StringProperty()
  url = db.StringProperty()
  video = db.StringProperty()
  screenshot = db.StringProperty()
  votes = db.IntegerProperty()
  
class Vote(db.Model):
  user = db.UserProperty()
  team = db.ReferenceProperty(Team)

def update_team(team_id, amount):
    team = Team.get(team_id)
    team.votes += amount
    team.put()
    
def update_vote(user, team, vote):
    if vote is None:
        vote = Vote(key_name = user.email())
        vote.user = user
    vote.team = team
    vote.put()
        
def increment_vote(user, team):
    vote = Vote.get_by_key_name(user.email())
    if vote:
        db.run_in_transaction(update_team, vote.team.key(), -1)
    db.run_in_transaction(update_team, team, 1)
    db.run_in_transaction(update_vote, user, Team.get(team), vote)
    
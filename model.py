from google.appengine.ext import db

class Team(db.Model):
  name = db.StringProperty()
  location = db.StringProperty()
  description = db.StringProperty()
  url = db.StringProperty()
  video = db.StringProperty()
  votes = db.IntegerProperty()
  hackday = db.StringProperty()
  user = db.UserProperty()
  
class Vote(db.Model):
  user = db.UserProperty()
  vote = db.ReferenceProperty(Team)

def do_increment_vote(user, team_to_vote_for):
    vote = Vote.get_by_key_name(user.email())
    if vote:
        old_team = vote.team
        old_team.votes -=1
        old_team.put()
    else:
        vote = Vote(ke_namey = user.email())
        vote.user = user
    team = Team.get_by_key_name(team_to_vote_for)
    team.votes += 1
    team.put()
    vote.put()
        
def increment_vote(user, team):
    db.run_in_transaction(do_increment_vote, user, team)
    
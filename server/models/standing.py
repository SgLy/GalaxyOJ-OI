from .. import db, app

class Standing(db.Model):
    """standing model."""

    id = db.Column(db.Integer, primary_key=True)

    contest_id = db.Column(db.Integer, db.ForeignKey('contest.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    problem_id = db.Column(db.Integer, db.ForeignKey('problem.id'))

    score = db.Column(db.Integer, default=0)
    score2 = db.Column(db.Integer, default=0)

    #only the last submission is valid
    def add_record(self, score, intime):
        if self.score2 is None: self.score2 = 0
        if intime: 
            self.score = score
            self.score2 = max(self.score2, score)
        else: 
            self.score2 = max(self.score2, score)

    def __repr__(self):
        return '<Standing %d>' % self.id if self.id else '<New Standing>'


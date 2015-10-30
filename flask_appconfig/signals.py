from flask.signals import Namespace

# signals
signals = Namespace()
db_before_reset = signals.signal('db-before-reset')
db_reset_dropped = signals.signal('db-reset-dropped')
db_reset_created = signals.signal('db-reset-created')
db_after_reset = signals.signal('db-after-reset')

from apscheduler.schedulers.background import BlockingScheduler

from factory import create_app, db
from server.message_queue_handler import MessageQueueHandler

app = create_app()
scheduler = BlockingScheduler()

@scheduler.scheduled_job('interval', minutes=1)
def process_messages():
    with app.app_context():
        MessageQueueHandler.process_message_queue()

if __name__ == '__main__':
    scheduler.start()
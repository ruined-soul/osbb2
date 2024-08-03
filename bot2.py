import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from apscheduler.schedulers.background import BackgroundScheduler

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Database setup
Base = declarative_base()
engine = create_engine('sqlite:///manga_team.db')
Session = sessionmaker(bind=engine)
session = Session()

class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True)
    task = Column(String, nullable=False)
    member = Column(String, nullable=False)
    progress = Column(Float, default=0.0)
    completed = Column(Boolean, default=False)

Base.metadata.create_all(engine)

# Bot commands
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Welcome to the Manga Editing Team Bot!')

def help_command(update: Update, context: CallbackContext) -> None:
    help_text = (
        "Available commands:\n"
        "/start - Welcome message\n"
        "/assign [task] [member] - Assign a task to a member\n"
        "/tasks [member] - List tasks assigned to a member\n"
        "/progress [task_id] [percentage] - Update task progress\n"
        "/help - List all available commands and their functions\n"
        "You can also upload files directly to the bot."
    )
    update.message.reply_text(help_text)

def assign(update: Update, context: CallbackContext) -> None:
    if len(context.args) < 2:
        update.message.reply_text('Usage: /assign [task] [member]')
        return

    task = context.args[0]
    member = context.args[1]
    new_task = Task(task=task, member=member)
    session.add(new_task)
    session.commit()
    update.message.reply_text(f'Task "{task}" assigned to {member}.')

def tasks(update: Update, context: CallbackContext) -> None:
    if not context.args:
        update.message.reply_text('Usage: /tasks [member]')
        return

    member = context.args[0]
    tasks = session.query(Task).filter_by(member=member, completed=False).all()
    if tasks:
        task_list = '\n'.join([f'{task.id}. {task.task} - {task.progress}% complete' for task in tasks])
        update.message.reply_text(f'Tasks for {member}:\n{task_list}')
    else:
        update.message.reply_text(f'No tasks found for {member}.')

def progress(update: Update, context: CallbackContext) -> None:
    if len(context.args) < 2:
        update.message.reply_text('Usage: /progress [task_id] [percentage]')
        return

    task_id = int(context.args[0])
    percentage = float(context.args[1])
    task = session.query(Task).filter_by(id=task_id).first()
    if task:
        task.progress = percentage
        session.commit()
        update.message.reply_text(f'Task "{task.task}" updated to {percentage}% complete.')
    else:
        update.message.reply_text('Task not found.')

def file_upload(update: Update, context: CallbackContext) -> None:
    document = update.message.document
    if document:
        file_path = f'./uploads/{document.file_name}'
        document.get_file().download(custom_path=file_path)
        update.message.reply_text(f'File "{document.file_name}" uploaded successfully.')
    else:
        update.message.reply_text('No file found to upload.')

def main() -> None:
    updater = Updater("7479912271:AAGboB2i4h-Ktc3H2BzAmz0fjBcx_caVffU")

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("assign", assign))
    dispatcher.add_handler(CommandHandler("tasks", tasks))
    dispatcher.add_handler(CommandHandler("progress", progress))
    dispatcher.add_handler(MessageHandler(Filters.document, file_upload))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

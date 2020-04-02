#  Copyright 2019 Christian Kramer
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files
#   (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge,
#   publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do
#   so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
#  LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO
#  EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
#  WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
#  SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import configparser
import copy
import logging
import time
import urllib.request

import schedule
from telegram import ParseMode
from telegram.ext import Updater, CommandHandler

from pageparser import MyHTMLParser

# create cfg parser
config = configparser.ConfigParser()
config.read('settings.ini')


# global infrastructure
update_table = {}
message = ""
table = None
old_table = None

# logging
logger = logging.getLogger()
logger.setLevel(config['DEFAULT']['LogLevel'])
fh = logging.FileHandler('covidbot.log')
fh.setLevel(config['DEFAULT']['LogLevel'])
ch = logging.StreamHandler()
ch.setLevel(config['DEFAULT']['LogLevel'])
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)


# read page content from configured url
def get_site_content():
    logger.debug("Get site content")
    fp = urllib.request.urlopen(config['DEFAULT']['PageUrl'], timeout=60)
    page_content = fp.read()
    page_str = page_content.decode("utf8")
    fp.close()
    logger.debug("Get site content finished")

    global table, old_table

    if page_str:
        parser = MyHTMLParser()
        parser.feed(page_str)
        title, table = parser.get_result()

        logger.debug(str(table))
        logger.debug(str(old_table))

        if str(table) != str(old_table):
            logger.debug("Data has been updated")
            global message
            message = get_message(title, table)
            old_table = copy.deepcopy(table)
            update_table.clear()
        else:
            logger.debug("Data has not changed")

        parser.close()
    else:
        logger.debug("Page content was not available, try again next time")



def get_message(title, table):
    header = ""
    data = ""
    for hstr in title:
        header += hstr + " | "
    for j, tdata in enumerate(table):
        for i, d in enumerate(tdata):
            if j < len(table)-1:
                if i < 2:
                    data += "*" + d + "* | "
                elif i == len(tdata)-1:
                    data += "`" + d + "` | "
                else:
                    data += d + " | "
            else:
                data += "*" + d + "* | "

        data += "\n"
    return header + "\n" + data


def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def check_for_update(context):
    chat_id = context.job.context
    update_status = update_table.get(chat_id)

    if update_status is True or update_status is None:
        context.bot.send_message(chat_id, text=message, parse_mode=ParseMode.MARKDOWN)
        update_table.update({chat_id: False})


def start(update, context):
    update.message.reply_text(
        'Willkommen beim CovidHessenBot. In diesem Chat werden ab jetzt die aktuellen Covid Zahlen in Hessen mitgeteilt')

    chat_id = update.message.chat_id
    update_table.update({chat_id: True})
    try:
        due = int(config['DEFAULT']['ChatJobTimer']) * 60
        if 'job' in context.chat_data:
            old_job = context.chat_data['job']
            old_job.schedule_removal()

        new_job = context.job_queue.run_repeating(check_for_update, due, first=0, context=chat_id)
        context.chat_data['job'] = new_job

        update.message.reply_text('')

    except (IndexError, ValueError):
        update.message.reply_text('Fehler beim Starten des Bots. Versuchen Sie es erneut.')


def cancel(update, context):
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)

    # remove job
    if 'job' not in context.chat_data:
        update.message.reply_text('Keine aktiven Jobs vorhanden.')
        return

    job = context.chat_data['job']
    job.schedule_removal()
    del context.chat_data['job']

    update.message.reply_text('Job erfolgreich gelöscht. Es werden keine weiteren Nachrichten gesendet')


def get_covid_data():
    get_site_content()


def main():
    updater = Updater(config['DEFAULT']['Token'], use_context=True)
    updater.logger = logger
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("cancel", cancel))
    dp.add_handler(CommandHandler("stop", cancel))
    dp.add_error_handler(error)
    get_covid_data()

    updater.start_polling()
    schedule.every(int(config['DEFAULT']['ScrapeJobTimer'])).minutes.do(get_covid_data)


if __name__ == "__main__":
    main()

    while True:
        schedule.run_pending()
        time.sleep(1)

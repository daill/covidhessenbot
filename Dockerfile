FROM python:3
ADD covidhessenbot.py /
ADD pageparser.py /
ADD settings.ini /
ADD safe_scheduler.py /
RUN pip install python-telegram-bot --upgrade
RUN pip install schedule
CMD [ "python", "./covidhessenbot.py" ]
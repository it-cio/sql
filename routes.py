import asyncio
import aioschedule

from data import sql
from asterisk import ami
from telegram import bot
from covid.prognosis import covid_request
from weather.forecast import weather_request


async def weather(greet):
    forecast = await weather_request()
    sql_forecast, sql_id = await asyncio.create_task(sql.select('weather'))

    if forecast != sql_forecast:
        try:
            weather_id = sql_id
            await bot.edit_message(greet + forecast, weather_id)
        except Exception as ex:
            print(f'{ex} (id: {sql_id})')
            weather_id = await bot.send_message(greet + forecast)
            await bot.pin_message(weather_id)
        finally:
            await asyncio.create_task(sql.update('weather', forecast, weather_id))
            await asyncio.sleep(1)


async def covid(greet):
    prognosis = await covid_request()
    sql_prognosis, sql_id = await asyncio.create_task(sql.select('covid'))

    if prognosis != sql_prognosis:
        try:
            covid_id = await bot.send_message(greet + prognosis)
            await asyncio.create_task(sql.update('covid', prognosis, covid_id))
        except Exception as ex:
            print(ex)
        finally:
            await asyncio.sleep(1)


async def ami_listener():
    ami.connect(state=False)
    while True:
        if ami.event:
            print(ami.event[0])
            ami.event = []
        elif ami.caller and ami.number:
            call_id = await bot.send_message(f'Incoming call\nfrom number: {ami.number[0]}\nto number: {ami.caller[0]}')
            ami.number, ami.caller = [], []
        elif ami.status:
            await bot.delete_message(call_id)
            bot.id_list.remove(call_id)
            ami.status = []
        await asyncio.sleep(1)


# choose a time interval to run functions
async def scheduler():
    aioschedule.every(15).to(30).seconds.do(weather, greet='Прогноз погоды: ')
    aioschedule.every(30).seconds.do(covid, greet='Коронавирус\nоперативные данные\n\n')
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)
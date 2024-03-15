import discord
import json
import sys
import requests
from discord.ext import commands
from discord.utils import get
from config import *
from webserver import keep_alive
from cryptoval import *

client = commands.Bot(command_prefix=PREFIX, intents=discord.Intents.all())

WALLET_DEFAULT = {"balance": 0, "card_name": "БЕЗ НАЗВАНИЯ"}


async def get_user_wallet(user_id):
    user_id = str(user_id)

    with open("wallets.json", "r") as file:
        users_wallets = json.load(file)

    if user_id not in users_wallets.keys():
        users_wallets[user_id] = WALLET_DEFAULT

    with open("wallets.json", "w") as file:
        json.dump(users_wallets, file)

    print(users_wallets[user_id])

    return users_wallets[user_id]


async def set_user_wallet(user_id, parameter, new_value):
    user_id = str(user_id)

    with open("wallets.json", "r") as file:
        users_wallets = json.load(file)

    if user_id not in users_wallets.keys():
        users_wallets[user_id] = WALLET_DEFAULT

    users_wallets[user_id][parameter] = new_value

    with open("wallets.json", "w") as file:
        json.dump(users_wallets, file)


@client.event
async def on_ready():
    print("банк работает")


# БАЛАНС
@client.command()
async def bal(ctx, user_mention=None):
    if user_mention != None:
        user = get(ctx.guild.members, id=int(user_mention[2:-1]))
        user_wallet = await get_user_wallet(user.id)
        embedVar = discord.Embed(title=f"<:icon_buster:1137360691569905714> КАРТА {user_wallet['card_name']}",
                                 color=0x2b2d32)
        embedVar.add_field(name="НА СЧЕТУ",
                           value=f"{user_wallet['balance']} АР(-ОВ)",
                           inline=False)
        await ctx.reply(embed=embedVar)

    else:
        user = get(ctx.guild.members, id=ctx.author.id)
        user_wallet = await get_user_wallet(user.id)
        embedVar = discord.Embed(title=f"<:icon_buster:1137360691569905714> КАРТА {user_wallet['card_name']}",
                                 color=0x2b2d32)
        embedVar.add_field(name="НА СЧЕТУ",
                           value=f"{user_wallet['balance']} АР(-ОВ)",
                           inline=False)
        await ctx.reply(embed=embedVar)


# МЕНЯТЬ БАЛАНС
@client.command()
@commands.has_any_role('Банкир')
async def cb(ctx, user_mention=None, amount=None):
    if user_mention is None or amount is None:
        await ctx.send("команда не полная")

    user = get(ctx.guild.members, id=int(user_mention[2:-1]))
    user_wallet = await get_user_wallet(user.id)
    user_wallet["balance"] += int(amount)
    await set_user_wallet(user.id, "balance", user_wallet['balance'])
    await ctx.send(f"счёт {user.name} стал {user_wallet['balance']} ар(-ов)")


# ПЕРЕВОДЫ
@client.command()
async def pay(ctx, komy=None, amount=None):
    if komy is None or amount is None:
        await ctx.send("команда не полная")

    if int(amount) < 1:
        await ctx.send("сумма неверна")

    otprav = get(ctx.guild.members, id=ctx.author.id)
    otprav_wallet = await get_user_wallet(otprav.id)

    print(otprav, otprav_wallet)

    poluch = get(ctx.guild.members, id=int(komy[2:-1]))
    poluch_wallet = await get_user_wallet(poluch.id)

    print(poluch, poluch_wallet)

    if otprav.id == poluch.id:
        await ctx.send("ошибка перевода")
        return

    if otprav_wallet['balance'] < int(amount):
        await ctx.send("ошибка перевода")
        return

    if ctx.author.id == int(komy[2:-1]):
        await ctx.send("ошибка перевода")
    else:
        otprav_wallet["balance"] -= int(amount)
        poluch_wallet["balance"] += int(amount)

        print(otprav_wallet, poluch_wallet)
        await set_user_wallet(otprav.id, "balance", otprav_wallet['balance'])
        await set_user_wallet(poluch.id, "balance", poluch_wallet['balance'])

        embedVar = discord.Embed(title=f"<:icon_buster:1137360691569905714> ПЕРЕВОД УСПЕШЕН!",
                                 color=0x2b2d32)
        embedVar.add_field(name=f"СУММА ПЕРЕВОДА: {amount} АР(-ОВ)",
                           value=f"{otprav.name} --> {poluch.name}",
                           inline=False)
        await ctx.send(embed=embedVar)


# МЕНЯТЬ ИМЯ КАРТЫ
@client.command()
async def cn(ctx, new_name=None):
    if new_name is None:
        await ctx.send("команда не полная")

    user = get(ctx.guild.members, id=ctx.author.id)
    user_wallet = await get_user_wallet(user.id)
    old_name = user_wallet['card_name'].upper()
    await set_user_wallet(user.id, "card_name", new_name.upper())
    embedVar = discord.Embed(title=f"<:icon_buster:1137360691569905714> ОПЕРАЦИЯ УСПЕШНА!",
                             color=0x2b2d32)
    embedVar.add_field(name=f"НАЗВАНИЕ КАРТЫ ИЗМЕНЕНО",
                       value=f"{old_name} --> {new_name.upper()}",
                       inline=False)
    await ctx.send(embed=embedVar)


# ТОП
@client.command()
async def top(ctx):
    with open("wallets.json") as file:
        uw = json.load(file)
    top_name = []
    top_bal = []
    for x in uw:
        y = await get_user_wallet(x)
        top_name.append(x)
        top_bal.append(int(y['balance']))
    max_mass = []
    for j in range(5):
        mx = 0
        mxi = 0
        for i in range(len(top_bal)):
            if mx < top_bal[i]:
                mx = top_bal[i]
                mxi = i
        o = []
        o.append(top_name[mxi])
        o.append(mx)
        top_name.pop(mxi)
        top_bal.pop(mxi)
        max_mass.append(o)

    embedVar = discord.Embed(title=f"<:icon_buster:1137360691569905714> ТОП ИГРОКОВ ПО БАЛАНСУ",
                             color=0x2b2d32)
    embedVar.add_field(name="# 1",
                       value=f"У <@{max_mass[0][0]}> {max_mass[0][1]} АР(-ОВ)",
                       inline=False)
    embedVar.add_field(name="# 2",
                       value=f"У <@{max_mass[1][0]}> {max_mass[1][1]} АР(-ОВ)",
                       inline=False)
    embedVar.add_field(name="# 3",
                       value=f"У <@{max_mass[2][0]}> {max_mass[2][1]} АР(-ОВ)",
                       inline=False)
    embedVar.add_field(name="# 4",
                       value=f"У <@{max_mass[3][0]}> {max_mass[3][1]} АР(-ОВ)",
                       inline=False)
    embedVar.add_field(name="# 5",
                       value=f"У <@{max_mass[4][0]}> {max_mass[4][1]} АР(-ОВ)",
                       inline=False)
    await ctx.send(embed=embedVar)


# ХЕЛПА
@client.command()
async def h(ctx):
    await ctx.reply(f"---команды для игроков---\n" \
                    f"b.bal - ваш баланс\n" \
                    f"b.bal @ник - чей-то баланс\n" \
                    f"b.pay @ник <сумма> - перевести кому-то аров\n" \
                    f"b.cn <название> - изменить имя карты\n" \
                    f"b.top - выводит топ игроков по балансу" \
                    f"\n" \
                    f"---команды для банкиров---\n" \
                    f"b.cb @ник <сумма> - изменить баланс на сумму аров")


client.run(token=TOKEN)

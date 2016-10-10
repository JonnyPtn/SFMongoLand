from sopel import module, config, trigger, db, tools, bot, trigger
from sopel.db import SopelDB
import re
import random
import time

def setup(bot):
    bot.playerdb = SopelDB(bot.config)

@module.commands('balance')
def check_balance(bot, trigger):
    balance = bot.playerdb.get_nick_value(trigger.nick,"balance")
    if balance is None:
        bot.reply("Headshoe pic plz...");
    else:
        bot.reply("Your balance is " + str(balance) + " sf::Tokens")

@module.rule('.invite ([\w\[\]]+)')
@module.require_owner
def invite_player(bot,trigger):
    bot.say("Welcome to the game " + trigger.group(1) + ", here's 50 sf::Tokens!")
    bot.playerdb.set_nick_value(trigger.group(1),"balance",50)
    bot.playerdb.set_nick_value(trigger.group(1),"health",50)
    bot.playerdb.set_nick_value(trigger.group(1),"attack",50)
    bot.playerdb.set_nick_value(trigger.group(1),"defense",50)

locations = ["A mysterious cave (easy)", "A majestic castle (hard)", "A creepy pit (medium)"]

monsters = [
    "A rabid Jetman leaps out, aggresively telling you how wrong you are! ",
    "King Gomila comes to meet you at the gates. ",
    "Out of the darkness appears a big smelly Steffi. "]

winStrings = [
    "You point out that actually there's plenty of evidence to the contrary, which causes him to have a psychotic episode and run off into the shadows. ",
    "Without a second thought, you rip his crown off, taking his head with it, and proclaim yourself the new king of Shit Foot Mongo Land. ",
    "You grab a nearby fire and throw it into the pit, immediately burning Steffi to a crisp. He always did like barbecues..."]

loseStrings = [
    "Unfortunately, the Jetman was right, and you were wrong. Go back to school! ",
    "They decide that despite your best efforts to look presentable, you're clearly still a scrub, and he swiftly executes you. ",
    "The stench is so overwhelming you pass out. Hours later you wake up, battered, bruised, and without your innocence. "]

winPercs = [90,5,50]

@module.commands('locations')
def list_locations(bot,trigger):
    bot.reply("There are many weird and wonderful places in Shit Foot Mongo Land, I have sent you them in a private message")
    count = 0
    for location in locations:
        bot.say(str(count+1) + ": " + locations[count],trigger.nick)
        count+=1

@module.commands('explore')
def explore_location(bot,trigger):
    location = int(trigger.group(2)) - 1

    #check they haven't already explored this hour
    lastExploreTime = bot.playerdb.get_nick_value(trigger.nick,"lastExploration")
    if lastExploreTime is not None:
        if lastExploreTime > time.time() - 600:
            bot.reply("You're too tired to explore again, chill")
            return

    bot.playerdb.set_nick_value(trigger.nick,"lastExploration",int(time.time()))
    message = monsters[location]
    win = random.randint(0,100)
    if win < winPercs[location]:
        message += winStrings[location]
        change = 100/winPercs[location]
    else:
        change = -100/winPercs[location]
        message += loseStrings[location]

    #chance of stat change related to difficulty
    if random.randint(0,100) > winPercs[location] :
        message += "Your stats have been affected: "
        #50\50 attack or defense
        if random.randint(0,1) == 0:
            stat = "attack"
        else:
            stat = "defense"
        message += str(stat) + " "
        current = int(bot.playerdb.get_nick_value(trigger.nick,stat))
        bot.playerdb.set_nick_value(trigger.nick,stat,current+change)
        message += str(change)

    if random.randint(0,100) > winPercs[location] :
        message += " Your balance has been affected: "
        balance = int(bot.playerdb.get_nick_value(trigger.nick,"balance"))
        bot.playerdb.set_nick_value(trigger.nick,"balance",int(balance)+int(change/abs(change) * (100 - winPercs[location])))
        message += str(change/abs(change)*(100 - winPercs[location])) 
    bot.reply(message)

@module.rule('.fite ([\w\[\]]+)')
@module.rule('.fight ([\w\[\]]+)')
def fight(bot, trigger):
    attackerBalance = bot.playerdb.get_nick_value(trigger.nick,"balance")
    if attackerBalance is None:
        bot.reply("You are not part of the game :(")
        return
    defenderBalance = bot.playerdb.get_nick_value(trigger.group(1),"balance")
    if defenderBalance is None:
        bot.reply(trigger.group(1) + " is not part of the game :(")
        return

    if trigger.nick == trigger.group(1):
        bot.reply("You hurt yourself and lost one sf::Token")
        bot.playerdb.set_nick_value(trigger.nick,"balance",int(attackerBalance) - 1)
        return

    #check they haven't already fought in the last 5 mins
    lastFightTime = bot.playerdb.get_nick_value(trigger.nick,trigger.group(1))
    if lastFightTime is not None:
        if lastFightTime > time.time() - 300:
            bot.reply("Don't be such a bully")
            return

    bot.playerdb.set_nick_value(trigger.nick,trigger.group(1),time.time())

    attackerAttack = bot.playerdb.get_nick_value(trigger.nick,"attack")
    if attackerAttack is None:
        attackerAttack = 50
        bot.playerdb.set_nick_value(trigger.nick,"attack",attackerAttack)
    defenderDefense = bot.playerdb.get_nick_value(trigger.group(1),"defense")
    if defenderDefense is None:
           defenderDefense = 50
           bot.playerdb.set_nick_value(trigger.group(1),"defense",defenderDefense)
    result = random.randint(0,int(attackerAttack) + int(defenderDefense))
    if result < attackerAttack:
        winner = trigger.nick
        loser = trigger.group(1)
    else:
        winner = trigger.group(1)
        loser = trigger.nick
    bot.say(winner + " was victorious! They won 1 sf::Token from " + loser)
    winnerbalance = bot.playerdb.get_nick_value(winner,"balance")
    loserbalance = bot.playerdb.get_nick_value(loser,"balance")
    bot.playerdb.set_nick_value(winner,"balance",winnerbalance + 1)
    bot.playerdb.set_nick_value(loser,"balance",loserbalance-1)
    winnerWins = bot.playerdb.get_nick_value(winner,"wins")
    loserLosses = bot.playerdb.get_nick_value(loser,"losses")
    if winnerWins is None:
        winnerWins = 0
    if loserLosses is None:
        loserLosses = 0
    bot.playerdb.set_nick_value(winner,"wins",int(winnerWins) + 1)
    bot.playerdb.set_nick_value(loser,"losses",int(loserLosses) + 1)

@module.rule('.give ([\w\[\]]+) (\d+)')
def give_tokens(bot, trigger):
    if int(trigger.group(2)) == 0:
        bot.reply("Are you mugging me off?")
    if trigger.nick == trigger.group(1):
        bot.reply("You sf::Muppet")
        return
    giverBalance = bot.playerdb.get_nick_value(trigger.nick,"balance")
    if giverBalance is None:
        bot.reply("You aren't part of the game :(")
        return
    receiverBalance = bot.playerdb.get_nick_value(trigger.group(1),"balance")
    if receiverBalance is None:
        bot.say(trigger.group(1) + " is not part of the game :(")
        return
    if int(trigger.group(2)) > int(giverBalance):
        bot.reply("you wish you had that many sf::Tokens")
        return
    bot.say(trigger.nick + " has generously given " + trigger.group(1) + " " + trigger.group(2) + " sf::Tokens")
    bot.playerdb.set_nick_value(trigger.group(1),"balance",receiverBalance + int(trigger.group(2)))
    bot.playerdb.set_nick_value(trigger.nick,"balance",giverBalance - int(trigger.group(2)))

@module.commands('record')
def get_record(bot,trigger):
    wins = bot.playerdb.get_nick_value(trigger.nick,"wins")
    losses = bot.playerdb.get_nick_value(trigger.nick,"losses")
    if wins is None and losses is None:
        bot.reply("You haven't had any fights yet, you kind soul!")
    else:
        if wins is None:
            wins = 0
        if losses is None:
            losses = 0
        bot.reply("Your record is " + str(wins) + ":" + str(losses))

@module.commands('stats')
def get_stats(bot,trigger):
    #use balance to check if valid player
    balance = bot.playerdb.get_nick_value(trigger.nick,"balance")
    if balance is None:
        bot.reply("You are not part of the game :(")
    else:
        attack = bot.playerdb.get_nick_value(trigger.nick,"attack")
        defense = bot.playerdb.get_nick_value(trigger.nick,"defense")
        if attack is None:
            attack = 50
        if defense is None:
            defense = 50
        bot.reply("Your attack is " + str(attack) + " and your defense is " + str(defense))

@module.commands('buy')
def buy_shit(bot,trigger):
    bot.reply("Haha you can't buy stuff")

@module.rule('stfu mongo')
def mug_off_mongo(bot,trigger):
        balance = bot.playerdb.get_nick_value(trigger.nick,"balance")
        bot.action("steals 1 sf::Token from " + trigger.nick + " for being a muggy prick",trigger.sender)
        bot.playerdb.set_nick_value(trigger.nick,"balance",int(balance) - 1)

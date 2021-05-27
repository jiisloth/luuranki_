import os
import json
from twitchio.ext import commands
import random
from dotenv import load_dotenv

load_dotenv()

env = os.environ
path = env['DATAPATH']
# set up the bot
bot = commands.Bot(
    irc_token=env['TMI_TOKEN'],
    client_id=env['CLIENT_ID'],
    nick=env['BOT_NICK'],
    prefix=env['BOT_PREFIX'],
    initial_channels=[env['CHANNEL']]
)

plebcommands = ["!commands", "!reset", "!vote"]
modcommands = ["!set", "!endvote", "!setderust", "rederust"]
mods = ["jiisloth"]

cats = 0

@bot.event
async def event_ready():
    'Called once when the bot goes online.'
    ws = bot._ws  # this is only needed to send messages within event_ready
    await ws.send_privmsg(env['CHANNEL'], "luuranki on täälla taas!")


@bot.event
async def event_message(ctx):
    'Runs every time a message is sent in chat.'

    # make sure the bot ignores itself and the streamer
    if ctx.author.name.lower() == env['BOT_NICK'].lower():
        return

    await bot.handle_commands(ctx)

    # await ctx.channel.send(ctx.content)

    if 'mee töihi' in ctx.content.lower():
        await ctx.channel.send(f"@{ctx.author.name}: Mee ite töihi!")

    if 'vauhtijuoksu' in ctx.content.lower():
        await ctx.channel.send(f"Vauhtijuoksu mainittu! Discordissa tavataan! Vauhtijuoksu.fi")

    if 'luuranki' in ctx.content.lower():
        texts = [
            "What??",
            "Mitä??"
        ]
        await ctx.channel.send(texts[random.randint(0, len(texts)-1)])

    global cats
    if 'catjam' in ctx.content.lower():
        cats += 1
        if cats > 1:
            cats = 0
            await ctx.channel.send(f"catJAM")
    else:
        cats -= 1
        if cats < 0:
            cats = 0

    extracommands = read_json("commands.json")
    for c in extracommands.keys():
        if ctx.content.lower().startswith(c):
            await ctx.channel.send(extracommands[c])


@bot.command(name='reset')
async def c_reset(ctx):
    texts = [
        "taasko vitti?",
        "slotti kerää ittes!",
        "NotLikeThis",
        "L2P",
        "slothpls"
    ]
    await ctx.send(texts[random.randint(0, len(texts)-1)])


@bot.command(name='commands')
async def c_commands(ctx):
    params = ctx.content.split(" ")
    data = read_json("commands.json")
    customcommands = data.keys()
    if len(params) == 1:
        await ctx.send('Try: {} or {}'.format(", ".join(plebcommands), ", ".join(customcommands)))
    else:
        if params[1] in ["mod", "m", "-m", "--mod"]:
            await ctx.send('These commands are for mods only: {}'.format(", ".join(modcommands)))
        elif params[1] in ["all", "a", "--all", "-a"]:
            await ctx.send('Try: {} or {}. Mod commands: {}'.format(", ".join(plebcommands), ", ".join(customcommands), ", ".join(modcommands)))
        else:
            await ctx.send('Try: {} or {}'.format(", ".join(plebcommands), ", ".join(customcommands)))


@bot.command(name='vote')
async def c_commands(ctx):
    params = ctx.content.split(" ")
    if len(params) == 1:
        await ctx.send('You can vote for next game to DERUST or UPKEEP. DERUSTing is a long process so the vote can go on for multiple weeks. UPKEEP is 1-N no reset runs depending on the game. Use "!vote derust" or "!vote upkeep" for more info!')
    if len(params) == 2:
        data = read_json("games.json")
        if params[1].lower() == "derust":
            current = data["current"]["name"]
            gamelist = count_votes(data["derust"])
            await ctx.send('Currently derusting: {}! Use "!vote derust <game>" to vote for next game to be practiced. Current standings: {}'.format(current, ", ".join(gamelist)))
        elif params[1].lower() == "upkeep":
            gamelist = count_votes(data["upkeep"])
            await ctx.send('Use "!vote upkeep <game>" to vote for the next noreset run. Current standings: {}'.format(", ".join(gamelist)))
        else:
            await ctx.send('You can vote for next game to DERUST or UPKEEP. DERUSTing is a long process so the vote can go on for multiple weeks. UPKEEP is 1-N no reset runs depending on the game. Use "!vote derust" or "!vote upkeep" for more info!')
    if len(params) > 2:
        data = read_json("games.json")
        if params[1].lower() == "derust" or params[1].lower() == "upkeep":
            game = get_game(" ".join(params[2:]), data[params[1].lower()])
            if game:
                remove_votes(ctx.author.name, params[1].lower())
                add_vote(ctx.author.name, game, params[1].lower())
                await ctx.send("{} voted for {}".format(ctx.author.name, game))
            else:
                await ctx.send("{} not found in games".format(" ".join(params[2:])))
        else:
            await ctx.send('You can vote for next game to DERUST or UPKEEP. DERUSTing is a long process so the vote can go on for multiple weeks. UPKEEP is 1-N no reset runs depending on the game. Use "!vote derust" or "!vote upkeep" for more info!')


@bot.command(name='set')
async def c_set(ctx):
    if check_mod(ctx):
        params = ctx.content.split(" ")
        if len(params) > 1:
            c = "!" + params[1]
            if len(params) > 2:
                set_command(c, " ".join(params[2:]))
                await ctx.send('Set command {}'.format(c))
            else:
                remove_command(c)
                await ctx.send('Removed command !{}'.format(c))
        else:
            await ctx.send('Moar parameters needed!')
    else:
        await ctx.send(f"@{ctx.author.name}: You do not have enough power!")


@bot.command(name='endvote')
async def c_endvote(ctx):
    if check_mod(ctx):
        params = ctx.content.split(" ")
        if len(params) == 2:
            c = params[1].lower()
            if c == "derust" or c == "upkeep":
                data = read_json("games.json")
                gamelist = count_votes(data[c])
                reset_votes(c)
                await ctx.send('Vote was won by {}! ({}) New vote starting..'.format(gamelist[0], ", ".join(gamelist[1:])))
            else:
                await ctx.send('use !endvote upkeep or !endvote derust!')
        else:
            await ctx.send('use !endvote upkeep or !endvote derust!')
    else:
        await ctx.send(f"@{ctx.author.name}: You do not have enough power!")



@bot.command(name='setderust')
async def c_setderust(ctx):
    if check_mod(ctx):
        params = ctx.content.split(" ")
        if len(params) == 2:
            data = read_json("games.json")
            current = data["current"].copy()
            gamename = get_game(" ".join(params[1:]), data["derust"])
            new = False
            for game in data["derust"]:
                if game["name"] == gamename:
                    new = game.copy()
                    break
            if new:
                data["derust"][:] = [d for d in data["derust"] if d.get('name') != gamename]
                data["upkeep"].append(current)
                data["current"] = new
                write_json("games.json", data)
                await ctx.send('Currently derusting {}!'.format(gamename))
            else:
                await ctx.send('Game not found!')
        else:
            await ctx.send('use !setderust <game>')
    else:
        await ctx.send(f"@{ctx.author.name}: You do not have enough power!")


@bot.command(name='rederust')
async def c_setderust(ctx):
    if check_mod(ctx):
        params = ctx.content.split(" ")
        if len(params) == 2:
            data = read_json("games.json")
            gamename = get_game(" ".join(params[1:]), data["upkeep"])
            new = False
            for game in data["upkeep"]:
                if game["name"] == gamename:
                    new = game.copy()
                    break
            if new:
                data["upkeep"][:] = [d for d in data["upkeep"] if d.get('name') != gamename]
                data["derust"].append(new)
                write_json("games.json", data)
                await ctx.send('Moved {} back to derusting!'.format(gamename))
            else:
                await ctx.send('Game not found!')
        else:
            await ctx.send('use !rederust <game>')
    else:
        await ctx.send(f"@{ctx.author.name}: You do not have enough power!")


def check_mod(ctx):
    if ctx.author.name.lower() in mods:
        return True
    else:
        return False


def count_votes(data):
    total = 0
    games = []
    for game in data:
        votes = len(game["votes"])
        total += votes
        games.append([game["name"], votes])
    random.shuffle(games)
    games = sorted(games, key=lambda x: x[1])[::-1]
    gameslist = []
    for game in games:
        game_str = game[0]
        if total > 0:
            game[1] = str(game[1]/total * 100)+"%"
            game_str += ": " + game[1]
        gameslist.append(game_str)
    return gameslist


def reset_votes(c):
    data = read_json("games.json")
    for game in data[c]:
        game["votes"] = []
    write_json("games.json", data)


def get_game(s, data):
    s = s.lower()
    g = False
    maybe = False
    for game in data:
        for h in game["handles"]:
            if h == s:
                g = game["name"]
            if s in h:
                maybe = game["name"]
    if not g and maybe:
        g = maybe
    return g


def remove_votes(user, category):
    data = read_json("games.json")
    for game in data[category]:
        if user in game["votes"]:
            game["votes"].remove(user)
    write_json("games.json", data)


def add_vote(user, g, category):
    data = read_json("games.json")
    for game in data[category]:
        if g == game["name"]:
            game["votes"].append(user)
    write_json("games.json", data)


def set_command(c, d):
    data = read_json("commands.json")
    data[c] = d
    write_json("commands.json", data)


def remove_command(c):
    data = read_json("commands.json")
    data.pop(c, None)
    write_json("commands.json", data)


def read_json(filename):
    with open(path + filename, 'r') as f:
        data = json.load(f)
    return data


def write_json(filename, data):
    with open(path + filename, 'w') as f:
        json.dump(data, f, indent=2)


def main():
    bot.run()


if __name__ == "__main__":
    main()

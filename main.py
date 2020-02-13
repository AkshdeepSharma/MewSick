import discord
from discord.ext import commands
import asyncio
import config as c
import os
import random
import re

if not discord.opus.is_loaded():
    discord.opus.load_opus('opus')


class JoinVoice:
    def __init__(self, message, player):
        self.channel = message.channel
        self.author = message.author
        self.player = player

    def __str__(self):
        """
        Replaces current str function with formatting for title of video and length.
        :return: string
        """
        request_format = "`{0.title}"
        duration = self.player.duration
        if duration:
            request_format = request_format + " [{0[0]}m {0[1]}s]`".format(divmod(duration, 60))
        return request_format.format(self.player)


class CurrentStatus:
    """
    Keeps track of the current state per each server.
    """
    def __init__(self, bot):
        self.current = None
        self.voice = None
        self.bot = bot
        self.play_next_song = asyncio.Event()
        self.current_queue = asyncio.Queue()
        self.audio_player = self.bot.loop.create_task(self.create_audio_player())

    def is_playing(self):
        """
        Checks if the player is playing any music.
        :return: Boolean
        """
        if self.voice is None or self.current is None:
            return False
        player = self.current.player
        return not player.is_done()

    @property
    def player(self):
        return self.current.player

    def skip(self):
        if self.is_playing():
            self.player.stop()

    def toggle_next(self):
        self.bot.loop.call_soon_threadsafe(self.play_next_song.set)

    async def create_audio_player(self):
        while True:
            self.play_next_song.clear()
            self.current = await self.current_queue.get()
            await self.bot.send_message(self.current.channel, '**Now playing** :notes: {}'.format(str(self.current)))
            self.current.player.start()
            await self.play_next_song.wait()


class Music:
    """
    Music bot commands.
    Must use prefix labelled in bot prefix at bottom of code (default '!')
    """
    def __init__(self, bot):
        self.bot = bot
        self.voice_status = {}

    def get_status(self, server):
        status = self.voice_status.get(server.id)
        if status is None:
            status = CurrentStatus(self.bot)
            self.voice_status[server.id] = status
        return status

    async def create_voice_client(self, channel):
        voice = await self.bot.join_voice_channel(channel)
        status = self.get_status(channel.server)
        status.voice = voice

    def __unload(self):
        for status in self.voice_status.values():
            try:
                status.audio_player.cancel()
                if status.voice:
                    self.bot.loop.create_task(status.voice.disconnect())
            except:
                pass

    @commands.command(pass_context=True)
    async def summon(self, ctx):
        """
        summons the bot into the requester's voice channel.
        :return: boolean
        """
        channel = ctx.message.author.voice.voice_channel
        if not channel:
            await self.bot.say('`Join a voice channel and try again.`')
            return False

        status = self.get_status(ctx.message.server)
        status.voice = await self.bot.join_voice_channel(channel)
        await self.bot.say('`Sup!` :wave:')
        return True

    @commands.command(pass_context=True)
    async def play(self, ctx, url):
        """
        plays the audio of the youtube url given. if no url is given, it instead searches youtube for the song.
        :param url: url of the song. if a legitimate url is not given (i.e. a search term), it searches the criteria on
                    youtube
        :return: None
        """
        status = self.get_status(ctx.message.server)
        print(status)
        options = {
            'default_search': 'auto',
            'quiet': True
        }

        if status.voice is None:
            join = await ctx.invoke(self.summon)
            if not join:
                return 0

        try:
            if url.startswith('http'):
                player = await status.voice.create_ytdl_player(url, ytdl_options=options, after=status.toggle_next)
            else:
                for attr, value in ctx.__dict__.items():
                    url = value.content[6:]
                    print(url)
                    break
                player = await status.voice.create_ytdl_player(url, ytdl_options=options,
                                                               after=status.toggle_next)
            print(player)
        except Exception as e:
            await self.bot.say('Error occurred: ' + str(e))
        else:
            song = JoinVoice(ctx.message, player)
            print(song)
            print(ctx.message)
            await self.bot.say('{} added to queue. :white_check_mark:'.format(str(song)))
            await status.current_queue.put(song)

    @commands.command(pass_context=True)
    async def pause(self, ctx):
        """
        pauses the current player
        :return: None
        """
        status = self.get_status(ctx.message.server)
        if status.is_playing():
            player = status.player
            player.pause()
            await self.bot.say(':pause_button: **Paused** ')

    @commands.command(pass_context=True)
    async def resume(self, ctx):
        """
        resumes the current player after paused
        :return: None
        """
        status = self.get_status(ctx.message.server)
        if status.is_playing():
            player = status.player
            player.resume()
            await self.bot.say(':notes: **Resumed**')

    @commands.command(pass_context=True)
    async def stop(self, ctx):
        """
        stops the current player, deletes the queue.
        :return: None
        """
        status = self.get_status(ctx.message.server)
        if status.is_playing():
            player = status.player
            player.stop()
        try:
            status.audio_player.cancel()
            del self.voice_status[ctx.message.server.id]
            await self.bot.say('`Disconnecting` :wave:')
            await status.voice.disconnect()
        except:
            pass

    @commands.command(pass_context=True)
    async def skip(self, ctx):
        """
        skips the current song.
        :return: None
        """
        status = self.get_status(ctx.message.server)
        if not status.is_playing():
            await bot.say('`Not playing anything.`')
            return 0
        status.skip()
        await self.bot.say(':fast_forward: **Skipped!**')

    @commands.command(pass_context=True)
    async def volume(self, ctx, volume_level=None):
        """
        changes the volume if volume_level. otherwise, returns the current volume level.
        :param volume_level: integer between 0-200
        :return: None
        """
        status = self.get_status(ctx.message.server)
        player = status.player
        if volume_level and 0 <= int(volume_level) <= 200:
            player.volume = int(volume_level) / 100
            await self.bot.say(':loudspeaker: `Volume set to {}'.format(str(int(player.volume * 100))) + '`')
            return
        elif volume_level:
            await self.bot.say(':loudspeaker: `Volume must be between 0 and 200.`')
            return
        await self.bot.say(':loudspeaker: `Volume: {}'.format(str(int(player.volume * 100))) + '`')

    @commands.command(pass_context=True)
    async def disconnect(self, ctx):
        """
        disconnects from the current voice channel. deletes the queue.
        :return: None
        """
        status = self.get_status(ctx.message.server)
        await bot.say('`Disconnecting` :wave:')
        del self.voice_status[ctx.message.server.id]
        await status.voice.disconnect()

    @commands.command(pass_context=True)
    async def queue(self, ctx):
        """
        returns the current queue if there is a queue.
        :return: None
        """
        status = self.get_status(ctx.message.server)
        if status.current_queue and status.is_playing():
            embed = discord.Embed(title='Music Queue')
            embed.add_field(name="`1.` {}".format(str(status.current)), value="------------")
            for i in range(len(status.current_queue._queue)):
                embed.add_field(name="{}. {}".format('`' + str(int(i + 2)) + '`', str(status.current_queue._queue[i])),
                                value="------------")
            await self.bot.say(embed=embed)
            print(status.current_queue)
        else:
            await bot.say('**Nothing in queue.**')


class TextCommands:
    """
    Commands for all text Music and Trivia commands.
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def brother(self, ctx):
        """
        meme.
        :return: None
        """
        await self.bot.say('bröther may I have some lööps https://i.imgur.com/LYjrBTj.jpg')

    @commands.command(pass_context=True)
    async def help(self, ctx):
        """
        help command for bot usage.
        :return: None
        """
        embed = discord.Embed(title='MewSick', description='Music and Trivia bot')
        embed.add_field(name='Author', value='@OAKLAND#0552')
        embed.add_field(name="Invite",
                        value="https://discordapp.com/oauth2/authorize?&client_"
                              "id=482804802003140609&scope=bot&permissions=8", inline=False)
        embed.add_field(name="Commands", value="------------", inline=False)
        embed.add_field(name="!summon", value="Bot joins user's channel.", inline=False)
        embed.add_field(name="!play url",
                        value="Bot will play this YouTube url. You can also search for a song if you don't want to use"
                              "the url (i.e !play walk it talk it). If the bot is not in a channel, it will "
                              "automatically join the requester's channel.", inline=False)
        embed.add_field(name="!pause", value="Pauses the current song.", inline=False)
        embed.add_field(name="!resume", value="Resumes the current song.", inline=False)
        embed.add_field(name="!stop", value="Completely stops audio playback. Current queue is destroyed. "
                                            "Bot disconnects.", inline=False)
        embed.add_field(name="!volume 0-200", value="Changes the bot's volume from 0-200.", inline=False)
        embed.add_field(name="!skip", value="Skips the current song.", inline=False)
        embed.add_field(name="!queue", value="Displays the current queue.", inline=False)
        embed.add_field(name="!disconnect", value="Disconnects the bot.", inline=False)
        embed.add_field(name="!trivia", value="Starts a game of trivia.", inline=False)
        embed.add_field(name="!halt", value="Stops a game of trivia in progress.", inline=False)
        embed.add_field(name="!brother", value="May I have some loops", inline=False)
        embed.add_field(name="!help", value="Sends this message.", inline=False)
        await self.bot.say(embed=embed)


class Trivia:
    """"
    All commands related to the trivia function.
    """
    def __init__(self, bot, win_limit=10, hint_time=15):
        self.bot = bot
        self.win_limit = win_limit
        self.hint_time = hint_time
        self.is_running = False
        self.current_question = None
        self.questions = []
        self.asked = []
        self.scores = {}
        self.trivia_channel = None
        self.cancel = True

        data_questions = os.listdir('trivia')

        for file in data_questions:
            filepath = 'trivia' + os.path.sep + file
            self.load_questions(filepath)
            #print('Loaded:', filepath)
        #print('Trivia questions done loading.')

    def load_questions(self, filepath):
        with open(filepath, encoding='utf-8', errors='replace') as qfile:
            lines = qfile.readlines()

        question = None
        category = None
        answer = None
        regex = None
        position = 0

        while position < len(lines):
            if lines[position].strip().startswith('#'):
                position += 1
                continue
            if lines[position].strip() == '':
                if question is not None and answer is not None:
                    q = Question(question=question, answer=answer, category=category, regex=regex)
                    self.questions.append(q)

                question = None
                category = None
                answer = None
                regex = None
                position += 1
                continue

            if lines[position].strip().lower().startswith('category'):
                category = lines[position].strip()[lines[position].find(':') + 1:].strip()
            elif lines[position].strip().lower().startswith('question'):
                question = lines[position].strip()[lines[position].find(':') + 1:].strip()
            elif lines[position].strip().lower().startswith('answer'):
                answer = lines[position].strip()[lines[position].find(':') + 1:].strip()
            elif lines[position].strip().lower().startswith('regexp'):
                regex = lines[position].strip()[lines[position].find(':') + 1:].strip()
            position += 1

    def trivia_start(self):
        return self.is_running

    def question_in_progress(self):
        return self.current_question is not None

    async def hint(self, hint_question, hint_number):
        if self.is_running and self.current_question is not None:
            await asyncio.sleep(self.hint_time)
            if self.current_question == hint_question and self.cancel is False:
                if hint_number >= 4:
                    await self.next_question(self.trivia_channel)
                hint = self.current_question.get_hint(hint_number)
                await self.bot.say('`Hint {}:` {}'.format(hint_number, hint))
                if hint_number < 4:
                    await self.hint(hint_question, hint_number + 1)

    @commands.command(pass_context=True)
    async def trivia(self, ctx):
        if self.is_running:
            await bot.say('`Trivia already started. Stop it with !halt.`')
        else:
            await self.reset()
            self.trivia_channel = ctx.message.channel
            await self.bot.say('`Trivia starting in 5 seconds...`')
            await asyncio.sleep(5)
            self.is_running = True
            await self.ask_question()

    async def reset(self):
        if self.is_running:
            await self.halt()
        self.current_question = None
        self.cancel = True
        self.is_running = False
        self.questions.append(self.asked)
        self.asked = []
        self.scores = {}

    @commands.command(pass_context=True)
    async def halt(self):
        if self.is_running:
            await self.bot.say('`Trivia stopped.`')
            if self.current_question is not None:
                await self.bot.say('`The correct answer is` **{}**.'.format(self.current_question.get_answer()))
            await self.print_scores()
            self.current_question = None
            self.cancel = True
            self.is_running = False
        else:
            await self.bot.say('`Trivia is currently not running! Start one with !trivia.`')

    async def ask_question(self):
        if self.is_running:
            q = random.randint(0, len(self.questions) - 1)
            self.current_question = self.questions[q]
            self.questions.remove(self.current_question)
            self.asked.append(self.current_question)
            await self.bot.say('`Question {}: {}`'.format(len(self.asked), self.current_question.ask_question()))
            self.cancel = False
            await self.hint(self.current_question, 1)

    async def next_question(self, channel):
        if self.is_running:
            if self.trivia_channel:
                await self.bot.say('`No one got it! The answer is` **{}.** `Next question!`'.format
                                   (self.current_question.get_answer()))
                self.current_question = None
                self.cancel = True
                await self.ask_question()

    async def answer_question(self, message):
        #print('AQ function called.')
        print(self.is_running, self.current_question)
        if self.is_running and self.current_question is not None:
            print('AQ in if.')
            if self.current_question.answer_check(message.content):
                print('right answer')
                self.cancel = True
                if message.author.name in self.scores:
                    self.scores[message.author.name] += 1
                else:
                    self.scores[message.author.name] = 1
                await self.bot.say('**{}** `is correct. The answer was` **{}.**'.format(message.author.name,
                                                                                    self.current_question.get_answer()))

                if self.scores[message.author.name] == self.win_limit:
                    await self.print_scores()
                    await self.bot.say('**{}** `has won! Congratulations!`'.format(message.author.name))
                    self.questions.append(self.asked)
                    self.asked = []
                    self.is_running = False
                elif len(self.asked) % 5 == 0:
                    await self.print_scores()
                await self.ask_question()

    async def print_scores(self):
        if self.is_running:
            await self.bot.say('`Current trivia scores:`')
        else:
            await self.bot.say('`Most recent trivia scores:`')

        highest = 0
        for name in self.scores:
            await self.bot.say('{}: {}'.format(name, self.scores[name]))
            if self.scores[name] > highest:
                highest = self.scores[name]
        if len(self.scores) == 0:
            self.bot.say('**No trivia scores to show.**')

        leaders = []
        for name in self.scores:
            if self.scores[name] == highest:
                leaders.append(name)
        await self.bot.say('`Current leader(s):` **{}**'.format(leaders))


class Question:
    """
    Class for the questions for trivia.
    """
    def __init__(self, question, answer, category=None, regex=None):
        self.question = question
        self.answer = answer
        self.category = category
        self.regex = regex
        self.hints = 0

    def ask_question(self):
        if self.category is None:
            question_text = '(General) '
        else:
            question_text = '({}) '.format(self.category)
        question_text += self.question
        return question_text

    def answer_check(self, answer):
        print('AC function called.')
        if self.regex is not None:
            match = re.fullmatch(self.regex.strip(), answer.strip())
            return match is not None
        return answer.lower().strip() == self.answer.lower().strip()

    def get_hint(self, hint_number):
        hint = []
        for i in range(len(self.answer)):
            if i % 5 < hint_number:
                hint = hint + list(self.answer[i])
            else:
                if self.answer[i] == ' ':
                    hint += '  '
                else:
                    hint += '_ '
        return '`' + ''.join(hint) + '`'

    def get_answer(self):
        return self.answer


bot = commands.Bot(command_prefix='.')
bot.remove_command('help')
bot.add_cog(Music(bot))
bot.add_cog(TextCommands(bot))
bot.add_cog(Trivia(bot))
bot.add_cog(Question)


@bot.event
async def on_ready():
    print("Ready to use!")


@bot.event
async def on_message(message):
    print(Trivia(bot).trivia_start())
    await Trivia(bot).answer_question(message)
    await bot.process_commands(message)

bot.run(c.TOKEN)

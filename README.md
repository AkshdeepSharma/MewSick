# MewSick
Discord music and trivia bot. The trivia part is under construction!
Note: This bot no longer works due to a change in Py3.7 which reserves async as a keyword.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine.

### How to Use

1. Clone this repository
2. Ensure your python version is 3.6 (3.7 and higher will NOT work due to discord.py's versioning)
3. Install the requirements.txt folder using pip
4. Create your own bot and access token from: https://discordapp.com/developers/applications/
5. Copy your bot token and place it within the config.py file
6. Invite your bot to your server
7. Download [ffmpeg](https://www.ffmpeg.org/). Add the directory to your path
7. Run your main.py file either using an IDE or command line
8. Enjoy!

## Commands and Help

Using the bot is easy! It has it's own help command to show you the functions, but I'll include it here!
Note that the default prefix is set to "!" , but it can be changed at the bottom of main.py.

!summon = Summons the bot to the requester's voice channel.

!play url = Bot will play this YouTube url. You can also search for a song if you don't want to use the url (i.e !play 
walk it talk it). If the bot is not in a channel, it will automatically join the requester's channel.

!pause = Pauses the current stream.

!resume = Resumes the current stream.

!stop = Stops the bot and destroys the queue.

!volume (0-200) = Changes the volume from 0-200. If no volume is chosen, it will simply show the current volume.

!skip = Skips the current song.

!queue = Shows the current queue.

!disconnect = Disconnects from the voice channel. The queue is also destroyed.

!trivia = Starts a game of trivia.

!halt = Stops a game of trivia.

!brother = Sends a picture of the meme "Bröther, may I have some lööps?"

!help = Displays a help message with all these commands.

## Built With

- [Python 3.6](https://www.python.org/downloads/release/python-360/)

- [ffmpeg](https://www.ffmpeg.org/)

- [MoxQuizz](moxquizz.de)

## Authors

- **Akshdeep Sharma**

## License

This project is licensed under the MIT License - see the LICENSE.md file for details



### ToDo:

- Trivia functionality:
- Scoring?
- Answer checking doesn't work
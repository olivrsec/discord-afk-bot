# discord-afk-bot

## A simple Discord bot that can automatically(or manually) move inactive users to an afk voice channel. 
The bot also can track a specific user, moves them after a set period of inactivity, and allows them to return to their original channel when they unmute(and contain built-in logs).

# Build it from source
1. clone the repository
`git clone https://github.com/olivrsec/discord-afk-bot.git
 cd discord-afk-bot`
2. install all the dependencies
`pip install -r requirements.txt`
(ensure to install python and pip before)
4. open the script and replace the following IDS with your values:
`idVoiceChannel = YOUR_AFK_VOICE_CHANNEL_ID
idChannel = YOUR_TEXT_CHANNEL_ID
idRole = YOUR_AFK_ROLE_ID
bot.run("YOUR_BOT_TOKEN")`

# Usage
`!autoafk @user` 
start/stop tracking a user for automatic afk.
`!afk @user [reason]`
marks a user(if no user is marked, you  as afk.
`!back @user`
removes afk status from a user and moves them back to the original voice channel.

by default, if the user tracked stays muted on a voice chat for 3 minutes he's moved to the afk channel, to change this time look for the `@tasks.loop` on the script, and change the minutes and the time on seconds right below.

# Contribute
Feel free to submit issues or pull requests if you want to improve the bot.

# License
This project is licensed under the MIT License.

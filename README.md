# About

This project aims to provide an easy way to coordinate players participating to a raid on discord servers, by keeping an auto-updated list of the players and all pratical information about an upcoming Pokemon Go raid.

It is currently used in a few discord servers around Paris and hosted on my personal server, but anyone is welcome to try it and/or contribute to the project.

The bot can be configured to be used alone, but it is advised to use it with [pogo-discord-mod-bot](https://github.com/tama/pogo-discord-mod-bot) for a better "workflow" (create raid channel -> handle raid players -> archive raid channel when raid is finished)

![Screenshot](https://github.com/tama/pogo-discord-raid-bot/blob/master/Capture.PNG?raw=true)

# Installation

## Using the existing Discord bot

You'll need to be an administrator of your discord server.
Simply invite the bot by clicking on [the invite link](https://discordapp.com/oauth2/authorize?client_id=353176813435879424&scope=bot), and give it read/write/manage channels rights.

## Using your own Discord bot

1. Clone this repository.
2. Install `pip` and dependencies required to run the bot.
3. Create a Discord bot and get its token (see [this link](https://github.com/Chikachi/DiscordIntegration/wiki/How-to-get-a-token-and-channel-ID-for-Discord) for an example on how to do it). 
4. Put the token in a `.token` file in the same folder as the `main.py` file.

**WARNING** : Do **not** put a line return at the end of the `.token` file, it should only contain the token and no extra character.

5. Create a `data/{serverid}` subfolder, where `serverid` is the id of the discord server (first number after the /channels part), eg  https://discordapp.com/channels/ **322379168048349185** /343135006681595924.
6. Invite the bot to the server.

If you want extra customization, you can edit the `plugin/default.py` file to set default message, set which messages will be recognized by the bot, which emoji will be used to represent each team etc...

# Contribute

The project is open source and is free to use. Pull requests are welcome.

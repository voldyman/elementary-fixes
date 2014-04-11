elementary Fixes Bot
====================

This twitter bot tweets about the bug fixes made by elementary developers.

##Installation

Rename sample-settings.py as settings.py and fill in the details.

Then just use this command to run the script

    $ python bot.py

##Info

The bot uses coroutines to send data to from the launcpad API to twitter api. Before threads were used but they felt like an overkill.

The coroutines are created and managed using python generators (which are pretty cool)

This bot is still experimental, use at yourown risk :)

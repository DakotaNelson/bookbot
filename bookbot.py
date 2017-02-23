import os
import time
from slackclient import SlackClient


# Resource for setting up slack bots:
# https://www.fullstackpython.com/blog/build-first-slack-bot-python.html

from tind import search_tind


# starterbot's ID as an environment variable
BOT_ID = os.environ.get("BOT_ID")
print BOT_ID

# constants
AT_BOT = "<@" + BOT_ID + ">"
EXAMPLE_COMMAND = "on" # or "about"

# instantiate Slack & Twilio clients
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
print slack_client

def handle_command(command, channel):
    """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
    """
    response = "Not sure what you mean. Try something like '@bookbot, find me a book on programming'"

    if EXAMPLE_COMMAND in command:
        print("command: {}".format(command))
        query = command.split('on')[-1].strip()
        print("query: {}".format(query))
        results = search_tind(query)
        slack_client.api_call("chat.postMessage", channel=channel,
                              text="Here are a few!", as_user=True)

        # only ever show 5 results
        if len(results) > 5:
            results = results[:5]

        for result in results:
            response = "*{}*, by {} ({})".format(result['title'], result['author'], result['link'])
            slack_client.api_call("chat.postMessage", channel=channel,
                                  text=response, as_user=True)
        return

    slack_client.api_call("chat.postMessage", channel=channel,
                          text=response, as_user=True)

def parse_slack_output(slack_rtm_output):
    """
        The Slack Real Time Messaging API is an events firehose.
        this parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and AT_BOT in output['text']:
                # return text after the @ mention, whitespace removed
                return output['text'].split(AT_BOT)[1].strip().lower(), \
                       output['channel']
    return None, None


if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        print("{} connected and running!".format(BOT_ID))
        while True:
            command, channel = parse_slack_output(slack_client.rtm_read())
            if command and channel:
                handle_command(command, channel)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")

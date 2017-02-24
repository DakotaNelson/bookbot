import os
import time
import random
import string

from slackclient import SlackClient

import urllib.parse
import psycopg2
import datetime

# Resource for setting up slack bots:
# https://www.fullstackpython.com/blog/build-first-slack-bot-python.html

from tind import search_tind



# Database stuff
urllib.parse.uses_netloc.append("postgres")
url = urllib.parse.urlparse(os.environ["DATABASE_URL"])

def make_conn():
    global url
    conn = psycopg2.connect(
    database=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port)
    return conn


def interact_with_database(instruction, debug=False):
    """
    debug = True: returns a string that tells you what you just did.
    debug = False: returns only cursor contents.
    """
    store = None
    conn = make_conn()
    with conn.cursor() as cur:
        # try:
        cur.execute(instruction)
        store = [row for row in cur]
        # except:
            # pass
    conn.commit()
    conn.close()
    if debug:
        if store:
            return "Your instruction was " + str(instruction) + " . Cursor output (if any) is: " + str(store)
        else:
            return "Your instruction was " + str(instruction) + " . No cursor output."
    else:
        return store




# starterbot's ID as an environment variable
BOT_ID = os.environ.get("BOT_ID")
print(BOT_ID)

# constants
AT_BOT = "<@" + BOT_ID + ">"
COMMANDS = ["on", "about"]

# instantiate Slack & Twilio clients
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

def handle_command(command, channel):
    """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
    """
    error_msgs = [
        "Not sure what you mean.",
        "I didn't catch that.",
        "Sorry, I'm confused.",
        "What was that?",
        "Huh?",
        "What?"
    ]

    joiners = [
        "Try something like",
        "Perhaps try",
        "I'm looking for things like"
    ]

    examples = [
        "find me a book",
        "I want something",
        "do you have anything",
        "could you find me something",
        "what about some stuff",
        "I'm looking for books",
        "could you do me a favor and refer me to some fine reading material",
        "can you get me something",
        "do you have any books",
        "I want a book",
    ]

    queries = [
        "programming",
        "engineering",
        "cats",
        "dogs",
        "trains",
        "information security",
        "materials science",
        "chemistry",
        "space manufacturing",
        "audio production",
        "chatbots",
        "library science",
        "welding",
        "musical theory",
        "the flight speed of unladen swallows"
    ]

    error = random.choice(error_msgs)
    joiner = random.choice(joiners)
    keyword = random.choice(COMMANDS)
    example = random.choice(examples)
    query = random.choice(queries)

    response = "{} {} '@bookbot, {} {} {}'".format(
        error,
        joiner,
        example,
        keyword,
        query
    )

    # determine if the user used any of our keywords
    tokens = command.split(' ')
    print("tokens:")
    print(tokens)
    keyword_locations = []
    for c in COMMANDS:
        try:
            keyword_locations.append(tokens.index(c))
        except ValueError:
            pass

    try:
        keyword_location = min(keyword_locations)
    except ValueError:
        # no keywords

        slack_client.api_call("chat.postMessage", channel=channel,
                              text=response, as_user=True)
        return

    # elif "events" in command:
    #     now = datetime.datetime.now()
    #     events = interact_with_database("select * from events where event_start between \'%s-%s-%s\' and \'%s-%s-%s\' order by event_start asc" #timestamps in postgres are 'YYYY-MM-DD HH-MM'
    #                             %(str(now.year), str(now.month), str(now.day),
    #                             str(now.year), str(now.month), str(int(now.day)+1)), debug = False)
    #     if events:
    #         for event in events:
    #             response = "Event: {}, Location: {}, Duration: {} to {}, Description: {}, Link: {}".format(event[1], event[5], event[3].time(), event[4].time(), event[6], event[7])
    #             slack_client.api_call("chat.postMessage", channel=channel,
    #                   text=response, as_user=True)
    #     else:
    #         response = "No events found!"
    #
    # slack_client.api_call("chat.postMessage", channel=channel,
    #                       text=response, as_user=True)

    print("command: {}".format(command))

    # parse the query from the command
    query = ' '.join(tokens[keyword_location+1:])
    print("query before cleaning: {}".format(query))
    for ch in string.punctuation:
        # remove punctuation
        query = query.replace(ch, "")
    # remove whitespace
    query = query.strip()
    print("query: {}".format(query))

    results = search_tind(query)
    # TODO what if no search results
    attachments = []

    # only ever show 5 results
    if len(results) > 5:
        results = results[:5]

    for result in results:
        author = result['author']
        title = result['title']
        link = result['link']
        desc = result['description']
        # TODO add some padding so one result with a description doesn't
        # overwhelm the rest
        attachment = {
            "fallback": "{}, by {}".format(title, author),
            "color": "#36a64f",
            # "pretext": "",
            # "author_name": author,
            "title": title,
            "title_link": link,
            "text": desc,
            "footer": "Olin Bookbot"
        }
        attachments.append(attachment)

    response_choices = [
        "Here are a few!",
        "How about these?",
        "Hope this helps!",
        "I found some:",
        "What about these?",
        "I dug up a few:",
        "Maybe these will help:",
        "No problem!"
    ]
    slack_client.api_call("chat.postMessage",
            channel=channel,
            text=random.choice(response_choices),
            attachments=attachments,
            as_user=True)

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

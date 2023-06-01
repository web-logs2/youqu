#Create a list where all elements are strings and expire after 10 seconds.  Do not use database
# cache = Cache(10)
from expiring_dict import ExpiringDict

stop_messages_list = ExpiringDict(max_len=100000, max_age_seconds=10)

def addStopMessages(user_id):
    stop_messages_list[str(user_id)] = True

def inStopMessages(user_id):
    return str(user_id) in stop_messages_list

def removeStopMessages(user_id):
    user_key = str(user_id)
    if user_key in stop_messages_list:
        del stop_messages_list[user_key]
def clearStopMessages():
    stop_messages_list.clear()



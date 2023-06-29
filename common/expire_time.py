import time


# def get_least_frequent_accessed_items(item_dict: dict):
#     for key in item_dict.keys():
#         item_dict[key]['access_frequency']

class ExpireTime(object):
    default_expire_time = time.time() + 60 * 60 * 5
    # default_frequency_duration = 60 * 60

    def __init__(self, expire_time: time = default_expire_time):
        self.expire_time = expire_time
        self.original_setup_time = time.time()
        self.last_access_time = time.time()
        # self.access_frequency_start_time = 0
        # self._access_frequency = 0

    def get_expire_time(self):
        return self.expire_time

    def set_expire_time(self, expire_time):
        self.expire_time = expire_time

    def is_expired(self):
        return self.expire_time < time.time()

    def get_last_access_time(self):
        return self.last_access_time

    def extend_expire_time(self, extend_time):
        self.expire_time += extend_time

    # def reset_access_frequency(self):
    #     self._access_frequency = 0

    # def add_access_frequency(self, default_frequency_duration=default_frequency_duration):
    #     if self.last_access_time + default_frequency_duration < time.time():
    #         self.reset_access_frequency()
    #         self.access_frequency_start_time = time.time()
    #     self._access_frequency += 1

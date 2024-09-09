import datetime as dt

class TimeThis():

    start_time: dt.datetime
    end_time: dt.datetime

    @property
    def time(self) -> dt.timedelta:
        if self.start_time is None or self.end_time is None:
            raise PermissionError("time should only be checked after exiting the 'with' block")
        return self.end_time - self.start_time

    def __enter__(self):
        self.start_time = dt.datetime.now()
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.end_time = dt.datetime.now()

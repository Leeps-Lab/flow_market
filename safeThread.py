import threading


class SafeThread(threading.Thread):
    lock = threading.Lock()
    thread_count = 0

    def __init__(self, func, interval, deadline, infinite):
        threading.Thread.__init__(self)
        self.func = func
        self.interval = interval
        self.deadline = deadline
        self.infinite = infinite
        self.current_timestamp = 0

        SafeThread.lock.acquire()
        self.thread_id = SafeThread.thread_count
        SafeThread.thread_count += 1
        SafeThread.lock.release()

    def start(self):
        if self.current_timestamp + self.interval >= self.deadline - 1:
            print("Stop creating new thread")
            return
        self.thread = threading.Timer(self.interval, self.run)
        self.thread.start()

    def run(self):
        self.current_timestamp += self.interval
        SafeThread.lock.acquire()
        self.func()
        SafeThread.lock.release()
        if self.infinite:
            self.start()

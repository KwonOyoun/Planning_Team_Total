# meeting_session.py
import threading
from queue import Queue
from playwright.sync_api import sync_playwright

class MeetingBrowserSession:
    def __init__(self, headless=False):
        self._queue = Queue()
        self._ready = threading.Event()

        self._thread = threading.Thread(
            target=self._run,
            daemon=True
        )
        self._thread.start()
        self._ready.wait()  # Playwright 준비될 때까지 대기

    def _run(self):
        self.p = sync_playwright().start()
        self.browser = self.p.chromium.launch(headless=False)
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        self.target_frame = None

        self._ready.set()

        while True:
            func, args, result_q = self._queue.get()
            try:
                result = func(*args)
                result_q.put(result)
            except Exception as e:
                result_q.put(e)

    def call(self, func, *args):
        result_q = Queue()
        self._queue.put((func, args, result_q))
        result = result_q.get()
        if isinstance(result, Exception):
            raise result
        return result

    def close(self):
        self.browser.close()
        self.p.stop()

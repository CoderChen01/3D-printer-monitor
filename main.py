from uuid import uuid4

from monitors import LocalMonitor


monitor = LocalMonitor(uuid4(), 200, 1, event_num=5)
ld, lh = monitor.run()

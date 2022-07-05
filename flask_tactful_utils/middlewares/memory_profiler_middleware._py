from pympler import summary, muppy, tracker
import psutil

from guppy import hpy
# from memory_profiler import profile

class MemoryProfiler:
    """ Wraps app in a middleware that logs memory usage after each request
    """

    def __init__(self, app):
        self.app = app
        self.tr = tracker.SummaryTracker()
    
    def __call__(self, environ, start_response):
        res = self.app(environ, start_response)
        
        if '/static' not in environ['PATH_INFO']:
            self.display_memory_usage() 
        return res

    
    def get_virtual_memory_usage_kb(self):
        """
        The process's current virtual memory size in Kb, as a float.
        """
        return float(psutil.Process().memory_info().vms) / 1024.0

    def display_memory_usage(self):
        """
        Print out a basic summary of memory usage.
        """
        # all_objects = muppy.get_objects()
        # mem_summary = summary.summarize(all_objects)
        # summary.print_(mem_summary, limit=5)
        self.tr.print_diff()
        # print("VM: %.2fMb", (get_virtual_memory_usage_kb() / 1024.0))
        # print "line by line", 
        hp = hpy()
        print (hp.heap())

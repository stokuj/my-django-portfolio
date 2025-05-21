# main/observers.py
"""
Implementation of the Observer pattern for visitor counting.
"""
from .models import PageView

class VisitorEvent:
    """
    Subject in the Observer pattern that notifies observers about new visits.
    """
    observers = []
    
    @classmethod
    def register(cls, observer):
        """Register a new observer"""
        cls.observers.append(observer)
    
    @classmethod
    def notify_new_visit(cls, request):
        """Notify all observers about a new visit"""
        for observer in cls.observers:
            observer.update(request)

class VisitorCounter:
    """
    Observer that updates the page view counter when notified about a new visit.
    """
    def update(self, request):
        """Update the page view counter"""
        counter = PageView.get_instance()
        counter.count += 1
        counter.save()

# Register the VisitorCounter as an observer
VisitorEvent.register(VisitorCounter())
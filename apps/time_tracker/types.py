from apps.time_tracker.models import IdleSession, WindowSession

AnySession = WindowSession | IdleSession

from app.services.session_manager import SessionManager


class ApplicationContext:
    """
    Holds application-wide runtime state.
    """

    def __init__(self):
        self.session = SessionManager()


application_context = ApplicationContext()
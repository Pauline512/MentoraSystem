from django.apps import AppConfig


class ProgressTrackingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'progress_tracking'
    verbose_name = 'Progress Tracking'
    
    def ready(self):
        """
        Import signals when the app is ready.
        This can be used for any initialization that needs to happen
        when the app starts up.
        """
        try:
            import progress_tracking.signals
        except ImportError:
            pass
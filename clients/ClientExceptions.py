class NoExecutableException(Exception):
    def __str__(self):
        return "There is no tasks in stack to execute"

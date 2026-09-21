class NoteConflictException(Exception):
    def __init__(self, message: str = "笔记已被更新，请刷新后重试", current_version: int | None = None):
        self.message = message
        self.current_version = current_version
        super().__init__(message)


class NoteAccessDeniedException(Exception):
    def __init__(self, message: str = "报名课程后才能使用课时笔记"):
        self.message = message
        super().__init__(message)

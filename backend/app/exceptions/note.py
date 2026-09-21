class NoteAccessException(Exception):
    """未报名或课时不可见，无权读写课时笔记。"""

    def __init__(self, message: str = "未报名该课程，无法使用课时笔记"):
        self.message = message
        super().__init__(message)


class NoteConflictException(Exception):
    """携带过期版本保存，返回冲突并附带服务端最新内容。"""

    def __init__(self, message: str = "笔记已被更新，请刷新后重试", version: int = 0, content: str = ""):
        self.message = message
        self.version = version
        self.content = content
        super().__init__(message)

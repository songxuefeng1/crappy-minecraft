import json
import os
from typing import Any, Dict, List, Union
from datetime import datetime

class MineCraftErrorHandler(Exception):
    def __init__(self, message: str):
        formatted = f"\033[0m[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] \033[31m{message}"
        super().__init__(formatted)

class FileNotFoundErrorHandler(MineCraftErrorHandler):
    def __init__(self, lostFile: str, message: str = "File not found"):
        full_message = f"{message} File not found `{lostFile}`".strip()
        super().__init__(full_message)
        self.lost_file = lostFile

class JsonFileHandler:
    def __init__(self, file_path: str, encoding: str = "utf-8"):
        """
        初始化JSON操作器
        :param file_path: json文件路径
        :param encoding: 文件编码，默认utf-8
        """
        if not os.path.isabs(file_path):
            file_path = os.path.normpath(os.path.join(os.path.dirname(__file__), file_path))
        self.file_path = file_path
        self.encoding = encoding
        if not os.path.exists(self.file_path):
            raise FileNotFoundErrorHandler(file_path)

    def _write_data(self, data: Union[Dict, List]):
        """底层写入文件私有方法"""
        with open(self.file_path, "w", encoding=self.encoding) as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def read(self) -> Union[Dict, List]:
        """读取整个json文件数据"""
        try:
            with open(self.file_path, "r", encoding=self.encoding) as f:
                return json.load(f)
        except json.JSONDecodeError:
            # 文件内容损坏，重置为空字典
            self._write_data({})
            return {}

    def save(self, data: Union[Dict, List]):
        """覆盖保存全新数据到文件"""
        self._write_data(data)

    def get(self, key: str, default: Any = None):
        """
        获取字典指定key的值
        :param key: 键名
        :param default: 不存在时返回默认值
        """
        data = self.read()
        if isinstance(data, dict):
            return data.get(key, default)
        return default

    def set(self, key: str, value: Any) -> None:
        """新增/修改字典键值对"""
        data = self.read()
        if not isinstance(data, dict):
            data = {}
        data[key] = value
        self._write_data(data)

    def delete_key(self, key: str) -> bool:
        """删除指定key，成功返回True，不存在返回False"""
        data = self.read()
        if isinstance(data, dict) and key in data:
            del data[key]
            self._write_data(data)
            return True
        return False

    def clear(self) -> None:
        """清空json，重置为空字典"""
        self._write_data({})

    def append_list(self, value: Any) -> None:
        """
        向根列表追加数据
        如果当前根是字典，自动转为空列表再追加
        """
        data = self.read()
        if not isinstance(data, list):
            data = []
        data.append(value)
        self._write_data(data)

    def print_format(self) -> None:
        """格式化打印当前json内容"""
        data = self.read()
        print(json.dumps(data, ensure_ascii=False, indent=4))

    def backup(self) -> str:
        """备份当前文件，生成xxx_backup.json，返回备份路径"""
        base, ext = os.path.splitext(self.file_path)
        backup_path = f"{base}_backup{ext}"
        import shutil
        shutil.copy2(self.file_path, backup_path)
        return backup_path

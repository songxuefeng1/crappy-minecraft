from ursina import color
from tkinter import Label, Entry, Button, Tk
import json
from pathlib import Path
from typing import Any



class unitModel:
    def __init__(self, setCol : color, setScale : float, x: int, y: int, z: int, name : str):
        self.color = setCol
        self.scale = setScale
        self.x = x
        self.y = y
        self.z = z
        self.name = name

    def reset(self, setCol : color, setScale : float):
        self.color = setCol
        self.scale = setScale

class inputGroup:
    def get(self):
        return self.enter.get()
    def __init__(self, master : Tk, labelTxt : str, btnInf="确定"):
        self.label = Label(master, text=labelTxt)
        self.enter = Entry(master)

class LocalStorage:
    def __init__(self, filePath: str):
        """初始化，指定存储的 JSON 文件路径"""
        self._file_path = Path(filePath)
        self._data: dict = {}
        self.load()

    def load(self) -> dict:
        """从文件加载数据到内存（自动处理不存在/空文件）"""
        try:
            if self._file_path.exists() and self._file_path.stat().st_size > 0:
                with open(self._file_path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            else:
                self._data = {}
        except (json.JSONDecodeError, Exception):
            self._data = {}
        return self._data

    def save(self, data: Any = None) -> None:
        """保存数据到文件（不传参则保存当前内存数据）"""
        if data is not None:
            self._data = data

        self._file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self._file_path, "w", encoding="utf-8") as f:
            json.dump(
                self._data,
                f,
                indent=4,
                ensure_ascii=False  # 中文不乱码
            )

    def reLocTargetFile(self, filePath: str) -> None:
        """重新定位存储文件（切换存储目标）"""
        self._file_path = Path(filePath)
        self.load()
    
    def getItem(self, key: str) -> Any:
        return self._data.get(key)

    def setItem(self, key: str, value: Any) -> None:
        self._data[key] = value
        self.save()
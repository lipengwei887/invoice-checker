"""
多线程管理模块
处理耗时任务的异步执行，避免 UI 卡死
"""

import threading
import queue
from typing import Callable, List, Optional, Any, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from enum import Enum


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "等待中"
    RUNNING = "运行中"
    COMPLETED = "已完成"
    CANCELLED = "已取消"
    ERROR = "出错"


@dataclass
class TaskInfo:
    """任务信息数据结构"""
    task_id: str
    name: str
    status: TaskStatus
    progress: float  # 0-100
    result: Any = None
    error: Optional[str] = None


class TaskManager:
    """
    任务管理器
    管理多线程任务的提交、执行和回调
    """
    
    def __init__(self, max_workers: int = 4):
        """
        初始化任务管理器
        
        Args:
            max_workers: 最大工作线程数
        """
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.tasks: Dict[str, TaskInfo] = {}
        self.callbacks: Dict[str, Callable] = {}
        self.progress_callbacks: Dict[str, Callable] = {}
        self._lock = threading.Lock()
        self._task_counter = 0
    
    def submit_task(
        self,
        name: str,
        func: Callable,
        *args,
        callback: Optional[Callable] = None,
        progress_callback: Optional[Callable] = None,
        **kwargs
    ) -> str:
        """
        提交任务到线程池
        
        Args:
            name: 任务名称
            func: 要执行的函数
            *args: 函数位置参数
            callback: 完成回调函数 (task_info) -> None
            progress_callback: 进度回调函数 (progress: float) -> None
            **kwargs: 函数关键字参数
            
        Returns:
            任务 ID
        """
        with self._lock:
            self._task_counter += 1
            task_id = f"task_{self._task_counter}_{threading.current_thread().ident}"
        
        # 创建任务信息
        task_info = TaskInfo(
            task_id=task_id,
            name=name,
            status=TaskStatus.PENDING,
            progress=0.0
        )
        
        self.tasks[task_id] = task_info
        
        if callback:
            self.callbacks[task_id] = callback
        
        if progress_callback:
            self.progress_callbacks[task_id] = progress_callback
        
        # 提交任务
        future = self.executor.submit(self._wrap_task, task_id, func, *args, **kwargs)
        future.add_done_callback(self._on_task_done)
        
        return task_id
    
    def submit_pdf_extraction(
        self,
        file_paths: List[str],
        extractor_class,
        callback: Optional[Callable] = None,
        progress_callback: Optional[Callable] = None
    ) -> str:
        """
        提交 PDF 提取任务
        
        Args:
            file_paths: PDF 文件路径列表
            extractor_class: PDF 提取器类
            callback: 完成回调
            progress_callback: 进度回调
            
        Returns:
            任务 ID
        """
        def extraction_task(paths, progress_fn):
            extractor = extractor_class()
            results = []
            total = len(paths)
            
            for i, path in enumerate(paths):
                result = extractor.extract_from_file(path)
                results.append(result)
                
                # 更新进度
                if progress_fn:
                    progress = (i + 1) / total * 100
                    progress_fn(progress)
            
            return results
        
        return self.submit_task(
            "PDF提取",
            extraction_task,
            file_paths,
            progress_callback,
            callback=callback,
            progress_callback=progress_callback
        )
    
    def submit_duplicate_check(
        self,
        invoices: List[Dict],
        checker_class,
        excel_manager=None,
        callback: Optional[Callable] = None,
        progress_callback: Optional[Callable] = None
    ) -> str:
        """
        提交查重任务
        
        Args:
            invoices: 发票数据列表
            checker_class: 查重器类
            excel_manager: ExcelManager 实例
            callback: 完成回调
            progress_callback: 进度回调
            
        Returns:
            任务 ID
        """
        def check_task(inv_list, progress_fn):
            checker = checker_class()
            
            # 分批处理，每批更新进度
            batch_size = max(1, len(inv_list) // 10)
            results = []
            
            for i in range(0, len(inv_list), batch_size):
                batch = inv_list[i:i + batch_size]
                batch_results = checker.check_with_excel_manager(batch, excel_manager)
                results.extend(batch_results)
                
                # 更新进度
                if progress_fn:
                    progress = min(100, (i + batch_size) / len(inv_list) * 100)
                    progress_fn(progress)
            
            if progress_fn:
                progress_fn(100.0)
            
            return results
        
        return self.submit_task(
            "查重任务",
            check_task,
            invoices,
            progress_callback,
            callback=callback,
            progress_callback=progress_callback
        )
    
    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务（尽力而为，无法强制终止已运行的线程）
        
        Args:
            task_id: 任务 ID
            
        Returns:
            是否成功取消
        """
        if task_id in self.tasks:
            task = self.tasks[task_id]
            if task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
                task.status = TaskStatus.CANCELLED
                return True
        return False
    
    def get_task_info(self, task_id: str) -> Optional[TaskInfo]:
        """
        获取任务信息
        """
        return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> List[TaskInfo]:
        """
        获取所有任务信息
        """
        return list(self.tasks.values())
    
    def update_progress(self, task_id: str, progress: float):
        """
        更新任务进度
        
        Args:
            task_id: 任务 ID
            progress: 进度值 (0-100)
        """
        if task_id in self.tasks:
            self.tasks[task_id].progress = max(0, min(100, progress))
            
            # 调用进度回调
            if task_id in self.progress_callbacks:
                try:
                    self.progress_callbacks[task_id](progress)
                except Exception:
                    pass
    
    def shutdown(self, wait: bool = True):
        """
        关闭线程池
        
        Args:
            wait: 是否等待所有任务完成
        """
        self.executor.shutdown(wait=wait)
    
    def _wrap_task(self, task_id: str, func: Callable, *args, **kwargs):
        """
        包装任务函数，处理状态和异常
        """
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        # 检查是否已取消
        if task.status == TaskStatus.CANCELLED:
            return None
        
        task.status = TaskStatus.RUNNING
        
        try:
            # 注入进度回调函数
            def progress_fn(p):
                self.update_progress(task_id, p)
            
            # 如果函数支持进度回调，注入它
            result = func(*args, progress_fn, **kwargs)
            
            if task.status != TaskStatus.CANCELLED:
                task.status = TaskStatus.COMPLETED
                task.result = result
                task.progress = 100.0
            
            return result
            
        except Exception as e:
            task.status = TaskStatus.ERROR
            task.error = str(e)
            raise
    
    def _on_task_done(self, future):
        """
        任务完成回调
        """
        # 查找对应的任务 ID
        task_id = None
        for tid, task in self.tasks.items():
            if task.status in [TaskStatus.COMPLETED, TaskStatus.ERROR]:
                task_id = tid
                break
        
        if not task_id:
            return
        
        # 调用用户回调
        if task_id in self.callbacks:
            try:
                task = self.tasks.get(task_id)
                self.callbacks[task_id](task)
            except Exception:
                pass


class UIThreadHelper:
    """
    UI 线程辅助类
    帮助在非主线程中安全更新 UI
    """
    
    def __init__(self, root_widget):
        """
        Args:
            root_widget: Tkinter/CustomTkinter 根组件
        """
        self.root = root_widget
        self._queue = queue.Queue()
        self._running = True
        
        # 启动队列处理
        self._process_queue()
    
    def run_on_ui(self, func: Callable, *args, **kwargs):
        """
        在主线程执行函数
        
        Args:
            func: 要在主线程执行的函数
            *args, **kwargs: 函数参数
        """
        self._queue.put((func, args, kwargs))
    
    def update_progress_bar(self, progress_bar, value: float):
        """
        安全更新进度条
        
        Args:
            progress_bar: 进度条组件
            value: 进度值 (0-100)
        """
        def update():
            try:
                progress_bar.set(value / 100)  # CustomTkinter 使用 0-1
            except Exception:
                pass
        
        self.run_on_ui(update)
    
    def update_label(self, label, text: str):
        """
        安全更新标签文本
        
        Args:
            label: 标签组件
            text: 新文本
        """
        def update():
            try:
                label.configure(text=text)
            except Exception:
                pass
        
        self.run_on_ui(update)
    
    def _process_queue(self):
        """
        处理 UI 更新队列
        """
        try:
            while not self._queue.empty():
                func, args, kwargs = self._queue.get_nowait()
                try:
                    func(*args, **kwargs)
                except Exception:
                    pass
        except queue.Empty:
            pass
        
        # 继续轮询
        if self._running and self.root:
            self.root.after(50, self._process_queue)
    
    def stop(self):
        """
        停止队列处理
        """
        self._running = False


# ==================== 便捷函数 ====================

def create_task_manager(max_workers: int = 4) -> TaskManager:
    """
    创建任务管理器实例
    
    Args:
        max_workers: 最大工作线程数
        
    Returns:
        TaskManager 实例
    """
    return TaskManager(max_workers=max_workers)


def run_in_thread(
    func: Callable,
    callback: Optional[Callable] = None,
    *args,
    **kwargs
) -> threading.Thread:
    """
    便捷函数：在后台线程运行函数
    
    Args:
        func: 要运行的函数
        callback: 完成回调
        *args, **kwargs: 函数参数
        
    Returns:
        Thread 对象
    """
    def wrapper():
        try:
            result = func(*args, **kwargs)
            if callback:
                callback(result, None)
        except Exception as e:
            if callback:
                callback(None, str(e))
    
    thread = threading.Thread(target=wrapper, daemon=True)
    thread.start()
    return thread

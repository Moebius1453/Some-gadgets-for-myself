import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import os
import sys
import threading
import shutil
import json
from datetime import datetime
import webbrowser
import queue
import time

class UniversalPyToExe:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Python程序打包工具 v3.0")
        self.root.geometry("900x650")
        
        # 设置窗口最小尺寸
        self.root.minsize(800, 600)
        
        # 打包状态
        self.packing = False
        self.process = None
        self.output_queue = queue.Queue()
        
        # 配置文件
        self.config_file = os.path.join(os.path.expanduser('~'), '.pytoexe_config.json')
        
        # 加载上次设置
        self.last_config = self.load_config()
        
        self.setup_ui()
        
    def load_config(self):
        """加载上次的配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def save_config(self):
        """保存当前配置"""
        config = {
            'output_dir': self.output_dir.get(),
            'single_file': self.single_file.get(),
            'no_console': self.no_console.get(),
            'clean_build': self.clean_build.get(),
            'icon_path': self.icon_path.get()
        }
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def setup_ui(self):
        # === 主框架 ===
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # === 标题栏 ===
        title_frame = tk.Frame(main_frame, bg="#2c3e50", height=60)
        title_frame.pack(fill="x", pady=(0, 10))
        title_frame.pack_propagate(False)
        
        tk.Label(title_frame, text="🐍 Python程序打包工具", 
                font=("微软雅黑", 16, "bold"), 
                fg="white", bg="#2c3e50").pack(side="left", padx=20)
        
        # 版本标签
        tk.Label(title_frame, text="v3.0", 
                font=("微软雅黑", 9), 
                fg="#95a5a6", bg="#2c3e50").pack(side="right", padx=20)
        
        # === 创建容器框架（带滚动条） ===
        container_frame = tk.Frame(main_frame)
        container_frame.pack(fill="both", expand=True)
        
        # 创建Canvas和滚动条
        self.canvas = tk.Canvas(container_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container_frame, orient="vertical", command=self.canvas.yview)
        
        # 创建可滚动框架
        self.scrollable_frame = tk.Frame(self.canvas)
        
        # 配置Canvas
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # 将滚动框架添加到Canvas
        window_id = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # 配置滚动区域
        def configure_scroll_region(event):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
        def configure_window_width(event):
            self.canvas.itemconfig(window_id, width=event.width)
        
        self.scrollable_frame.bind("<Configure>", configure_scroll_region)
        self.canvas.bind("<Configure>", configure_window_width)
        
        # 绑定鼠标滚轮
        def on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        self.canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        # 布局Canvas和滚动条
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # === 内容区域（放在滚动框架内）===
        content = tk.Frame(self.scrollable_frame)
        content.pack(fill="x", padx=20, pady=10)
        
        # 创建Notebook选项卡
        notebook = ttk.Notebook(content)
        notebook.pack(fill="both", expand=True)
        
        # 基本设置标签页
        basic_frame = tk.Frame(notebook)
        notebook.add(basic_frame, text="基本设置")
        self.setup_basic_tab(basic_frame)
        
        # 高级设置标签页
        advanced_frame = tk.Frame(notebook)
        notebook.add(advanced_frame, text="高级设置")
        self.setup_advanced_tab(advanced_frame)
        
        # 日志标签页
        log_frame = tk.Frame(notebook)
        notebook.add(log_frame, text="打包日志")
        self.setup_log_tab(log_frame)
        
        # === 底部控制栏 ===
        bottom_frame = tk.Frame(main_frame)
        bottom_frame.pack(fill="x", pady=(10, 0))
        
        # 进度条
        self.progress = ttk.Progressbar(bottom_frame, mode='indeterminate', length=300)
        self.progress.pack(side="left", padx=(0, 10))
        
        # 状态标签
        self.status_label = tk.Label(bottom_frame, text="就绪", 
                                    font=("微软雅黑", 10),
                                    width=30, anchor="w")
        self.status_label.pack(side="left", fill="x", expand=True)
        
        # 操作按钮
        self.pack_button = tk.Button(bottom_frame, text="🚀 开始打包", 
                                    command=self.start_packing,
                                    font=("微软雅黑", 10, "bold"),
                                    width=12,
                                    bg="#27ae60", fg="white")
        self.pack_button.pack(side="right", padx=(5, 0))
        
        self.cancel_button = tk.Button(bottom_frame, text="❌ 停止", 
                                      command=self.cancel_packing,
                                      font=("微软雅黑", 10),
                                      width=8,
                                      bg="#e74c3c", fg="white",
                                      state="disabled")
        self.cancel_button.pack(side="right", padx=5)
        
        # 设置按钮
        tk.Button(bottom_frame, text="⚙️", 
                 command=self.show_settings,
                 font=("微软雅黑", 10),
                 width=3).pack(side="right", padx=5)
        
        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 开始检查输出队列
        self.check_output_queue()
    
    def setup_basic_tab(self, parent):
        content = tk.Frame(parent)
        content.pack(fill="both", expand=True, padx=10, pady=10)
        
        # === 选择Python文件 ===
        file_frame = ttk.LabelFrame(content, text="1. 选择Python文件", padding=15)
        file_frame.pack(fill="x", pady=(0, 15))
        
        ttk.Label(file_frame, text="主程序文件:").pack(anchor="w", pady=2)
        
        file_entry_frame = tk.Frame(file_frame)
        file_entry_frame.pack(fill="x", pady=5)
        
        self.py_file_path = tk.StringVar()
        file_entry = ttk.Entry(file_entry_frame, textvariable=self.py_file_path)
        file_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        ttk.Button(file_entry_frame, text="浏览...", 
                  command=self.browse_py_file).pack(side="left")
        
        # === 程序信息设置 ===
        info_frame = ttk.LabelFrame(content, text="2. 程序信息设置", padding=15)
        info_frame.pack(fill="x", pady=(0, 15))
        
        # 程序名称
        ttk.Label(info_frame, text="程序名称:").grid(row=0, column=0, sticky="w", pady=5)
        
        default_name = self.last_config.get('app_name', 'MyProgram')
        self.app_name = tk.StringVar(value=default_name)
        ttk.Entry(info_frame, textvariable=self.app_name, width=30).grid(
            row=0, column=1, sticky="w", padx=10, pady=5)
        
        # 输出目录
        ttk.Label(info_frame, text="输出目录:").grid(row=1, column=0, sticky="w", pady=5)
        
        default_dir = self.last_config.get('output_dir', os.path.expanduser("~/Desktop"))
        self.output_dir = tk.StringVar(value=default_dir)
        output_entry_frame = tk.Frame(info_frame)
        output_entry_frame.grid(row=1, column=1, sticky="ew", padx=10, pady=5)
        
        output_entry = ttk.Entry(output_entry_frame, textvariable=self.output_dir)
        output_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        ttk.Button(output_entry_frame, text="浏览...", 
                  command=self.browse_output_dir).pack(side="left")
        
        # 程序图标（可选）
        ttk.Label(info_frame, text="程序图标:").grid(row=2, column=0, sticky="w", pady=5)
        
        default_icon = self.last_config.get('icon_path', '')
        self.icon_path = tk.StringVar(value=default_icon)
        icon_entry_frame = tk.Frame(info_frame)
        icon_entry_frame.grid(row=2, column=1, sticky="ew", padx=10, pady=5)
        
        icon_entry = ttk.Entry(icon_entry_frame, textvariable=self.icon_path)
        icon_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        ttk.Button(icon_entry_frame, text="浏览...", 
                  command=self.browse_icon_file).pack(side="left")
        
        # 设置列权重
        info_frame.columnconfigure(1, weight=1)
        
        # === 打包模式 ===
        mode_frame = ttk.LabelFrame(content, text="3. 打包模式", padding=15)
        mode_frame.pack(fill="x", pady=(0, 15))
        
        # 单文件选项
        self.single_file = tk.BooleanVar(value=self.last_config.get('single_file', True))
        single_file_frame = tk.Frame(mode_frame)
        single_file_frame.pack(anchor="w", pady=5)
        
        ttk.Checkbutton(single_file_frame, text="单文件模式", 
                       variable=self.single_file).pack(side="left")
        
        tk.Label(single_file_frame, text="(一个EXE包含所有依赖，可单独发送)",
                font=("微软雅黑", 9), fg="gray").pack(side="left", padx=10)
        
        # 控制台选项
        self.no_console = tk.BooleanVar(value=self.last_config.get('no_console', True))
        console_frame = tk.Frame(mode_frame)
        console_frame.pack(anchor="w", pady=5)
        
        ttk.Checkbutton(console_frame, text="无控制台窗口", 
                       variable=self.no_console).pack(side="left")
        
        tk.Label(console_frame, text="(适合GUI程序)",
                font=("微软雅黑", 9), fg="gray").pack(side="left", padx=10)
        
        # === 优化选项 ===
        opt_frame = ttk.LabelFrame(content, text="4. 优化选项", padding=15)
        opt_frame.pack(fill="x", pady=(0, 15))
        
        # 清理选项
        self.clean_build = tk.BooleanVar(value=self.last_config.get('clean_build', True))
        ttk.Checkbutton(opt_frame, text="打包后清理临时文件", 
                       variable=self.clean_build).pack(anchor="w", pady=2)
        
        # UPX压缩
        self.use_upx = tk.BooleanVar(value=False)
        ttk.Checkbutton(opt_frame, text="使用UPX压缩(减小体积，但可能被误报)", 
                       variable=self.use_upx).pack(anchor="w", pady=2)
        
        # 调试信息
        self.debug_mode = tk.BooleanVar(value=False)
        ttk.Checkbutton(opt_frame, text="包含调试信息(方便排错)", 
                       variable=self.debug_mode).pack(anchor="w", pady=2)
    
    def setup_advanced_tab(self, parent):
        content = tk.Frame(parent)
        content.pack(fill="both", expand=True, padx=10, pady=10)
        
        # === 依赖检测 ===
        deps_frame = ttk.LabelFrame(content, text="依赖检测", padding=15)
        deps_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        ttk.Label(deps_frame, text="检测到的import语句:").pack(anchor="w", pady=2)
        
        # 依赖文本框
        deps_text_frame = tk.Frame(deps_frame)
        deps_text_frame.pack(fill="both", expand=True, pady=5)
        
        self.deps_text = tk.Text(deps_text_frame, height=8,
                                font=("Consolas", 9), wrap="word")
        deps_scrollbar = ttk.Scrollbar(deps_text_frame, command=self.deps_text.yview)
        self.deps_text.configure(yscrollcommand=deps_scrollbar.set)
        
        self.deps_text.pack(side="left", fill="both", expand=True)
        deps_scrollbar.pack(side="right", fill="y")
        
        button_frame = tk.Frame(deps_frame)
        button_frame.pack(fill="x", pady=5)
        
        ttk.Button(button_frame, text="检测依赖", 
                  command=self.detect_dependencies).pack(side="left", padx=(0, 10))
        
        ttk.Button(button_frame, text="清空", 
                  command=lambda: self.deps_text.delete(1.0, tk.END)).pack(side="left")
        
        # === 隐藏导入 ===
        hidden_frame = ttk.LabelFrame(content, text="隐藏导入", padding=15)
        hidden_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(hidden_frame, text="需要手动添加的模块:").pack(anchor="w", pady=2)
        
        hidden_entry_frame = tk.Frame(hidden_frame)
        hidden_entry_frame.pack(fill="x", pady=5)
        
        default_hidden = self.last_config.get('hidden_imports', '')
        self.hidden_imports = tk.StringVar(value=default_hidden)
        ttk.Entry(hidden_entry_frame, textvariable=self.hidden_imports).pack(
            side="left", fill="x", expand=True, padx=(0, 10))
        
        ttk.Button(hidden_entry_frame, text="添加", 
                  command=self.add_hidden_import).pack(side="left")
        
        tk.Label(hidden_frame, text="多个模块用逗号分隔，如：pyautogui,PIL", 
                font=("微软雅黑", 8), fg="gray").pack(anchor="w", pady=2)
        
        # === 额外参数 ===
        args_frame = ttk.LabelFrame(content, text="额外参数", padding=15)
        args_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(args_frame, text="PyInstaller额外参数:").pack(anchor="w", pady=2)
        
        self.extra_args = tk.StringVar()
        ttk.Entry(args_frame, textvariable=self.extra_args).pack(fill="x", pady=5)
        
        tk.Label(args_frame, text="例如：--add-data 'data;data' --add-binary 'lib;lib'", 
                font=("微软雅黑", 8), fg="gray").pack(anchor="w")
        
        # === 快速工具 ===
        tools_frame = ttk.LabelFrame(content, text="快速工具", padding=15)
        tools_frame.pack(fill="x")
        
        tools_buttons = [
            ("📖 PyInstaller文档", lambda: webbrowser.open("https://pyinstaller.org/")),
            ("🗂️ 打开输出目录", self.open_output_dir),
            ("🧹 清理临时文件", self.clean_temp_files),
            ("📊 检查PyInstaller", self.check_pyinstaller)
        ]
        
        for i, (text, command) in enumerate(tools_buttons):
            ttk.Button(tools_frame, text=text, command=command).grid(
                row=i//2, column=i%2, padx=5, pady=5, sticky="ew")
        
        tools_frame.columnconfigure(0, weight=1)
        tools_frame.columnconfigure(1, weight=1)
    
    def setup_log_tab(self, parent):
        content = tk.Frame(parent)
        content.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 日志控制按钮
        log_control_frame = tk.Frame(content)
        log_control_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Button(log_control_frame, text="清空日志", 
                  command=lambda: self.log_text.delete(1.0, tk.END)).pack(side="left", padx=(0, 10))
        
        ttk.Button(log_control_frame, text="保存日志", 
                  command=self.save_log).pack(side="left", padx=(0, 10))
        
        ttk.Button(log_control_frame, text="复制日志", 
                  command=self.copy_log).pack(side="left")
        
        # 日志文本框
        log_text_frame = tk.Frame(content)
        log_text_frame.pack(fill="both", expand=True)
        
        self.log_text = tk.Text(log_text_frame, height=20,
                              font=("Consolas", 9), wrap="word")
        log_scrollbar = ttk.Scrollbar(log_text_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side="left", fill="both", expand=True)
        log_scrollbar.pack(side="right", fill="y")
    
    def check_output_queue(self):
        """检查输出队列并更新界面"""
        try:
            while True:
                message = self.output_queue.get_nowait()
                self.log(message)
        except queue.Empty:
            pass
        finally:
            # 每100ms检查一次队列
            self.root.after(100, self.check_output_queue)
    
    def browse_py_file(self):
        """选择Python文件"""
        file_path = filedialog.askopenfilename(
            title="选择Python主程序文件",
            filetypes=[("Python文件", "*.py"), ("所有文件", "*.*")]
        )
        if file_path:
            self.py_file_path.set(file_path)
            # 自动设置程序名称
            name = os.path.splitext(os.path.basename(file_path))[0]
            self.app_name.set(name)
            self.log(f"📄 已选择文件: {file_path}")
    
    def browse_output_dir(self):
        """选择输出目录"""
        dir_path = filedialog.askdirectory(
            title="选择输出目录"
        )
        if dir_path:
            self.output_dir.set(dir_path)
            self.log(f"📁 输出目录: {dir_path}")
    
    def browse_icon_file(self):
        """选择图标文件"""
        file_path = filedialog.askopenfilename(
            title="选择图标文件",
            filetypes=[("图标文件", "*.ico"), ("PNG文件", "*.png"), ("所有文件", "*.*")]
        )
        if file_path:
            self.icon_path.set(file_path)
            self.log(f"🖼️ 图标文件: {file_path}")
    
    def detect_dependencies(self):
        """检测Python文件的依赖"""
        py_file = self.py_file_path.get()
        if not py_file or not os.path.exists(py_file):
            messagebox.showerror("错误", "请先选择Python文件！")
            return
        
        self.log("🔍 开始检测依赖...")
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            imports = []
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('import ') or line.startswith('from '):
                    imports.append(line)
            
            self.deps_text.delete(1.0, tk.END)
            if imports:
                self.deps_text.insert(tk.END, f"共检测到 {len(imports)} 个导入:\n")
                self.deps_text.insert(tk.END, "="*50 + "\n")
                for imp in imports[:30]:
                    self.deps_text.insert(tk.END, imp + '\n')
                if len(imports) > 30:
                    self.deps_text.insert(tk.END, f"...还有{len(imports)-30}个\n")
                self.deps_text.insert(tk.END, "="*50)
            else:
                self.deps_text.insert(tk.END, "未检测到import语句")
            
            self.log(f"✅ 检测完成，找到{len(imports)}个导入语句")
            
        except Exception as e:
            self.log(f"❌ 检测依赖时出错: {e}")
            messagebox.showerror("错误", f"检测依赖时出错: {e}")
    
    def add_hidden_import(self):
        """添加隐藏导入"""
        hidden = self.hidden_imports.get().strip()
        if hidden:
            self.log(f"➕ 添加隐藏导入: {hidden}")
            self.hidden_imports.set("")
    
    def log(self, message):
        """记录日志（线程安全）"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        
        # 在线程中调用时使用队列
        if threading.current_thread() is not threading.main_thread():
            self.output_queue.put(log_message)
        else:
            self.log_text.insert(tk.END, log_message + "\n")
            self.log_text.see(tk.END)
            self.status_label.config(text=message[:50])
    
    def save_log(self):
        """保存日志到文件"""
        file_path = filedialog.asksaveasfilename(
            title="保存日志文件",
            defaultextension=".log",
            filetypes=[("日志文件", "*.log"), ("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.get(1.0, tk.END))
                self.log(f"💾 日志已保存到: {file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"保存日志失败: {e}")
    
    def copy_log(self):
        """复制日志到剪贴板"""
        log_content = self.log_text.get(1.0, tk.END)
        self.root.clipboard_clear()
        self.root.clipboard_append(log_content)
        self.log("📋 日志已复制到剪贴板")
    
    def open_output_dir(self):
        """打开输出目录"""
        output_dir = self.output_dir.get()
        if os.path.exists(output_dir):
            os.startfile(output_dir)
            self.log(f"📂 打开目录: {output_dir}")
        else:
            messagebox.showwarning("提示", "输出目录不存在！")
    
    def clean_temp_files(self):
        """清理临时文件"""
        if messagebox.askyesno("确认", "清理所有临时文件（build文件夹和.spec文件）？"):
            try:
                cleaned = 0
                
                # 清理当前目录
                if os.path.exists("build"):
                    shutil.rmtree("build")
                    cleaned += 1
                    self.log("🗑️ 清理: build/")
                
                # 清理.spec文件
                for spec_file in os.listdir('.'):
                    if spec_file.endswith('.spec'):
                        os.remove(spec_file)
                        cleaned += 1
                        self.log(f"🗑️ 清理: {spec_file}")
                
                # 清理输出目录中的build
                output_dir = self.output_dir.get()
                build_dir = os.path.join(output_dir, "build")
                if os.path.exists(build_dir):
                    shutil.rmtree(build_dir)
                    cleaned += 1
                    self.log(f"🗑️ 清理: {build_dir}")
                
                if cleaned > 0:
                    self.log(f"✅ 已清理 {cleaned} 个临时项目")
                else:
                    self.log("✅ 没有找到需要清理的临时文件")
                    
            except Exception as e:
                self.log(f"❌ 清理失败: {e}")
    
    def check_pyinstaller(self):
        """检查PyInstaller"""
        try:
            result = subprocess.run(
                ["pyinstaller", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            version = result.stdout.strip() if result.stdout else "未知"
            self.log(f"✅ PyInstaller 版本: {version}")
        except Exception as e:
            self.log(f"❌ PyInstaller 检查失败: {e}")
            self.log("请运行: pip install pyinstaller")
    
    def show_settings(self):
        """显示设置窗口"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("设置")
        settings_window.geometry("500x400")
        settings_window.resizable(False, False)
        
        # 使设置窗口模态
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # 设置内容
        ttk.Label(settings_window, text="高级设置", font=("微软雅黑", 12, "bold")).pack(pady=10)
        
        # Python路径设置
        path_frame = ttk.LabelFrame(settings_window, text="Python路径", padding=10)
        path_frame.pack(fill="x", padx=20, pady=5)
        
        self.python_path = tk.StringVar(value=sys.executable)
        ttk.Entry(path_frame, textvariable=self.python_path).pack(fill="x", pady=5)
        
        # 打包超时设置
        timeout_frame = ttk.LabelFrame(settings_window, text="打包超时（秒）", padding=10)
        timeout_frame.pack(fill="x", padx=20, pady=5)
        
        self.timeout = tk.IntVar(value=300)  # 5分钟
        ttk.Spinbox(timeout_frame, from_=60, to=3600, textvariable=self.timeout, width=10).pack()
        
        # 内存限制
        memory_frame = ttk.LabelFrame(settings_window, text="内存限制（MB）", padding=10)
        memory_frame.pack(fill="x", padx=20, pady=5)
        
        self.memory_limit = tk.IntVar(value=2048)  # 2GB
        ttk.Spinbox(memory_frame, from_=512, to=8192, textvariable=self.memory_limit, width=10).pack()
        
        # 保存设置按钮
        ttk.Button(settings_window, text="保存设置", 
                  command=lambda: self.save_settings(settings_window)).pack(pady=20)
        
        ttk.Button(settings_window, text="取消", 
                  command=settings_window.destroy).pack(pady=5)
    
    def save_settings(self, window):
        """保存设置"""
        # 这里可以添加保存设置到配置文件的代码
        self.log("⚙️ 设置已保存")
        window.destroy()
    
    def start_packing(self):
        """开始打包"""
        py_file = self.py_file_path.get()
        if not py_file or not os.path.exists(py_file):
            messagebox.showerror("错误", "请先选择有效的Python文件！")
            return
        
        if self.packing:
            return
        
        # 确认开始打包
        if not messagebox.askyesno("确认", 
                                  f"确定开始打包吗？\n"
                                  f"程序：{os.path.basename(py_file)}\n"
                                  f"输出到：{self.output_dir.get()}"):
            return
        
        self.packing = True
        self.pack_button.config(state="disabled")
        self.cancel_button.config(state="normal")
        self.progress.start()
        
        # 清空日志
        self.log_text.delete(1.0, tk.END)
        
        # 保存当前配置
        self.save_config()
        
        # 在新线程中打包
        thread = threading.Thread(target=self.pack_in_thread, daemon=True)
        thread.start()
    
    def pack_in_thread(self):
        """在后台线程中执行打包"""
        try:
            py_file = self.py_file_path.get()
            app_name = self.app_name.get()
            icon_path = self.icon_path.get()
            output_dir = self.output_dir.get()
            
            # 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)
            
            # 构建PyInstaller命令
            cmd = ["pyinstaller"]
            
            # 基本选项
            if self.single_file.get():
                cmd.append("--onefile")
            
            if self.no_console.get():
                cmd.append("--windowed")
            else:
                cmd.append("--console")
            
            if icon_path and os.path.exists(icon_path):
                cmd.append(f"--icon={icon_path}")
            
            # 清理选项
            cmd.append("--clean")
            
            # UPX压缩
            if not self.use_upx.get():
                cmd.append("--noupx")
            
            # 调试模式
            if self.debug_mode.get():
                cmd.append("--debug=all")
            
            # 输出路径设置
            cmd.append(f"--distpath={output_dir}")
            cmd.append(f"--workpath={os.path.join(output_dir, 'build')}")
            cmd.append(f"--specpath={output_dir}")
            
            # 添加隐藏导入
            hidden_imports = self.hidden_imports.get().strip()
            if hidden_imports:
                for module in hidden_imports.split(','):
                    module = module.strip()
                    if module:
                        cmd.append(f"--hidden-import={module}")
            
            # 额外参数
            extra_args = self.extra_args.get().strip()
            if extra_args:
                cmd.extend(extra_args.split())
            
            # 程序名称和主文件
            cmd.append(f"--name={app_name}")
            cmd.append(py_file)
            
            self.log("="*70)
            self.log(f"🚀 开始打包: {os.path.basename(py_file)}")
            self.log(f"📁 输出目录: {output_dir}")
            self.log(f"⚙️  打包命令: {' '.join(cmd)}")
            self.log("="*70)
            
            # 执行打包命令（超时设置）
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # 合并输出
                text=True,
                encoding='utf-8',
                errors='ignore',
                bufsize=1,
                universal_newlines=True
            )
            
            # 实时读取输出
            for line in iter(self.process.stdout.readline, ''):
                if line.strip():
                    self.output_queue.put(f"  {line.strip()}")
            
            # 等待进程完成（带超时）
            timeout = 300  # 5分钟
            start_time = time.time()
            
            while self.process.poll() is None:
                if time.time() - start_time > timeout:
                    self.process.terminate()
                    self.log(f"⏰ 打包超时（{timeout}秒），已终止")
                    break
                time.sleep(0.1)
            
            return_code = self.process.wait()
            
            # 检查打包结果
            if return_code == 0 or return_code is None:
                # 根据打包模式确定EXE路径
                if self.single_file.get():
                    exe_path = os.path.join(output_dir, f"{app_name}.exe")
                else:
                    exe_path = os.path.join(output_dir, app_name, f"{app_name}.exe")
                
                if os.path.exists(exe_path):
                    exe_size = os.path.getsize(exe_path) / (1024*1024)  # MB
                    self.log("="*70)
                    self.log(f"✅ 打包成功！")
                    self.log(f"📄 EXE文件: {exe_path}")
                    self.log(f"📏 文件大小: {exe_size:.2f} MB")
                    
                    # 清理build文件夹
                    if self.clean_build.get():
                        build_dir = os.path.join(output_dir, "build")
                        if os.path.exists(build_dir):
                            try:
                                shutil.rmtree(build_dir)
                                self.log(f"🗑️  已清理build文件夹")
                            except Exception as e:
                                self.log(f"⚠️  清理build文件夹失败: {e}")
                    
                    self.log("="*70)
                    
                    # 显示成功消息
                    success_msg = (
                        f"✅ 打包成功！\n\n"
                        f"程序: {app_name}.exe\n"
                        f"大小: {exe_size:.2f} MB\n"
                        f"位置: {output_dir}"
                    )
                    
                    self.root.after(0, lambda: self.show_success_message(success_msg, output_dir, exe_path))
                    
                else:
                    self.log("❌ EXE文件未生成，请检查错误信息")
                    self.root.after(0, lambda: messagebox.showerror(
                        "失败", "EXE文件未生成，请检查错误信息"))
            else:
                self.log(f"❌ 打包失败，返回码: {return_code}")
                self.root.after(0, lambda: messagebox.showerror(
                    "失败", f"打包失败，返回码: {return_code}"))
            
        except Exception as e:
            self.log(f"❌ 打包过程中出错: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror(
                "错误", f"打包过程中出错:\n{str(e)}"))
        
        finally:
            self.packing = False
            self.process = None
            self.root.after(0, self.finish_packing)
    
    def show_success_message(self, message, output_dir, exe_path):
        """显示成功消息"""
        result = messagebox.askyesno("打包成功", 
                                    message + "\n\n是否打开输出文件夹？")
        if result:
            try:
                if os.path.exists(exe_path):
                    # 打开EXE所在文件夹
                    os.startfile(output_dir)
            except:
                self.log(f"无法打开文件夹: {output_dir}")
    
    def finish_packing(self):
        """完成打包后的清理工作"""
        self.pack_button.config(state="normal")
        self.cancel_button.config(state="disabled")
        self.progress.stop()
        self.status_label.config(text="打包完成")
    
    def cancel_packing(self):
        """取消打包"""
        if self.process and self.packing:
            if messagebox.askyesno("确认", "确定要取消打包吗？"):
                try:
                    self.process.terminate()
                    self.log("正在终止打包进程...")
                    self.packing = False
                except:
                    self.log("无法终止进程")
        else:
            messagebox.showinfo("提示", "没有正在运行的打包任务")
    
    def on_closing(self):
        """窗口关闭事件"""
        if self.packing:
            if messagebox.askyesno("确认", "打包正在进行中，确定要退出吗？"):
                try:
                    if self.process:
                        self.process.terminate()
                except:
                    pass
                self.root.destroy()
        else:
            self.root.destroy()
    
    def run(self):
        self.root.mainloop()

def check_dependencies():
    """检查依赖"""
    try:
        import PyInstaller
        return True
    except ImportError:
        result = messagebox.askyesno("依赖缺失", 
                                   "未检测到PyInstaller，是否自动安装？\n需要管理员权限。")
        if result:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
                messagebox.showinfo("成功", "PyInstaller安装成功！")
                return True
            except:
                messagebox.showerror("错误", "安装失败，请手动运行: pip install pyinstaller")
                return False
        return False

if __name__ == "__main__":
    if check_dependencies():
        app = UniversalPyToExe()
        app.run()
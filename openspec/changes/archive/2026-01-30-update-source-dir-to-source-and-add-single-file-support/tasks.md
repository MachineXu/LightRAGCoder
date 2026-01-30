## 1. 代码修改

- [x] 1.1 重命名 `add_source_dir_arg()` 函数为 `add_source_arg()`
- [x] 1.2 修改函数实现，更新帮助文本为 "Comma-separated list of source files or directories"
- [x] 1.3 更新 build 命令调用，使用 `add_source_arg()` 替代 `add_source_dir_arg()`
- [x] 1.4 修改参数解析逻辑，添加路径类型检查（文件 vs 目录）
- [x] 1.5 更新错误提示信息，支持文件和目录的区分验证
- [x] 1.6 确保参数值解析正确处理逗号分隔的文件和目录混合列表
- [x] 1.7 删除所有 `replace('\\', '/')` 斜杠替换操作，并移除 `as_posix()` 调用（storage_setting.py 第131、157行，lightragcoder.py 第149行）
- [x] 1.8 更新 `get_source_dirs_from_settings()` 和 `create_default_settings()` 函数逻辑以支持文件路径
- [x] 1.9 修改 `repo_graphrag/utils/file_reader.py` 中的 `read_dir()` 函数以支持单个文件输入

## 2. 文档更新

- [x] 2.1 搜索所有 `--source-dir` 的出现位置：`grep -r "source-dir" . --include="*.md" --include="*.py"`
- [x] 2.2 更新 README.md 中的命令行示例和参数说明
- [x] 2.3 更新 LightRAGCoder使用说明.md 中的中文文档
- [x] 2.4 更新命令行帮助文本中的示例输出
- [x] 2.5 更新 CHANGELOG.md，添加破坏性变更说明和迁移指南

## 3. 测试验证

- [x] 3.1 测试单个文件输入：`lightragcoder build --source /path/to/file.py --storage-dir test --description "test"`
- [x] 3.2 测试多个逗号分隔文件：`lightragcoder build --source file1.py,file2.js,file3.java --storage-dir test --description "test"`
- [x] 3.3 测试目录输入（保持现有功能）：`lightragcoder build --source /path/to/dir --storage-dir test --description "test"`
- [x] 3.4 测试文件和目录混合输入：`lightragcoder build --source /path/to/dir,file.py --storage-dir test --description "test"`
- [x] 3.5 测试错误处理：不存在的文件/目录、无效路径等
- [x] 3.6 验证帮助文本更新：`lightragcoder build --help` 应显示正确的参数说明
- [x] 3.7 测试跨平台路径兼容性：验证Windows反斜杠路径和Unix正斜杠路径都能正确处理
- [x] 3.8 测试 `file_reader.py` 的单个文件支持：验证单个文件、多个文件、目录和混合输入都能正确读取

## 4. 清理与最终检查

- [x] 4.1 运行项目测试套件（如果有）
- [x] 4.2 确保没有遗漏的 `--source-dir` 引用
- [x] 4.3 检查代码格式和风格一致性
- [x] 4.4 验证所有任务完成后，变更功能完整可用
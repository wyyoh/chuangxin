ConeShare-Guard 使用说明

1. 程序功能
ConeShare-Guard.exe 用于读取一个 BLIF 网表文件，并生成一个功能等价的优化后 BLIF 网表文件。

2. 运行环境
适用于 Windows 64 位命令行环境。
无需安装 Python、pip、PyYAML 或其他第三方依赖。
无需额外提供 bin、configs 或 tools 目录。

3. 单用例运行命令
ConeShare-Guard.exe --input input.blif --output output.blif

也支持位置参数方式：
ConeShare-Guard.exe input.blif output.blif

4. 默认运行方式
将 input.blif 放在当前目录后直接运行：
ConeShare-Guard.exe

程序会读取当前目录下的 input.blif，并生成当前目录下的 output.blif。

5. 等价性验证
验收环境可使用 ABC 工具验证输入输出等价性：
abc -c "cec input.blif output.blif"

如果输出包含 "Networks are equivalent"，表示等价性验证通过。

6. 注意事项
输入文件必须是合法 BLIF 文件。
正常运行时，程序默认只生成用户指定的 output.blif。
默认不生成日志、工作目录、CSV、JSON 或报告文件。
仅在排查问题时，可使用以下命令保留调试信息：
ConeShare-Guard.exe --input input.blif --output output.blif --debug --workdir debug_work

7. 返回码说明
0：运行成功，已生成 output.blif
1：参数错误
2：输入文件不存在或不可读
3：内部 ABC 工具释放失败或无法运行
4：优化失败，但已尝试安全回退
5：无法生成任何有效输出

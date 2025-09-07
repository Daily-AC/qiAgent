### 一些说明
1. 打开to_mofa/agent-hub/qiAgent/qiagent/main.py，修改19行代码，将路径改为你机器上qiagent的绝对路径。
2. 将简历pdf放置to_mofa/examples/qiAgent/input
3. 输出文件在to_mofa/examples/qiAgent/output

### 快速开始
```python
# 用qiAgent的环境即可
dora up
dora build a.yml
dora start a.yml

# 另起终端，注意Python环境切换成qiAgent环境
terminal-input
```
terminal-input启动后输入你放在input里面的pdf文件名即可，.pdf也要加上。
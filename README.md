# CSDN Helper
#### QQ机器人自动下载CSDN资源

## [最新版本下载](https://github.com/y85171642/csdn_helper_pub/releases/latest) *使用方法参考下载包中的 【使用说明】* 

## 1. 开发环境：

* 需要 python3.7 以上版本。

* 安装 requirements.txt 依赖库： ```pip install -r requirements.txt``` (建议使用 [独立环境](https://www.jianshu.com/p/6a3ff66cb8d3) 安装)。

* 运行CoolQ插件：酷Q Air 目录下 CQA.exe。如发生错误，参考下文 **CoolQ 插件使用 注意事项**。

* 配置 csdn_helper/config.ini 配置文件，完成自己想要的配置。

* 在 csdn_helper 目录下运行 coolq.py ```python coolq.py``` （如果有独立Python环境，请切换到独立环境中运行）。

* 尝试 发送QQ消息 ```-help``` 给登录的账户（需要是好友，或者在同一个群组中），验证是否运行成功。

* csdb_helper/db/database.db 是下载信息保存的数据库文件，可使用Sqlite数据库管理软件查看数据。

## 2. CoolQ 使用：

* CoolQ 官网 https://cqp.cc/

* CoolQ Python插件 [python-aiocqhttp](https://github.com/richardchien/python-aiocqhttp)

* CoolQ 插件使用 [注意事项](https://cqhttp.cc/docs/4.10/#/)

  >注意如果 酷Q 启动时报错说插件加载失败，或者系统弹窗提示缺少 DLL 文件，则需要安装 [VC++ 2017 运行库](https://aka.ms/vs/15/release/VC_redist.x86.exe)（**一定要装 x86 也就是 32 位版本！**），如果你的系统是 Windows 7 或 Windows Server 2008、或者安装 VC++ 2017 运行库之后仍然加载失败，则还需要安装 [通用 C 运行库更新](https://support.microsoft.com/zh-cn/help/3118401/update-for-universal-c-runtime-in-windows)，在这个链接里选择你系统对应的版本下载安装即可。如果此时还加载失败，请尝试重启系统。

## 3. Selenium Chrome：

* 需要 Chrome 74以上版本，或替换对应的 [chromedriver 驱动](http://npm.taobao.org/mirrors/chromedriver/)。

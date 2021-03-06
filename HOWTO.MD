# 迁移工具使用方法

迁移工具支持将S3, OSS, Qiniu，文件列表等文件迁移到COS对象存储。工具只支持在 linux/macos 下运行，系统自带的Python版本在2.6以上。

## 系统依赖
工具运行平台为\*nix，需要有Python2.7及以上环境，同时机器应该安装pip, gcc与python-dev。您可以使用系统自带的包管理器安装相关依赖。

在centos上，使用如下命令安装：
```bash
sudo yum install python-pip python-devel gcc gcc-c++ libxml2-devel
```

在ubuntu/debian上，使用如下命令安装：
```bash
sudo apt-get install python-pip python-dev gcc gcc-c++ libxml2-devel
```

## 安装方法

推荐使用pip安装，安装pip的方法，可以参考[官网](https://pip.pypa.io/en/latest/installing/)或者使用apt/yum等包管理工具安装python-pip包。

```bash
 pip install -U cos_migrate_tool_for_restore
```
执行完上述命令后，可以尝试使用如下命令检测是否安装成功。
```bash
cos_migrate_tool_for_restore -h
```

## 卸载方法

执行如下命令：
```
pip uninstall cos_migrate_tool_for_restore
```

## 使用方法

在安装成功后，系统会有一个可执行命令 `cos_migrate_tool_for_restore`，之后的迁移过程都是使用该命令。执行命令的方式如下：

```bash
    cos_migrate_tool_for_restore -c /path/to/your/conf
```

配置文件自行编写，模版参考下章内容。在配置文件中，需要配置一个工作目录，之后迁移过程中产生的临时文件都在放置在该目录，请保证目录空间足够大，如果并行执行多个迁移任务，推荐使用不同的目录。

在迁移过程中，你可以查看你设定的工作目录下面的 fail_file.txt 来查看迁移失败的文件列表。

## 配置文件

配置文件模板, common 部分配置基本配置,workspace是上述的工作目录。source 部分配置数据源的信息，如果你想迁移oss到cos，该部分就是配置oss的属性。destination 部分配置cos属性。

!! 配置文件请删除注释文字，即 `# 注释` 部分，空白模板参考 [链接](https://github.com/tencentyun/cos_migrate_tool_for_restore/tree/master/conf)

```bash
[common]
workspace=/tmp/tmp6   # 工作目录
threads=20            # 工作线程数，如果不配置，则为10线程

[source]
type=oss
accesskeyid=
accesskeysecret=
bucket=
endpoint=

[destination]
type=cosv4
region=shanghai
accesskeyid=
appid=
accesskeysecret=
bucket=sdktest
```

### 迁移OSS

```bash
[common]
workspace=/tmp/tmp6

[source]
type=oss
accesskeyid=         # oss accesskey id
accesskeysecret=     # oss accesskey secret
bucket=              # 要迁移的bucket名
endpoint=            # oss 的endpoint，例如 oss-cn-beijing.aliyuncs.com

[destination]
type=cosv4
region=shanghai            # cos 的 region，如shanghai, guangzhou
accesskeyid=               # cos 的 secretid
appid=                     # cos 的 appid
accesskeysecret=           # cos 的 secretkey
bucket=sdktest             # cos 的 bucket
prefix_dir=/dir21         # cos 的目录，迁移的文件都会位于该目录下，不配置该项则迁移到根目录
overwrite=true             # 覆盖cos上已有的同名文件，如果不需要，请删除该行
```

###  迁移qiniu

```bash
[common]
workspace=/tmp/tmp11
       

[source]
type=qiniu
accesskeyid=               # qiniu 的 accesskeyid
accesskeysecret=           # qiniu 的 accesskeysecret
bucket=                    # 要迁移的qiniu的bucket
domain_url=                # qiniu 的下载域名
prefix=dir1                # 要迁移的目录，如果要迁移整个bucket，删除此行


[destination]
type=cosv4
region=shanghai            # cos 的 region，如shanghai, guangzhou
accesskeyid=               # cos 的 secretid
appid=                     # cos 的 appid
accesskeysecret=           # cos 的 secretkey
bucket=sdktest             # cos 的 bucket
prefix_dir=/dir21         # cos 的目录，迁移的文件都会位于该目录下，不配置该项则迁移到根目录
overwrite=true             # 是否覆盖上传，如果不需要，删除此行
```

### 迁移S3

```bash
[common]
workspace=/tmp/tmp21

[source]
type=s3
accesskeyid=               # s3 的 accesskey id
accesskeysecret=           # s3 的 accesskey secret
bucket=                    # s3 的要迁移的bucket名
prefix=dir1                # s3 的要迁移的目录，如果要迁移整个bucket，删除此行

[destination]
type=cosv4
region=shanghai
accesskeyid=

appid=
accesskeysecret=
bucket=


```

### 迁移列表文件

```bash
[common]
workspace=

[source]
type=url
url_list_file=/tmp/urllist.txt   # 要迁移的文件url列表文件，文件每一行为一个完整的url
timeout=3                        # http请求的超时时间

[destination]
type=cosv4
region=
accesskeyid=
appid=
accesskeysecret=
bucket=
```
### 迁移COSv3
```bash
[common]
workspace=

[source]
type=cosv3
accesskeyid=
appid=
accesskeysecret=
bucket=                     # http请求的超时时间

[destination]
type=cosv4
region=
accesskeyid=
appid=
accesskeysecret=
bucket=
```

### COS v3 迁移到 COS v4

```bash
[common]
workspace=

[source]
type=cosv3
accesskeyid=
appid=
accesskeysecret=
bucket=           

[destination]
type=cosv4
region=
accesskeyid=
appid=
accesskeysecret=
bucket=
```

### COS v4 迁移到 COS v4
```bash
[common]
workspace=

[source]
type=cosv4
accesskeyid=
region=
appid=
accesskeysecret=
bucket=         
prefix_dir=/foo   # cos 的目录，迁移的文件都会位于该目录下，不配置该项则迁移到根目录

[destination]
type=cosv4
region=
accesskeyid=
appid=
accesskeysecret=
bucket=
```

### 常见错误与解决办法

1. pip 命令不存在。 使用 apt install python-pip 或者 yum install python-pip 命令安装PIP。
2. 使用pip安装迁移工具不成功。尝试执行 sudo pip install cos_migrate_tool_for_restore。
3. 提示找不到argparse，使用pip安装 sudo pip install argparse
4. 对于一直迁移不成功的文件，可能是COS上有同名残损文件，可以尝试指定 `overwrite=true` 参数来覆盖。
5. 迁移前工具会先判断文件是否已经在COS上，提示文件不存在的错误的正常的


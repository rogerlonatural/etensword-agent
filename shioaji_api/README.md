
# 倚天劍代理程式(使用永豐金 Shioaji API)安裝說明



## 註冊使用者與代理機

### 取名字

* 為自己的代理機取個名字(不能與其他代理機相同, 且只能由字母、數字、破折號 (-)、半形句號 (.)、底線 (_)、波浪號 (~)、百分比符號 (%) 或加號 (+) 組成，而且開頭必須為英文字母 (但不得以 goog 為開頭)。)
* 用任意工具產生一組 agent_id (GUID), 並將此 GUID 填入設定檔
    * 參考工具: https://www.uuidgenerator.net/
* 將以上資料交給 Roger 註冊, 註冊完會拿到一個金鑰檔(.json), 請妥善保管


### 建立目錄

1. c:\vagrant
2. c:\vagrant_data
3. c:\vagrant_data\<代理程式名稱>
4. c:\vagrant_data\<代理程式名稱>\config

### 複製金鑰檔(.json)

將金鑰檔更名並複製到

c:\vagrant_data\<代理程式名稱>\config\agent_key.json


### 複製憑證

永豐金憑證申請下載: 

* https://www.sinotrade.com.tw/CSCenter/CSCenter_13_1?tab=2
* https://www.spf.com.tw/question/list15c823701f70000039332dfb0ecc46f6.html

預設儲存位置: C:\ekey\551\身分證字號\F\Sinopac.pfx

將憑證複製到 

c:\vagrant_data\<代理程式名稱>\config\Sinopac.pfx


### 建立設定擋

c:\vagrant_data\<代理程式名稱>\config\agent_settings.ini

範本: https://github.com/rogerlonatural/etensword-agent/blob/master/config/agent_settings.ini


### 修改設定檔

* 修改設定值

  ```
  
  [order_agent]
  agent_id=< 填入你的agent_id(GUID) >
  
  [shioaj_api]
  person_id=<身分證字號>
  passwd=<永豐金登入密碼>
  ca_path=/app/config/Sinopac.pfx
  ca_passwd=<永豐金憑證密碼>
  account_id=<永豐金帳號>
  

  [gcp]
  ...
  SUBSCRIPTION=< 填入你的代理機名字 >
  GOOGLE_APPLICATION_CREDENTIALS=< 填入你的金鑰檔(.json)路徑 >
  
  
  [logging]
  log_file_path=< 此處留白 >
  log_level=INFO


  ```

### 建立代理機起動檔 (start.sh)

c:\vagrant_data\<代理程式名稱>\start.sh


### 修改代理機起動檔 (start.sh)

```

docker run --rm \
       -v /vagrant_data/<代理程式名稱>/config:/app/config  \
       gcr.io/etensword-order-agent/agent-app:latest 

```


## Install VirtualBox

下載: https://www.virtualbox.org/wiki/Downloads

選擇 Windows hosts

Next > Next > Next > ... (use default value)




## Install Vagrant 及 Centos-7-Docker VM

### 下載: https://www.vagrantup.com/downloads

選擇 Windows 64-bit

安裝: Next > Next > Next > ... (use default value)

Restart windows


### 開啟命令列視窗 Command Prompt

### 切換目錄

cd c:\vagrant

### 檢查 Vagrant 是否安裝好

```
c:\vagrant>vagrant version
Installed Version: 2.2.9
Latest Version: 2.2.9

You're running an up-to-date version of Vagrant!
```

### 執行 vagrant init

```
c:\vagrant>vagrant init genebean/centos-7-docker-ce --box-version 2.3.20190814


A `Vagrantfile` has been placed in this directory. You are now
ready to `vagrant up` your first virtual environment! Please read
the comments in the Vagrantfile as well as documentation on
`vagrantup.com` for more information on using Vagrant.
```

### 確認 Vagrantfile 有生成

```
c:\vagrant>dir
 Volume in drive C is Windows
 Volume Serial Number is 227D-9D9A

 Directory of c:\vagrant

08/01/2020  04:14 AM    <DIR>          .
08/01/2020  04:14 AM    <DIR>          ..
08/01/2020  04:14 AM             3,080 Vagrantfile
               1 File(s)          3,080 bytes
               2 Dir(s)  122,354,421,760 bytes free
```

### 編輯 Vagrantfile

```
  # Create a private network, which allows host-only access to the machine
  # using a specific IP. 


  config.vm.network "private_network", ip: "192.168.33.10"



  # Share an additional folder to the guest VM. The first argument is
  # the path on the host to the actual folder. The second argument is
  # the path on the guest to mount the folder. And the optional third
  # argument is a set of non-required options.

  
  config.vm.synced_folder "c:/vagrant_data", "/vagrant_data"



  # Provider-specific configuration so you can fine-tune various
  # backing providers for Vagrant. These expose provider-specific options.
  # Example for VirtualBox:


  
  config.vm.provider "virtualbox" do |vb|
     # Display the VirtualBox GUI when booting the machine
     # vb.gui = true
  
     # Customize the amount of memory on the VM:

     # 如果RAM夠的話, 可以放大一點, 比如4096 or 8192
     vb.memory = "1024"       
  end

  
```


### 啟動 Vagrant

```
c:\vagrant>vagrant up

……….
……….
………. (wait for a while)

Virtualbox on your host claims:   6.0.10
VBoxService inside the vm claims: 5.2.18
Going on, assuming VBoxService is correct...
==> default: Checking for guest additions in VM...
==> default: Configuring and enabling network interfaces...
    default: SSH address: 127.0.0.1:2222
    default: SSH username: vagrant
    default: SSH auth method: private key
==> default: Mounting shared folders...
    default: /vagrant => C:/roger_lo/Vagrant_VM/centos-7-docker-ce
    default: /vagrant_data => C:/vagrant_data
```


### 登入 vagrant

```
c:\vagrant>vagrant ssh

Last failed login: Wed Aug 14 13:31:57 EDT 2019 from 10.0.2.2 on ssh:notty
There was 1 failed login attempt since the last successful login.
                  ____             __                ____________
                 / __ \____  _____/ /_____  _____   / ____/ ____/
                / / / / __ \/ ___/ //_/ _ \/ ___/  / /   / __/
               / /_/ / /_/ / /__/ ,< /  __/ /     / /___/ /___
              /_____/\____/\___/_/|_|\___/_/      \____/_____/

             __             ______                ____
            / /_  __  __   / ____/__  ____  ___  / __ )___  ____ _____
           / __ \/ / / /  / / __/ _ \/ __ \/ _ \/ __  / _ \/ __ `/ __ \
          / /_/ / /_/ /  / /_/ /  __/ / / /  __/ /_/ /  __/ /_/ / / / /
         /_.___/\__, /   \____/\___/_/ /_/\___/_____/\___/\__,_/_/ /_/
               /____/
                        Created on Wed August 14, 2019
```


### 檢查 docker 有裝好

```
~ » docker version                                                                              

Client: Docker Engine - Community
 Version:           19.03.1
 API version:       1.40
 Go version:        go1.12.5
 Git commit:        74b1e89
 Built:             Thu Jul 25 21:21:07 2019
 OS/Arch:           linux/amd64
 Experimental:      false

Server: Docker Engine - Community
 Engine:
  Version:          19.03.1
  ….…. 
```


### 檢查相關設定

```

> cd /vagrant_data/代理程式名稱>/

> ls -al

  < 應有 start.sh >

> ls -al /vagrant_data/代理程式名稱>/config/

  < 應有 agent_key.json, agent_settings.ini, Sinopac.pfx >


```

### 啟動代理程式

```

> cd /vagrant_data/<代理程式名稱>/

> sh start.sh

Get ini_file path from environment variable ETENSWORD_AGENT_CONF => /app/config/agent_settings.ini
2020-08-01 13:53:08,596 - INFO - [EtenSwordAgent-20.0725.00] Order agent type: shioaji_api
2020-08-01 13:53:08,602 - INFO - [EtenSwordAgent-20.0725.00] Listening for messages on projects/EtenSword/subscriptions/<代理程式名稱>..

```


### 測試

* 登入 https://web.etensword.com , 使用 Google 帳號看是否能成功登入
* 切換至控制台, 點選[查詢未平倉]按鈕, 檢查代理程式是否成功回應



----

===== 以上步驟只需安裝時做一次, 之後啟動代理程式只需從 _啟動 Vagrant_  這步驟開始即可 =====


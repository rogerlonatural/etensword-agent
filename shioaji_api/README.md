
# 倚天劍代理程式(使用永豐金Shioaji API)安裝說明

## 準備環境

* Windows 10 中文版以上
* 安裝 Vagrant
    * Download: https://www.vagrantup.com/downloads

* 安裝 Anaconda3 (內含 Python3) 並測試成功
    * https://zhuanlan.zhihu.com/p/75717350 (不要裝 Tensorflow)
* 安裝 git for Windows
    * https://git-scm.com/download/win

## 安裝代理程式

* 下載: https://github.com/rogerlonatural/etensword-agent
    * Download ZIP file 到 C:\ 並解壓縮
    * 解壓縮後目錄結構如下:
    
       ```
      C:\etensword-agent-master\
              conf\
              etensword\
              mockApi\
              setup.py
              test_order_agent.py
              requirements.txt
       ```
* 打開 **Anaconda3 prompt**

  ```
  # 檢查Python安裝版本
  (base) C:\Users\roger_lo> python --version
  Python 3.7.6
  
  # 切換到代理程式根目錄
  (base) C:\Users\roger_lo> cd C:\etensword-agent-master\
  
  # 安裝相依套件
  (base) C:\etensword-agent-master> python -m pip install -r requirements.txt
  
  # 安裝代理程式自己
  (base) C:\etensword-agent-master> python setup.py install
  

  ```


## 註冊使用者與代理機
* 提供使用者的 Google 帳號
* 為自己的代理機取個名字(不能與其他代理機相同, 且只能由字母、數字、破折號 (-)、半形句號 (.)、底線 (_)、波浪號 (~)、百分比符號 (%) 或加號 (+) 組成，而且開頭必須為英文字母 (但不得以 goog 為開頭)。)
* 用任意工具產生一組 agent_id (GUID), 並將此 GUID 填入設定檔
    * 參考工具: https://www.uuidgenerator.net/
* 將以上資料交給 Roger 註冊, 註冊完會拿到一個金鑰檔(.json), 須將此金鑰檔存在代理程式能夠讀取到的目錄

## 修改設定檔
* 先選定一目錄用來存放設定檔與金鑰檔, 最好與程式路徑不同, 以免之後更新程式時不慎被覆蓋
* 將範本設定檔(C:\etensword-agent-master\config\agent_settings.ini)與金鑰檔(.json)複製至此目錄
* 修改設定值
  ```
  
  [order_agent]
  agent_id=< 填入你的agent_id(GUID) >
  
  
  [smart_api]
  exec_path=< 填入你的元大 Smart API 執行檔 (Order.exe, GetAccount.exe, ...) 的存放目錄, 結尾要有 \ >
  
  [gcp]
  ...
  SUBSCRIPTION=< 填入你的代理幾名字 >
  GOOGLE_APPLICATION_CREDENTIALS=< 填入你的金鑰檔(.json)路徑 >
  
  
  [logging]
  log_file_path=< 填入你的log檔目錄, 結尾要有 \, 需確定代理程式有寫入權限 >EtenSwordAgent-{date}.log
  log_level=INFO


  ```

## 設定環境變數
* 新增環境變數 ETENSWORD_AGENT_CONF = <你的設定檔路徑>
    * 如何新增環境變數, 請參考: https://www.java.com/zh_TW/download/help/path.xml


----

===== 以上步驟只需安裝時做一次, 之後啟動代理程式只需下面步驟 =====

----


## 啟動代理程式
* 啟動元大 Smart API 並登入
* 打開 **Anaconda3 prompt**

  ```

  # 切換到代理程式之子目錄etensword
  (base) C:\Users\roger_lo> cd C:\etensword-agent-master\etensword\
  
  # 執行代理程式
  (base) C:\etensword-agent-master> python order_agent.py
  
  2020-05-24 21:56:30,033 - INFO - [EtenSwordAgent] Listening for messages on projects/EtenSword/..

  ```

## 測試

* 登入 https://web.etensword.com , 使用 Google 帳號看是否能成功登入
* 切換至控制台, 點選[查詢未平倉]按鈕, 檢查代理程式是否成功回應


## 更新代理程式

* 關閉目前正在執行代理程式的 **Anaconda3 prompt**

* 將原本代理程式目錄更名備份, 如 C:\etensword-agent-master => C:\etensword-agent-<備份日期>

* 下載新版代理程式: https://github.com/rogerlonatural/etensword-agent
    * Download ZIP file 到 C:\ 並解壓縮

* 打開新的 **Anaconda3 prompt**

  ```
  
  (base) C:\Users\roger_lo> python -m pip install --force C:\etensword-agent-master

  # 切換至代理程式目錄
  (base) C:\Users\roger_lo> CD C:\etensword-agent-master
  
  # 執行代理程式
  (base) C:\etensword-agent-master> python .\etensword\order_agent.py  
  
  
  # 檢查執行結果確定版號日期 [EtenSwordAgent-xx.xxx.xx] 是否更新 
  
  2020-06-03 22:31:54,747 - INFO - [EtenSwordAgent-20.0603.00] Listening for messages on projects/EtenSword/subscriptions/....
  
  
  ```
  
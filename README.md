#倚天劍代理程式安裝說明

## 準備環境

* Windows 10 中文版以上
* 安裝元大 Smart API 並開通下單 API 權限
    * https://www.yuantafutures.com.tw/file-repository/content/smartAPI/page1.html
* 安裝 Anaconda3 (內含 Python3) 並測試成功
    * https://zhuanlan.zhihu.com/p/75717350 (不要裝 Tensorflow)


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
  
  # 切換到代理程式目錄
  (base) C:\Users\roger_lo> cd C:\etensword-agent-master\
  
  # 安裝相依套件
  (base) C:\etensword-agent-master> pip install -r requirements.txt
  
  # 安裝代理程式自己
  (base) C:\etensword-agent-master> python setup.py install
  

  ```


## 註冊使用者與代理機
* 提供使用者的 Google 帳號
* 為自己的代理機取個名字(不能與其他代理機相同)
* 用任意工具產生一組 agent_id (GUID), 並將此 GUID 填入設定檔
    * 參考工具: https://www.uuidgenerator.net/
* 將以上資料交給 roger 註冊並取得金鑰檔(.json), 須將此金鑰檔存在代理程式能夠讀取到的目錄

## 修改設定檔
* 

## 設定環境變數




===== 以上步驟只需做一次, 之後啟動代理程式只需下面步驟 =====

----


## 啟動代理程式


* 測試


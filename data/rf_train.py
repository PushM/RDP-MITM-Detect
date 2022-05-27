# 导入包
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import GridSearchCV
import matplotlib.pyplot as plt
import time
import pickle
import numpy as np
import pandas as pd
if(__name__ == '__main__'):
      cc_data = pd.read_csv('mitm.csv')
      cc_data.head()
      data = cc_data.iloc[:,:-1]
      lable = cc_data.iloc[:,-1]

      Xtrain, Xtest, Ytrain, Ytest = train_test_split(data,lable,test_size=0.5)
      clf = DecisionTreeClassifier(random_state=0)
      rfc = RandomForestClassifier(random_state=0)
      clf = clf.fit(Xtrain,Ytrain)
      rfc = rfc.fit(Xtrain,Ytrain)
      score_c = clf.score(Xtest,Ytest)
      score_r = rfc.score(Xtest,Ytest)
      print("Single Tree:{}".format(score_c),"Random Forest:{}".format(score_r))
      # 保存模型
      with open('rdpmitm_rfc.pickle', 'wb') as f:
            pickle.dump(rfc,f)
      # rfc_l = []
      # clf_l = []
      # for i in range(10):
      #       rfc = RandomForestClassifier(n_estimators=25)
      #       rfc_s = cross_val_score(rfc,data,lable,cv=10).mean()
      #       rfc_l.append(rfc_s)
      #       clf = DecisionTreeClassifier()
      #       clf_s = cross_val_score(clf,data,lable,cv=10).mean()
      #       clf_l.append(clf_s)
      # plt.plot(range(1,11),rfc_l,label = "Random Forest")
      # plt.plot(range(1,11),clf_l,label = "Decision Tree")
      # plt.legend()
      # plt.show()
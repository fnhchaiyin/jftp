#-*- coding: utf-8 -*-
import os
import time
import re
from ftplib import FTP
class Xfer(object):
    '''''
    @note: upload local file or dirs recursively to ftp server
    '''
    def __init__(self):
        self.ftp = FTP()
        self.connected=False
        try:
            os.mkdir(os.getcwd()+'/log')
        except Exception as e:
            print e
        self.today=time.strftime("%Y-%m-%d")
        self.log_file=open('./log/%s.log' % self.today,'a')
    def log_save(self,comment):
        self.log_file.write(time.strftime("%Y-%m-%d_%H:%M:%S:")+str(comment)+'\n')
        #log_file.flush()
        #print (comment)
    def setFtpParams(self, ip, uname, pwd, port = 21, timeout = 60,expire_day=0,exclude=[],isdelete=False,delete_from_server=False):
        self.ip = ip
        self.uname = uname
        self.pwd = pwd
        self.port = port
        self.timeout = timeout
        self.expire_day=expire_day
        self.exclude=exclude
        self.isdelete=isdelete
        self.delete_from_server=delete_from_server
    def is_expire(self,file=''):
        ex=time.time()-os.stat(file).st_mtime
        if ex>(self.expire_day * 24 * 3600):
            return True
        else:
            return False
    def delfile(self,file=''):
        if self.isdelete:
            self.log_save('try to delete local file:%s' % file)
            try:
                os.remove(file)
                self.log_save('+++ delete file:%s success!' % (file))
            except Exception as e:
                self.log_save('+++ delete file:%s failed!' % (file))
                self.log_save(e)
    def delfromserver(self,src=''):
        try:
            self.log_save('try to delete file from server:%s' % src)
            self.ftp.delete(src)
            self.log_save('delete file from server:%s success' % src)
        except Exception as e:
            self.log_save('delete file failed:%s' %src)
    def is_include(self,file_path):
        if not self.exclude:
            return True
        for i in self.exclude:
            r = re.findall(i, file_path)
            if r:
                return False
            else:
                return True
    def initEnv(self):
        try:
            self.log_save('### connect ftp server: %s ...'%self.ip)
            self.ftp.connect(host=self.ip, port=self.port)
            self.ftp.login(self.uname, self.pwd)
            self.log_save(self.ftp.getwelcome())
        except Exception as e:
            self.log_save(e)
            self.log_save('login ftp server failed!')

    def clearEnv(self):
        if self.connected:
            self.ftp.close()
            self.log_save('### disconnect ftp server: %s!'%self.ip)
            self.connected = False

    def rm_dir(self,localdir):
        if self.isdelete:
            try:
                os.rmdir(localdir)
                self.log_save('remove folder:%s success' % localdir)
            except Exception as e:
                self.log_save('remove folder:%s failed' % localdir)
                self.log_save(e)
#上传
    def send_file(self,file):
        if self.is_expire(file=file) and self.is_include(file_path=file):
            try:
                outf=open(file, 'rb')
                self.ftp.storbinary('STOR ' + file,outf,1024)
                outf.close()
                self.log_save('+++ upload file:%s success!' % file)
            except Exception as e:
                self.log_save('+++ upload file:%s failed!' % file)
                self.log_save(e)
            self.delfile(file=file)
    def uploadDir(self, dir='.'):
        if self.is_include(file_path=dir):
            if dir in self.ftp.nlst():
                self.ftp.cwd(dir)
            else:
                self.ftp.mkd(dir)
                self.ftp.cwd(dir)
            os.chdir(dir)
            list = os.listdir('.')
            for file in list:
                if os.path.isfile(file):
                    self.send_file(file)
                if os.path.isdir(file):
                    self.uploadDir(file)
            self.ftp.cwd('..')
            os.chdir('..')
            self.rm_dir(localdir=dir)

    def upload(self, src='.',rsrc='.'):
        if self.connected:
            try:
                os.chdir(os.path.split(src)[0])
            except Exception as e:
                self.log_save(e)
                return
            try:
                self.ftp.cwd(rsrc)
            except Exception as e:
                self.log_save(e)
                return
            if os.path.isfile(src):
                self.send_file(file=os.path.split(src)[1])
            if os.path.isdir(src):
                name = os.path.split(src)[-1]
                try:
                    os.chdir(src)
                    os.chdir('..')
                except Exception as e:
                    self.log_save(e)
                self.uploadDir(dir=name)
##下载
    def get_file(self,remotefile):
        if self.is_include(file_path=remotefile):
            try:
                outf=open(remotefile, "wb").write
                self.ftp.retrbinary('RETR ' + remotefile, outf,1024)
                # self.ftp.delete(remotefile)
                self.log_save('+++ get file:%s success!' % remotefile)
            except Exception as e:
                self.log_save('+++ get file:%s failed!' % remotefile)
                self.log_save(e)
            if self.delete_from_server:
                self.delfromserver(src=remotefile)
    def download_dir(self,rsrc=''):
        if self.is_include(file_path=rsrc):
            if rsrc in os.listdir('.'):
                os.chdir(rsrc)
            else:
                try:
                    os.mkdir(rsrc)
                except Exception as e:
                    self.log_save(e)
                os.chdir(rsrc)
            self.ftp.cwd(rsrc)
            dirs = []
            files = []
            def walk_dir(line):
                if line.startswith('d'):
                    dirs.append(line.split()[-1])
                if line.startswith('-'):
                    files.append(line.split()[-1])
            self.ftp.retrlines('LIST ', callback=walk_dir)
            for i in dirs[2:]:
                self.download_dir(rsrc=i)
            for n in files:
                self.get_file(remotefile=n)
            try:
                self.ftp.cwd('..')
            except Exception as e:
                self.log_save(e)
            if self.delete_from_server:
                try:
                    self.ftp.rmd(rsrc)
                except Exception as e:
                    self.log_save(e)
            os.chdir('..')
    def download(self, src='.', rsrc='.'):
        if self.connected:
            os.chdir(src)
            self.ftp.cwd(os.path.split(rsrc)[0])
            dirs = []
            files = []
            def walk_dir(line):
                if line.startswith('d'):
                    dirs.append(line.split()[-1])
                if line.startswith('-'):
                    files.append(line.split()[-1])
            self.ftp.retrlines('LIST ', callback=walk_dir)
            if os.path.split(rsrc)[1] in dirs:
                self.download_dir(rsrc=os.path.split(rsrc)[1])
            if os.path.split(rsrc)[1] in files:
                self.get_file(os.path.split(rsrc)[1])
if __name__ == '__main__':
    date=time.strftime("%Y%m%d")
    xfer = Xfer()
    xfer.setFtpParams(ip='127.0.0.1', uname='ftp', pwd='ftp', port = 21, timeout = 60,expire_day=0,exclude=[],isdelete=False,delete_from_server=False)
    #expire_day 过期时间，设置过期时间为30，将会传送30天前的文件，如设置为0或不设置将传送所有文件
    #isdelete 传送后删除本地文件，True为删除，False为保留
    #exclude 按文件名排除文件，['tar.gz','tmp']将不对文件名中包含tar.gz或tmp的文件进行传送和删除
    #delete_from_server 下载后从服务器上删除
    #上传，src为本地目录/文件，rsrc为目的目录/文件
    xfer.initEnv()
    xfer.upload(src='/tmp/tt',rsrc='/a/a')
    #下载，src为本地目录，rfile为远程文件
    # xfer.download(src='/tmp',rsrc='.')
    # xfer.download(src='/tmp',rsrc='/f/b/tt')
    xfer.clearEnv()
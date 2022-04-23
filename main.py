import ftplib
import os
import sys
import math
import json

class main:
    ftp = None
    host=""
    user=""
    password=""
    home=""
    sizeWritten = 0
    totalSize = 0
    def __init__(self):
        file = open(".env")
        for line in file:
            value = line.split(":")[1].replace("\n","")
            key = line.split(":")[0]
            if(key=="host"):
                self.host = value
            elif(key=="user"):
                self.user=value
            elif(key=="password"):
                self.password=value
                
            elif(key=="home"):
                self.home=value

    def connect(self):
        self.ftp = ftplib.FTP(self.host)
        self.ftp.login(self.user, self.password)

        data = []
        self.ftp.cwd(self.home)
        self.ftp.dir(data.append)

    def exists(self,path):
        filename = os.path.basename(path)
        if(not os.path.exists(path.replace(filename,""))):
            return False
        files = os.listdir(path.replace(filename,""))
       
        for f in files:
            if(f == filename):
                return True
        return False

    def getListOfNames(self,show):
        files = []
        try:
            self.ftp.cwd(self.home)
            self.ftp.cwd(""+show)
            files = self.ftp.nlst()
            self.ftp.cwd("..")
        except ftplib.error_perm as resp:
            if str(resp) == "550 No files found":
                print("No files in this directory")
            else:
                raise
        files.remove(".")
        files.remove("..")
        files.remove("info.json")
        return files


    def getFile(self, path):
        if(not self.exists(path)):
            filename = os.path.basename(path)
            if not os.path.exists(path.replace(filename,"")):
                os.makedirs(path.replace(filename,""))
            self.ftp.retrbinary("RETR " + path ,open(""+path, 'wb').write)
        else:
            print("")

    def disconect(self):
        self.ftp.quit()

    def listfolder(self,path):
        files = []
        try:
            self.ftp.cwd(""+path)
            files = self.ftp.nlst()
            self.ftp.cwd("..")
        except ftplib.error_perm as resp:
            if str(resp) == "550 No files found":
                print("No files in this directory")
            else:
                raise
        i = 1
        for f in files:
            if(f != "." and f != ".." and f[0]!="." and f != "info.json"):
                print("Episode: "+str(i)+": "+f)
                i+=1

    def handle(self,block):
        self.sizeWritten += 1024
        percentComplete = self.sizeWritten / self.totalSize
        print(str(math.floor((self.sizeWritten / self.totalSize)*100))+" %")

    def setTotalSize(self,path):
        files = os.listdir(path)
        os.chdir(path)
        for f in files:
            if os.path.isfile(path + r'/{}'.format(f)):
                self.totalSize += os.path.getsize(f)
            elif os.path.isdir(path + r'/{}'.format(f)):
                self.setTotalSize(path + r'/{}'.format(f))
        os.chdir('..')

    def uploadfolder(self,path):
        self.setTotalSize(path)
        files = os.listdir(path)
        os.chdir(path)
        for f in files:
            if os.path.isfile(path + r'/{}'.format(f)):
                fh = open(f, 'rb') 
                self.ftp.storbinary('STOR %s' % f, fh,callback=self.handle,blocksize=1024)
                fh.close()
            elif os.path.isdir(path + r'/{}'.format(f)):
                self.ftp.mkd(f)
                self.ftp.cwd(f)
                self.uploadfolder(path + r'/{}'.format(f))
        self.ftp.cwd('..')
        os.chdir('..')
        
    def uploadShow(self,path,name=None,episodes="",season="",discription="",lastWatched="0"):
        if(name==None):
            name = os.path.basename(path)

        self.ftp.mkd(name)
        self.ftp.cwd(name)
        self.uploadfolder(path)
        infoJson = '{"name":"'+name+'","season":"'+str(season)+'","episodes":"'+str(episodes)+'","discription":"'+discription+'","lastWatched":"'+lastWatched+'"}'
        tempInfo = open("info.json","w")
        tempInfo.write(infoJson)
        tempInfo.close()
        fh = open("info.json", 'rb')
        self.ftp.cwd("/alfred/torrents/"+name)
        self.ftp.storbinary('STOR %s' % "info.json", fh)

    def getInfo(self,show):
        self.getFile(show+"/info.json")
        return json.loads(open(show+"/info.json","r").read())
    
    def updateInfo(self,show,key,value):
        info = self.getInfo(show)
        info[key] = value
        file = open(show+"/info.json","w")
        file.write(json.dumps(info))
        file.close()
        self.uploadFile(show+"/info.json")


    def uploadFile(self, path):
        fh = open(path, 'rb') 
        self.ftp.storbinary('STOR %s' % path, fh,blocksize=1024)

def createDir(path):
    if not os.path.exists(path):
        os.makedirs(path)


def updateLastWatch(ftp,show):

    file = show.split("/")[len(show.split("/"))-1]
    show = show.replace("/"+file,"")

    ftp.updateInfo(show,"lastWatched",file)
    

m = main()
m.connect()
USER = os.environ['HOME']

upload = False
discription = ""
name=None
episodes=""
season=""
discription=""
path=""

play = False
episode = ""
show = ""

List = False
listpath = "."

i = 0
for arg in sys.argv:
    
    if(arg=="-u"):
        upload = True
        path = sys.argv[i+1]
    
    if(arg=="-p"):
        play = True
        show = sys.argv[i+1]
    
    if(arg=="-l"):
        List = True
        try:
            listpath = sys.argv[i+1]
        except:
            listpath = "."

    if(arg == "-w"):
        print("You watched %s last time " % m.getInfo(sys.argv[i+1])["lastWatched"])

    if(upload==True):
        if(arg=="--discription"):
            discription = sys.argv[i+1]
        elif(arg=="--name"):
            name = sys.argv[i+1]
        elif(arg=="--episodes"):
            episodes = sys.argv[i+1]
        elif(arg=="--season"):
            season = sys.argv[i+1]
        
    i+=1


if(upload==True):
    m.uploadShow(path,name,episodes,season,discription)

if(play):
    
    file = show.split("/")[len(show.split("/"))-1]
    
    try:
        episode = int(file)
        episodename=(m.getListOfNames(show.replace("/"+file,""))[episode-1])
        show = show.replace(file,episodename)
        file=episodename
    except:
        try:
            last = m.getInfo(show)["lastWatched"]
            i = 1
            episodes = m.getListOfNames(show)
            for f in episodes:
                if(f==last and i < len(episodes)):
                    show += "/"+episodes[i]
                    file = episodes[i]
                if(i >= len(episodes)):
                    print("You have watched all the episodes")
                i+=1
        except:
            print("error :(")
    try:
        print("playing %s" %file)
        m.getFile(show)
        os.system("vlc "+show.replace(file,"'")+file+"'")
        updateLastWatch(m,show)
    except:
        print("idk")
    

if(List):
    m.listfolder(listpath)

m.disconect()

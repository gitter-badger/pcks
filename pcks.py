import sys, os, re, traceback
import urllib.request as dllib

version = "1.2 Alpha"
mirror = "http://stones.ddns.net/mirror"

sysbitset = "x86"

def incUsage():
    print("Incorrect usage.")
    print("""Check "pcks help" for more information""")
    exit()

def shelp():
    print("PackedStone Version " + version)
    print()
    print("Usage:")
    print("pcks install <PACKAGE> : Installs a package")
    print("pcks update : Updates all packages")
    print("pcks source <PACKAGE>: Downloads the sourcecode")
    print()

def updateSysInfo():
    if(sys.maxsize > 2**32):
        sysbitset = "x64"

def mkdirs(path):
    if(os.path.exists(path)):
        pass
    else:
        os.makedirs(path)

def download(url):
    request = dllib.urlopen(url)
    file = request.read()
    return file

def getNewPkglist(url):

    print("Updating PKGList from " + str(url))

    """try:"""
    request = dllib.urlopen(url + "/PKGLIST")
    pkglist = request.read().decode("UTF-8")

    """except:
        print("Could not get PKGList for reason: ")
        traceback.print_exception()"""

    try:
        oldfile = open("/etc/pcks/pkglist.list", "r")
        oldlist = oldfile.read()
        oldfile.close()
        
        file = open("/etc/pcks/pkglist.list", "w")
        file.truncate()
        file.write(pkglist)
        file.close()
    except:
        print("Could not write PKGlist file. Are you root?")
        exit()

def install(package, url):

    installedfile = open("/etc/pcks/installed.list", "r")
    installed = installedfile.read().splitlines()
    installedfile.close()

    rightline = ""
    
    for line in installed:
        if(package in line):
            print("You have already installed " + str(package))
            exit()
    
    getNewPkglist(url)
    
    file = open("/etc/pcks/pkglist.list", "r")
    pkglist = file.read().splitlines()
    file.close()

    foundPkg = False
    locpkg = ""
    
    for pkg in pkglist:
        if(package in pkg):
            locpkg = pkg
            foundPkg = True

    if(foundPkg != True):
        print("Could not locate package " + str(package))
        exit()

    pkgurls = locpkg.split()

    pathx86 = pkgurls[1]
    pathx64 = pkgurls[2]

    pkgpath = ""

    if(sysbitset == "x64" and pathx64 != "no_x64"):
        pkgpath = url + "/" + pathx64
        pkginfo = download(url + "/" + pathx64 + "PKGINFO").decode("UTF-8")
    else:
        pkgpath = url + "/" + pathx86
        pkginfo = download(url + "/" + pathx86 + "PKGINFO").decode("UTF-8")

    pkginfo = pkginfo.split("\n")

    pkgname = ""
    pkgautor = ""
    pkglicense = ""
    pkgversion = ""

    pkgbinarys = []
    pkgsupportfiles = []
    pkgsos = []
    pkgsources = []

    for line in pkginfo:
        if("PKGNAME" in line):
            lineargs = line.split()
            pkgname = lineargs[1]
        elif("PKGAUTH" in line):
            lineargs = line.split()
            pkgautor = lineargs[1]
        elif("PKGLICNS" in line):
            lineargs = line.split()
            pkglicense = lineargs[1]
        elif("PKGVERS" in line):
            lineargs = line.split()
            pkgversion = lineargs[1]
        elif("BINARYS" in line):
            lineargs = line.split()
            for binary in lineargs[1:]:
                pkgbinarys.append(binary)
        elif("SUPPORTFILES" in line):
            lineargs = line.split()
            for supfile in lineargs[1:]:
                pkgsupportfiles.append(supfile)
        elif("SHAREDOBJECTS" in line):
            lineargs = line.split()
            for so in lineargs[1:]:
                pkgsos.append(so)
        elif("SOURCES" in line):
            lineargs = line.split()
            for source in lineargs[1:]:
                pkgsources.append(source)
        else:
            pass
    
    print("You are about to install this package:")
    print()
    print("Name: " + pkgname)
    print("Version: " + pkgversion)
    print("Autor: " + pkgautor)
    print("License: " + pkglicense)
    print()
    cont = str(input("Do you want to continue? [Y/N] "))
    print()
    if(cont == "N" or cont == "n"):
        print("Aborted")
        exit()

    installedfiles = []
    
    for binary in pkgbinarys:
        bindata = download(pkgpath + str(binary))

        binfile = open("/usr/bin/" + str(binary), "bw")
        binfile.write(bindata)
        binfile.close()

        installedfiles.append("/usr/bin/" + str(binary))
        print("Written executable in /usr/bin/" + str(binary))

        os.system("chmod +x /usr/bin/" + str(binary))

    for so in pkgsos:
        sodata = download(pkgpath + str(so))

        sofile = open("/usr/lib/" + str(so), "bw")
        sofile.write(bindata)
        sofile.close()

        installedfiles.append("/usr/lib/" + str(so))
        print("Written shared object in /usr/lib/" + str(so))

    for rawsupfile in pkgsupportfiles:
        rawsupfile = rawsupfile.replace("(", " ").replace(")", " ").replace("in", "")

        suplist = rawsupfile.split()
        
        supfile = suplist[0]
        suppath = suplist[1]

        supfiledata = download(pkgpath + str(supfile))

        mkdirs(suppath)

        realsupfile = open(str(suppath) + str(supfile), "bw")
        realsupfile.write(supfiledata)
        realsupfile.close()

        installedfiles.append(str(suppath) + str(supfile))
        print("Written supportfile in " + str(suppath) + str(supfile))

    installedstring = str(package) + ": "

    for insfile in installedfiles:
        installedstring += insfile + " "

    installedstring += "\n"

    with open("/etc/pcks/installed.list", "a") as installed:
        installed.write(installedstring)

    print()
    print("Done")
    print()

def remove(package):
    installedfile = open("/etc/pcks/installed.list", "r")
    installed = installedfile.read().splitlines()
    installedfile.close()

    rightline = ""
    
    for line in installed:
        if(package in line):
            rightline = line

    if(rightline == ""):
        print("You dont have package " + str(package) + " installed.")
        exit()

    files = rightline.split()

    print()
    print("You are about to remove package " + str(files[0]).replace(":", "") + " with all its files.")
    desc = str(input("Do you want to continue? [Y/N]"))
    if(desc == "N" or desc == "n"):
        print("Aborted")
        exit()

    print()
    files.remove(files[0])

    for file in files:
        try:
            os.system("rm -f " + str(file))
            print("Removed " + str(file))
        except:
            print("Could not remove file " + str(file))

    installedfile = open("/etc/pcks/installed.list", "r")
    installed = installedfile.read().splitlines()
    installedfile.close()

    installed.remove(rightline)

    newinsfile = ""

    for line in installed:
        newinsfile += line + "\n"

    try:
        installedfile = open("/etc/pcks/installed.list", "w")
        installed = installedfile.write(newinsfile)
        installedfile.close()
    except:
        print("Could not write installed file. Are you root?")
        exit()

    print()
    print("Done")
    print()

def update(package, mirror):
    remove(package)
    install(package, mirror)

def selfupd(url):
    print("Downloading update ...")
    try:
        updatedata = download(url + "/pcks")
    except:
        print("Could not get update from " + url)
        exit()

    print("Installing update ...")
    try:
        updatefile = open("/usr/bin/pcks", "bw")
        updatefile.write(updatedata)
        print("Done \n")
        exit()
    except:
        print("Could not install update. Are you root?")
        exit()

def source(package, url):
    getNewPkglist(url)
    
    file = open("/etc/pcks/pkglist.list", "r")
    pkglist = file.read().splitlines()
    file.close()

    foundPkg = False
    locpkg = ""
    
    for pkg in pkglist:
        if(package in pkg):
            locpkg = pkg
            foundPkg = True

    if(foundPkg != True):
        print("Could not locate package " + str(package))
        exit()

    pkgurls = locpkg.split()

    pathsource = pkgurls[3]

    index = download(url + "/" + pathsource).decode("UTF-8")

    filepattern = re.compile('*.py"')

    filelist = filepattern.findall(index)

    for file in filelist:
        print(file)
    
args = sys.argv
updateSysInfo()

if(len(args) == 1):
    incUsage()
elif(args[1] == "install"):
    
    package = args[2]
    install(package, mirror)
    """except:
        incUsage()
        traceback.print_exception()"""
elif(args[1] == "source"):
    """try:
    package = args[2]
    source(package, mirror)
    except:
        incUsage()
        traceback.print_tb()"""
    print("Not implemented yet.")
elif(args[1] == "update"):
    """try:"""
    package = args[2]
    update(package, mirror)
    """except:
        incUsage()
        traceback.print_tb()"""
elif(args[1] == "remove"):
    """try:"""
    package = args[2]
    remove(package)
    """except:
        incUsage()
        traceback.print_tb()"""
elif(args[1] == "help"):
    shelp()
elif(args[1] == "selfupd"):
    selfupd(mirror)
else:
    shelp()

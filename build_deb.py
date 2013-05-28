#!/usr/bin/python3
'''
Created on 28.05.2013

@author: vlkv
'''
import os
import subprocess
import reggata
import shutil


if __name__ == '__main__':
    
    cwd = os.getcwd()
    assert os.path.exists(os.path.join(cwd, "dist_debian"))
    assert os.path.exists(os.path.join(cwd, "setup.py"))
    assert os.path.exists(os.path.join(cwd, "reggata"))

    subprocess.call(["python3", "setup.py", "sdist"])
    reggataSrcTarballName = "reggata-" + reggata.__version__ + ".tar.gz"
    reggataSrcTarballPath = os.path.join(cwd, "dist", reggataSrcTarballName) 
    assert os.path.exists(reggataSrcTarballPath)

    targetDir = os.path.join(cwd, "dist_debian", "target_dir")
    shutil.rmtree(targetDir)
    os.makedirs(targetDir, exist_ok=True)
    
    reggataSrcOrigTarballName = "reggata_" + reggata.__version__ + ".orig.tar.gz"
    reggataSrcOrigTarballPath = os.path.join(targetDir, reggataSrcOrigTarballName)
    shutil.copy(reggataSrcTarballPath, reggataSrcOrigTarballPath)
    assert os.path.exists(reggataSrcOrigTarballPath)
    
    os.chdir(os.path.join(targetDir))
    subprocess.call(["tar", "-xvzf", reggataSrcOrigTarballName])
    reggataSrcOrigDir = os.path.join(targetDir, "reggata-" + reggata.__version__)
    assert os.path.exists(reggataSrcOrigDir)
    
    shutil.copytree(os.path.join(cwd, "dist_debian", "debian"), 
                    os.path.join(reggataSrcOrigDir, "debian"))
    
    os.chdir(os.path.join(reggataSrcOrigDir, "debian"))
    subprocess.call(["debuild", "-us", "-uc"])
    
    print("Done")




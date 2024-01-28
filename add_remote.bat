
    @echo off
    :: branch change
    git init
    git add .
    git commit -m "update"
    git checkout v.One_Transmission
    git remote add Priyansh-666 https://github.com/Priyansh-666/v.One
    git branch v.One_Transmission
    git push Priyansh-666 v.One_Transmission
    
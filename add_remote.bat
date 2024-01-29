
    @echo off
    :: branch change
    git init
    git add .
    git commit -m "update"
    git checkout v.One_Transmission
    git remote add Fusion-Techsal https://github.com/Fusion-Techsal/v.One
    git branch v.One_Transmission
    git push Fusion-Techsal v.One_Transmission
    
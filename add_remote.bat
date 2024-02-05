
    @echo off
    :: branch change
    git init
    git add .
    git commit -m "update"
    git checkout v.One_GetLiveOptions
    git remote add Fusion-Techsal https://github.com/Fusion-Techsal/v.One
    git branch v.One_GetLiveOptions
    git push Fusion-Techsal v.One_GetLiveOptions
    
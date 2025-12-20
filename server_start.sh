#! /bin/bash
/home/steam/steamcmd/arma3/arma3server_x64 -name=spagistan -config=server.cfg \
        -mod=@cba\;@cuptcore\;@cupmaps\;@ace\;@cigs\;@enhancedmove\;@grad\;@rhsafrf\;@rhsgref\;@rhssaf\;@rhsusaf\;@enhancedmi24\
\;@gymbench\;@crocus\;@bulat\;@tbd\;@2b9\;@d20\;@modernscopes\;@type63\;@mt12\;@cupinteriors\;@rhsmag\
\;@sling\;@safe\;@tfaran\;@tfarb\;@unconactors\;@zeusenhanced\;@crows\;@tohcharacters\;@pronelauncher\;@pinned\;@sla\
        -servermod=@deformer \
        #>>log${pid}.txt 2>&1

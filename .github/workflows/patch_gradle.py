import sys,re
f=sys.argv[1]
c=open(f).read()
if 'signingConfigs' not in c:
    sc='signingConfigs {\n    release {\n        storeFile file(\'whoamisec.keystore\')\n        storePassword System.getenv(\'KS_PASS\') ?: \'WhoamiSec2026\'\n        keyAlias \'whoamisec\'\n        keyPassword System.getenv(\'KS_PASS\') ?: \'WhoamiSec2026\'\n    }\n}\n'
    c=c.replace('buildTypes {',sc+'buildTypes {')
    if 'signingConfig signingConfigs.release' not in c:
        c=c.replace('release {','release {\n            signingConfig signingConfigs.release')
for p,r in [('minSdkVersion\\s+\\d+','minSdkVersion 23'),('targetSdkVersion\\s+\\d+','targetSdkVersion 34'),('compileSdkVersion\\s+\\d+','compileSdkVersion 34')]:
    c=re.sub(p,r,c)
open(f,'w').write(c)
print('Patched')

#!/usr/bin/env bash
read -s -p "Passphrase: " P
export EMAIL_PASSPHRASE="$P"
cd /home/jace/45dgof8/email-agent
node -e "
const crypto=require('crypto'),fs=require('fs');
const blob=JSON.parse(fs.readFileSync('email-credentials.enc.json','utf-8'));
const salt=Buffer.from(blob.salt,'base64'),iv=Buffer.from(blob.iv,'base64'),data=Buffer.from(blob.data,'base64');
try {
  const key=crypto.pbkdf2Sync(process.env.EMAIL_PASSPHRASE,salt,600000,32,'sha256');
  const dec=crypto.createDecipheriv('aes-256-gcm',key,iv);
  dec.setAuthTag(data.subarray(data.length-16));
  JSON.parse(dec.update(data.subarray(0,data.length-16))+dec.final('utf-8'));
  process.exit(0);
} catch(e) { process.exit(1); }
" 2>&1
if [ $? -eq 0 ]; then
  grep -q "EMAIL_PASSPHRASE=" ~/.opencode/secrets.env \
    && sed -i "/EMAIL_PASSPHRASE=/c\export EMAIL_PASSPHRASE='$P'" ~/.opencode/secrets.env \
    || echo "export EMAIL_PASSPHRASE='$P'" >> ~/.opencode/secrets.env
  echo "✅ Saved to secrets.env. Never type it again."
else
  echo "❌ Wrong passphrase"
fi
unset EMAIL_PASSPHRASE P

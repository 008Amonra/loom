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
  const cfg=JSON.parse(dec.update(data.subarray(0,data.length-16))+dec.final('utf-8'));
  console.log('✅ Correct! Accounts:',Object.keys(cfg).join(', '));
} catch(e) { console.log('❌ Wrong passphrase'); }
" 2>&1
unset EMAIL_PASSPHRASE

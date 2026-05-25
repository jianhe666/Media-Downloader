# 一次性运行：创建自签代码签名证书并加入信任存储
# Run once: creates self-signed code signing cert and trusts it

$cert = New-SelfSignedCertificate -Type CodeSigningCert -Subject 'CN=jianhe666' -CertStoreLocation 'Cert:\CurrentUser\My'
$pwd = ConvertTo-SecureString -String 'jianhe666' -Force -AsPlainText
Export-PfxCertificate -Cert $cert -FilePath "$PSScriptRoot\cert.pfx" -Password $pwd

$store = New-Object System.Security.Cryptography.X509Certificates.X509Store 'TrustedPublisher', 'CurrentUser'
$store.Open('ReadWrite'); $store.Add($cert); $store.Close()

$store2 = New-Object System.Security.Cryptography.X509Certificates.X509Store 'Root', 'CurrentUser'
$store2.Open('ReadWrite'); $store2.Add($cert); $store2.Close()

Write-Host "Certificate created and trusted. Publisher: jianhe666"

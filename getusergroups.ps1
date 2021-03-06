Start-Transcript -Path "C:\Users\user\Documents\transcript.txt"

Get-ADUser -SearchBase "OU=AADSync,OU=Users,OU=DW,DC=ad,DC=domain,DC=com" -Filter {(enabled -eq $true) -and (EmailAddress -like "*@emaildomain.com")} -Properties * | Select SamAccountName, EmailAddress, department, stronghold | Sort Name | Select @{Name="First Name";Expression={$_.SamAccountName}},@{Name="Email";Expression={$_.EmailAddress}},@{Name="Last Name";Expression={$_.department}},@{Name="Position";Expression={$_.stronghold}} | Export-CSV -NoTypeInformation -Path "C:\Users\user\Documents\users.csv"

$sourceCSV = "C:\Users\user\Documents\users.csv" ;

$startrow = 0 ;

$counter = 1 ;

$header = Get-Content -Path C:\Users\user\Documents\users.csv -TotalCount 1

$rows = (Import-Csv C:\Users\user\Documents\users.csv).count

Remove-Item C:\Users\user\Documents\tmp\*.*

while ($startrow -lt $rows)
{

Import-CSV C:\Users\user\Documents\users.csv | select-object -skip $startrow -first 280 | Export-CSV "C:\Users\user\Documents\tmp\$($counter).csv" -Force -NoTypeInformation;

$startrow += 280 ;

$counter++ ;

}

aws s3 rm s3://s3-bucket-name/adusers/ --recursive

aws s3 cp --recursive C:\Users\user\Documents\tmp\ s3://s3-bucket-name/adusers/

